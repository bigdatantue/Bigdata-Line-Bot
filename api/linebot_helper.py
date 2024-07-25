from config import Config
from map import DatabaseCollectionMap, DatabaseDocumentMap
from linebot.v3.messaging import (
    ApiClient,
    ApiException,
    MessagingApi,
    MessagingApiBlob,
    ReplyMessageRequest,
    MulticastRequest,
    PushMessageRequest,
    RichMenuRequest,
    URIAction,
    MessageAction,
    PostbackAction,
    RichMenuSwitchAction,
    CreateRichMenuAliasRequest,
    QuickReply,
    QuickReplyItem
)
import requests
import random
import json
import re

config = Config()
configuration = config.configuration
firebaseService = config.firebaseService

class LineBotHelper:
    @staticmethod
    def get_user_info(user_id: str):
        """Returns 使用者資訊
        list: [使用者名稱, 使用者大頭貼]
        """
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            user_info = line_bot_api.get_profile(user_id)
            return [user_info.display_name, user_info.picture_url]
        
    @staticmethod
    def reply_message(event, messages: list):
        """
        回覆多則訊息
        """
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=messages
                )
            )

    @staticmethod
    def multicast_message(user_ids: list, messages: list):
        """
        推播多則訊息給多位user
        """
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.multicast_with_http_info(
                MulticastRequest(
                    to=user_ids,
                    messages=messages
                )
            )

    @staticmethod
    def push_message(user_id: str, messages: list):
        """
        推播多則訊息給一位user
        """
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.push_message_with_http_info(
                PushMessageRequest(
                    to=user_id,
                    messages=messages
                )
            )
    
    @staticmethod
    def generate_id(k: int=20):
        """
        生成ID
        """
        CHARS='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        return ''.join(random.choices(CHARS, k=k))

    @staticmethod
    def map_params(item: dict, map: dict):
        """Returns 根據 map 的 value 對應 item 的 value 重新生成 { map的key: 對應item產生的值 } 的字典
        dict: 對應後的參數 { flex message上設定的變數名稱: 要替換的資料值 }
        """
        params = {}
        for key, value in map.items():
            if callable(value):
                params[key] = value(item)
            else:
                params[key] = item.get(value)
        return params
        
    @staticmethod
    def replace_variable(text: str, variable_dict: dict):
        """Returns 取代變數後的文字 e.g. {{semester}} -> 代表semester是一個變數，取代成variable_dict中key為semester的值
        str: 取代變數後的文字
        """
        def replace(match):
            key = match.group(1)
            return str(variable_dict.get(key, match.group(0)))

        # 匹配 {{variable}} 的正規表達式
        pattern = r'\{\{([a-zA-Z0-9_]*)\}\}'
        replaced_text = re.sub(pattern, replace, text)
        return replaced_text
    
    @staticmethod
    def create_action(action: dict):
        """Returns
        Action: action 物件
        """
        if action['type'] == 'uri':
            return URIAction(uri=action.get('uri'))
        elif action['type'] == 'message':
            return MessageAction(text=action.get('text'), label=action.get('label'))
        elif action['type'] == 'postback':
            return PostbackAction(data=action.get('data'), label=action.get('label'), display_text=action.get('displayText'))
        elif action['type'] == 'richmenuswitch':
            return RichMenuSwitchAction(
                rich_menu_alias_id=action.get('richMenuAliasId'),
                data=action.get('data')
            )
        else:
            raise ValueError('Invalid action type')


# class RichMenuHelper:
    # with ApiClient(configuration) as api_client:
    #     line_bot_api = MessagingApi(api_client)
    #     line_bot_api_blob = MessagingApiBlob(api_client)
    #     # CRUD of rich menu
    #     line_bot_api.create_rich_menu(RichMenuRequest.from_json(
    #         firebaseService.get_data(
    #             DatabaseCollectionMap.RICH_MENU,
    #             DatabaseDocumentMap.RICH_MENU
    #         )
    #     ))
    #     line_bot_api.get_rich_menu('a')
    #     line_bot_api.get_rich_menu_list()
    #     line_bot_api.set_default_rich_menu('a')
    #     line_bot_api.delete_rich_menu('a')
    #     # CRUD of rich menu alias
    #     line_bot_api.create_rich_menu_alias(
    #         CreateRichMenuAliasRequest(
    #             richMenuAliasId='page1',
    #             richMenuId='a'
    #         )
    #     )
    #     line_bot_api.get_rich_menu_alias('page1')
    #     line_bot_api.get_rich_menu_alias_list()
    #     line_bot_api.update_rich_menu_alias(
    #         'page1',
    #         CreateRichMenuAliasRequest(richMenuAliasId='page1', richMenuId='a')
    #     )
    #     line_bot_api.delete_rich_menu_alias('page1')
    #     # CRUD of rich menu image
    #     line_bot_api_blob.get_rich_menu_image('a')
    #     line_bot_api_blob.set_rich_menu_image('a', 'image_path')


class QuickReplyHelper:
    @staticmethod
    def create_quick_reply(quick_reply_data: list[dict]):
        """Returns
        QuickReply: 快速回覆選項
        """
        return QuickReply(
            items=[QuickReplyItem(action=LineBotHelper.create_action(json.loads(item))) for item in quick_reply_data]
        )
    
class FlexMessageHelper:
    @staticmethod
    def create_carousel_bubbles(items: list[dict], line_flex_json: json, params_map: dict = None):
        """ Returns 根據 items 生成並替換 carousel bubbles的變數
        json: carousel bubbles
        """
        bubbles = []
        for item in items:
            # 複製原始的 bubble
            new_bubble = line_flex_json['contents'][0].copy()
            item_params = LineBotHelper.map_params(item, params_map)
            # 在新 bubble 中進行變數替換
            new_bubble = LineBotHelper.replace_variable(json.dumps(new_bubble), item_params)
            
            # 將新 bubble 添加到 bubbles 中
            bubbles.append(json.loads(new_bubble))
        
        # 將生成的 bubbles 放回 line_flex_json 中
        line_flex_json['contents'] = bubbles

        return line_flex_json
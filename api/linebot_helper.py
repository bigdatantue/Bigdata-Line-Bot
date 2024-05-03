from config import Config
from map import DatabaseCollectionMap, DatabaseDocumentMap
from linebot.v3.messaging import (
    ApiClient,
    ApiException,
    MessagingApi,
    MessagingApiBlob,
    ReplyMessageRequest,
    RichMenuRequest,
    RichMenuArea,
    RichMenuSize,
    RichMenuBounds,
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

class RichMenuHelper:
    def create_rich_menu_areas(rich_menu):
        """Returns
        list: 圖文選單的areas
        """
        return [
            RichMenuArea(
                bounds=RichMenuBounds(
                    x=info['bounds']['x'],
                    y=info['bounds']['y'],
                    width=info['bounds']['width'],
                    height=info['bounds']['height']
                ),
                action=LineBotHelper.create_action(info['action'])
            ) for info in rich_menu['areas']
        ]
    
    def create_rich_menu_request(rich_menu, areas):
        """Returns
        RichMenuRequest: 圖文選單的request
        """
        return RichMenuRequest(
            size=RichMenuSize(width=rich_menu['size']['width'], height=rich_menu['size']['height']),
            selected=rich_menu['selected'],
            name=rich_menu['name'],
            chat_bar_text=rich_menu['chatBarText'],
            areas=areas
        )
    
    def set_rich_menu_image(line_bot_blob_api, rich_menu_id, image_url):
        """
        設定圖文選單的圖片
        """
        response = requests.get(image_url)
        if response.status_code != 200:
            raise ValueError('Invalid image url')
        else:
            line_bot_blob_api.set_rich_menu_image(
                rich_menu_id=rich_menu_id,
                body=response.content,
                _headers={'Content-Type': 'image/png'}
            )
    
    def create_rich_menu_alias(line_bot_api, alias_id, rich_menu_id):
        """
        建立圖文選單的alias
        """
        try:
            line_bot_api.delete_rich_menu_alias(alias_id)
        except ApiException as e:
            if e.status != 404:
                raise
        alias = CreateRichMenuAliasRequest(
            rich_menu_alias_id=alias_id,
            rich_menu_id=rich_menu_id
        )
        line_bot_api.create_rich_menu_alias(alias)

    @staticmethod
    def create_rich_menu():
        """
        建立圖文選單
        """
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_blob_api = MessagingApiBlob(api_client)

            # 圖文選單 A
            rich_menu_a_data = firebaseService.get_data(
                DatabaseCollectionMap.RICH_MENU,
                DatabaseDocumentMap.RICH_MENU.get('a')
            )
            rich_menu_a = json.loads(rich_menu_a_data.get('richmenu'))
            rich_menu_a_to_create = __class__.create_rich_menu_request(rich_menu_a, __class__.create_rich_menu_areas(rich_menu_a))

            rich_menu_a_id = line_bot_api.create_rich_menu(rich_menu_request=rich_menu_a_to_create).rich_menu_id
            rich_menu_a_url = rich_menu_a_data.get('image_url')
            __class__.set_rich_menu_image(line_bot_blob_api, rich_menu_a_id, rich_menu_a_url)
            __class__.create_rich_menu_alias(line_bot_api, 'page1', rich_menu_a_id)

            line_bot_api.set_default_rich_menu(rich_menu_a_id)

            # 圖文選單 B
            rich_menu_b_data = firebaseService.get_data(
                DatabaseCollectionMap.RICH_MENU,
                DatabaseDocumentMap.RICH_MENU.get("b")
            )
            rich_menu_b = json.loads(rich_menu_b_data.get('richmenu'))
            rich_menu_b_to_create = __class__.create_rich_menu_request(rich_menu_b, __class__.create_rich_menu_areas(rich_menu_b))
            rich_menu_b_id = line_bot_api.create_rich_menu(rich_menu_request=rich_menu_b_to_create).rich_menu_id
            rich_menu_b_url = rich_menu_b_data.get('image_url')
            __class__.set_rich_menu_image(line_bot_blob_api, rich_menu_b_id, rich_menu_b_url)
            __class__.create_rich_menu_alias(line_bot_api, 'page2', rich_menu_b_id)

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
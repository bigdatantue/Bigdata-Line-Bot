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
    QuickReplyItem,
    ShowLoadingAnimationRequest
)
import requests
import random
import json
import re
import pytz
from datetime import datetime

config = Config()
configuration = config.configuration
firebaseService = config.firebaseService

class LineBotHelper:
    @staticmethod
    def get_user_info(user_id: str):
        """Returns 使用者資訊
        list: [使用者名稱, 使用者大頭貼, 使用者語系, 使用者狀態訊息]
        """
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            user_info = line_bot_api.get_profile(user_id)
            return [user_info.display_name, user_info.picture_url, user_info.language, user_info.status_message]

    @staticmethod
    def show_loading_animation_(event, time: int=10):
        """
        顯示載入動畫
        """
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.show_loading_animation(
                ShowLoadingAnimationRequest(chatId=event.source.user_id, loadingSeconds=time)
            )
        
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
    def get_current_time():
        """Returns
        datetime: 現在時間
        """
        return datetime.now(pytz.timezone('Asia/Taipei'))
    
    @staticmethod
    def convert_timedelta_to_string(timedelta):
        """Returns
        str: 時間字串 (小時:分鐘:秒 e.g. 01:20:43)
        """
        hours = timedelta.days * 24 + timedelta.seconds // 3600
        minutes = (timedelta.seconds % 3600) // 60
        seconds = timedelta.seconds % 60
        hours = hours if len(str(hours)) >= 2 else f'0{hours}'
        minutes = minutes if len(str(minutes)) == 2 else f'0{minutes}'
        seconds = seconds if len(str(seconds)) == 2 else f'0{seconds}'
        return f'{hours}:{minutes}:{seconds}'
    
    @staticmethod
    def generate_id(k: int=20):
        """
        生成ID
        """
        CHARS='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        return ''.join(random.choices(CHARS, k=k))
        
    @staticmethod
    def replace_variable(text: str, variable_dict: dict, max_count: int = 0):
        """Returns 取代變數後的文字 e.g. {{semester}} -> 代表semester是一個變數，取代成variable_dict中key為semester的值
        str: 取代變數後的文字
        """
        def replace(match):
            key = match.group(1)
            return str(variable_dict.get(key, match.group(0)))

        # 匹配 {{variable}} 的正規表達式
        pattern = r'\{\{([a-zA-Z0-9_]*)\}\}'
        replaced_text = re.sub(pattern, replace, text, count=max_count)
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
    @staticmethod
    def set_rich_menu_image_(rich_menu_id, image_url):
        """
        設定圖文選單的圖片
        """
        with ApiClient(configuration) as api_client:
            line_bot_blob_api = MessagingApiBlob(api_client)
            response = requests.get(image_url)
            if response.status_code != 200:
                raise ValueError('Invalid image url')
            else:
                line_bot_blob_api.set_rich_menu_image(
                    rich_menu_id=rich_menu_id,
                    body=response.content,
                    _headers={'Content-Type': 'image/png'}
                )

    @staticmethod
    def create_rich_menu_alias_(alias_id, rich_menu_id):
        """
        建立圖文選單的alias
        """
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
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
    def create_rich_menu_(menu_type, alias_id):
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_blob_api = MessagingApiBlob(api_client)
            # 設定 rich menu image
            rich_menu_str = firebaseService.get_data(
                DatabaseCollectionMap.RICH_MENU,
                DatabaseDocumentMap.RICH_MENU.get(menu_type)
            ).get('richmenu')
            rich_menu_id = line_bot_api.create_rich_menu(
                rich_menu_request=RichMenuRequest.from_json(rich_menu_str)
            ).rich_menu_id
            rich_menu_url = firebaseService.get_data(
                DatabaseCollectionMap.RICH_MENU,
                DatabaseDocumentMap.RICH_MENU.get(menu_type)
            ).get('image_url')
            __class__.set_rich_menu_image_(rich_menu_id, rich_menu_url)
            __class__.create_rich_menu_alias_(alias_id, rich_menu_id)

#-----------------以下為設定rich menu的程式-----------------
# 設定rich menu，並將alias id為page1的rich menu設為預設
# RichMenuHelper.create_rich_menu_('a', 'page1')
# RichMenuHelper.create_rich_menu_('b', 'page2')
# with ApiClient(configuration) as api_client:
#     line_bot_api = MessagingApi(api_client)
#     line_bot_api.set_default_rich_menu(line_bot_api.get_rich_menu_alias('page1').rich_menu_id)


#-----------------以下為sdk提供的方法-----------------
# with ApiClient(configuration) as api_client:
#     line_bot_api = MessagingApi(api_client)
#     line_bot_api_blob = MessagingApiBlob(api_client)
#     # CRUD of rich menu
#     line_bot_api.create_rich_menu(
#         rich_menu_request=RichMenuRequest.from_json(firebaseService.get_data(
#                 DatabaseCollectionMap.RICH_MENU,
#                 DatabaseDocumentMap.RICH_MENU.get('a')
#         ).get('richmenu'))
#     ).rich_menu_id
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
#     response = requests.get(firebaseService.get_data(
#         DatabaseCollectionMap.RICH_MENU,
#         DatabaseDocumentMap.RICH_MENU.get('a')
#     ).get('image_url'))
#     image_content = response.content
#     headers = {'Content-Type': 'image/png'}
#     line_bot_api_blob.set_rich_menu_image(
#         rich_menu_id='richmenu-c88b6b533abd76ac9068cf5296720e60',
#         body=image_content,
#         _headers=headers
#     )
    
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
    def create_carousel_bubbles(items: list[dict], line_flex_json: json):
        """ Returns 根據 items 生成並替換 carousel bubbles的變數
        json: carousel bubbles
        """
        bubbles = []
        for item in items:
            # 複製原始的 bubble
            new_bubble = line_flex_json['contents'][0].copy()
            # 在新 bubble 中進行變數替換
            new_bubble = LineBotHelper.replace_variable(json.dumps(new_bubble), item)
            
            # 將新 bubble 添加到 bubbles 中
            bubbles.append(json.loads(new_bubble))
        
        # 將生成的 bubbles 放回 line_flex_json 中
        line_flex_json['contents'] = bubbles

        return line_flex_json
from config import Config
from linebot.v3.messaging import (
    ApiClient,
    ApiException,
    MessagingApi,
    MessagingApiBlob,
    RichMenuRequest,
    RichMenuArea,
    RichMenuSize,
    RichMenuBounds,
    URIAction,
    MessageAction,
    RichMenuSwitchAction,
    CreateRichMenuAliasRequest
)
config = Config()
configuration = config.configuration

class RichMenuHelper:
    def rich_menu_a_json():
        return {
            "size": {
                "width": 2500,
                "height": 1686
            },
            "selected": True,
            "name": "圖文選單 1",
            "chatBarText": "查看更多資訊",
            "areas": [
                {
                "bounds": {
                    "x": 0,
                    "y": 0,
                    "width": 832,
                    "height": 841
                },
                "action": {
                    "type": "richmenuswitch",
                    "richMenuAliasId": "richmenu-alias-b",
                    "data": "richmenu-changed-to-b"
                }
                },
                {
                "bounds": {
                    "x": 832,
                    "y": 0,
                    "width": 836,
                    "height": 841
                },
                "action": {
                    "type": "message",
                    "text": "證書申請流程"
                }
                },
                {
                "bounds": {
                    "x": 1665,
                    "y": 0,
                    "width": 832,
                    "height": 841
                },
                "action": {
                    "type": "message",
                    "text": "詳細課程介紹"
                }
                },
                {
                "bounds": {
                    "x": 0,
                    "y": 841,
                    "width": 836,
                    "height": 845
                },
                "action": {
                    "type": "message",
                    "text": "社群學習資源"
                }
                },
                {
                "bounds": {
                    "x": 832,
                    "y": 841,
                    "width": 836,
                    "height": 845
                },
                "action": {
                    "type": "message",
                    "text": "輔導預約"
                }
                },
                {
                "bounds": {
                    "x": 1665,
                    "y": 841,
                    "width": 832,
                    "height": 845
                },
                "action": {
                    "type": "message",
                    "text": "主功能選單"
                }
                }
            ]
        }

    def rich_menu_b_json():
        return {
            "size": {
                "width": 2500,
                "height": 1686
            },
            "selected": False,
            "name": "圖文選單 2",
            "chatBarText": "查看更多資訊",
            "areas": [
                {
                "bounds": {
                    "x": 100,
                    "y": 106,
                    "width": 662,
                    "height": 662
                },
                "action": {
                    "type": "richmenuswitch",
                    "richMenuAliasId": "richmenu-alias-a",
                    "data": "richmenu-changed-to-a"
                }
                },
                {
                "bounds": {
                    "x": 921,
                    "y": 106,
                    "width": 658,
                    "height": 662
                },
                "action": {
                    "type": "message",
                    "text": "證書申請流程"
                }
                },
                {
                "bounds": {
                    "x": 1765,
                    "y": 106,
                    "width": 661,
                    "height": 662
                },
                "action": {
                    "type": "message",
                    "text": "詳細課程介紹"
                }
                },
                {
                "bounds": {
                    "x": 103,
                    "y": 915,
                    "width": 662,
                    "height": 662
                },
                "action": {
                    "type": "message",
                    "text": "社群學習資源"
                }
                },
                {
                "bounds": {
                    "x": 918,
                    "y": 915,
                    "width": 661,
                    "height": 662
                },
                "action": {
                    "type": "message",
                    "text": "輔導預約"
                }
                },
                {
                "bounds": {
                    "x": 1762,
                    "y": 909,
                    "width": 662,
                    "height": 663
                },
                "action": {
                    "type": "message",
                    "text": "主功能選單"
                }
                }
            ]
        }

    def create_action(action):
        """
        建立圖文選單的action
        """
        if action['type'] == 'uri':
            return URIAction(uri=action.get('uri'))
        elif action['type'] == 'message':
            return MessageAction(text=action.get('text'))
        elif action['type'] == 'richmenuswitch':
            return RichMenuSwitchAction(
                rich_menu_alias_id=action.get('richMenuAliasId'),
                data=action.get('data')
            )
        else:
            raise ValueError('Invalid action type')
        
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
                action=__class__.create_action(info['action'])
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
            chat_bar_text=rich_menu['name'],
            areas=areas
        )
    
    def set_rich_menu_image(line_bot_blob_api, rich_menu_id, image_path):
        """
        設定圖文選單的圖片
        """
        with open(image_path, 'rb') as image:
            line_bot_blob_api.set_rich_menu_image(
                rich_menu_id=rich_menu_id,
                body=bytearray(image.read()),
                _headers={'Content-Type': 'image/png'}
            )
    
    def create_rich_menu_alias(line_bot_api, alias_id, rich_menu_id):
        """
        建立圖文選單的alias
        """
        try:
            line_bot_api.delete_rich_menu_alias(alias_id)
        except ApiException as e:
            if e.status_code != 404:
                raise
        alias = CreateRichMenuAliasRequest(
            rich_menu_alias_id=alias_id,
            rich_menu_id=rich_menu_id
        )
        line_bot_api.create_rich_menu_alias(alias)

    def create_rich_menu():
        """
        建立圖文選單
        """
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_blob_api = MessagingApiBlob(api_client)

            # 圖文選單 A
            rich_menu_a = __class__.rich_menu_a_json()
            rich_menu_a_to_create = __class__.create_rich_menu_request(rich_menu_a, __class__.create_rich_menu_areas(rich_menu_a))

            rich_menu_a_id = line_bot_api.create_rich_menu(rich_menu_request=rich_menu_a_to_create).rich_menu_id
            __class__.set_rich_menu_image(line_bot_blob_api, rich_menu_a_id, 'src/images/richmenu1.png')
            __class__.create_rich_menu_alias(line_bot_api, 'richmenu-alias-a', rich_menu_a_id)

            line_bot_api.set_default_rich_menu(rich_menu_a_id)

            # 圖文選單 B
            rich_menu_b = __class__.rich_menu_b_json()
            rich_menu_b_to_create = __class__.create_rich_menu_request(rich_menu_b, __class__.create_rich_menu_areas(rich_menu_b))
            rich_menu_b_id = line_bot_api.create_rich_menu(rich_menu_request=rich_menu_b_to_create).rich_menu_id
            __class__.set_rich_menu_image(line_bot_blob_api, rich_menu_b_id, 'src/images/richmenu2.png')
            __class__.create_rich_menu_alias(line_bot_api, 'richmenu-alias-b', rich_menu_b_id)
            
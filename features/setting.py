from .base import Feature, register_feature
from linebot.v3.messaging import (
    FlexMessage,
    FlexContainer
)
from map import DatabaseCollectionMap, DatabaseDocumentMap, LIFFSize
from api.linebot_helper import LineBotHelper

@register_feature('setting')
class Setting(Feature):
    """
    設定
    """
    def execute_message(self, event, **kwargs):
        request = kwargs.get('request')
        line_flex_str = self.firebaseService.get_data(
            DatabaseCollectionMap.LINE_FLEX,
            DatabaseDocumentMap.LINE_FLEX.get("setting")
        ).get("select")
        register_url = request.url_root.replace('http:', 'https:') + 'notify/register?state=' + event.source.user_id
        userinfo_url = f'https://liff.line.me/{LIFFSize.TALL.value}/userinfo?userId={event.source.user_id}'
        line_flex_str = LineBotHelper.replace_variable(line_flex_str, {'register_url': register_url, 'userinfo_url': userinfo_url})
        return LineBotHelper.reply_message(event, [FlexMessage(alt_text='選擇設定項目', contents=FlexContainer.from_json(line_flex_str))])

    def execute_postback(self, event, **kwargs):
        pass
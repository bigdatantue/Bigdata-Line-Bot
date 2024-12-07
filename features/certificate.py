from .base import Feature, register_feature
from linebot.v3.messaging import (
    FlexMessage,
    FlexContainer,
    ImageMessage
)
from map import DatabaseCollectionMap
from api.linebot_helper import LineBotHelper

@register_feature('certificate')
class Certificate(Feature):
    """
    證書申請流程
    """
    def execute_message(self, event, **kwargs):
        line_flex_str = self.firebaseService.get_data(
            DatabaseCollectionMap.LINE_FLEX,
            "certificate"
        ).get('summary')
        return LineBotHelper.reply_message(event, [FlexMessage(alt_text='證書申請流程', contents=FlexContainer.from_json(line_flex_str))])

    def execute_postback(self, event, **kwargs):
        params = kwargs.get('params')
        if params.get('type') == 'process':
            image_url = 'https://bigdatalinebot.blob.core.windows.net/linebot/Micro-Credit-Course-Apply-Process.png'
            return LineBotHelper.reply_message(event, [ImageMessage(original_content_url=image_url, preview_image_url=image_url)])
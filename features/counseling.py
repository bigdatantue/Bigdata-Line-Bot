from .base import Feature, register_feature
from linebot.v3.messaging import (
    FlexMessage,
    FlexContainer
)
from map import DatabaseCollectionMap
from api.linebot_helper import LineBotHelper

@register_feature('counseling')
class Counseling(Feature):
    """
    課程諮詢建議
    """
    def execute_message(self, event, **kwargs):
        line_flex_str = self.firebaseService.get_data(
            DatabaseCollectionMap.LINE_FLEX,
            "counseling"
        ).get('select')
        return LineBotHelper.reply_message(event, [FlexMessage(alt_text='課程諮詢/建議', contents=FlexContainer.from_json(line_flex_str))])

    def execute_postback(self, event, **kwargs):
        pass
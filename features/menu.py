from .base import Feature, register_feature
from linebot.v3.messaging import (
    FlexMessage,
    FlexContainer
)
from map import DatabaseCollectionMap
from api.linebot_helper import LineBotHelper

@register_feature('menu')
class Menu(Feature):
    """
    主選單
    """
    def execute_message(self, event, **kwargs):
        line_flex_str = self.firebaseService.get_data(
            DatabaseCollectionMap.LINE_FLEX,
            "menu"
        ).get("main")
        return LineBotHelper.reply_message(event, [FlexMessage(alt_text='主選單', contents=FlexContainer.from_json(line_flex_str))])
        

    def execute_postback(self, event, **kwargs):
        pass
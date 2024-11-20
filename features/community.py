from .base import Feature, register_feature
from linebot.v3.messaging import (
    FlexMessage,
    FlexContainer
)
from map import DatabaseCollectionMap, DatabaseDocumentMap
from api.linebot_helper import LineBotHelper, FlexMessageHelper
import json

@register_feature('community')
class Community(Feature):
    """
    社群學習資源
    """
    def execute_message(self, event, **kwargs):
        line_flex_str = self.firebaseService.get_data(
            DatabaseCollectionMap.LINE_FLEX,
            DatabaseDocumentMap.LINE_FLEX.get("community")
        ).get("summary")
        LineBotHelper.reply_message(event, [FlexMessage(alt_text='社群學習資源', contents=FlexContainer.from_json(line_flex_str))])

    def execute_postback(self, event, **kwargs):
        microcourses = self.spreadsheetService.get_worksheet_data('microcourses')
        line_flex_template = self.firebaseService.get_data(
            DatabaseCollectionMap.LINE_FLEX,
            DatabaseDocumentMap.LINE_FLEX.get("community")
        ).get("microcourse")
        line_flex_json = FlexMessageHelper.create_carousel_bubbles(microcourses, json.loads(line_flex_template))
        line_flex_str = json.dumps(line_flex_json)
        LineBotHelper.reply_message(event, [FlexMessage(alt_text='社群學習資源', contents=FlexContainer.from_json(line_flex_str))])
        return
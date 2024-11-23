from .base import Feature, register_feature
from linebot.v3.messaging import (
    TextMessage,
    FlexMessage,
    FlexContainer
)
from map import DatabaseCollectionMap
from api.linebot_helper import LineBotHelper, FlexMessageHelper
import json

@register_feature('faq')
class FAQ(Feature):
    """
    常見問答
    """
    def execute_message(self, event, **kwargs):
        user_msg = event.message.text
        if user_msg == "常見問答":
            faqs = self.firebaseService.get_collection_data(DatabaseCollectionMap.FAQ)
            for faq in faqs:
                faq['action_text'] = faq['category']
            line_flex_template = self.firebaseService.get_data(
                DatabaseCollectionMap.LINE_FLEX,
                "faq"
            ).get("select")
        else:
            faq_questions = self.firebaseService.get_collection_data(DatabaseCollectionMap.FAQ_QUESTION)
            faqs = [faq for faq in faq_questions if faq['category'] in user_msg]
            line_flex_template = self.firebaseService.get_data(
                DatabaseCollectionMap.LINE_FLEX,
                "faq"
            ).get("question")
        line_flex_json = FlexMessageHelper.create_carousel_bubbles(faqs, json.loads(line_flex_template))
        line_flex_str = json.dumps(line_flex_json)
        return LineBotHelper.reply_message(event, [FlexMessage(alt_text='常見問答', contents=FlexContainer.from_json(line_flex_str))])

    def execute_postback(self, event, **kwargs):
        params = kwargs.get('params')
        id = params.get('id')
        faq_questions = self.firebaseService.get_collection_data(DatabaseCollectionMap.FAQ_QUESTION)
        answer = [faq for faq in faq_questions if faq.get('id') == int(id)][0].get('answer')
        return LineBotHelper.reply_message(event, [TextMessage(text=answer)])
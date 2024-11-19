from config import Config
from map import DatabaseDocumentMap, DatabaseCollectionMap, LIFFSize
from api.linebot_helper import LineBotHelper, QuickReplyHelper, FlexMessageHelper
from linebot.v3.messaging import (
    TextMessage,
    FlexMessage,
    FlexContainer
)
from abc import ABC, abstractmethod
import json

config = Config()
spreadsheetService = config.spreadsheetService
firebaseService = config.firebaseService

class Template(ABC):
    PERMISSION = 1
    @abstractmethod
    def execute(self, event, **kwargs):
        pass

class TemplateFactory:
    def __init__(self):
        self.template_map = {
            'menu': Menu,
            'setting': Setting,
            'course': Course,
            'certificate': Certificate,
            'counseling': Counseling,
            'community': Communtity,
            'equipment': Equipment,
            'quiz': Quiz,
            'faq': FAQ
        }

    def get_template(self, task_name):
        template_class = self.template_map.get(task_name)
        if template_class:
            return template_class
        else:
            print("找不到對應的模板")
            return None

class Menu(Template):
    """
    主選單
    """
    def execute(self, event, **kwargs):
        line_flex_str = firebaseService.get_data('line_flex', DatabaseDocumentMap.LINE_FLEX.get("menu")).get("main")
        LineBotHelper.reply_message(event, [FlexMessage(alt_text='主選單', contents=FlexContainer.from_json(line_flex_str))])

class Setting(Template):
    """
    設定
    """
    def execute(self, event, **kwargs):
        request = kwargs.get('request')
        line_flex_str = firebaseService.get_data('line_flex', 'setting').get('select')
        register_url = request.url_root.replace('http:', 'https:') + 'notify/register?state=' + event.source.user_id
        userinfo_url = f'https://liff.line.me/{LIFFSize.TALL.value}/userinfo?userId={event.source.user_id}'
        line_flex_str = LineBotHelper.replace_variable(line_flex_str, {'register_url': register_url, 'userinfo_url': userinfo_url})
        return LineBotHelper.reply_message(event, [FlexMessage(alt_text='選擇設定項目', contents=FlexContainer.from_json(line_flex_str))])
        
class Course(Template):
    """
    開課修業查詢
    """
    def execute(self, event, **kwargs):
        line_flex_str = firebaseService.get_data('line_flex', DatabaseDocumentMap.LINE_FLEX.get("course")).get("select")
        LineBotHelper.reply_message(event, [FlexMessage(alt_text='開課時間查詢', contents=FlexContainer.from_json(line_flex_str))])

class Certificate(Template):
    """
    證書申請流程
    """
    def execute(self, event, **kwargs):
        line_flex_str = firebaseService.get_data('line_flex', DatabaseDocumentMap.LINE_FLEX.get("certificate")).get('summary')
        LineBotHelper.reply_message(event, [FlexMessage(alt_text='證書申請流程', contents=FlexContainer.from_json(line_flex_str))])

class Counseling(Template):
    """
    課程諮詢建議
    """
    def execute(self, event, **kwargs):
        line_flex_str = firebaseService.get_data(
            DatabaseCollectionMap.LINE_FLEX,
            DatabaseDocumentMap.LINE_FLEX.get("counseling")
        ).get('select')
        LineBotHelper.reply_message(event, [FlexMessage(alt_text='課程諮詢/建議', contents=FlexContainer.from_json(line_flex_str))])

class Communtity(Template):
    """
    社群學習資源
    """
    def execute(self, event, **kwargs):
        line_flex_str = firebaseService.get_data('line_flex', DatabaseDocumentMap.LINE_FLEX.get("community")).get("summary")
        LineBotHelper.reply_message(event, [FlexMessage(alt_text='社群學習資源', contents=FlexContainer.from_json(line_flex_str))])

class Equipment(Template):
    """
    設備租借
    """
    def execute(self, event, **kwargs):
        line_flex_str = firebaseService.get_data('line_flex', DatabaseDocumentMap.LINE_FLEX.get("equipment")).get("select")
        rent_url = f'https://liff.line.me/{LIFFSize.TALL.value}/rent?userId={event.source.user_id}'
        line_flex_str = LineBotHelper.replace_variable(line_flex_str, {'rent_url': rent_url})
        LineBotHelper.reply_message(event, [FlexMessage(alt_text='設備租借', contents=FlexContainer.from_json(line_flex_str))])

class Quiz(Template):
    """
    知識測驗
    """
    def execute(self, event, **kwargs):
        line_flex_str = firebaseService.get_data('line_flex', DatabaseDocumentMap.LINE_FLEX.get("quiz")).get('start')
        LineBotHelper.reply_message(event, [FlexMessage(alt_text='知識測驗', contents=FlexContainer.from_json(line_flex_str))])

class FAQ(Template):
    """
    常見問答
    """
    def execute(self, event, **kwargs):
        user_msg = event.message.text
        if user_msg == "常見問答":
            faqs = spreadsheetService.get_worksheet_data('faqs')
            for faq in faqs:
                faq['action_text'] = faq['category']
            line_flex_template = firebaseService.get_data(
                DatabaseCollectionMap.LINE_FLEX,
                DatabaseDocumentMap.LINE_FLEX.get("faq")
            ).get("select")
            
        else:
            faq_questions = spreadsheetService.get_worksheet_data('faq_questions')
            faqs = [faq for faq in faq_questions if faq['category'] in user_msg]
            line_flex_template = firebaseService.get_data(
                DatabaseCollectionMap.LINE_FLEX,
                DatabaseDocumentMap.LINE_FLEX.get("faq")
            ).get("question")
        line_flex_json = FlexMessageHelper.create_carousel_bubbles(faqs, json.loads(line_flex_template))
        line_flex_str = json.dumps(line_flex_json)
        LineBotHelper.reply_message(event, [FlexMessage(alt_text='常見問答', contents=FlexContainer.from_json(line_flex_str))])
        return
from config import Config
from map import DatabaseDocumentMap
from api.linebot_helper import LineBotHelper, QuickReplyHelper
from linebot.v3.messaging import (
    TextMessage,
    FlexMessage,
    FlexContainer
)
from abc import ABC, abstractmethod

config = Config()
firebaseService = config.firebaseService

class Template(ABC):
    PERMISSION = 1
    @abstractmethod
    def execute(self, event):
        pass

class TemplateFactory:
    def __init__(self):
        self.template_map = {
            'menu': Menu,
            'course': Course,
            'certificate': Certificate,
            'community': Communtity,
            'counseling': Counseling,
            'equipment': Equipment
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
    def execute(self, event):
        line_flex_str = firebaseService.get_data('line_flex', DatabaseDocumentMap.LINE_FLEX.get("menu")).get("main")
        LineBotHelper.reply_message(event, [FlexMessage(alt_text='主選單', contents=FlexContainer.from_json(line_flex_str))])
        
class Course(Template):
    """
    開課時間查詢
    """
    def execute(self, event):
        quick_reply_data = firebaseService.get_data('quick_reply', DatabaseDocumentMap.QUICK_REPLY.get("course")).get("semester")
        LineBotHelper.reply_message(event, [TextMessage(text=quick_reply_data.get('text'), quick_reply=QuickReplyHelper.create_quick_reply(quick_reply_data.get('actions')))])

class Certificate(Template):
    """
    證書申請流程
    """
    def execute(self, event):
        line_flex_str = firebaseService.get_data('line_flex', DatabaseDocumentMap.LINE_FLEX.get("certificate")).get('summary')
        LineBotHelper.reply_message(event, [FlexMessage(alt_text='證書申請流程', contents=FlexContainer.from_json(line_flex_str))])

class Communtity(Template):
    """
    社群學習資源
    """
    def execute(self, event):
        line_flex_str = firebaseService.get_data('line_flex', DatabaseDocumentMap.LINE_FLEX.get("community")).get("summary")
        LineBotHelper.reply_message(event, [FlexMessage(alt_text='社群學習資源', contents=FlexContainer.from_json(line_flex_str))])

class Counseling(Template):
    """
    線上輔導+實體預約
    """
    def execute(self, event):
        line_flex_str = firebaseService.get_data('line_flex', DatabaseDocumentMap.LINE_FLEX.get("counseling")).get("select")
        LineBotHelper.reply_message(event, [FlexMessage(alt_text='線上輔導+實體預約', contents=FlexContainer.from_json(line_flex_str))])

class Equipment(Template):
    """
    設備租借
    """
    def execute(self, event):
        line_flex_str = firebaseService.get_data('line_flex', DatabaseDocumentMap.LINE_FLEX.get("equipment")).get("select")
        LineBotHelper.reply_message(event, [FlexMessage(alt_text='設備租借', contents=FlexContainer.from_json(line_flex_str))])
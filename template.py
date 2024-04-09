from config import Config
from map import DatabaseDocumentMap
from api.linebot_helper import LineBotHelper, QuickReplyHelper
from linebot.v3.messaging import (
    TextMessage
)
from abc import ABC, abstractmethod

config = Config()
firebaseService = config.firebaseService

class Template(ABC):
    @abstractmethod
    def execute(self, event):
        pass

class TemplateFactory:
    def __init__(self):
        self.template_map = {
            'course': Course,
        }

    def get_template(self, task_name):
        template_class = self.template_map.get(task_name)
        if template_class:
            return template_class
        else:
            print("找不到對應的模板")
            return None

class Course(Template):
    def execute(self, event):
        quick_reply_data = firebaseService.get_data('quick_reply', DatabaseDocumentMap.QUICK_REPLY.get("course").get("semester"))
        LineBotHelper.reply_message(event, [TextMessage(text=quick_reply_data.get('text'), quick_reply=QuickReplyHelper.create_quick_reply(quick_reply_data.get('actions')))])
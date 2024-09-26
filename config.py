import sys
import os
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.messaging import (
    Configuration
)
import pygsheets
import json
from api.spreadsheet import SpreadsheetService
from api.firebase import FireBaseService
from api.line_notify import LineNotifyService
from map import FeatureStatus

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
    
class Config(metaclass=Singleton):
    def __init__(self):
        self.CHANNEL_SECRET = os.getenv('CHANNEL_SECRET', None)
        self.CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN', None)
        self.SPREADSHEET_URL = os.getenv('SPREADSHEET_URL', None)
        self.FIREBASE_CREDENTIALS = os.getenv('FIREBASE_CREDENTIALS', None)
        self.LINE_NOTIFY_CLIENT_ID = os.getenv('LINE_NOTIFY_CLIENT_ID', None)
        self.LINE_NOTIFY_CLIENT_SECRET = os.getenv('LINE_NOTIFY_CLIENT_SECRET', None)
        self.LINE_NOTIFY_GROUP_TOKEN = os.getenv('LINE_NOTIFY_GROUP_TOKEN', None)
        self.check_env()
        self.line_bot_init()
        self.feature_init()

    def check_env(self):
        """確認環境變數是否正確設定"""
        if self.CHANNEL_SECRET is None or self.CHANNEL_ACCESS_TOKEN is None:
            print("Please set LINE_CHANNEL_SECRET, LINE_CHANNEL_ACCESS_TOKEN environment variables.")
            sys.exit(1)

        if os.getenv('GDRIVE_API_CREDENTIALS') is None:
            print("Please set GDRIVE_API_CREDENTIALS environment variable.")
            sys.exit(1)
        
        if self.SPREADSHEET_URL is None:
            print("Please set SPREADSHEET_URL environment variable.")
            sys.exit(1)
        
        if self.FIREBASE_CREDENTIALS is None:
            print("Please set FIREBASE_CREDENTIALS environment variable.")
            sys.exit(1)

        if self.LINE_NOTIFY_CLIENT_ID is None or self.LINE_NOTIFY_CLIENT_SECRET is None:
            print("Please set LINE_NOTIFY_CLIENT_ID, LINE_NOTIFY_CLIENT_SECRET environment variables.")
            sys.exit(1)

        if os.getenv('LIFF_ID_COMPACT') is None or os.getenv('LIFF_ID_TALL') is None or os.getenv('LIFF_ID_FULL') is None:
            print("Please set LIFF_ID_COMPACT, LIFF_ID_TALL, LIFF_ID_FULL environment variables.")
            sys.exit(1)        

    def line_bot_init(self):
        """初始化LINE Bot相關物件"""
        self.handler = WebhookHandler(self.CHANNEL_SECRET)
        self.configuration = Configuration(access_token=self.CHANNEL_ACCESS_TOKEN)
        self.spreadsheetService = SpreadsheetService(pygsheets.authorize(service_account_env_var='GDRIVE_API_CREDENTIALS'), self.SPREADSHEET_URL)
        self.firebaseService = FireBaseService(json.loads(self.FIREBASE_CREDENTIALS))
        self.lineNotifyService = LineNotifyService(self.LINE_NOTIFY_CLIENT_ID, self.LINE_NOTIFY_CLIENT_SECRET)
    
    def feature_init(self):
        self.feature = {
            'menu': FeatureStatus.ENABLE,
            'setting': FeatureStatus.ENABLE,
            'faq': FeatureStatus.DISABLE,
            'course': FeatureStatus.ENABLE,
            'certificate': FeatureStatus.ENABLE,
            'community': FeatureStatus.ENABLE,
            'equipment': FeatureStatus.ENABLE,
            'gallery': FeatureStatus.DISABLE,
            'quiz': FeatureStatus.ENABLE
        }
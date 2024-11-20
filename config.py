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
        self._load_environment_variables()
        self._check_env()
        self._line_bot_init()
        self._feature_init()

    def _load_environment_variables(self):
        self.CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')
        self.CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
        self.SPREADSHEET_URL = os.getenv('SPREADSHEET_URL')
        self.FIREBASE_CREDENTIALS = os.getenv('FIREBASE_CREDENTIALS')
        self.LINE_NOTIFY_CLIENT_ID = os.getenv('LINE_NOTIFY_CLIENT_ID')
        self.LINE_NOTIFY_CLIENT_SECRET = os.getenv('LINE_NOTIFY_CLIENT_SECRET')
        self.LINE_NOTIFY_GROUP_TOKEN = os.getenv('LINE_NOTIFY_GROUP_TOKEN')
        self.GDRIVE_API_CREDENTIALS = os.getenv('GDRIVE_API_CREDENTIALS')
        self.LIFF_ID_COMPACT = os.getenv('LIFF_ID_COMPACT')
        self.LIFF_ID_TALL = os.getenv('LIFF_ID_TALL')
        self.LIFF_ID_FULL = os.getenv('LIFF_ID_FULL')

    def _check_env(self):
        required_vars = [
            'CHANNEL_SECRET', 'CHANNEL_ACCESS_TOKEN', 'GDRIVE_API_CREDENTIALS',
            'SPREADSHEET_URL', 'FIREBASE_CREDENTIALS', 'LINE_NOTIFY_CLIENT_ID',
            'LINE_NOTIFY_CLIENT_SECRET', 'LINE_NOTIFY_GROUP_TOKEN',
            'LIFF_ID_COMPACT', 'LIFF_ID_TALL', 'LIFF_ID_FULL'
        ]
        
        missing_vars = [var for var in required_vars if getattr(self, var) is None]
        
        if missing_vars:
            print(f"Please set the following environment variables: {', '.join(missing_vars)}")
            sys.exit(1)

    def _line_bot_init(self):
        """初始化LINE Bot相關物件"""
        self.handler = WebhookHandler(self.CHANNEL_SECRET)
        self.configuration = Configuration(access_token=self.CHANNEL_ACCESS_TOKEN)
        self.spreadsheetService = SpreadsheetService(pygsheets.authorize(service_account_env_var='GDRIVE_API_CREDENTIALS'), self.SPREADSHEET_URL)
        self.firebaseService = FireBaseService(json.loads(self.FIREBASE_CREDENTIALS))
        self.lineNotifyService = LineNotifyService(self.LINE_NOTIFY_CLIENT_ID, self.LINE_NOTIFY_CLIENT_SECRET)
    
    def _feature_init(self):
        self.feature = {
            'menu': FeatureStatus.ENABLE,
            'setting': FeatureStatus.ENABLE,
            'faq': FeatureStatus.ENABLE,
            'course': FeatureStatus.ENABLE,
            'certificate': FeatureStatus.ENABLE,
            'counseling': FeatureStatus.ENABLE,
            'community': FeatureStatus.ENABLE,
            'equipment': FeatureStatus.ENABLE,
            'gallery': FeatureStatus.DISABLE,
            'quiz': FeatureStatus.ENABLE
        }

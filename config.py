import sys
import os
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.messaging import (
    Configuration
)
import pygsheets
from api.spreadsheet import SpreadsheetService

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
        self.check_env()
        self.handler = None
        self.configuration = None
        self.line_bot_init()

    def check_env(self):
        """確認環境變數是否正確設定"""
        if self.CHANNEL_SECRET is None or self.CHANNEL_ACCESS_TOKEN is None:
            print("Please set LINE_CHANNEL_SECRET, LINE_CHANNEL_ACCESS_TOKEN environment variables.")
            sys.exit(1)
        
        if self.SPREADSHEET_URL is None:
            print("Please set SPREADSHEET_URL environment variable.")
            sys.exit(1)

    def line_bot_init(self):
        """初始化LINE Bot相關物件"""
        self.handler = WebhookHandler(self.CHANNEL_SECRET)
        self.configuration = Configuration(access_token=self.CHANNEL_ACCESS_TOKEN)
        self.spreadsheetService = SpreadsheetService(pygsheets.authorize(service_account_env_var='GDRIVE_API_CREDENTIALS'), self.SPREADSHEET_URL)
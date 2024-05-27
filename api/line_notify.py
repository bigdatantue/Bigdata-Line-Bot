import requests
import json

class LineNotifyService:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
    
    def get_notify_token(self, authorize_code, redirect_uri, client_id, client_secret):
        """
        取得使用者Line Notify Token
        """
        body = {
            "grant_type": "authorization_code",
            "code": authorize_code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret
        }
        r = requests.post("https://notify-bot.line.me/oauth/token", data=body)
        return r.json()["access_token"]
    
    def check_notify_status(self, token):
        """
        檢查使用者Line Notify狀態(包含status, targetType, target)
        """
        headers = {"Authorization": "Bearer " + token}
        r = requests.get("https://notify-api.line.me/api/status", headers=headers)
        return json.loads(r.text)
    
    def send_notify_message(self, token, msg):
        """
        發送Line Notify訊息
        """
        headers = {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/x-www-form-urlencoded"
        }

        payload = {'message': msg}
        r = requests.post("https://notify-api.line.me/api/notify", headers=headers, data=payload)
        return r.status_code
from config import Config
from strategy import TaskStrategy, TemplateStrategy
from map import Map, FeatureStatus, Permission
from api.linebot_helper import LineBotHelper
from flask import Flask, request, abort
from line_notify_app import line_notify_app
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.webhooks import (
    MessageEvent,
    PostbackEvent,
    FollowEvent,
    UnfollowEvent,
    TextMessageContent
)
from linebot.v3.messaging import (
    ImageMessage,
    TextMessage
)

app = Flask(__name__)
app.register_blueprint(line_notify_app, url_prefix='/notify')

# 初始化 Config
config = Config()
configuration = config.configuration
line_handler = config.handler
spreadsheetService = config.spreadsheetService
firebaseService = config.firebaseService

# domain root
@app.route('/')
def home():
    return 'Bigdata Line Bot!'

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'

@line_handler.add(FollowEvent)
def handle_follow(event):
    """
    Handle加入好友事件
    """
    try:
        # 取得使用者ID
        user_id = event.source.user_id
        # 檢查使用者是否存在，若不存在則新增至試算表
        if not spreadsheetService.check_user_exists('user_info', user_id):
            user_info = LineBotHelper.get_user_info(user_id)
            user_info.insert(0, user_id)
            # 新增一般使用者權限
            user_info.append(Permission.USER)
            spreadsheetService.add_user('user_info', user_info)
            
        #使用者在試算表的好友狀態設為True
        spreadsheetService.set_user_status(user_id, True)

        welcome_message = '歡迎加入❤️\n我是教育大數據機器人，\n可以解決您關於微型學程的各式問題。'
        image_url = 'https://i.imgur.com/RFQKmop.png'

        messages = [
            ImageMessage(original_content_url=image_url, preview_image_url=image_url),
            TextMessage(text=welcome_message)
        ]
        LineBotHelper.reply_message(event, messages)
    except Exception as e:
        app.logger.error(e)
        LineBotHelper.reply_message(event, [TextMessage(text='發生錯誤，請聯繫系統管理員！')])
    
@line_handler.add(UnfollowEvent)
def handle_unfollow(event):
    """
    Handle使用者封鎖或刪除好友事件
    """
    try:
        user_id = event.source.user_id
        
        #使用者在試算表的好友狀態設為False
        spreadsheetService.set_user_status(user_id, False)
    except Exception as e:
        app.logger.error(e)

@line_handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """
    Handle文字訊息事件
    """
    try:
        # 取得使用者文字訊息
        user_msg = event.message.text
        user_id = event.source.user_id
        feature = Map.FEATURE.get(user_msg)    
        temp = firebaseService.get_data('temp', user_id)

        # 判斷使用者輸入的文字是否為功能
        if feature:
            # 如果使用者跳出上個功能，則刪除暫存資料
            if temp:
                firebaseService.delete_data('temp', user_id)
            feature_status = config.feature.get(feature)
            if feature_status == FeatureStatus.DISABLE:
                return LineBotHelper.reply_message(event, [TextMessage(text='此功能尚未開放，敬請期待！')])
            elif feature_status == FeatureStatus.MAINTENANCE:
                return LineBotHelper.reply_message(event, [TextMessage(text='此功能維護中，請見諒！')])
            else:
                # 動態選擇Template Strategy(第一次輸入功能文字)
                strategy = TemplateStrategy('message', feature)
                strategy_class = strategy.strategy_action()
                if strategy_class:
                    task = strategy_class()
                    task.execute(event, request=request)
                    return
        elif temp:
            # 動態選擇Task Strategy(功能中需要使用者輸入文字)
            strategy = TaskStrategy('message', temp.get('task'))
            strategy_class = strategy.strategy_action()
            if strategy_class:
                task = strategy_class()
                task.execute(event, {'user_msg': user_msg})
                return
    except Exception as e:
        app.logger.error(e)
        LineBotHelper.reply_message(event, [TextMessage(text='發生錯誤，請聯繫系統管理員！')])

@line_handler.add(PostbackEvent)
def handle_postback(event):
    """
    Handle Postback事件
    """
    try:
        postback_data = event.postback.data
        # 如果有datetimpicker的參數，才會有postback_params
        postback_params = event.postback.params
        params = postback_params if postback_params else {}
        if '=' in postback_data:
            # 重新拆解Postback Data的參數
            for param in postback_data.split('&'):
                key, value = param.split('=')
                params[key] = value
        
        # 動態選擇Task Strategy
        strategy = TaskStrategy('postback', params)
        strategy_class = strategy.strategy_action()
        if strategy_class:
            task = strategy_class()
            task.execute(event, params)
            return
    except Exception as e:
        app.logger.error(e)
        LineBotHelper.reply_message(event, [TextMessage(text='發生錯誤，請聯繫系統管理員！')])

if __name__ == "__main__":
    app.run()
from config import Config
from strategy import TaskStrategy, TemplateStrategy
from map import Map, FeatureStatus, Permission
from api.linebot_helper import LineBotHelper
from flask import Flask, request, abort
from line_notify_app import line_notify_app
from liff_app import liff_app
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.webhooks import (
    MessageEvent,
    PostbackEvent,
    FollowEvent,
    UnfollowEvent,
    TextMessageContent,
    ImageMessageContent
)
from linebot.v3.messaging import (
    ImageMessage,
    TextMessage
)
import traceback

app = Flask(__name__)
app.register_blueprint(line_notify_app, url_prefix='/notify')
app.register_blueprint(liff_app, url_prefix='/liff')

# 初始化 Config
config = Config()
configuration = config.configuration
line_handler = config.handler
spreadsheetService = config.spreadsheetService
firebaseService = config.firebaseService
lineNotifyService = config.lineNotifyService

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
        LineBotHelper.show_loading_animation_(event)
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
        error_message = ''.join(traceback.format_exception(None, e, e.__traceback__))
        LineBotHelper.push_message(config.LINE_GROUP_ID, [TextMessage(text=f'發生錯誤！\n{error_message}')])
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
        error_message = ''.join(traceback.format_exception(None, e, e.__traceback__))
        LineBotHelper.push_message(config.LINE_GROUP_ID, [TextMessage(text=f'發生錯誤！\n{error_message}')])

@line_handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """
    Handle文字訊息事件
    """
    try:
        if LineBotHelper.check_is_fixing():
            return LineBotHelper.reply_message(event, [TextMessage(text='系統維護中，請稍後再試！')])
        # 取得使用者文字訊息
        user_msg = event.message.text
        user_id = event.source.user_id
        feature = Map.FEATURE.get(user_msg)
        # 如果使用者輸入的文字為FAQ的文字，則設定功能為FAQ
        if user_msg in Map.FAQ_SET:
            feature = 'faq'
        temp = firebaseService.get_data('temp', user_id)

        # 判斷使用者輸入的文字是否為功能
        if feature:
            LineBotHelper.show_loading_animation_(event)
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
            LineBotHelper.show_loading_animation_(event)
            # 動態選擇Task Strategy(功能中需要使用者輸入文字)
            strategy = TaskStrategy('message', temp.get('task'))
            strategy_class = strategy.strategy_action()
            if strategy_class:
                task = strategy_class()
                task.execute(event, {'user_msg': user_msg})
                return
    except Exception as e:
        app.logger.error(e)
        error_message = ''.join(traceback.format_exception(None, e, e.__traceback__))
        LineBotHelper.push_message(config.LINE_GROUP_ID, [TextMessage(text=f'發生錯誤！\n{error_message}')])
        LineBotHelper.reply_message(event, [TextMessage(text='發生錯誤，請聯繫系統管理員！')])

@line_handler.add(MessageEvent, message=ImageMessageContent)
def handle_image(event):
    """
    Handle圖片訊息事件
    """
    try:
        if LineBotHelper.check_is_fixing():
            return LineBotHelper.reply_message(event, [TextMessage(text='系統維護中，請稍後再試！')])
        # 傳送linenotify通知有使用者上傳圖片
        msg = f'有使用者上傳圖片！\nUser ID: {event.source.user_id}'
        lineNotifyService.send_notify_message(config.LINE_NOTIFY_GROUP_TOKEN, msg)
        return LineBotHelper.reply_message(event, [TextMessage(text='圖片上傳成功！')])
    except Exception as e:
        app.logger.error(e)
        error_message = ''.join(traceback.format_exception(None, e, e.__traceback__))
        lineNotifyService.send_notify_message(config.LINE_NOTIFY_GROUP_TOKEN, f'發生錯誤！\n{error_message}')
        LineBotHelper.reply_message(event, [TextMessage(text='發生錯誤，請聯繫系統管理員！')])

@line_handler.add(PostbackEvent)
def handle_postback(event):
    """
    Handle Postback事件
    """
    try:
        postback_data = event.postback.data
        if 'richmenu' in postback_data:
            return
        LineBotHelper.show_loading_animation_(event)
        if LineBotHelper.check_is_fixing():
            return LineBotHelper.reply_message(event, [TextMessage(text='系統維護中，請稍後再試！')])
        
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
        error_message = ''.join(traceback.format_exception(None, e, e.__traceback__))
        LineBotHelper.push_message(config.LINE_GROUP_ID, [TextMessage(text=f'發生錯誤！\n{error_message}')])
        LineBotHelper.reply_message(event, [TextMessage(text='發生錯誤，請聯繫系統管理員！')])

if __name__ == "__main__":
    app.run()
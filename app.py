from config import Config
from features.base import feature_factory
from map import Map, FeatureStatus, Permission, DatabaseCollectionMap
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
        user_id = event.source.user_id
        # 檢查使用者是否存在，若不存在則新增至資料庫
        if not firebaseService.get_data(DatabaseCollectionMap.USER, user_id):
            user_info = LineBotHelper.get_user_info(user_id)
            # 設定使用者的權限為USER，並設定為啟用狀態
            user_info.update({'permission': Permission.USER, 'isActive': True})
            firebaseService.add_data(DatabaseCollectionMap.USER, user_id, user_info)

        follow_doc = firebaseService.get_data(DatabaseCollectionMap.CONFIG, 'follow')
        welcome_message = follow_doc.get('welcome_message').replace('\\n', '\n')
        image_url = follow_doc.get('welcome_image')

        messages = [
            ImageMessage(original_content_url=image_url, preview_image_url=image_url),
            TextMessage(text=welcome_message)
        ]
        LineBotHelper.reply_message(event, messages)
    except Exception as e:
        app.logger.error(e)
        error_message = ''.join(traceback.format_exception(None, e, e.__traceback__))
        lineNotifyService.send_notify_message(config.LINE_NOTIFY_GROUP_TOKEN, f'發生錯誤！\n{error_message}')
        LineBotHelper.reply_message(event, [TextMessage(text='發生錯誤，請聯繫系統管理員！')])
    
@line_handler.add(UnfollowEvent)
def handle_unfollow(event):
    """
    Handle使用者封鎖或刪除好友事件
    """
    try:
        user_id = event.source.user_id
        # 使用者在資料庫中的isActive設定為False
        firebaseService.update_data('users', user_id, {'isActive': False})
    except Exception as e:
        app.logger.error(e)
        error_message = ''.join(traceback.format_exception(None, e, e.__traceback__))
        lineNotifyService.send_notify_message(config.LINE_NOTIFY_GROUP_TOKEN, f'發生錯誤！\n{error_message}')

@line_handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """
    Handle文字訊息事件
    """
    try:
        if LineBotHelper.check_is_fixing():
            return LineBotHelper.reply_message(event, [TextMessage(text='系統維護中，請稍後再試！')])
        
        user_msg = event.message.text
        user_id = event.source.user_id
        feature = Map.FEATURE.get(user_msg)
        # 如果使用者輸入的文字為FAQ的文字，則設定功能為FAQ
        if user_msg in Map.FAQ_SET:
            feature = 'faq'
        
        temp = firebaseService.get_data(DatabaseCollectionMap.TEMP, user_id)

        # 判斷使用者輸入的文字是否為功能
        if feature:
            LineBotHelper.show_loading_animation_(event)
            # 如果使用者跳出上個功能，則刪除暫存資料
            if temp:
                firebaseService.delete_data(DatabaseCollectionMap.TEMP, user_id)
            
            feature_status = config.feature.get(feature)
            match feature_status:
                case FeatureStatus.DISABLE:
                    return LineBotHelper.reply_message(event, [TextMessage(text='此功能尚未開放，敬請期待！')])
                case FeatureStatus.MAINTENANCE:
                    return LineBotHelper.reply_message(event, [TextMessage(text='此功能維護中，請見諒！')])
                
            feature_instance = feature_factory.get_feature(feature)
            if feature_instance:
                feature_instance.execute_message(event, request=request)
        elif temp:
            LineBotHelper.show_loading_animation_(event)
            feature_instance = feature_factory.get_feature(temp.get('task'))
            if feature_instance:
                feature_instance.execute_message(event, user_msg=user_msg)
    except Exception as e:
        app.logger.error(e)
        error_message = ''.join(traceback.format_exception(None, e, e.__traceback__))
        lineNotifyService.send_notify_message(config.LINE_NOTIFY_GROUP_TOKEN, f'發生錯誤！\n{error_message}')
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

        # 切換圖文選單也會觸發postback事件，因此需過濾掉
        if 'richmenu' in postback_data:
            return
        LineBotHelper.show_loading_animation_(event)
        if LineBotHelper.check_is_fixing():
            return LineBotHelper.reply_message(event, [TextMessage(text='系統維護中，請稍後再試！')])
        
        params = event.postback.params or {}
        if '=' in postback_data:
            params.update(dict(param.split('=') for param in postback_data.split('&')))
        
        feature_instance = feature_factory.get_feature(params.get('task'))
        if feature_instance:
            feature_instance.execute_postback(event, params=params)
    except Exception as e:
        app.logger.error(e)
        error_message = ''.join(traceback.format_exception(None, e, e.__traceback__))
        lineNotifyService.send_notify_message(config.LINE_NOTIFY_GROUP_TOKEN, f'發生錯誤！\n{error_message}')
        LineBotHelper.reply_message(event, [TextMessage(text='發生錯誤，請聯繫系統管理員！')])

doc_watch = firebaseService.on_snapshot("quiz_questions")

if __name__ == "__main__":
    app.run()
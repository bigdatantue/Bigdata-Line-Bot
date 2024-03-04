from flask import Flask, request, abort
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.webhooks import (
    MessageEvent,
    FollowEvent,
    TextMessageContent
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    ImageMessage,
    TextMessage
)
import sys
import os

app = Flask(__name__)

# LINE 聊天機器人的基本資料
CHANNEL_SECRET = os.getenv('CHANNEL_SECRET', None)
CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN', None)

if CHANNEL_SECRET is None or CHANNEL_ACCESS_TOKEN is None:
    print("Please set LINE_CHANNEL_SECRET, LINE_CHANNEL_ACCESS_TOKEN environment variables.")
    sys.exit(1)

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
line_handler = WebhookHandler(CHANNEL_SECRET)

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

# 處理加入好友事件
@line_handler.add(FollowEvent)
def handle_follow(event):
    # 歡迎訊息
    welcome_message = '歡迎加入❤️\n我是教育大數據機器人，\n可以解決您關於微型學程的各式問題。'

    # 圖片訊息
    image_url = 'https://i.imgur.com/RFQKmop.png'

    # 回覆訊息
    reply_message(event, [ImageMessage(original_content_url=image_url, preview_image_url=image_url),
                          TextMessage(text=welcome_message)])


# 處理文字訊息
@line_handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    # 取得使用者文字訊息
    user_msg = event.message.text
    reply_message(event, [TextMessage(text=user_msg)])


# 回覆多則訊息
def reply_message(event, messages):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=messages
            )
        )
if __name__ == "__main__":
    app.run()
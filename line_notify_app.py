from config import Config
from flask import Blueprint, request, render_template
from api.linebot_helper import LineBotHelper

line_notify_app = Blueprint('line_notify_app', __name__)

config = Config()
lineNotifyService = config.lineNotifyService
spreadsheetService = config.spreadsheetService

@line_notify_app.route('/register', methods=['GET'])
def line_notify_register():
    """
    連動Line Notify頁面
    """
    client_id = lineNotifyService.client_id
    redirect_uri = request.url_root.replace('http:', 'https:') + 'notify/callback'
    state = request.args.get('state')
    url = f'https://notify-bot.line.me/oauth/authorize?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope=notify&state={state}'
    return render_template('notify/register.html', **locals())

@line_notify_app.route('/callback', methods=['GET'])
def line_notify():
    """
    Line Notify Callback畫面(連動成功、失敗畫面)
    """
    authorizeCode = request.args.get('code')
    user_id = request.args.get('state')
    redirect_uri = request.url_root.replace('http:', 'https:') + 'notify/callback'
    token = lineNotifyService.get_notify_token(authorizeCode, redirect_uri, lineNotifyService.client_id, lineNotifyService.client_secret)
    current_time = LineBotHelper.get_current_time().strftime('%Y-%m-%d %H:%M:%S')
    
    # 若取得token失敗，則回傳錯誤頁面
    if not token:
        return render_template('notify/error.html')
    user_info = lineNotifyService.check_notify_status(token)
    user_info = [user_id, token, user_info['targetType'],  user_info['target'], current_time]

    spreadsheetService.add_user('notify_info', user_info)
    msg = "感謝您連動「國北教大教育大數據微學程」Line Notify 推播服務，若未來您想解除連動，請點選 https://notify-bot.line.me/my/ 後將連動解除即可。"
    lineNotifyService.send_notify_message(token, msg)
    return render_template('notify/callback.html')
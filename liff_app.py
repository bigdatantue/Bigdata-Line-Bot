from config import Config
from map import LIFFSize
from flask import Blueprint, request, render_template, jsonify

liff_app = Blueprint('liff_app', __name__)

config = Config()
spreadsheetService = config.spreadsheetService

# ----------------LIFF 三種尺寸跳轉用頁面(勿動) Start----------------

@liff_app.route('/full', methods=['GET'])
def full():
    liff_id = LIFFSize.FULL.value
    return render_template('liff/liff.html', liff_id=liff_id)

@liff_app.route('/tall', methods=['GET'])
def tall():
    liff_id = LIFFSize.TALL.value
    return render_template('liff/liff.html', liff_id=liff_id)

@liff_app.route('/compact', methods=['GET'])
def compact():
    liff_id = LIFFSize.COMPACT.value
    return render_template('liff/liff.html', liff_id=liff_id)

# ----------------LIFF 三種尺寸跳轉用頁面(勿動) End----------------

# ----------------LIFF 頁面(根據需求設定不同大小) Start----------------
@liff_app.route('/tall/userinfo', methods=['GET'])
def userinfo():
    liff_id = LIFFSize.TALL.value
    user_id = request.args.get('userId')
    user_infos = spreadsheetService.get_worksheet_data('user_details')
    user_info = [user_info for user_info in user_infos if user_info['user_id'] == user_id]
    user_info = user_info[0] if user_info else None

    return render_template('liff/userinfo.html', **locals())

@liff_app.route('/userinfo', methods=['POST'])
def userinfo_post():
    data = request.form
    user_id = data.get('userId')
    user_data = [data.get(field) if data.get(field) else '' for field in ['userId', 'name', 'studentId', 'email', 'phone', 'college', 'department', 'grade']]
    
    wks = spreadsheetService.sh.worksheet_by_title('user_details')
    row_index = spreadsheetService.get_row_index(wks, 'user_id', user_id)
    
    if row_index:
        spreadsheetService.update_cells_values('user_details', f'A{row_index}:H{row_index}', [user_data])
    else:
        wks.append_table(values=user_data)
    return jsonify({'message': '設定成功'})
# ----------------LIFF 頁面(根據需求設定不同大小) End----------------

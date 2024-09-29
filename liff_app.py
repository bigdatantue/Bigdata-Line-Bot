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
    if user_info:
        phone = str(user_info['phone'])
        # 判斷電話號碼長度是否不足10位，如果不足則補0
        if len(phone) < 10:
            phone = phone.zfill(10)
        user_info['phone'] = phone
    return render_template('liff/userinfo.html', **locals())

@liff_app.route('/userinfo', methods=['POST'])
def userinfo_post():
    data = request.form
    user_id = data.get('userId')
    #此處的順序需與試算表的欄位順序一致、名稱需與userinfo.html的data一致
    column_list = ['userId', 'name', 'identity', 'gender', 'studentId', 'email', 'phone', 'college', 'schoolName', 'department', 'grade', 'extDepartment', 'extGrade', 'organization']
    user_data = [data.get(field) if data.get(field) else '' for field in column_list]
                 
    
    wks = spreadsheetService.sh.worksheet_by_title('user_details')
    row_index = spreadsheetService.get_row_index(wks, 'user_id', user_id)
    
    if row_index:
        spreadsheetService.update_cells_values('user_details', f'A{row_index}:N{row_index}', [user_data])
    else:
        wks.append_table(values=user_data)
    return jsonify({'message': '設定成功'})
# ----------------LIFF 頁面(根據需求設定不同大小) End----------------

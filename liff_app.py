from config import Config
from map import LIFFSize, EquipmentStatus, DatabaseCollectionMap, Permission, EquipmentType, EquipmentName
from flask import Blueprint, request, render_template, jsonify
from api.linebot_helper import LineBotHelper
from linebot.v3.messaging import (
    FlexMessage,
    FlexContainer
)
import traceback

liff_app = Blueprint('liff_app', __name__)

config = Config()
firebaseService = config.firebaseService
lineNotifyService = config.lineNotifyService

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
# ----------------使用者詳細資料 Start----------------
@liff_app.route('/tall/userinfo', methods=['GET'])
def userinfo():
    liff_id = LIFFSize.TALL.value
    user_id = request.args.get('userId')
    user_info = firebaseService.filter_data('users', [('userId', '==', user_id)])
    user_info = user_info[0].get('details')
    return render_template('liff/userinfo.html', **locals())

@liff_app.route('/userinfo', methods=['POST'])
def userinfo_post():
    try:
        data = request.form.to_dict()
        user_id = data.pop('userId')
        user_info = firebaseService.filter_data('users', [('userId', '==', user_id)])[0].get('details')
        if user_info:
            verification = user_info.pop('verification')
            verrfication_keys = ['identity', 'name', 'studentId', 'college', 'department', 'grade']
            # 如果身份已驗證，限制資料修改
            if verification and any(data.get(key) != user_info.get(key) for key in verrfication_keys):
                return jsonify({'success': False, 'message': '身分已驗證，無法修改姓名、學號及學籍資料'})
            # 將verification加回data並更新到Firebase
            data.update({'verification': verification})
        else:
            data.update({'verification': False})
        firebaseService.update_data('users', user_id, {'details': data})

        return jsonify({'success': True, 'message': '設定成功'})
    except Exception as e:
        error_message = ''.join(traceback.format_exception(None, e, e.__traceback__))
        lineNotifyService.send_notify_message(config.LINE_NOTIFY_GROUP_TOKEN, f'發生錯誤！\n{error_message}')
        return jsonify({'success': False, 'message': "發生錯誤，請聯繫系統管理員"})
# ----------------使用者詳細資料 End----------------

# ----------------設備租借 Start----------------
@liff_app.route('/tall/rent', methods=['GET'])
def rent():
    liff_id = LIFFSize.TALL.value
    user_id = request.args.get('userId')
    user_info = firebaseService.filter_data('users', [('userId', '==', user_id)])[0].get('details')

    # 計算每種設備的可借數量
    equipments = []
    for key, equipment_id in EquipmentType.__members__.items():
        equipment = {'equipment_name': EquipmentName[key].value}
        conditions = [
            ('type', '==', equipment_id),
            ('status', '==', EquipmentStatus.AVAILABLE)
        ]
        equipment['available_amount'] = len(firebaseService.filter_data('equipments', conditions))
        equipment['equipment_id'] = equipment_id.value
        equipments.append(equipment)

    return render_template('liff/rent.html', **locals())

@liff_app.route('/rent', methods=['POST'])
def submit_rent():
    data = request.form
    user_id = data.get('userId')

    try:
        # 將處理過的 postback_data 存入 Firebase TEMP
        firebaseService.add_data(DatabaseCollectionMap.TEMP, user_id, data)
        supervisors = [user.get('userId') for user in firebaseService.filter_data('users', [('permission', '>=', Permission.LEADER)])]
        line_flex_template = firebaseService.get_data(
            DatabaseCollectionMap.LINE_FLEX,
            "equipment"
        ).get("approve")
        line_flex_str = LineBotHelper.replace_variable(line_flex_template, data)
        LineBotHelper.multicast_message(supervisors, [
            FlexMessage(alt_text='租借申請確認', contents=FlexContainer.from_json(line_flex_str))
        ])

        return jsonify({'message': "提交成功，等候審核處理"})

    except Exception as e:
        print(f'Error: {e}')
        return jsonify({'error': '提交失敗，請稍後再試'}), 500
# ----------------設備租借 End----------------

# ----------------LIFF 頁面(根據需求設定不同大小) End----------------

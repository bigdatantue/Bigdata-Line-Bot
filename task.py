from config import Config
from map import Map, DatabaseCollectionMap, DatabaseDocumentMap, FlexParamMap, EquipmentStatus, Permission
from api.linebot_helper import LineBotHelper, QuickReplyHelper, FlexMessageHelper
from linebot.v3.messaging import (
    TextMessage,
    ImageMessage,
    FlexMessage,
    FlexContainer
)
from abc import ABC, abstractmethod
import json
import pandas as pd
from datetime import datetime
import re

config = Config()
spreadsheetService = config.spreadsheetService
firebaseService = config.firebaseService


class Task(ABC):
    @abstractmethod
    def execute(self, event, params):
        pass

class TaskFactory:
    def __init__(self):
        self.task_map = {
            'course': Course,
            'community': Communtity,
            'certificate': Certificate,
            'counseling': Counseling,
            'equipment': Equipment
        }

    def get_task(self, task_name):
        task_class = self.task_map.get(task_name)
        if task_class:
            return task_class
        else:
            print("找不到對應的任務")
            return None

class Course(Task):
    """
    開課時間查詢
    """
    def execute(self, event, params):
        course_record_id = params.get('course_record')
        course_category = params.get('category')

        #如果有course_record_id，則回傳該課程的詳細資訊
        if course_record_id:
            course = __class__.__get_course_records(id=course_record_id)[0]
            line_flex_template = firebaseService.get_data(
                DatabaseCollectionMap.LINE_FLEX,
                DatabaseDocumentMap.LINE_FLEX.get("course")
            ).get('detail')
            params = LineBotHelper.map_params(course, FlexParamMap.COURSE)
            line_flex_str = LineBotHelper.replace_variable(line_flex_template, params)
            
            LineBotHelper.reply_message(event, [FlexMessage(alt_text='詳細說明', contents=FlexContainer.from_json(line_flex_str))])
            return
        
        #否則如果有course_category，則回傳該類別的課程資訊
        elif course_category:
            course_map = Map.COURSE
            # 拆解學年和學期
            year = params.get('semester')[:3]
            semester = params.get('semester')[3:]
            courses = __class__.__get_course_records(year=year, semester=semester)
            if course_category != 'overview':
                courses = [course for course in courses if course.get('category') == course_map.get(course_category)]
            if len(courses) == 0:
                message = f'{year}學年度第{semester}學期沒有{course_map.get(course_category)}課程資料'
                LineBotHelper.reply_message(event, [TextMessage(text=message)])
            else:
                line_flex_template = firebaseService.get_data(
                    DatabaseCollectionMap.LINE_FLEX, 
                    DatabaseDocumentMap.LINE_FLEX.get("course")
                ).get('summary')
                line_flex_json = FlexMessageHelper.create_carousel_bubbles(courses, json.loads(line_flex_template), FlexParamMap.COURSE)
                line_flex_str = json.dumps(line_flex_json)
                LineBotHelper.reply_message(event, [FlexMessage(alt_text=course_map.get(course_category), contents=FlexContainer.from_json(line_flex_str))])
            return
        
        #否則回傳課程類別的快速回覆選項
        else:
            quick_reply_data = firebaseService.get_data(
                DatabaseCollectionMap.QUICK_REPLY,
                DatabaseDocumentMap.QUICK_REPLY.get("course")
            ).get("category")
            for i, text in enumerate(quick_reply_data.get('actions')):
                quick_reply_data.get('actions')[i] = LineBotHelper.replace_variable(text, params)
            LineBotHelper.reply_message(event, [TextMessage(text=quick_reply_data.get('text'), quick_reply=QuickReplyHelper.create_quick_reply(quick_reply_data.get('actions')))])
            return
            

    def __get_course_records(id=None, year=None, semester=None):
        """Returns
        list: 課程資料
        """
        courses = spreadsheetService.get_worksheet_data('courses')
        course_records = spreadsheetService.get_worksheet_data('course_records')

        courses_df = pd.DataFrame(courses)
        course_records_df = pd.DataFrame(course_records)

        # 將開始與結束節次補零 (ex: 1 -> 01)
        course_records_df['start_class'] = course_records_df['start_class'].apply(lambda x: str(x).zfill(2))
        course_records_df['end_class'] = course_records_df['end_class'].apply(lambda x: str(x).zfill(2))

        # 將課程資料與課程紀錄資料合併
        merged_data = pd.merge(courses_df, course_records_df, on='course_id', how='inner').astype(str)
        # 根據條件篩選資料
        if id:
            merged_data = merged_data[merged_data['id'] == str(id)]
        elif year and semester:
            merged_data = merged_data[(merged_data['year'] == year) & (merged_data['semester'] == semester)]
        return merged_data.to_dict(orient='records')
    
class Communtity(Task):
    """
    社群學習資源
    """
    def execute(self, event, params):
        microcourses = spreadsheetService.get_worksheet_data('microcourses')
        line_flex_template = firebaseService.get_data(
            DatabaseCollectionMap.LINE_FLEX,
            DatabaseDocumentMap.LINE_FLEX.get("community")
        ).get("microcourse")
        line_flex_json = FlexMessageHelper.create_carousel_bubbles(microcourses, json.loads(line_flex_template), FlexParamMap.COMMUNITY)
        line_flex_str = json.dumps(line_flex_json)
        LineBotHelper.reply_message(event, [FlexMessage(alt_text='社群學習資源', contents=FlexContainer.from_json(line_flex_str))])
        return
    
class Certificate(Task):
    """
    證書查詢
    """
    def execute(self, event, params):
        type = params.get('type')
        if type == 'process':
            image_url = 'https://bigdatalinebot.blob.core.windows.net/linebot/Micro-Credit-Course-Apply-Process.png'
            LineBotHelper.reply_message(event, [ImageMessage(original_content_url=image_url, preview_image_url=image_url)])
            return

class Counseling(Task):
    """
    線上輔導+實體預約
    """
    def execute(self, event, params):
        counseling_type = params.get('type')
        if counseling_type == 'online':
            line_flex_str = firebaseService.get_data(
                DatabaseCollectionMap.LINE_FLEX,
                DatabaseDocumentMap.LINE_FLEX.get("counseling")
            ).get("online")
            LineBotHelper.reply_message(event, [FlexMessage(alt_text='線上輔導', contents=FlexContainer.from_json(line_flex_str))])
            return
        else:
            line_flex_str = firebaseService.get_data(
                DatabaseCollectionMap.LINE_FLEX,
                DatabaseDocumentMap.LINE_FLEX.get("counseling")
            ).get("physical")
            LineBotHelper.reply_message(event, [FlexMessage(alt_text='實體預約', contents=FlexContainer.from_json(line_flex_str))])
            return
        
class Equipment(Task):
    """
    設備租借
    """
    def execute(self, event, params):
        user_id = event.source.user_id
        user_msg = params.get('user_msg')
        decision = params.get('decision')
        if decision:
            borrower_user_id = params.get('borrower_user_id')
            borrower_info = firebaseService.get_data(DatabaseCollectionMap.TEMP, borrower_user_id)
            if not borrower_info:
                return LineBotHelper.reply_message(event, [TextMessage(text='此租借申請已審核過')])
            # 使用者回覆設備租借核准
            if decision == '1':
                # 設備租借核准
                borrower_id = __class__.__rent_equipment(borrower_info)
                firebaseService.delete_data(DatabaseCollectionMap.TEMP, borrower_user_id)
                borrow_records = __class__.__get_borrow_records(borrower_user_id, borrower_id)
                line_flex_template = firebaseService.get_data(
                    DatabaseCollectionMap.LINE_FLEX,
                    DatabaseDocumentMap.LINE_FLEX.get("equipment")
                ).get("record")
                line_flex_json = FlexMessageHelper.create_carousel_bubbles(borrow_records, json.loads(line_flex_template), FlexParamMap.EQUIPMENT)
                line_flex_str = json.dumps(line_flex_json)
                LineBotHelper.reply_message(event, [TextMessage(text='設備租借核准'), FlexMessage(alt_text='借用清單', contents=FlexContainer.from_json(line_flex_str))])
                LineBotHelper.push_message(borrower_user_id, [TextMessage(text='設備租借核准'), FlexMessage(alt_text='借用清單', contents=FlexContainer.from_json(line_flex_str))])
                return
            else:
                # 設備租借不核准
                firebaseService.delete_data(DatabaseCollectionMap.TEMP, borrower_user_id)
                LineBotHelper.reply_message(event, [TextMessage(text='設備租借不通過')])
                LineBotHelper.push_message(borrower_user_id, [TextMessage(text='設備租借不通過')])
                return
        if user_msg:
            # 如果有使用者輸入文字，則進入填寫借用人資料流程
            borrower_info = firebaseService.get_data(DatabaseCollectionMap.TEMP, user_id)
            prompts = ['請輸入系所班級', '請輸入email', '請輸入手機號碼', '已送出租借申請']
            keys = ['name', 'department', 'email', 'phone']
            for key, prompt in zip(keys, prompts):
                if key not in borrower_info['borrowerData']:
                    if key == 'email' and not __class__.__check_email(user_msg):
                        return LineBotHelper.reply_message(event, [TextMessage(text='請輸入正確的email格式')])
                    elif key == 'phone' and not __class__.__check_phone(user_msg):
                        return LineBotHelper.reply_message(event, [TextMessage(text='請輸入正確的手機號碼格式')])
                    borrower_info['borrowerData'][key] = user_msg
                    firebaseService.update_data(DatabaseCollectionMap.TEMP, user_id, borrower_info)
                    if key == 'phone':
                        # 最後一個資料輸入完畢，進行設備租借
                        user_info_data = spreadsheetService.get_worksheet_data('user_info')
                        user_info_data = [user for user in user_info_data if user.get('permission') >= Permission.LEADER]
                        user_ids = [user.get('user_id') for user in user_info_data]
                        line_flex_str = firebaseService.get_data(
                            DatabaseCollectionMap.LINE_FLEX,
                            DatabaseDocumentMap.LINE_FLEX.get("equipment")
                        ).get("approve")
                        items = {
                            'equipment_name': Map.EQUIPMENT_NAME.get(int(borrower_info['equipment_id'])),
                            'borrower_user_id': user_id,
                            'name': borrower_info['borrowerData']['name'],
                            'borrower_department': borrower_info['borrowerData']['department'],
                            'borrower_email': borrower_info['borrowerData']['email'],
                            'borrower_phone': borrower_info['borrowerData']['phone'],
                            'amount': borrower_info['amount'],
                            'start_date': borrower_info['startDate'],
                            'pickup_time': borrower_info['selectedTime'],
                            'end_date': borrower_info['endDate'],
                            'return_time': borrower_info['returnTime']
                        }
                        line_flex_str = LineBotHelper.replace_variable(line_flex_str, items)
                        LineBotHelper.multicast_message(user_ids, [FlexMessage(alt_text='租借申請確認', contents=FlexContainer.from_json(line_flex_str))])
                    return LineBotHelper.reply_message(event, [TextMessage(text=prompt)])
        else:
            type = params.get('type')
            if type == 'borrow':
                equipment_id = params.get('equipment_id')
                amount = params.get('amount')
                confirmed = params.get('status') == 'confirm'
                if confirmed:
                    # 送出租借資訊
                    start_date = params.get('start_date')
                    pickup_time = params.get('pickup_time')
                    end_date = params.get('end_date')
                    return_time = params.get('return_time')
                    data = {
                        'task': 'equipment',
                        'equipment_id': equipment_id,
                        'amount': params.get('amount'),
                        'startDate': start_date,
                        'selectedTime': pickup_time,
                        'endDate': end_date,
                        'returnTime': return_time,
                        'borrower': user_id,
                        'borrowerData': {}
                    }
                    is_valid, error_msg = __class__.__check_borrow_data(start_date.replace(' ',''), pickup_time.replace(' ',''), end_date.replace(' ',''), return_time.replace(' ',''))
                    if is_valid:
                        firebaseService.add_data(DatabaseCollectionMap.TEMP, user_id, data)
                        return LineBotHelper.reply_message(event, [TextMessage(text='請輸入借用人姓名')])
                    else:
                        return LineBotHelper.reply_message(event, [TextMessage(text=error_msg)])
                elif amount:
                    # 編輯租借資訊
                    item = params.get('item')
                    line_flex_template = firebaseService.get_data(
                        DatabaseCollectionMap.LINE_FLEX,
                        DatabaseDocumentMap.LINE_FLEX.get("equipment")
                    ).get("confirm")
                    items = {
                        'equipment_id': equipment_id,
                        'equipment_name': Map.EQUIPMENT_NAME.get(int(equipment_id)),
                        'amount': amount,
                        'start_date': params.get('start_date', ' '),
                        'pickup_time': params.get('pickup_time', ' '),
                        'end_date': params.get('end_date', ' '),
                        'return_time': params.get('return_time', ' ')
                    }
                    # 重新設定使用者修改的欄位
                    items[item] = params.get('date') if item == 'start_date' or item == 'end_date' else params.get('time')
                    
                    line_flex_str = LineBotHelper.replace_variable(line_flex_template, items)
                    return LineBotHelper.reply_message(event, [FlexMessage(alt_text='確認租借', contents=FlexContainer.from_json(line_flex_str))])
                elif equipment_id:
                    # 選擇租借數量
                    quick_reply_data = firebaseService.get_data(
                        DatabaseCollectionMap.QUICK_REPLY,
                        DatabaseDocumentMap.QUICK_REPLY.get("equipment")
                    ).get("amount")
                    for i, text in enumerate(quick_reply_data.get('actions')):
                        quick_reply_data.get('actions')[i] = LineBotHelper.replace_variable(text, params)
                    return LineBotHelper.reply_message(event, [TextMessage(text=quick_reply_data.get('text'), quick_reply=QuickReplyHelper.create_quick_reply(quick_reply_data.get('actions')))])
                else:
                    # 選擇租借設備
                    equipments = spreadsheetService.get_worksheet_data('equipments')
                    equipment_status_data = firebaseService.get_collection_data('equipments')

                    # 計算設備總數、已借出數、可借出數
                    for i in range(len(equipments)):
                        total_amount = len([equipment for equipment in equipment_status_data if equipment.get('type') == equipments[i].get('equipment_id')])
                        lend_amount = len([equipment for equipment in equipment_status_data if equipment.get('type') == equipments[i].get('equipment_id') and equipment.get('status') == EquipmentStatus.LEND])
                        equipments[i]['total_amount'] = total_amount
                        equipments[i]['lend_amount'] = lend_amount
                        equipments[i]['available_amount'] = total_amount - lend_amount

                    line_flex_template = firebaseService.get_data(
                        DatabaseCollectionMap.LINE_FLEX,
                        DatabaseDocumentMap.LINE_FLEX.get("equipment")
                    ).get("equipment_summary")
                    line_flex_template = FlexMessageHelper.create_carousel_bubbles(equipments, json.loads(line_flex_template), FlexParamMap.EQUIPMENT)
                    line_flex_template = json.dumps(line_flex_template)
                    return LineBotHelper.reply_message(event, [FlexMessage(alt_text='設備租借', contents=FlexContainer.from_json(line_flex_template))])
            else:
                # 查詢借用清單
                borrow_records = __class__.__get_borrow_records(user_id)
                if len(borrow_records) == 0:
                    LineBotHelper.reply_message(event, [TextMessage(text='您目前沒有借用任何設備')])
                    return
                line_flex_template = firebaseService.get_data(
                    DatabaseCollectionMap.LINE_FLEX,
                    DatabaseDocumentMap.LINE_FLEX.get("equipment")
                ).get("record")
                line_flex_json = FlexMessageHelper.create_carousel_bubbles(borrow_records, json.loads(line_flex_template), FlexParamMap.EQUIPMENT)
                line_flex_str = json.dumps(line_flex_json)
                return LineBotHelper.reply_message(event, [FlexMessage(alt_text='借用清單', contents=FlexContainer.from_json(line_flex_str))])

    def __check_borrow_data(start_date, pickup_time, end_date, return_time):
        """Returns
        Tuple[bool, str]: 是否合法, 錯誤訊息
        """
        if start_date and pickup_time and end_date and return_time:
            # 檢查借用結束日期是否大於借用開始日期
            start_datetime = datetime.strptime(f'{start_date} {pickup_time}', '%Y-%m-%d %H:%M')
            end_datetime = datetime.strptime(f'{end_date} {return_time}', '%Y-%m-%d %H:%M')
            if start_datetime >= end_datetime:
                return False, '借用結束日期時間需大於借用開始日期時間'
            else:
                return True, ''
        else:
            return False, '請填寫完整借用資訊'

    def __check_email(email: str):
        """Returns
        bool: email格式是否合法
        """
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        return re.fullmatch(regex, email)
    
    def __check_phone(phone: str):
        """Returns 
        bool: 手機號碼格式是否合法
        """
        regex = r'^09\d{8}$'
        return re.fullmatch(regex, phone)
    
    def __rent_equipment(params: dict):
        """租借設備(更新資料庫)
        Returns
        str: 借用者id
        """
        equipment_status_data = firebaseService.get_collection_data('equipments')
        # 取得可借出的設備
        equipment_status_data = [equipment for equipment in equipment_status_data if str(equipment.get('type')) == params.get('equipment_id') and equipment.get('status') == EquipmentStatus.AVAILABLE]
        # 隨機產生id
        borrower_id = LineBotHelper.generate_id()
        # 更新設備狀態
        for equipment in equipment_status_data[:int(params.get('amount'))]:
            equipment['borrowerId'] = borrower_id
            equipment['borrower'] = params.get('borrower')
            equipment['status'] = EquipmentStatus.LEND
            equipment['startDate'] = params.get('startDate')
            equipment['selectedTime'] = params.get('selectedTime')
            equipment['endDate'] = params.get('endDate')
            equipment['returnTime'] = params.get('returnTime')
            equipment['borrowerData'] = params.get('borrowerData')
            firebaseService.update_data('equipments', equipment.get('_id'), equipment)
        return borrower_id
    
    def __get_borrow_records(user_id: str, borrower_id: str=None):
        """Returns
        list: 借用紀錄
        """
        equipments = firebaseService.get_collection_data('equipments')
        
        borrow_records_dict = {}
        for equipment in equipments:
            # 前者為該使用者借用的所有設備，後者為該使用者借用且為borrower_id的設備
            if (not borrower_id and equipment.get('borrower') == user_id) or (borrower_id and equipment.get('borrower') == user_id and equipment.get('borrowerId') == borrower_id):
                # borrower_id_ 多一個底線是為了避免與參數名稱衝突
                borrower_id_ = equipment.get('borrowerId')
                if borrower_id_ not in borrow_records_dict:
                    borrow_records_dict[borrower_id_] = {
                        'amount': 0,
                        'equipment_name': equipment.get('name'),
                        'start_date': equipment.get('startDate'),
                        'end_date': equipment.get('endDate'),
                        'return_time': equipment.get('returnTime'),
                        'id': []
                    }
                borrow_records_dict[borrower_id_]['amount'] += 1
                borrow_records_dict[borrower_id_]['id'].append(equipment.get('_id'))

        # 將借用紀錄整理成list(不需要borrower_id_這個key了，只把需要的資料取出來)
        borrow_records = []
        for borrower_id, record in borrow_records_dict.items():
            record['id'] = '\\n'.join(record['id'])
            borrow_records.append(record)

        return borrow_records
from config import Config
from map import Map, DatabaseCollectionMap, DatabaseDocumentMap, EquipmentStatus, Permission
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
import pytz
from datetime import datetime
import re
import random

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
            'equipment': Equipment,
            'quiz': Quiz
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
            line_flex_str = LineBotHelper.replace_variable(line_flex_template, course)
            
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
                line_flex_json = FlexMessageHelper.create_carousel_bubbles(courses, json.loads(line_flex_template))
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
        line_flex_json = FlexMessageHelper.create_carousel_bubbles(microcourses, json.loads(line_flex_template))
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
                line_flex_json = FlexMessageHelper.create_carousel_bubbles(borrow_records, json.loads(line_flex_template))
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

                    for i in range(len(equipments)):
                        equipment_id = equipments[i].get('equipment_id')
                        
                        total_conditions = [('type', '==', equipment_id)]
                        total_amount = len(firebaseService.filter_data('equipments', total_conditions))
                        lend_conditions = [
                            ('type', '==', equipment_id),
                            ('status', '==', EquipmentStatus.LEND)
                        ]
                        lend_amount = len(firebaseService.filter_data('equipments', lend_conditions))
                        
                        # 更新設備資訊
                        equipments[i]['total_amount'] = total_amount
                        equipments[i]['lend_amount'] = lend_amount
                        equipments[i]['available_amount'] = total_amount - lend_amount
                    line_flex_template = firebaseService.get_data(
                        DatabaseCollectionMap.LINE_FLEX,
                        DatabaseDocumentMap.LINE_FLEX.get("equipment")
                    ).get("equipment_summary")
                    line_flex_template = FlexMessageHelper.create_carousel_bubbles(equipments, json.loads(line_flex_template))
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
                line_flex_json = FlexMessageHelper.create_carousel_bubbles(borrow_records, json.loads(line_flex_template))
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
        conditions = [
            ('type', '==', int(params.get('equipment_id'))),
            ('status', '==', EquipmentStatus.AVAILABLE)
        ]
        equipment_status_data = firebaseService.filter_data('equipments', conditions)
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
        conditions = [('borrower', '==', user_id)]
        equipments = firebaseService.filter_data('equipments', conditions)

        if borrower_id:
            conditions.append(('borrowerId', '==', borrower_id))

        equipments = firebaseService.filter_data('equipments', conditions)
        borrow_records_dict = {}
        for equipment in equipments:
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

class Quiz(Task):
    """
    知識測驗
    """
    def execute(self, event, params):
        user_id = event.source.user_id
        question_no = params.get('no')
        if question_no:
            question_no = int(question_no)
            # 從temp取得題目
            temp_data = firebaseService.get_data(DatabaseCollectionMap.TEMP, user_id)
            quiz_id = params.get('quiz_id')
            
            # 防止點選之前的測驗
            if not temp_data or quiz_id != temp_data.get('quiz_id'):
                return LineBotHelper.reply_message(event, [TextMessage(text='該測驗已結束！')])

            # 防止重複作答
            if question_no < temp_data.get('no'):
                return LineBotHelper.reply_message(event, [TextMessage(text='請勿重複作答!')])
            
            # 防止競賽已結束後繼續作答
            competition_id = temp_data.get('competition_id')
            if competition_id and not __class__.__check_competition_open_time(competition_id):
                return LineBotHelper.reply_message(event, [TextMessage(text='該競賽已結束!')])
            
            quiz_questions = temp_data.get('questions')
            
            # 使用者的答案
            answer = params.get('answer').lower()

            # 判斷答案是否正確
            last_quiz_question = quiz_questions[question_no - 1]
            is_correct = answer == last_quiz_question.get('answer').lower()
            answer_line_flex_str = __class__.__generate_answer_line_flex(last_quiz_question, is_correct)

            # 記錄該題作答(選擇的答案人數+1)
            __class__.__create_answer_record(temp_data.get('mode'), user_id, temp_data.get('quiz_id'), last_quiz_question, answer, event.timestamp)
            if is_correct:
                temp_data['correct_amount'] += 1

            if question_no < temp_data.get('question_amount'):
                question_line_flex_str = __class__.__generate_question_line_flex(quiz_questions[question_no], quiz_id, question_no, temp_data.get('question_amount'))
                firebaseService.update_data(DatabaseCollectionMap.TEMP, user_id, {'no': question_no + 1, 'correct_amount': temp_data.get('correct_amount')})
                return LineBotHelper.reply_message(event, [
                    FlexMessage(alt_text='測驗解答', contents=FlexContainer.from_json(answer_line_flex_str)),
                    FlexMessage(alt_text='測驗題目', contents=FlexContainer.from_json(question_line_flex_str))
                ])
            else:
                # 生成測驗結果
                mode = temp_data.get('mode')
                if mode == 'general':
                    # 一般模式                    
                    result_line_flex_str = __class__.__generate_general_quiz_result(user_id, temp_data)
                else:
                    # 競賽模式
                    result_line_flex_str = __class__.__generate_competition_quiz_result(user_id, temp_data)
                firebaseService.delete_data(DatabaseCollectionMap.TEMP, user_id)
                return LineBotHelper.reply_message(event, [
                    FlexMessage(alt_text='測驗解答', contents=FlexContainer.from_json(answer_line_flex_str)),
                    FlexMessage(alt_text='測驗結果', contents=FlexContainer.from_json(result_line_flex_str))
                ])
        else:
            # 進行測驗
            mode = params.get('mode')
            category = params.get('category')
            quiz_flex_datas = spreadsheetService.get_worksheet_data('quizzes')
            if category:
                competition_id = params.get('competition_id')
                quiz_id = LineBotHelper.generate_id()
                current_time = LineBotHelper.get_current_time().strftime('%Y-%m-%d %H:%M:%S')
                if mode == 'competition':
                    competition_logs = spreadsheetService.get_worksheet_data('competitions')
                    competition_log = [log for log in competition_logs if log.get('competition_id') == competition_id and log.get('user_id') == user_id]
                    if len(competition_log) > 0:
                        if competition_log[0].get('time_spent'):
                            return LineBotHelper.reply_message(event, [TextMessage(text='您已參加過此競賽')])
                        else:
                            return LineBotHelper.reply_message(event, [TextMessage(text='您的競賽已在進行中')])
                    if __class__.__check_competition_open_time(competition_id):
                        wks = spreadsheetService.sh.worksheet_by_title('competitions')
                        wks.append_table([competition_id, quiz_id, user_id, current_time])
                    else:
                        return LineBotHelper.reply_message(event, [TextMessage(text='目前尚未開放測驗')])
                # 隨機抽取題目，並存入TEMP
                quiz_flex_data = [quiz for quiz in quiz_flex_datas if quiz.get('enable') and quiz.get('mode') == mode and quiz.get('category') == category][0]
                question_amount = quiz_flex_data.get('question_amount')
                database_amount = quiz_flex_data.get('database_amount')
                questions = spreadsheetService.get_worksheet_data('quiz_questions')
                quiz_questions = random.sample([question for question in questions if question.get('category') == category and question.get('is_competition')], database_amount)
                quiz_questions.extend(random.sample([question for question in questions if question.get('category') == category and not question.get('is_competition')], question_amount - database_amount))
                data = {
                    'task': 'quiz',
                    'mode': mode,
                    'competition_id': competition_id,
                    'category': category,
                    'no': 1,
                    'questions': quiz_questions,
                    'question_amount': question_amount,
                    'correct_amount': 0,
                    'quiz_id': quiz_id,
                    'start_time': current_time,
                }
                firebaseService.add_data(DatabaseCollectionMap.TEMP, user_id, data)

                line_flex_str = __class__.__generate_question_line_flex(quiz_questions[0], quiz_id, 0, question_amount)
                return LineBotHelper.reply_message(event, [FlexMessage(alt_text='測驗題目', contents=FlexContainer.from_json(line_flex_str))])
            else:
                line_flex_template = firebaseService.get_data(
                    DatabaseCollectionMap.LINE_FLEX,
                    DatabaseDocumentMap.LINE_FLEX.get("quiz")
                ).get('select')
                quiz_flex_data = [quiz for quiz in quiz_flex_datas if quiz.get('enable') and quiz.get('mode') == mode]
                if len(quiz_flex_data) == 0:
                    # 確認選擇的測驗類別是否有開放
                    return LineBotHelper.reply_message(event, [TextMessage(text='目前尚未開放此測驗模式')])
                else:
                    for quiz in quiz_flex_data:
                        quiz['start_time'] = quiz.get('start_time') if quiz.get('start_time') else '無期限'
                        quiz['end_time'] = quiz.get('end_time') if quiz.get('end_time') else '無期限'
                    line_flex_json = FlexMessageHelper.create_carousel_bubbles(quiz_flex_data, json.loads(line_flex_template))
                    return LineBotHelper.reply_message(event, [FlexMessage(alt_text='選擇測驗類別', contents=FlexContainer.from_json(json.dumps(line_flex_json)))])
    
    def __generate_question_line_flex(question: dict, quiz_id: str, question_no: int, question_amount: int):
        """Returns
        生成題目的Line Flex
        """
        gold_star_url = "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gold_star_28.png"
        gray_star_url = "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gray_star_28.png"

        question.update({
            'quiz_id': quiz_id,
            'no': question_no + 1,
            'width': (100 // question_amount) * question_no
        })

        line_flex_quiz = firebaseService.get_data(
            DatabaseCollectionMap.LINE_FLEX,
            DatabaseDocumentMap.LINE_FLEX.get("quiz")
        )
        line_flex_str = line_flex_quiz.get('question_with_image') if question.get('image_url') else line_flex_quiz.get('question')
        line_flex_str = LineBotHelper.replace_variable(line_flex_str, question)
        # 生成星星
        difficulty = int(question.get('difficulty'))
        line_flex_str = LineBotHelper.replace_variable(line_flex_str, {"star_url": gold_star_url}, difficulty)
        line_flex_str = LineBotHelper.replace_variable(line_flex_str, {"star_url": gray_star_url}, 5 - difficulty)
        return line_flex_str
    
    def __generate_answer_line_flex(question: dict, is_correct: bool):
        """Returns
        生成答案的Line Flex
        """
        line_flex_quiz = firebaseService.get_data(
            DatabaseCollectionMap.LINE_FLEX,
            DatabaseDocumentMap.LINE_FLEX.get("quiz")
        )
        line_flex_str = line_flex_quiz.get('correct') if is_correct else line_flex_quiz.get('wrong')

        # 計算該題正確率
        total_correct_amount = question.get(f"{question.get('answer').upper()}_vote_count")
        total_correct_amount += 1 if is_correct else 0
        total_count = question.get('total_count') + 1
        correct_rate = round(total_correct_amount / total_count*100)
        question.update({
            'correct_rate': correct_rate
        })
        line_flex_str = LineBotHelper.replace_variable(line_flex_str, question)
        return line_flex_str

    def __create_answer_record(mode: str, user_id: str, quiz_id: str, question: dict, answer: str, timestamp: int):
        """
        記錄該題作答(選擇的答案人數+1)以及個別題目記錄到quiz_records(個人的答題紀錄)
        """
        # 更新該題作答人數(quiz_questions)
        column_map = {
            'a': 'A_vote_count',
            'b': 'B_vote_count',
            'c': 'C_vote_count',
            'd': 'D_vote_count'
        }
        column_name = column_map.get(answer)
        wks = spreadsheetService.sh.worksheet_by_title('quiz_questions')
        col_index = spreadsheetService.get_column_index(wks, column_name)
        row_index = int(question.get('id')) + 1
        spreadsheetService.update_cell_value('quiz_questions', (row_index, col_index), int(question.get(column_name)) + 1)

        # 紀錄該題作答(quiz_records)
        question_id = question.get('id')
        taiwan_tz = pytz.timezone('Asia/Taipei')
        event_time = datetime.fromtimestamp(timestamp/1000, taiwan_tz).strftime('%Y-%m-%d %H:%M:%S')
        wks = spreadsheetService.sh.worksheet_by_title('quiz_records')
        wks.append_table(values=[mode, quiz_id, user_id, question_id, answer, event_time])

    # 生成測驗結果
    def __generate_general_quiz_result(user_id: str, params: dict):
        """
        生成測驗結果，並記錄整個quiz結果到quiz_log(個人的測驗紀錄)
        """
        correct_amount = params.get('correct_amount')
        # 個別測驗紀錄正確率在quiz_log中
        wks = spreadsheetService.sh.worksheet_by_title('quiz_logs')
        wks.append_table(values=[params.get('quiz_id'), user_id, correct_amount, params.get('question_amount')])
        quiz_logs = spreadsheetService.get_worksheet_data('quiz_logs')
        defeat_rate = round(len([log for log in quiz_logs if log['correct_amount'] < correct_amount])/len(quiz_logs)*100, 2) if correct_amount > 0 else 0
        params.update({'defeat_rate': defeat_rate})
        
        # 產生測驗結果line flex
        line_flex_str = firebaseService.get_data(
            DatabaseCollectionMap.LINE_FLEX,
            DatabaseDocumentMap.LINE_FLEX.get("quiz")
        ).get('general_result')
        line_flex_str = LineBotHelper.replace_variable(line_flex_str, params)
        return line_flex_str
    
    def __generate_competition_quiz_result(user_id: str, params: dict):
        """
        生成測驗結果，並記錄整個quiz結果到compitition(個人的競賽測驗紀錄)
        """
        correct_amount = params.get('correct_amount')
        quiz_records = spreadsheetService.get_worksheet_data('quiz_records')
        
        # 測驗開始與結束時間計算
        current_time = params.get('start_time')
        current_time = datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S')
        end_time = [record for record in quiz_records if record.get('quiz_id') == params.get('quiz_id')][-1].get('timestamp')
        end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
        end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S')
        spend_time = end_time - current_time
        spend_time_str = LineBotHelper.convert_timedelta_to_string(spend_time)
        
        # 紀錄測驗結果資料
        wks = spreadsheetService.sh.worksheet_by_title('competitions')
        row_index = spreadsheetService.get_row_index(wks, 'quiz_id', params.get('quiz_id'))
        # 取得開始與結束的欄位索引並轉換成字母
        start_column_index = spreadsheetService.get_column_index(wks, 'end_time')
        start_column_index = chr(start_column_index + ord('A') - 1)
        end_column_index = spreadsheetService.get_column_index(wks, 'question_amount')
        end_column_index = chr(end_column_index + ord('A') - 1)
        
        spreadsheetService.update_cells_values('competitions', f"{start_column_index}{row_index}:{end_column_index}{row_index}", [[end_time_str, spend_time_str, correct_amount, params.get('question_amount')]])
        
        # 產生結果line flex
        line_flex_str = firebaseService.get_data(
            DatabaseCollectionMap.LINE_FLEX,
            DatabaseDocumentMap.LINE_FLEX.get("quiz")
        ).get('competition_result')
        hours, minutes, seconds = spend_time_str.split(':')
        params.update({'hours': hours, 'minutes': minutes, 'seconds': seconds})
        line_flex_str = LineBotHelper.replace_variable(line_flex_str, params)
        return line_flex_str
    
    def __check_competition_open_time(competition_id: str):
        """Returns
        bool: 是否在競賽時間內
        """
        quiz_flex_datas = spreadsheetService.get_worksheet_data('quizzes')
        quiz_flex_data = [quiz for quiz in quiz_flex_datas if quiz.get('enable') and quiz.get('competition_id') == competition_id][0]
        start_time = quiz_flex_data["start_time"]
        end_time = quiz_flex_data["end_time"]
        current_time = LineBotHelper.get_current_time()
        # 檢查測驗時間是否在設定的區間內
        taiwan_tz = pytz.timezone('Asia/Taipei')
        start_time = taiwan_tz.localize(datetime.strptime(start_time, '%Y-%m-%d %H:%M'))
        end_time = taiwan_tz.localize(datetime.strptime(end_time, '%Y-%m-%d %H:%M'))
        return current_time >= start_time and current_time <= end_time
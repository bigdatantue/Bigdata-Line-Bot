from config import Config
from map import Map, DatabaseCollectionMap, DatabaseDocumentMap, EquipmentStatus, Permission, LIFFSize
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
import math

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
            'equipment': Equipment,
            'quiz': Quiz,
            'faq': FAQ
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
    開課修業查詢
    """
    def execute(self, event, params):
        type = params.get('type')
        if type == 'open':
            quick_reply_data = firebaseService.get_data(
                DatabaseCollectionMap.QUICK_REPLY,
                DatabaseDocumentMap.QUICK_REPLY.get("course")
            ).get("semester")
            LineBotHelper.reply_message(event, [TextMessage(text=quick_reply_data.get('text'), quick_reply=QuickReplyHelper.create_quick_reply(quick_reply_data.get('actions')))])
                
        elif type == 'progress':
            # 查詢修課進度
            user_id = event.source.user_id
            user_details = spreadsheetService.get_worksheet_data('user_details')
            user_detail = next((user for user in user_details if user.get('user_id') == user_id), None)
            # 確認使用者填完的資料是否已經認證
            if not user_detail['verification']:
                return LineBotHelper.reply_message(event, [TextMessage(text='請先在圖文選單點擊【設定】中的【設定個人資料】填寫表單，並傳送學生證正面照片完成認證')])

            user_student_id = user_detail['student_id']
            user_courses = [course for course in spreadsheetService.get_worksheet_data('user_courses_records') if course.get('student_id') == user_student_id]
            # 取得課程資料
            courses_df = pd.DataFrame(spreadsheetService.get_worksheet_data('courses'))
            courses_records_df = pd.DataFrame(spreadsheetService.get_worksheet_data('course_records'))
            user_courses_df = pd.DataFrame(user_courses)
            # 確認使用者是否修過此微學程的課程
            if not user_courses:
                df_merged = pd.merge(courses_df, courses_records_df, on='course_id', how='left').astype(str)
                df_merged['semester'] = '-'
                df_merged['credit'] = 0
                df_merged['status'] = '未修畢'
                df_merged['color'] = '#000000'
            else:
                df_temp = pd.merge(user_courses_df, courses_records_df, left_on='record_id', right_on='id', how='inner')

                # 取得學生同課程最新的修課紀錄
                df_temp['id'] = df_temp['id'].astype(int)
                df_temp = df_temp.loc[df_temp.groupby("course_id")['id'].idxmax()]

                df_merged = pd.merge(courses_df, df_temp, on='course_id', how='left')
                df_merged[['status', 'color']] = df_merged.apply(lambda row: pd.Series(__class__.__get_study_status(row)), axis=1)
                df_merged['semester'] = df_merged.apply(lambda row: f"{int(row['year'])}-{int(row['semester'])}" if pd.notna(row['year']) and pd.notna(row['semester']) else '-', axis=1)
                df_merged['pass'] = pd.to_numeric(df_merged['pass']).fillna(0).astype(int)
                df_merged['credit'] = pd.to_numeric(df_merged['credit']).fillna(0).astype(int)

            # 取得line flex template以及替換修課資料變數
            line_flex_template = firebaseService.get_data(
                DatabaseCollectionMap.LINE_FLEX,
                DatabaseDocumentMap.LINE_FLEX.get("course")
            ).get('progress')
            for course_record in df_merged.to_dict(orient='records'):
                course_id = course_record['course_id']
                variable_dict = { f"{key}{course_id}": course_record[key] for key in ['status', 'category', 'semester', 'color'] }
                line_flex_template = LineBotHelper.replace_variable(line_flex_template, variable_dict)

            # 建立替換學分數據的字典
            completed_required_credit = df_merged[(df_merged['type'] == '必修') & df_merged['pass']]['credit'].sum()
            incompleted_required_credit = max(6 - completed_required_credit, 0)
            completed_elective_credit = df_merged[(df_merged['type'] == '選修') & df_merged['pass']]['credit'].sum()
            incompleted_elective_credit = max(4 - completed_elective_credit, 0)
            standard = '已達到發證標準' if incompleted_required_credit <= 0 and incompleted_elective_credit <= 0 else '尚未符合發證標準'
            color = '#00BB00' if standard == '已達到發證標準' else '#FF0000'
            credits_summary = {
                'completed_required_credit': completed_required_credit,
                'incompleted_required_credit': incompleted_required_credit,
                'completed_elective_credit': completed_elective_credit,
                'incompleted_elective_credit': incompleted_elective_credit,
                'standard': standard,
                'color': color
            }

            line_flex_str = LineBotHelper.replace_variable(line_flex_template, credits_summary)
            return LineBotHelper.reply_message(event, [FlexMessage(alt_text='修課進度', contents=FlexContainer.from_json(line_flex_str))])
            
        else:
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
                return LineBotHelper.reply_message(event, [FlexMessage(alt_text='詳細說明', contents=FlexContainer.from_json(line_flex_str))])
            
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

                    bubble_amount = 12
                    flex_message_bubbles = []
                    for i in range(math.ceil(len(courses) / bubble_amount)):
                        temp = courses[i*bubble_amount:i*bubble_amount+bubble_amount] if i*bubble_amount+bubble_amount < len(courses) else courses[i*bubble_amount:]
                        line_flex_json = FlexMessageHelper.create_carousel_bubbles(temp, json.loads(line_flex_template))
                        line_flex_str = json.dumps(line_flex_json)
                        flex_message_bubbles.append(FlexContainer.from_json(line_flex_str))
                return LineBotHelper.reply_message(event, [FlexMessage(alt_text=course_map.get(course_category), contents=flex) for flex in flex_message_bubbles])
            
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

    def __get_study_status(row):
        """Returns
        str: 學生修課狀態以及對應的顏色
        """
        if pd.notna(row['student_id']):
            if row['pass'] == 1:
                return '已修畢', '#00BB00'
            else:
                return '未通過', '#FF0000'
        else:
            return '未修畢', '#000000'
    
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
        
class Equipment(Task):
    """
    設備租借
    """
    def execute(self, event, params):
        user_id = event.source.user_id
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
        else:
            type = params.get('type')
            if type != 'borrow':
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
        # 為何要修改這邊的名稱呢？不直接在LIFF_APP中修改？
        # 因為LIFF_APP要發送Flex Message的變數名稱有底線的形式，所以只能在這裡配合修改
        for equipment in equipment_status_data[:int(params.get('amount'))]:
            equipment['borrowerId'] = borrower_id
            equipment['borrower'] = params.get('borrower')
            equipment['status'] = EquipmentStatus.LEND
            equipment['startDate'] = params.get('start_date')
            equipment['endDate'] = params.get('end_date')
            equipment['returnTime'] = params.get('return_time')
            equipment['borrowerData'] = {
                'department': params.get('borrower_department'),
                'email': params.get('borrower_email'),
                'name': params.get('name'),
                'phone': params.get('borrower_phone')
            }
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
    gold_star_url = "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gold_star_28.png"
    gray_star_url = "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gray_star_28.png"
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
            type = params.get('type')
            question_id = params.get('id')
            category = params.get('category')
            competition_id = params.get('competition_id')
            quiz_flex_datas = spreadsheetService.get_worksheet_data('quizzes')
            if mode == 'rank':
                # 排行榜
                rank_line_flex_str = __class__.__generate_rank_line_flex(competition_id, user_id)
                return LineBotHelper.reply_message(event, [FlexMessage(alt_text='排行榜', contents=FlexContainer.from_json(rank_line_flex_str))])
            elif mode == 'history' and not question_id:
                if type == 'user':
                    return __class__.__generate_personal_history_question(event, category, user_id)
                elif type == 'all':
                    return __class__.__generate_global_history_question(event, category)
                else:
                    return __class__.__generate_history_select(event, category)
            elif mode == 'history' and question_id:
                return __class__.__generate_complete_history_question(event, question_id)

            elif mode == 'competition_rule':
                # 測驗說明
                line_flex_str = firebaseService.get_data(
                    DatabaseCollectionMap.LINE_FLEX,
                    DatabaseDocumentMap.LINE_FLEX.get("quiz")
                ).get('competition_rule')
                userinfo_url = f'https://liff.line.me/{LIFFSize.TALL.value}/userinfo?userId={user_id}'
                line_flex_json = LineBotHelper.replace_variable(line_flex_str, {'category': category, 'competition_id': competition_id, 'userinfo_url': userinfo_url})
                return LineBotHelper.reply_message(event, [FlexMessage(alt_text='測驗說明', contents=FlexContainer.from_json(line_flex_json))])
            if category:
                quiz_id = LineBotHelper.generate_id()
                current_time = LineBotHelper.get_current_time().strftime('%Y-%m-%d %H:%M:%S')
                if mode == 'competition':
                    # 確認使用者是否有在設定中填寫資料
                    user_details = spreadsheetService.get_worksheet_data('user_details')
                    user_detail = [user for user in user_details if user.get('user_id') == user_id]
                    if len(user_detail) == 0:
                        return LineBotHelper.reply_message(event, [TextMessage(text='請先在圖文選單點擊【設定】中的【設定個人資料】填寫表單，完成填寫後才可以參與競賽')])
                    
                    competition_logs = spreadsheetService.get_worksheet_data('competitions')
                    competition_log = [log for log in competition_logs if log.get('competition_id') == competition_id and log.get('user_id') == user_id]
                    if len(competition_log) > 0:
                        quiz_id = competition_log[0].get('quiz_id')
                        quiz_records = spreadsheetService.get_worksheet_data('quiz_records')
                        quiz_record = [record for record in quiz_records if record.get('quiz_id') == quiz_id]
                        if competition_id and not __class__.__check_competition_open_time(competition_id):
                            return LineBotHelper.reply_message(event, [TextMessage(text='該競賽已結束!')])
                        elif competition_log[0].get('time_spent'):
                            return LineBotHelper.reply_message(event, [TextMessage(text='您已參加過此競賽')])
                        elif len(quiz_record) > 0:
                            firebaseService.delete_data(DatabaseCollectionMap.TEMP, user_id)
                            return LineBotHelper.reply_message(event, [TextMessage(text='偵測到異常行為，視為未完賽')])
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
                quiz_questions = random.sample([question for question in questions if question.get('category') == category and not question.get('is_competition')], database_amount)
                quiz_questions.extend(random.sample([question for question in questions if question.get('category') == category and question.get('is_competition')], question_amount - database_amount))
                random.shuffle(quiz_questions)
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
                line_flex_data = firebaseService.get_data(
                    DatabaseCollectionMap.LINE_FLEX,
                    DatabaseDocumentMap.LINE_FLEX.get("quiz")
                )
                line_flex_template = line_flex_data.get('general_select') if mode == 'general' else line_flex_data.get('competition_select')

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
        question.update({
            'quiz_id': quiz_id,
            'no': question_no + 1,
            'width': round((100 / question_amount) * question_no)
        })

        line_flex_quiz = firebaseService.get_data(
            DatabaseCollectionMap.LINE_FLEX,
            DatabaseDocumentMap.LINE_FLEX.get("quiz")
        )
        line_flex_str = line_flex_quiz.get('question_with_image') if question.get('image_url') else line_flex_quiz.get('question')
        line_flex_str = LineBotHelper.replace_variable(line_flex_str, question)
        # 生成星星
        difficulty = int(question.get('difficulty'))
        line_flex_str = LineBotHelper.replace_variable(line_flex_str, {"star_url": __class__.gold_star_url}, difficulty)
        line_flex_str = LineBotHelper.replace_variable(line_flex_str, {"star_url": __class__.gray_star_url}, 5 - difficulty)
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
        user_infos = spreadsheetService.get_worksheet_data('user_info')
        user_picture_url = [user for user in user_infos if user.get('user_id') == user_id][0].get('picture_url')
        params.update({'hours': hours, 'minutes': minutes, 'seconds': seconds, 'user_picture_url': user_picture_url})
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
    
    def __generate_rank_line_flex(competition_id: str, user_id: str):
        """
        生成排行榜的Line Flex
        """
        def format_time_spent_str(time_spent: str):
            """Returns
            str: 格式化後的時間(只留mm:ss, 超過59:59則回傳>59:59)
            """
            if time_spent.split(':')[0] == '0':
                return ':'.join(time_spent.split(':')[1:])
            return '>59:59'
        
        def get_user_data(user_info: list, user_id: str):
            """Returns
            dict: 使用者資料
            """
            info = [info for info in user_info if info.get('user_id') == user_id][0]
            return {
                'mode': 'competition',
                'user_display_name': info.get('display_name'),
                'user_picture_url': info.get('picture_url'),
                'user_rank': '-',
                'user_correct_rate': '-',
                'user_time_spent': '-',
            }
            
        def generate_mask(display_name: str):
            """Returns
            str: 隱藏使用者名稱
            """
            if len(display_name) == 1:
                display_name = '*'
            elif len(display_name) == 2:
                display_name = display_name[0] + '*'
            elif len(display_name) == 3:
                display_name = display_name[0] + '*' + display_name[-1]
            else:
                display_name = display_name[0] + '**' + display_name[-1]
            return display_name

        user_info = spreadsheetService.get_worksheet_data('user_info')
        competions = spreadsheetService.get_worksheet_data('competitions')
        competition = [competition for competition in competions if competition.get('competition_id') == competition_id and competition.get('time_spent')]
        merged_data = []
        data = {}
        if len(competition) == 0:
            # 還未有人參賽
            data = get_user_data(user_info, user_id)
        else:
            merged_data_df = pd.merge(pd.DataFrame(user_info), pd.DataFrame(competition), on='user_id')

            # 依照正確率、答題時間排序進行排名
            merged_data_df['rank'] = merged_data_df[['correct_amount', 'time_spent']].apply(
                lambda x: (-x['correct_amount'], x['time_spent']), axis=1
            ).rank(method='min').astype(int)
            merged_data_df = merged_data_df.sort_values(by='rank', ascending=True, ignore_index=True)
            merged_data = merged_data_df.to_dict(orient='records')
            user_competition = [data for data in merged_data if data.get('user_id') == user_id]
            
            if len(user_competition) == 0:
                # 使用者未參賽
                data = get_user_data(user_info, user_id)
            else:
                # 使用者已參賽
                user_competition = user_competition[0]
                user_time_spent = format_time_spent_str(user_competition.get('time_spent'))
                data = {
                    'mode': 'competition',
                    'user_display_name': user_competition.get('display_name'),
                    'user_picture_url': user_competition.get('picture_url'),
                    'user_rank': user_competition.get('rank'),
                    'user_correct_rate': round(int(user_competition.get('correct_amount')) / int(user_competition.get('question_amount')) * 100),
                    'user_time_spent': user_time_spent,
                }

        line_flex_str = firebaseService.get_data(
            DatabaseCollectionMap.LINE_FLEX,
            DatabaseDocumentMap.LINE_FLEX.get("quiz")
        ).get('rank')
        line_flex_str = LineBotHelper.replace_variable(line_flex_str, data)

        # 生成排行榜前5名
        for i in range(5):
            # 若前五名有資料則顯示，否則顯示'-'
            if len(merged_data) >= i + 1:
                merged_data[i]['correct_rate'] = round(int(merged_data[i].get('correct_amount')) / int(merged_data[i].get('question_amount')) * 100)
                merged_data[i]['display_name'] = generate_mask(merged_data[i].get('display_name'))
                merged_data[i]['time_spent'] = format_time_spent_str(merged_data[i].get('time_spent'))
                line_flex_str = LineBotHelper.replace_variable(line_flex_str, merged_data[i], 1)
            else:
                data = {
                    'rank': '-',
                    'display_name': '-',
                    'picture_url': 'https://example.com/default.png',
                    'correct_rate': '-',
                    'time_spent': '-'
                }
                line_flex_str = LineBotHelper.replace_variable(line_flex_str, data)
                break
        return line_flex_str

    def __generate_history_select(event, category):
        """Return
        使用者點擊歷史答題功能後，生成讓使用者選擇「我的錯題」和「全服錯題」選項的Flex Message
        """
        line_flex_str = firebaseService.get_data(
            DatabaseCollectionMap.LINE_FLEX,
            DatabaseDocumentMap.LINE_FLEX.get("quiz")
        ).get('history_select')
        line_flex_str = LineBotHelper.replace_variable(line_flex_str, {"category" : category})
        return LineBotHelper.reply_message(event, [FlexMessage(alt_text='選擇查看範圍', contents=FlexContainer.from_json(line_flex_str))])

    def __generate_global_history_question(event, category):
        """Return
        生成「全服錯題」的Carousel，包含全服答錯率最高的十題
        """
        quiz_questions = spreadsheetService.get_worksheet_data('quiz_questions')
        # 過濾掉回答數為0、且為同個類別主題的題目
        filtered_questions = [q for q in quiz_questions if q['category'] == category and float(q['total_count']) != 0]
        if not filtered_questions:
            return LineBotHelper.reply_message(event, [TextMessage(text='全服尚未有任何答題紀錄！')])
        else:
            # 根據正確率排序並選取前10個題目（正確率最低的前十題）
            sorted_questions = sorted(filtered_questions, key=lambda x: float(x['correct_rate']))[:10]

            # 生成carousel bubble
            line_flex_str = firebaseService.get_data(
                DatabaseCollectionMap.LINE_FLEX,
                DatabaseDocumentMap.LINE_FLEX.get("quiz")
            ).get('history_question_list')

            for question in sorted_questions:
                question['width'] = 100 - question['correct_rate']
                difficulty = int(question['difficulty'])

                # 根據難度逐個替換 star_url
                for i in range(difficulty):
                    question[f'star_url_{i+1}'] = __class__.gold_star_url  # 替換金色星星
                for i in range(5 - difficulty):
                    question[f'star_url_{difficulty + i + 1}'] = __class__.gray_star_url  # 替換灰色星星

            line_flex_str = FlexMessageHelper.create_carousel_bubbles(sorted_questions, json.loads(line_flex_str))
            line_flex_str = json.dumps(line_flex_str)
            return LineBotHelper.reply_message(event, [FlexMessage(alt_text='全服答錯率最高的前10個題目', contents=FlexContainer.from_json(line_flex_str))])

    def __generate_personal_history_question(event, category, user_id):
        """Return
        生成「我的錯題」的Carousel，包含個人答錯率最高的十題
        """
        quiz_records_df = pd.DataFrame(spreadsheetService.get_worksheet_data('quiz_records'))
        quiz_questions_df = pd.DataFrame(spreadsheetService.get_worksheet_data('quiz_questions'))

        # 篩選該類別題目
        quiz_questions_df = quiz_questions_df[quiz_questions_df['category'] == category]
        
        # 判斷該類別是否有任何答題記錄（依據total_count欄位）
        if quiz_questions_df['total_count'].sum() == 0:
            return LineBotHelper.reply_message(event, [TextMessage(text=f'類別「{category}」尚未有任何答題記錄！')])
        else:
            # 為了避免兩個DataFrame欄位名稱重複，將quiz_questions的answer欄位改名為correct_answer
            quiz_questions_df = quiz_questions_df.rename(columns={'answer': 'correct_answer'})
            merged_df = pd.merge(quiz_records_df, quiz_questions_df, left_on='question_id', right_on='id', how='left')

            # 選取user_id為user_id的資料（該使用者個人的答題資料）
            user_records_df = merged_df[merged_df['user_id'] == user_id]

            # 判斷使用者是否有作答過任何題目（是否在quiz_records中有該使用者的答題記錄）
            if user_records_df.empty:
                return LineBotHelper.reply_message(event, [TextMessage(text='您尚未作答過任何題目！')])
            else:
                # 新增is_correct欄位，判斷使用者的答案是否正確
                user_records_df['is_correct'] = user_records_df.apply(
                    lambda row: 1 if row['answer'].lower() == row['correct_answer'].lower() else 0, axis=1
                )

                # 計算每個題目的答題次數和答對次數
                question_stats = user_records_df.groupby('question_id').agg(
                    total_attempts=('question_id', 'size'),
                    correct_attempts=('is_correct', 'sum')
                ).reset_index()

                # 計算每個題目的答對率
                question_stats['personal_correct_rate'] = (question_stats['correct_attempts'] / question_stats['total_attempts']) * 100

                # 合併question_stats和quiz_questions，並選取personal_correct_rate最低的前10個題目
                ten_questions_df = pd.merge(question_stats, quiz_questions_df, left_on='question_id', right_on='id', how='left').sort_values(by='personal_correct_rate').head(10)
                
                # 加入width欄位
                ten_questions_df['width'] = 100 - ten_questions_df['correct_rate']  # 以正確率計算錯誤率並存入
                # 加入star_url欄位，根據difficulty計算
                for i, row in ten_questions_df.iterrows():
                    difficulty = int(row['difficulty'])

                    # 生成星星列表
                    star_urls = [__class__.gold_star_url] * difficulty + [__class__.gray_star_url] * (5 - difficulty)

                    # 將star_url列表中的每個URL存入對應的欄位
                    for index, star_url in enumerate(star_urls):
                        ten_questions_df.at[i, f'star_url_{index + 1}'] = star_url

                # 抓模板
                line_flex_str = firebaseService.get_data(
                    DatabaseCollectionMap.LINE_FLEX,
                    DatabaseDocumentMap.LINE_FLEX.get("quiz")
                ).get('history_question_list')

                # 生成carousel bubble
                line_flex_str = FlexMessageHelper.create_carousel_bubbles(ten_questions_df.to_dict('records'), json.loads(line_flex_str))
                line_flex_str = json.dumps(line_flex_str)
                return LineBotHelper.reply_message(event, [FlexMessage(alt_text='個人答錯率最高的前10個題目', contents=FlexContainer.from_json(line_flex_str))])

    def __generate_complete_history_question(event, question_id):
        """Return
        生成完整測驗題目的Flex Message（包含答案）
        """
        quiz_questions = spreadsheetService.get_worksheet_data('quiz_questions')

        # 只提取id == question_id的題目資料
        quiz_question = [question for question in quiz_questions if question.get('id') == int(question_id)][0]

        # 生成題目的Line Flex
        line_flex_str = firebaseService.get_data(
            DatabaseCollectionMap.LINE_FLEX,
            DatabaseDocumentMap.LINE_FLEX.get("quiz")
        ).get('history_question_with_image' if quiz_question.get('image_url') else 'history_question')
        quiz_question['width'] = 100 - quiz_question['correct_rate']
        line_flex_str = LineBotHelper.replace_variable(line_flex_str, quiz_question)

        # 生成星星
        difficulty = int(quiz_question['difficulty'])
        line_flex_str = LineBotHelper.replace_variable(line_flex_str, {"star_url": __class__.gold_star_url}, difficulty)
        line_flex_str = LineBotHelper.replace_variable(line_flex_str, {"star_url": __class__.gray_star_url}, 5 - difficulty)
        return LineBotHelper.reply_message(event, [FlexMessage(alt_text='完整測驗題目', contents=FlexContainer.from_json(line_flex_str))])

class FAQ(Task):
    """
    常見問答
    """
    def execute(self, event, params):
        id = params.get('id')
        faq_questions = spreadsheetService.get_worksheet_data('faq_questions')
        answer = [faq for faq in faq_questions if faq.get('id') == int(id)][0].get('answer')
        return LineBotHelper.reply_message(event, [TextMessage(text=answer)])
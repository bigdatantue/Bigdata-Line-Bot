from .base import Feature, register_feature
from linebot.v3.messaging import (
    TextMessage,
    FlexMessage,
    FlexContainer
)
from api.linebot_helper import LineBotHelper, QuickReplyHelper, FlexMessageHelper
from map import Map, DatabaseCollectionMap
import pandas as pd
import json
import math

@register_feature('course')
class Course(Feature):
    """
    開課修業查詢
    """
    def execute_message(self, event, **kwargs):
        line_flex_str = self.firebaseService.get_data(
            DatabaseCollectionMap.LINE_FLEX,
            "course"
        ).get("select")
        return LineBotHelper.reply_message(event, [FlexMessage(alt_text='開課時間查詢', contents=FlexContainer.from_json(line_flex_str))])

    def execute_postback(self, event, **kwargs):
        params = kwargs.get('params')
        type = params.get('type')
        if type == 'open':
            quick_reply_data = self.firebaseService.get_data(
                DatabaseCollectionMap.QUICK_REPLY,
                "course"
            ).get("semester")
            return LineBotHelper.reply_message(event, [TextMessage(text=quick_reply_data.get('text'), quick_reply=QuickReplyHelper.create_quick_reply(quick_reply_data.get('actions')))])
                
        elif type == 'progress':
            # 查詢修課進度
            user_id = event.source.user_id

            user_detail = self.firebaseService.filter_data('users', [('userId', '==', user_id)])[0].get('details')
            # 確認使用者填完的資料是否已經認證
            if not user_detail or not user_detail['verification']:
                return LineBotHelper.reply_message(event, [TextMessage(text='請先在圖文選單點擊【設定】中的【設定個人資料】填寫表單，並傳送學生證正面照片完成認證')])

            student_id = user_detail['studentId']
            user_courses = self.firebaseService.filter_data('course_study_records', [('student_id', '==', student_id)])
            # 取得課程資料
            courses_df = pd.DataFrame(self.firebaseService.get_collection_data(DatabaseCollectionMap.COURSE))
            courses_records_df = pd.DataFrame(self.firebaseService.get_collection_data(DatabaseCollectionMap.COURSE_OPEN))
            user_courses_df = pd.DataFrame(user_courses)
            # 確認使用者是否修過此微學程的課程
            if not user_courses:
                df_merged = pd.merge(courses_df, courses_records_df, on='course_id', how='left').astype(str)
                df_merged['semester'] = '-'
                df_merged['credit'] = 0
                df_merged['status'] = '未修畢'
                df_merged['color'] = '#000000'
            else:
                df_temp = pd.merge(user_courses_df, courses_records_df, left_on='record_id', right_on='id', how='inner', suffixes=(None, '_to_drop'))
                df_temp = df_temp.drop(columns=['id_to_drop'])

                # 取得學生同課程最新的修課紀錄
                df_temp['id'] = df_temp['id'].astype(int)
                df_temp = df_temp.loc[df_temp.groupby("course_id")['id'].idxmax()]

                df_merged = pd.merge(courses_df, df_temp, on='course_id', how='left')
                df_merged[['status', 'color']] = df_merged.apply(lambda row: pd.Series(self.__get_study_status(row)), axis=1)
                df_merged['semester'] = df_merged.apply(lambda row: f"{int(row['year'])}-{int(row['semester'])}" if pd.notna(row['year']) and pd.notna(row['semester']) else '-', axis=1)
                df_merged['pass'] = pd.to_numeric(df_merged['pass']).fillna(0).astype(int)
                df_merged['credit'] = pd.to_numeric(df_merged['credit']).fillna(0).astype(int)

            # 取得line flex template以及替換修課資料變數
            line_flex_template = self.firebaseService.get_data(
                DatabaseCollectionMap.LINE_FLEX,
                "course"
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

            # 如果有course_record_id，則回傳該課程的詳細資訊
            if course_record_id:
                course = self.__get_course_records(id=int(course_record_id))[0]
                line_flex_template = self.firebaseService.get_data(
                    DatabaseCollectionMap.LINE_FLEX,
                    "course"
                ).get('detail')
                line_flex_str = LineBotHelper.replace_variable(line_flex_template, course)
                return LineBotHelper.reply_message(event, [FlexMessage(alt_text='詳細說明', contents=FlexContainer.from_json(line_flex_str))])
            
            # 否則如果有course_category，則回傳該類別的課程資訊
            elif course_category:
                course_map = {
                    'overview': '總覽',
                    'basic': '基礎',
                    'advanced': '進階',
                    'practical': '實務'
                }
                # 拆解學年和學期
                year = params.get('semester')[:3]
                semester = params.get('semester')[3:]
                courses = self.__get_course_records(year=year, semester=semester)
                if course_category != 'overview':
                    courses = [course for course in courses if course.get('category') == course_map.get(course_category)]
                if len(courses) == 0:
                    message = f'{year}學年度第{semester}學期沒有{course_map.get(course_category)}課程資料'
                    LineBotHelper.reply_message(event, [TextMessage(text=message)])
                else:
                    line_flex_template = self.firebaseService.get_data(
                        DatabaseCollectionMap.LINE_FLEX, 
                        "course"
                    ).get('summary')

                    bubble_amount = 12
                    flex_message_bubbles = []
                    for i in range(math.ceil(len(courses) / bubble_amount)):
                        temp = courses[i*bubble_amount:i*bubble_amount+bubble_amount] if i*bubble_amount+bubble_amount < len(courses) else courses[i*bubble_amount:]
                        line_flex_json = FlexMessageHelper.create_carousel_bubbles(temp, json.loads(line_flex_template))
                        line_flex_str = json.dumps(line_flex_json)
                        flex_message_bubbles.append(FlexContainer.from_json(line_flex_str))
                return LineBotHelper.reply_message(event, [FlexMessage(alt_text=course_map.get(course_category), contents=flex) for flex in flex_message_bubbles])
            
            # 否則回傳課程類別的快速回覆選項
            else:
                quick_reply_data = self.firebaseService.get_data(
                    DatabaseCollectionMap.QUICK_REPLY,
                    "course"
                ).get("category")
                for i, text in enumerate(quick_reply_data.get('actions')):
                    quick_reply_data.get('actions')[i] = LineBotHelper.replace_variable(text, params)
                return LineBotHelper.reply_message(event, [TextMessage(text=quick_reply_data.get('text'), quick_reply=QuickReplyHelper.create_quick_reply(quick_reply_data.get('actions')))])
            
    def __get_course_records(self, id=None, year=None, semester=None):
        """Returns
        list: 課程資料
        """
        courses = self.firebaseService.get_collection_data(DatabaseCollectionMap.COURSE)
        course_records = self.firebaseService.get_collection_data(DatabaseCollectionMap.COURSE_OPEN)

        courses_df = pd.DataFrame(courses)
        course_records_df = pd.DataFrame(course_records)

        # 將課程資料與課程紀錄資料合併
        merged_data = pd.merge(courses_df, course_records_df, on='course_id', how='inner')
        # 根據條件篩選資料
        if id:
            merged_data = merged_data[merged_data['id'] == id]
        elif year and semester:
            merged_data = merged_data[(merged_data['year'] == year) & (merged_data['semester'] == semester)]
        return merged_data.to_dict(orient='records')
    
    def __get_study_status(self, row):
        """Returns
        Tuple: (修課狀態, 修課狀態顏色)
        """
        if pd.notna(row['student_id']):
            if row['pass'] == 1:
                return '已修畢', '#00BB00'
            else:
                return '未通過', '#FF0000'
        else:
            return '未修畢', '#000000'
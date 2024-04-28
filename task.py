from config import Config
from map import Map, DatabaseCollectionMap, DatabaseDocumentMap, FlexParamMap
from api.linebot_helper import LineBotHelper, QuickReplyHelper, FlexMessageHelper
from linebot.v3.messaging import (
    TextMessage,
    FlexMessage,
    FlexContainer
)
from abc import ABC, abstractmethod
import json
import pandas as pd

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
                DatabaseDocumentMap.LINE_FLEX.get("course").get("detail")
            ).get('flex')
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
                    DatabaseDocumentMap.LINE_FLEX.get("course").get("carousel")
                ).get('flex')
                line_flex_json = FlexMessageHelper.create_carousel_bubbles(courses, json.loads(line_flex_template), FlexParamMap.COURSE)
                line_flex_str = json.dumps(line_flex_json)
                LineBotHelper.reply_message(event, [FlexMessage(alt_text=course_map.get(course_category), contents=FlexContainer.from_json(line_flex_str))])
            return
        
        #否則回傳課程類別的快速回覆選項
        else:
            quick_reply_data = firebaseService.get_data(
                DatabaseCollectionMap.QUICK_REPLY,
                DatabaseDocumentMap.QUICK_REPLY.get("course").get("category")
            )
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
            DatabaseDocumentMap.LINE_FLEX.get("community").get("microcourse")
        ).get('flex')
        line_flex_json = FlexMessageHelper.create_carousel_bubbles(microcourses, json.loads(line_flex_template), FlexParamMap.COMMUNITY)
        line_flex_str = json.dumps(line_flex_json)
        LineBotHelper.reply_message(event, [FlexMessage(alt_text='社群學習資源', contents=FlexContainer.from_json(line_flex_str))])
        return
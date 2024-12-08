from .base import Feature, register_feature
from linebot.v3.messaging import (
    TextMessage,
    FlexMessage,
    FlexContainer
)
from map import DatabaseCollectionMap, LIFFSize
from api.linebot_helper import LineBotHelper, FlexMessageHelper
import pandas as pd
import json
import random
import pytz
from datetime import datetime

@register_feature('quiz')
class Quiz(Feature):
    """
    知識測驗
    """
    gold_star_url = "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gold_star_28.png"
    gray_star_url = "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gray_star_28.png"
    def execute_message(self, event, **kwargs):
        line_flex_str = self.firebaseService.get_data(
            DatabaseCollectionMap.LINE_FLEX,
            "quiz"
        ).get('start')
        return LineBotHelper.reply_message(event, [FlexMessage(alt_text='知識測驗', contents=FlexContainer.from_json(line_flex_str))])

    def execute_postback(self, event, **kwargs):
        params = kwargs.get('params')
        user_id = event.source.user_id
        question_no = params.get('no')
        if question_no:
            question_no = int(question_no)
            # 從temp取得題目
            temp_data = self.firebaseService.get_data(DatabaseCollectionMap.TEMP, user_id)
            quiz_id = params.get('quiz_id')
            
            # 防止點選之前的測驗
            if not temp_data or quiz_id != temp_data.get('quiz_id'):
                return LineBotHelper.reply_message(event, [TextMessage(text='該測驗已結束！')])

            # 防止重複作答
            if question_no < temp_data.get('no'):
                return LineBotHelper.reply_message(event, [TextMessage(text='請勿重複作答!')])
            
            # 防止競賽已結束後繼續作答
            competition_id = temp_data.get('competition_id')
            if competition_id and not self.__check_competition_open_time(competition_id):
                return LineBotHelper.reply_message(event, [TextMessage(text='該競賽已結束!')])
            
            quiz_questions = temp_data.get('questions')
            
            # 使用者的答案
            answer = params.get('answer').lower()

            # 判斷答案是否正確
            last_quiz_question = quiz_questions[question_no - 1]
            is_correct = answer == last_quiz_question.get('answer').lower()
            answer_line_flex_str = self.__generate_answer_line_flex(last_quiz_question, is_correct)

            # 記錄該題作答(選擇的答案人數+1)
            self.__create_answer_record(temp_data.get('mode'), user_id, temp_data.get('quiz_id'), last_quiz_question, answer)
            if is_correct:
                temp_data['correct_amount'] += 1

            if question_no < temp_data.get('question_amount'):
                question_line_flex_str = self.__generate_question_line_flex(quiz_questions[question_no], quiz_id, question_no, temp_data.get('question_amount'))
                self.firebaseService.update_data(DatabaseCollectionMap.TEMP, user_id, {'no': question_no + 1, 'correct_amount': temp_data.get('correct_amount')})
                return LineBotHelper.reply_message(event, [
                    FlexMessage(alt_text='測驗解答', contents=FlexContainer.from_json(answer_line_flex_str)),
                    FlexMessage(alt_text='測驗題目', contents=FlexContainer.from_json(question_line_flex_str))
                ])
            else:
                # 生成測驗結果
                mode = temp_data.get('mode')
                if mode == 'general':
                    # 一般模式                    
                    result_line_flex_str = self.__generate_general_quiz_result(user_id, temp_data)
                else:
                    # 競賽模式
                    result_line_flex_str = self.__generate_competition_quiz_result(user_id, temp_data)
                self.firebaseService.delete_data(DatabaseCollectionMap.TEMP, user_id)
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
            quiz_flex_datas = self.firebaseService.get_collection_data(DatabaseCollectionMap.QUIZ)

            if mode == 'rank':
                # 排行榜
                rank_line_flex_str = self.__generate_rank_line_flex(competition_id, user_id)
                return LineBotHelper.reply_message(event, [FlexMessage(alt_text='排行榜', contents=FlexContainer.from_json(rank_line_flex_str))])
            elif mode == 'history' and not question_id:
                if type == 'user':
                    return self.__generate_personal_history_question(event, category, user_id)
                elif type == 'all':
                    return self.__generate_global_history_question(event, category)
                else:
                    return self.__generate_history_select(event, category)
            elif mode == 'history' and question_id:
                return self.__generate_complete_history_question(event, question_id)

            elif mode == 'competition_rule':
                # 測驗說明
                line_flex_str = self.firebaseService.get_data(
                    DatabaseCollectionMap.LINE_FLEX,
                    "quiz"
                ).get('competition_rule')
                userinfo_url = f'https://liff.line.me/{LIFFSize.TALL.value}/userinfo?userId={user_id}'
                line_flex_json = LineBotHelper.replace_variable(line_flex_str, {'category': category, 'competition_id': competition_id, 'userinfo_url': userinfo_url})
                return LineBotHelper.reply_message(event, [FlexMessage(alt_text='測驗說明', contents=FlexContainer.from_json(line_flex_json))])
            if category:
                quiz_id = LineBotHelper.generate_id()
                current_time = LineBotHelper.get_current_time()
                if mode == 'competition':
                    # 確認使用者是否有在設定中填寫資料
                    user_detail = self.firebaseService.get_data(DatabaseCollectionMap.USER, user_id).get('details')
                    if not user_detail:
                        return LineBotHelper.reply_message(event, [TextMessage(text='請先在圖文選單點擊【設定】中的【設定個人資料】填寫表單，完成填寫後才可以參與競賽')])
                    
                    competition_log = self.firebaseService.filter_data(DatabaseCollectionMap.COMPETITION, [('competition_id', '==', competition_id), ('user_id', '==', user_id)])
                    if len(competition_log) > 0:
                        quiz_id = competition_log[0].get('quiz_id')
                        quiz_record = self.firebaseService.filter_data(DatabaseCollectionMap.QUIZ_RECORD, [('quiz_id', '==', quiz_id)])
                        if competition_id and not self.__check_competition_open_time(competition_id):
                            return LineBotHelper.reply_message(event, [TextMessage(text='該競賽已結束!')])
                        elif competition_log[0].get('time_spent'):
                            return LineBotHelper.reply_message(event, [TextMessage(text='您已參加過此競賽')])
                        elif len(quiz_record) > 0:
                            self.firebaseService.delete_data(DatabaseCollectionMap.TEMP, user_id)
                            return LineBotHelper.reply_message(event, [TextMessage(text='偵測到異常行為，視為未完賽')])
                        else:
                            return LineBotHelper.reply_message(event, [TextMessage(text='您的競賽已在進行中')])
                    if self.__check_competition_open_time(competition_id):
                        self.firebaseService.add_data(
                            DatabaseCollectionMap.COMPETITION,
                            quiz_id,
                            {
                                'competition_id': competition_id,
                                'quiz_id': quiz_id, 'user_id': user_id,
                                'start_time': current_time
                            }
                        )
                    else:
                        return LineBotHelper.reply_message(event, [TextMessage(text='目前尚未開放測驗')])
                # 隨機抽取題目，並存入TEMP
                quiz_flex_data = [quiz for quiz in quiz_flex_datas if quiz.get('enable') and quiz.get('mode') == mode and quiz.get('category') == category][0]
                question_amount = quiz_flex_data.get('question_amount')
                database_amount = quiz_flex_data.get('database_amount')
                quiz_questions = random.sample(self.firebaseService.filter_data(DatabaseCollectionMap.QUIZ_QUESTION, [('category', '==', category), ('is_competition', '==', False)]) , database_amount)
                quiz_questions.extend(random.sample(self.firebaseService.filter_data(DatabaseCollectionMap.QUIZ_QUESTION, [('category', '==', category), ('is_competition', '==', True)]), question_amount - database_amount))
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
                self.firebaseService.add_data(DatabaseCollectionMap.TEMP, user_id, data)

                line_flex_str = self.__generate_question_line_flex(quiz_questions[0], quiz_id, 0, question_amount)
                return LineBotHelper.reply_message(event, [FlexMessage(alt_text='測驗題目', contents=FlexContainer.from_json(line_flex_str))])
            else:
                line_flex_data = self.firebaseService.get_data(
                    DatabaseCollectionMap.LINE_FLEX,
                    "quiz"
                )
                line_flex_template = line_flex_data.get('general_select') if mode == 'general' else line_flex_data.get('competition_select')

                quiz_flex_data = [quiz for quiz in quiz_flex_datas if quiz.get('enable') and quiz.get('mode') == mode]
                if len(quiz_flex_data) == 0:
                    # 確認選擇的測驗類別是否有開放
                    return LineBotHelper.reply_message(event, [TextMessage(text='目前尚未開放此測驗模式')])
                else:
                    taiwan_tz = pytz.timezone('Asia/Taipei')
                    for quiz in quiz_flex_data:
                        quiz['start_time'] = quiz.get('start_time').astimezone(taiwan_tz).strftime('%Y-%m-%d %H:%M') if quiz.get('start_time') else '無期限'
                        quiz['end_time'] = quiz.get('end_time').astimezone(taiwan_tz).strftime('%Y-%m-%d %H:%M') if quiz.get('end_time') else '無期限'
                    line_flex_json = FlexMessageHelper.create_carousel_bubbles(quiz_flex_data, json.loads(line_flex_template))
                    return LineBotHelper.reply_message(event, [FlexMessage(alt_text='選擇測驗類別', contents=FlexContainer.from_json(json.dumps(line_flex_json)))])
    
    def __generate_question_line_flex(self, question: dict, quiz_id: str, question_no: int, question_amount: int):
        """Returns
        生成題目的Line Flex
        """
        question.update({
            'quiz_id': quiz_id,
            'no': question_no + 1,
            'width': round((100 / question_amount) * question_no)
        })

        line_flex_quiz = self.firebaseService.get_data(
            DatabaseCollectionMap.LINE_FLEX,
            "quiz"
        )
        line_flex_str = line_flex_quiz.get('question_with_image') if question.get('image_url') else line_flex_quiz.get('question')
        line_flex_str = LineBotHelper.replace_variable(line_flex_str, question)
        # 生成星星
        difficulty = int(question.get('difficulty'))
        line_flex_str = LineBotHelper.replace_variable(line_flex_str, {"star_url": self.gold_star_url}, difficulty)
        line_flex_str = LineBotHelper.replace_variable(line_flex_str, {"star_url": self.gray_star_url}, 5 - difficulty)
        return line_flex_str
    
    def __generate_answer_line_flex(self, question: dict, is_correct: bool):
        """Returns
        生成答案的Line Flex
        """
        line_flex_quiz = self.firebaseService.get_data(
            DatabaseCollectionMap.LINE_FLEX,
            "quiz"
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

    def __create_answer_record(self, mode: str, user_id: str, quiz_id: str, question: dict, answer: str):
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
        self.firebaseService.update_data(
            DatabaseCollectionMap.QUIZ_QUESTION,
            str(question.get('id')),
            {
                column_name: question.get(column_name) + 1,
                'total_count': question.get('total_count') + 1,
                'correct_count': question.get('correct_count') + 1 if answer == question.get('answer').lower() else question.get('correct_count'),
                'wrong_count': question.get('wrong_count') + 1 if answer != question.get('answer').lower() else question.get('wrong_count')
            }
        )

        # 紀錄該題作答(quiz_records)
        question_id = question.get('id')
        taiwan_tz = pytz.timezone('Asia/Taipei')
        event_time = LineBotHelper.get_current_time().astimezone(taiwan_tz)
        self.firebaseService.add_data(
            DatabaseCollectionMap.QUIZ_RECORD,
            LineBotHelper.generate_id(),
            {
                'mode': mode,
                'quiz_id': quiz_id,
                'user_id': user_id,
                'question_id': question_id,
                'answer': answer,
                'timestamp': event_time
            }
        )

    def __generate_general_quiz_result(self, user_id: str, params: dict):
        """
        生成測驗結果，並記錄整個quiz結果到quiz_log(個人的測驗紀錄)
        """
        correct_amount = params.get('correct_amount')
        # 個別測驗紀錄正確率在quiz_log中
        quiz_id = params.get('quiz_id')
        self.firebaseService.add_data(
            DatabaseCollectionMap.QUIZ_LOG,
            quiz_id,
            {
                'quiz_id': quiz_id,
                'user_id': user_id,
                'correct_amount': correct_amount,
                'question_amount': params.get('question_amount')
            }
        )
        defeat_count = self.firebaseService.get_aggregate_count(DatabaseCollectionMap.QUIZ_LOG, [('correct_amount', '<', correct_amount)])
        total_count = self.firebaseService.get_aggregate_count(DatabaseCollectionMap.QUIZ_LOG, [('correct_amount', '>=', 0)])
        defeat_rate = round((defeat_count / total_count)*100, 2) if correct_amount > 0 else 0
        params.update({'defeat_rate': defeat_rate})
        
        # 產生測驗結果line flex
        line_flex_str = self.firebaseService.get_data(
            DatabaseCollectionMap.LINE_FLEX,
            "quiz"
        ).get('general_result')
        line_flex_str = LineBotHelper.replace_variable(line_flex_str, params)
        return line_flex_str
    
    def __generate_competition_quiz_result(self, user_id: str, params: dict):
        """
        生成測驗結果，並記錄整個quiz結果到compitition(個人的競賽測驗紀錄)
        """
        correct_amount = params.get('correct_amount')
        quiz_records = self.firebaseService.filter_data(DatabaseCollectionMap.QUIZ_RECORD, [('quiz_id', '==', params.get('quiz_id'))], ('timestamp', 'asc'))
        
        # 測驗開始與結束時間計算
        start_time = params.get('start_time')
        end_time = quiz_records[-1].get('timestamp')
        spend_time = end_time - start_time
        spend_time_str = LineBotHelper.convert_timedelta_to_string(spend_time)
        
        # 紀錄測驗結果資料
        self.firebaseService.update_data(
            DatabaseCollectionMap.COMPETITION,
            params.get('quiz_id'),
            {
                'end_time': end_time,
                'time_spent': spend_time_str,
                'correct_amount': correct_amount,
                'question_amount': params.get('question_amount')
            }
        )
        
        # 產生結果line flex
        line_flex_str = self.firebaseService.get_data(
            DatabaseCollectionMap.LINE_FLEX,
            "quiz"
        ).get('competition_result')
        hours, minutes, seconds = spend_time_str.split(':')
        user_info = self.firebaseService.get_data(DatabaseCollectionMap.USER, user_id)
        user_picture_url = user_info.get('pictureUrl')
        params.update({'hours': hours, 'minutes': minutes, 'seconds': seconds, 'user_picture_url': user_picture_url})
        line_flex_str = LineBotHelper.replace_variable(line_flex_str, params)
        return line_flex_str
    
    def __check_competition_open_time(self, competition_id: str):
        """Returns
        bool: 是否在競賽時間內
        """
        quiz_flex_data = self.firebaseService.filter_data(DatabaseCollectionMap.QUIZ, [('enable', '==', True), ('competition_id', '==', competition_id)])[0]
        start_time = quiz_flex_data["start_time"]
        end_time = quiz_flex_data["end_time"]
        current_time = LineBotHelper.get_current_time()
        return current_time >= start_time and current_time <= end_time
    
    def __generate_rank_line_flex(self, competition_id: str, user_id: str):
        """
        生成排行榜的Line Flex
        """
        def format_time_spent_str(time_spent: str):
            """Returns
            str: 格式化後的時間(只留mm:ss, 超過59:59則回傳>59:59)
            """
            if time_spent.split(':')[0] == '00':
                return ':'.join(time_spent.split(':')[1:])
            return '>59:59'
        
        def get_user_data(user_info: list, user_id: str):
            """Returns
            dict: 使用者資料
            """
            return {
                'mode': 'competition',
                'user_display_name': user_info.get('displayName'),
                'user_picture_url': user_info.get('pictureUrl'),
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

        user_info = self.firebaseService.get_data(DatabaseCollectionMap.USER, user_id)
        competitions = self.firebaseService.filter_data(DatabaseCollectionMap.COMPETITION, [('competition_id', '==', competition_id), ('time_spent', '!=', '')])
        data = {}
        if len(competitions) == 0:
            # 還未有人參賽
            data = get_user_data(user_info, user_id)
        else:
            competition_df = pd.DataFrame(competitions)

            # 依照正確率、答題時間排序進行排名
            competition_df['rank'] = competition_df[['correct_amount', 'time_spent']].apply(
                lambda x: (-x['correct_amount'], x['time_spent']), axis=1
            ).rank(method='min').astype(int)
            competition_df = competition_df.sort_values(by='rank', ascending=True, ignore_index=True)
            competitions = competition_df.to_dict(orient='records')[:5]
            user_competition = [competition for competition in competitions if competition.get('user_id') == user_id]
            
            if len(user_competition) == 0:
                # 使用者未參賽
                data = get_user_data(user_info, user_id)
            else:
                # 使用者已參賽
                user_competition = user_competition[0]
                user_info = self.firebaseService.get_data(DatabaseCollectionMap.USER, user_id)
                user_time_spent = format_time_spent_str(user_competition.get('time_spent'))
                data = {
                    'mode': 'competition',
                    'user_display_name': user_info.get('displayName'),
                    'user_picture_url': user_info.get('pictureUrl'),
                    'user_rank': user_competition.get('rank'),
                    'user_correct_rate': round(int(user_competition.get('correct_amount')) / int(user_competition.get('question_amount')) * 100),
                    'user_time_spent': user_time_spent,
                }

        line_flex_str = self.firebaseService.get_data(
            DatabaseCollectionMap.LINE_FLEX,
            "quiz"
        ).get('rank')
        line_flex_str = LineBotHelper.replace_variable(line_flex_str, data)

        # 生成排行榜前5名
        for i in range(5):
            # 若前五名有資料則顯示，否則顯示'-'
            if len(competitions) >= i + 1:
                user_info = self.firebaseService.get_data(DatabaseCollectionMap.USER, competitions[i].get('user_id'))
                competitions[i]['correct_rate'] = round(int(competitions[i].get('correct_amount')) / int(competitions[i].get('question_amount')) * 100)
                competitions[i]['displayName'] = generate_mask(user_info.get('displayName'))
                competitions[i]['pictureUrl'] = user_info.get('pictureUrl')
                competitions[i]['time_spent'] = format_time_spent_str(competitions[i].get('time_spent'))
                line_flex_str = LineBotHelper.replace_variable(line_flex_str, competitions[i], 1)
            else:
                data = {
                    'rank': '-',
                    'displayName': '-',
                    'pictureUrl': 'https://example.com/default.png', # 為了讓圖片不會顯示隨便寫的網址
                    'correct_rate': '-',
                    'time_spent': '-'
                }
                line_flex_str = LineBotHelper.replace_variable(line_flex_str, data)
                break
        return line_flex_str

    def __generate_history_select(self, event, category):
        """Return
        使用者點擊歷史答題功能後，生成讓使用者選擇「我的錯題」和「全服錯題」選項的Flex Message
        """
        line_flex_str = self.firebaseService.get_data(
            DatabaseCollectionMap.LINE_FLEX,
            "quiz"
        ).get('history_select')
        line_flex_str = LineBotHelper.replace_variable(line_flex_str, {"category" : category})
        return LineBotHelper.reply_message(event, [FlexMessage(alt_text='選擇查看範圍', contents=FlexContainer.from_json(line_flex_str))])

    def __generate_global_history_question(self, event, category):
        """Return
        生成「全服錯題」的Carousel，包含全服答錯率最高的十題
        """
        # 過濾掉回答數為0、且為同個類別主題的題目
        quiz_questions = self.firebaseService.filter_data(DatabaseCollectionMap.QUIZ_QUESTION, [('category', '==', category), ('total_count', '>', 0)], ('correct_rate', 'asc'), 10)

        if not quiz_questions:
            return LineBotHelper.reply_message(event, [TextMessage(text='全服尚未有任何答題紀錄！')])
        else:
            # 生成carousel bubble
            line_flex_str = self.firebaseService.get_data(
                DatabaseCollectionMap.LINE_FLEX,
                "quiz"
            ).get('history_question_list')

            for question in quiz_questions:
                question['width'] = 100 - question['correct_rate']
                difficulty = int(question['difficulty'])

                # 根據難度逐個替換 star_url
                for i in range(difficulty):
                    question[f'star_url_{i+1}'] = self.gold_star_url  # 替換金色星星
                for i in range(5 - difficulty):
                    question[f'star_url_{difficulty + i + 1}'] = self.gray_star_url  # 替換灰色星星

            line_flex_str = FlexMessageHelper.create_carousel_bubbles(quiz_questions, json.loads(line_flex_str))
            line_flex_str = json.dumps(line_flex_str)
            return LineBotHelper.reply_message(event, [FlexMessage(alt_text='全服錯題', contents=FlexContainer.from_json(line_flex_str))])

    def __generate_personal_history_question(self, event, category, user_id):
        """Return
        生成「我的錯題」的Carousel，包含個人答錯率最高的十題
        """
        quiz_records_df = pd.DataFrame(self.firebaseService.filter_data(DatabaseCollectionMap.QUIZ_RECORD, [('user_id', '==', user_id)]))
        quiz_questions_df = pd.DataFrame(self.firebaseService.filter_data(DatabaseCollectionMap.QUIZ_QUESTION, [('category', '==', category)]))
        
        # 判斷該類別是否有任何答題記錄（依據total_count欄位）
        if quiz_questions_df['total_count'].sum() == 0:
            return LineBotHelper.reply_message(event, [TextMessage(text='尚未有任何答題記錄！')])
        else:
            # 為了避免兩個DataFrame欄位名稱重複，將quiz_questions的answer欄位改名為correct_answer
            quiz_questions_df = quiz_questions_df.rename(columns={'answer': 'correct_answer'})
            merged_df = pd.merge(quiz_records_df, quiz_questions_df, left_on='question_id', right_on='id', how='left')

            # 判斷使用者是否有作答過任何題目（是否在quiz_records中有該使用者的答題記錄）
            if merged_df.empty:
                return LineBotHelper.reply_message(event, [TextMessage(text='您尚未作答過任何題目！')])
            else:
                # 新增is_correct欄位，判斷使用者的答案是否正確
                merged_df['is_correct'] = merged_df.apply(
                    lambda row: 1 if row['answer'].lower() == row['correct_answer'].lower() else 0, axis=1
                )

                # 計算每個題目的答題次數和答對次數
                question_stats = merged_df.groupby('question_id').agg(
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
                    star_urls = [self.gold_star_url] * difficulty + [self.gray_star_url] * (5 - difficulty)

                    # 將star_url列表中的每個URL存入對應的欄位
                    for index, star_url in enumerate(star_urls):
                        ten_questions_df.at[i, f'star_url_{index + 1}'] = star_url

                # 抓模板
                line_flex_str = self.firebaseService.get_data(
                    DatabaseCollectionMap.LINE_FLEX,
                    "quiz"
                ).get('history_question_list')

                # 生成carousel bubble
                line_flex_str = FlexMessageHelper.create_carousel_bubbles(ten_questions_df.to_dict('records'), json.loads(line_flex_str))
                line_flex_str = json.dumps(line_flex_str)
                return LineBotHelper.reply_message(event, [FlexMessage(alt_text='我的錯題', contents=FlexContainer.from_json(line_flex_str))])

    def __generate_complete_history_question(self, event, question_id):
        """Return
        生成完整測驗題目的Flex Message（包含答案）
        """
        # 只提取id == question_id的題目資料
        quiz_question = self.firebaseService.filter_data(DatabaseCollectionMap.QUIZ_QUESTION, [('id', '==', int(question_id))])[0]

        # 生成題目的Line Flex
        line_flex_str = self.firebaseService.get_data(
            DatabaseCollectionMap.LINE_FLEX,
            "quiz"
        ).get('history_question_with_image' if quiz_question.get('image_url') else 'history_question')
        quiz_question['width'] = 100 - quiz_question['correct_rate']
        line_flex_str = LineBotHelper.replace_variable(line_flex_str, quiz_question)

        # 生成星星
        difficulty = int(quiz_question['difficulty'])
        line_flex_str = LineBotHelper.replace_variable(line_flex_str, {"star_url": self.gold_star_url}, difficulty)
        line_flex_str = LineBotHelper.replace_variable(line_flex_str, {"star_url": self.gray_star_url}, 5 - difficulty)
        return LineBotHelper.reply_message(event, [FlexMessage(alt_text='完整測驗題目', contents=FlexContainer.from_json(line_flex_str))])
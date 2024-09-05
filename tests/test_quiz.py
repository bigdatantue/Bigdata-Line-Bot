import unittest
from config import Config
from task import Quiz
from linebot.v3.messaging import (
    ApiClient,
    MessagingApi,
    ValidateMessageRequest,
    FlexMessage,
    FlexContainer
)

class TestQuiz(unittest.TestCase):
    def setUp(self):
        print('setup')
        self.config = Config()
        self.configuration = self.config.configuration
        self.spreadsheetService = self.config.spreadsheetService
        self.firebaseService = self.config.firebaseService
    
    def tearDown(self):
        print('teardown')

    def test_generate_question_line_flex(self):
        """
        測試生成問題的FlexMessage
        """
        quiz_questions = self.spreadsheetService.get_worksheet_data('quiz_questions')
        # quiz_questions = [question for question in quiz_questions if question['category'] == 'linebot']
        for idx, quiz_question in enumerate(quiz_questions):
            print(f"Testing quiz question {idx + 1}, question_id: {quiz_question['id']}")
            
            # 使用反射調用private method
            line_flex_str = Quiz._Quiz__generate_question_line_flex(quiz_question, "quiz_id", idx)

            with ApiClient(self.configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                # 檢查生成的FlexMessage是否有效
                line_bot_api.validate_reply(
                    ValidateMessageRequest(
                        messages=[FlexMessage(alt_text="問題", contents=FlexContainer.from_json(line_flex_str))]
                    )
                )

    def test_generate_answer_line_flex(self):
        """
        測試生成答案的FlexMessage
        """
        quiz_questions = self.spreadsheetService.get_worksheet_data('quiz_questions')
        quiz_questions = [question for question in quiz_questions if question['category'] == 'linebot']
        for idx, quiz_question in enumerate(quiz_questions):
            print(f"Testing quiz question {idx + 1}, question_id: {quiz_question['id']}")
            
            # 使用反射調用private method
            line_flex_str = Quiz._Quiz__generate_answer_line_flex(quiz_question, True)

            with ApiClient(self.configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                # 檢查生成的FlexMessage是否有效
                line_bot_api.validate_reply(
                    ValidateMessageRequest(
                        messages=[FlexMessage(alt_text="答案", contents=FlexContainer.from_json(line_flex_str))]
                    )
                )

if __name__ == '__main__':
    unittest.main()
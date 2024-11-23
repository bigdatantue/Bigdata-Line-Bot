from enum import Enum, IntEnum
import os

class FeatureStatus(Enum):
    """
    功能狀態
    """
    # 啟用
    ENABLE = 1
    # 維護
    MAINTENANCE = 2
    # 未開放
    DISABLE = 3

class EquipmentStatus(IntEnum):
    """
    設備狀態
    """
    # 可借用
    AVAILABLE = 1
    # 已借出
    LEND = 2

class EquipmentType(IntEnum):
    """
    設備類型
    """
    # 小栗方 AI 學習機
    AI = 1
    # VIA Pixetto 視覺感測器
    VIA = 2
    # ALK950 邊緣運算推論器
    ALK = 3

class EquipmentName(Enum):
    """
    設備名稱
    """
    AI = '小栗方 AI 學習機'
    VIA = 'VIA Pixetto 視覺感測器'
    ALK = 'ALK950 邊緣運算推論器'

class Permission(IntEnum):
    """
    權限
    """
    # 一般使用者
    USER = 1
    # 工作人員
    STAFF = 2
    # 工作領導者
    LEADER = 3
    # 管理員
    ADMIN = 4

class LIFFSize(Enum):
    """
    LIFF尺寸
    """
    # Compact
    COMPACT = os.getenv('LIFF_ID_COMPACT')
    # Tall
    TALL = os.getenv('LIFF_ID_TALL')
    # Full
    FULL = os.getenv('LIFF_ID_FULL')

class Map:
    """
    其他Map
    """
    FEATURE = {
        '主選單': 'menu',
        '設定': 'setting',
        '常見問答': 'faq',
        '開課修業查詢': 'course',
        '證書申請流程': 'certificate',
        '課程諮詢建議': 'counseling',
        '社群學習資源': 'community',
        '設備租借': 'equipment',
        '活動資訊': 'activity',
        '知識測驗': 'quiz'
    }        
    FAQ_SET = set({'課程內容', '學分與證書', '選課相關', '學習輔導', '活動消息'})

class DatabaseCollectionMap:
    """
    Map資料庫Collection名稱
    """
    CONFIG = "config"
    RICH_MENU = "rich_menu"
    LINE_FLEX = "line_flex"
    QUICK_REPLY = "quick_reply"
    TEMP = "temp"
    USER = "users"
    COURSE = "courses"
    COURSE_OPEN = "course_open_records"
    COURSE_STUDY = "course_study_records"
    MICROCOURSE = "microcourses"
    EQUIPMENT = "equipments"
    FAQ = "faqs"
    FAQ_QUESTION = "faq_questions"
    QUIZ = "quizzes"
    QUIZ_QUESTION = "quiz_questions"
    QUIZ_RECORD = "quiz_records"
    QUIZ_LOG = "quiz_logs"
    COMPETITION = "competitions"
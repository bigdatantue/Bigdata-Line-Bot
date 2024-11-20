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
        '計畫成果展示': 'gallery',
        '知識測驗': 'quiz'
    }        
    FAQ_SET = set({'課程內容', '學分與證書', '選課相關', '學習輔導', '活動消息'})
    COURSE = {
        'overview': '總覽',
        'basic': '基礎',
        'advanced': '進階',
        'practical': '實務'
    }
    EQUIPMENT_NAME = {
        EquipmentType.AI: '小栗方 AI 學習機',
        EquipmentType.VIA: 'VIA Pixetto 視覺感測器',
        EquipmentType.ALK: 'ALK950 邊緣運算推論器'
    }

class DatabaseCollectionMap:
    """
    Map資料庫Collection名稱
    """
    CONFIG = "config"
    RICH_MENU = "rich_menu"
    LINE_FLEX = "line_flex"
    QUICK_REPLY = "quick_reply"
    TEMP = "temp"

class DatabaseDocumentMap:
    """
    Map資料庫Document名稱
    """
    CONFIG = {
        "system": "system"
    }
    RICH_MENU = {
        "a": "page1",
        "b": "page2"
    }
    LINE_FLEX = {
        "menu": "menu",
        "setting": "setting",
        "course": "course",
        "certificate": "certificate",
        "counseling": "counseling",
        "community": "community",
        "equipment": "equipment",
        "quiz": "quiz",
        "faq": "faq"
    }
    QUICK_REPLY = {
        "course": "course",
        "equipment": "equipment"
    }
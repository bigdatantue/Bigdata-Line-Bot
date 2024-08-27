from enum import Enum, IntEnum

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

class Map:
    """
    其他Map
    """
    FEATURE = {
        '主選單': 'menu',
        '設定': 'setting',
        '常見問答': 'faq',
        '開課時間查詢': 'course',
        '證書申請流程': 'certificate',
        '社群學習資源': 'community',
        '線上輔導+實體預約': 'counseling',
        '設備租借': 'equipment',
        '計畫成果展示': 'gallery',
        '知識測驗': 'quiz'
    }
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
    RICH_MENU = "rich_menu"
    LINE_FLEX = "line_flex"
    QUICK_REPLY = "quick_reply"
    TEMP = "temp"

class DatabaseDocumentMap:
    """
    Map資料庫Document名稱
    """
    RICH_MENU = {
        "a": "page1",
        "b": "page2"
    }
    LINE_FLEX = {
        "menu": "menu",
        "course": "course",
        "certificate": "certificate",
        "community": "community",
        "counseling": "counseling",
        "equipment": "equipment",
        "quiz": "quiz"
    }
    QUICK_REPLY = {
        "course": "course",
        "equipment": "equipment"
    }

class FlexParamMap:
    """
    Map Flex Message變數 {key: value} 對應 {flex message上設定的變數名稱: 要填入的資料值(可能為資料表欄位名稱)}
    """
    COURSE = {
        'cover_url': 'course_cover_url',
        'course_cname': 'course_cname',
        'year': 'year',
        'semester': 'semester',
        'week': 'week',
        'start_class': 'start_class',
        'end_class': 'end_class',
        'professor': 'professor',
        'category': 'category',
        'credit': 'credit',
        'class': 'class',
        'postback_data': lambda item: f"task=course&course_record={item.get('id')}"
    }

    COMMUNITY = {
        'cover_url': 'cover_url',
        'course_name': 'course_name',
        'course_desc': 'course_desc',
        'list_url': 'list_url',
    }

    EQUIPMENT = {
        'cover_url': 'cover_url',
        'equipment_name': 'equipment_name',
        'total_amount': 'total_amount',
        'lend_amount': 'lend_amount',
        'available_amount': 'available_amount',
        'equipment_id': 'equipment_id',
        'id': 'id',
        'amount': 'amount',
        'start_date': 'start_date',
        'end_date': 'end_date',
        'return_time': 'return_time'
    }

class Map:
    """
    其他Map
    """
    COURSE = {
        'overview': '總攬',
        'basic': '基礎',
        'advanced': '進階',
        'practical': '實務'
    }

class DatabaseCollectionMap:
    """
    Map資料庫Collection名稱
    """
    RICH_MENU = "rich_menu"
    LINE_FLEX = "line_flex"
    QUICK_REPLY = "quick_reply"

class DatabaseDocumentMap:
    """
    Map資料庫Document名稱
    """
    RICH_MENU = {
        "a": "1LStCWmV4rBBDNGknB62",
        "b": "jUa6Z0Fk7OMwFtDzmoyd"
    }
    LINE_FLEX = {
        "course": {
            "carousel": "tGSG2ubenRbo7jPB3Uy4",
            "detail": "WLMwWm4x5fxaErVmFKeH"
        },
        "certificate": {
            "carousel": "M3SylLgx9hHH7vSrPNuu",
        }
    }
    QUICK_REPLY = {
        "course": {
            "semester": "0ZKS1zEG8aNb5GfsBQ6e",
            "category": "svGO9YamzyGwjHXZPMpS"
        }
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

class Map:
    """
    其他Map
    """
    COURSE = {
        'overview': '總覽',
        'basic': '基礎',
        'advanced': '進階',
        'practical': '實務'
    }
    EQUIPMENT_TYPES = {
        '1': '小栗方 AI 學習機',
        '2': 'VIA Pixetto 視覺感測器',
        '3': 'ALK950 邊緣運算推論器'
    }
    EQUIPMENT_STATUS = {
        'available': 1,
        'lend': 2
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
        },
        "community": {
            "carousel": "m4d0AbQPWK2t5AlSTbl0",
            "microcourse": "by8eewOekAKTjl7gu4OH"
        },
        "counseling": {
            "select": "waLYz91Ia1z8TKrhkGSZ",
            "online": "xNzv8OupG7Ph4ujJ8hrp",
            "physical": "QZogxSAeeA4SooowIwTO"
        },
        "equipment": {
            "carousel": "1Q2N5tLGQsW0PLuaRfyk",
            "borrow": "Yua6r0nL1lSHEB3qIJTP",
            "search": "eWdGFYXpKeScIDKQIOkc",
            "confirm": "eA6KrG2kgkvz6U7IghFo"
        }
    }
    QUICK_REPLY = {
        "course": {
            "semester": "0ZKS1zEG8aNb5GfsBQ6e",
            "category": "svGO9YamzyGwjHXZPMpS"
        },
        "equipment": {
            "amount": "ULjCDTW63ie3yxA1462z"
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

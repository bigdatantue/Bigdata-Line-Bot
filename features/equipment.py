from .base import Feature, register_feature
from linebot.v3.messaging import (
    TextMessage,
    FlexMessage,
    FlexContainer
)
from map import DatabaseCollectionMap, DatabaseDocumentMap, EquipmentStatus, LIFFSize
from api.linebot_helper import LineBotHelper, FlexMessageHelper
import json

@register_feature('equipment')
class Equipment(Feature):
    """
    設備租借
    """
    def execute_message(self, event, **kwargs):
        line_flex_str = self.firebaseService.get_data(
            DatabaseCollectionMap.LINE_FLEX,
            DatabaseDocumentMap.LINE_FLEX.get("equipment")
        ).get("select")
        rent_url = f'https://liff.line.me/{LIFFSize.TALL.value}/rent?userId={event.source.user_id}'
        line_flex_str = LineBotHelper.replace_variable(line_flex_str, {'rent_url': rent_url})
        LineBotHelper.reply_message(event, [FlexMessage(alt_text='設備租借', contents=FlexContainer.from_json(line_flex_str))])

    def execute_postback(self, event, **kwargs):
        params = kwargs.get('params')
        user_id = event.source.user_id
        decision = params.get('decision')
        if decision:
            borrower_user_id = params.get('borrower_user_id')
            borrower_info = self.firebaseService.get_data(DatabaseCollectionMap.TEMP, borrower_user_id)
            if not borrower_info:
                return LineBotHelper.reply_message(event, [TextMessage(text='此租借申請已審核過')])
            # 使用者回覆設備租借核准
            if decision == '1':
                # 設備租借核准
                borrower_id = __class__.__rent_equipment(borrower_info)
                self.firebaseService.delete_data(DatabaseCollectionMap.TEMP, borrower_user_id)
                borrow_records = __class__.__get_borrow_records(borrower_user_id, borrower_id)
                line_flex_template = self.firebaseService.get_data(
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
                self.firebaseService.delete_data(DatabaseCollectionMap.TEMP, borrower_user_id)
                LineBotHelper.reply_message(event, [TextMessage(text='設備租借不通過')])
                return LineBotHelper.push_message(borrower_user_id, [TextMessage(text='設備租借不通過')])
                
        else:
            type = params.get('type')
            if type != 'borrow':
                # 查詢借用清單
                borrow_records = __class__.__get_borrow_records(user_id)
                if len(borrow_records) == 0:
                    return LineBotHelper.reply_message(event, [TextMessage(text='您目前沒有借用任何設備')])
                line_flex_template = self.firebaseService.get_data(
                    DatabaseCollectionMap.LINE_FLEX,
                    DatabaseDocumentMap.LINE_FLEX.get("equipment")
                ).get("record")
                line_flex_json = FlexMessageHelper.create_carousel_bubbles(borrow_records, json.loads(line_flex_template))
                line_flex_str = json.dumps(line_flex_json)
                return LineBotHelper.reply_message(event, [FlexMessage(alt_text='借用清單', contents=FlexContainer.from_json(line_flex_str))])

    def __rent_equipment(self, params: dict):
        """租借設備(更新資料庫)
        Returns
        str: 借用者id
        """
        conditions = [
            ('type', '==', int(params.get('equipment_id'))),
            ('status', '==', EquipmentStatus.AVAILABLE)
        ]
        equipment_status_data = self.firebaseService.filter_data('equipments', conditions)
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
            self.firebaseService.update_data('equipments', equipment.get('_id'), equipment)
        return borrower_id
    
    def __get_borrow_records(self, user_id: str, borrower_id: str=None):
        """Returns
        list: 借用紀錄
        """
        conditions = [('borrower', '==', user_id)]
        equipments = self.firebaseService.filter_data('equipments', conditions)

        if borrower_id:
            conditions.append(('borrowerId', '==', borrower_id))

        equipments = self.firebaseService.filter_data('equipments', conditions)
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
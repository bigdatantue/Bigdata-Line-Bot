class SpreadsheetService:
    def __init__(self, gc, url):
        self.gc = gc
        self.sh = self.gc.open_by_url(url)

    def check_user_exists(self, user_id):
        """
        檢查使用者是否存在於試算表
        """
        wks = self.sh.worksheet_by_title('user_info')
        column_index = self.get_column_index(wks, 'user_id')
        user_ids = wks.get_col(column_index)
        return user_id in user_ids
        
    def add_user(self, user_info):
        """
        新增使用者至試算表
        """
        wks = self.sh.worksheet_by_title('user_info')
        wks.append_table(values=user_info)

    def get_column_index(self, wks, column_name):
        """Returns
        int: column_name 所在的 column index
        """
        return wks.get_row(1).index(column_name) + 1

    
    def get_user_row_index(self, wks, user_id):
        """Returns
        int: user_id 所在的 row index
        """
        column_index = self.get_column_index(wks, 'user_id')
        user_ids = wks.get_col(column_index)
        return user_ids.index(user_id) + 1
        
    def set_user_status(self, user_id, is_active):
        """
        設定使用者的is_active
        """
        wks = self.sh.worksheet_by_title('user_info')
        user_row_index = self.get_user_row_index(wks, user_id)
        column_index = self.get_column_index(wks, 'is_active')
        wks.update_value((user_row_index, column_index), is_active)
    
    def get_worksheet_data(self, title: str):
        """
        Summary:
            取得工作表資料
        Args:
            title: 工作表名稱
        Returns:
            list: 工作表資料
        """
        wks = self.sh.worksheet_by_title(title)
        return wks.get_all_records()
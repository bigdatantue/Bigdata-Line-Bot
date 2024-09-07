from datetime import datetime
import pytz

class SpreadsheetService:
    def __init__(self, gc, url):
        self.gc = gc
        self.sh = self.gc.open_by_url(url)

    def check_user_exists(self, wks_name, user_id):
        """
        檢查使用者是否存在於試算表
        """
        wks = self.sh.worksheet_by_title(wks_name)
        column_index = self.get_column_index(wks, 'user_id')
        user_ids = wks.get_col(column_index)
        return user_id in user_ids
        
    def add_user(self, wks_name, user_info):
        """
        新增使用者至試算表
        """
        wks = self.sh.worksheet_by_title(wks_name)
        wks.append_table(values=user_info)

    def get_column_index(self, wks, column_name):
        """Returns
        int: column_name 所在的 column index
        """
        return wks.get_row(1).index(column_name) + 1
    
    def get_row_index(self, wks, column_name, value):
        """Returns
        int: value 所在的 row index
        """
        column_index = self.get_column_index(wks, column_name)
        column_values = wks.get_col(column_index)
        return column_values.index(value) + 1
        
    def set_user_status(self, user_id, is_active):
        """
        設定使用者的is_active及更新時間
        """
        wks = self.sh.worksheet_by_title('user_info')
        user_row_index = self.get_row_index(wks, 'user_id', user_id)
        column_index = self.get_column_index(wks, 'is_active')
        wks.update_value((user_row_index, column_index), is_active)
        #紀錄時間
        taiwan_tz = pytz.timezone('Asia/Taipei')
        timestamp = datetime.now(taiwan_tz).strftime('%Y-%m-%d %H:%M:%S')
        column_index = self.get_column_index(wks, 'timestamp')
        wks.update_value((user_row_index, column_index), timestamp)
    
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
    
    def update_cell_value(self, title: str, range: tuple, value: str):
        """
        Summary:
            更新工作表資料
        Args:
            title: 工作表名稱
            range: 要更新的列索引(E.g. (row, col))
            value: 要更新的資料
        """
        wks = self.sh.worksheet_by_title(title)
        wks.update_value(range, value)
        
    def update_cells_values(self, title: str, range: str, values: list):
        """
        Summary:
            更新工作表資料
        Args:
            title: 工作表名稱
            range: 要更新的列索範圍(E.g. 'A1:B1')
            values: 要更新的資料(E.g. [['row1-1', 'row1-2']] 或 [['row1'], ['row2']])
        """
        wks = self.sh.worksheet_by_title(title)
        wks.update_values(range, values)
    
    def delete_row_data(self, title, index):
        """
        Summary:
            刪除工作表資料
        Args:
            title: 工作表名稱
        """
        wks = self.sh.worksheet_by_title(title)
        wks.delete_rows(index)
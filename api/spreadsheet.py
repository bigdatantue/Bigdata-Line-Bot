class SpreadsheetService:
    def __init__(self, gc, url):
        self.gc = gc
        self.sh = self.gc.open_by_url(url)

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
        return column_values.index(value) + 1 if value in column_values else None
    
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
// 獲取特定欄位名稱的欄位索引
function getColumnIndex(worksheet_name, column_name) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(worksheet_name);
  var range = sheet.getRange(1, 1, 1, sheet.getLastColumn());
  var values = range.getValues()[0];
  return values.indexOf(column_name) + 1;
}

function getRowIndex(worksheet_name, column_name, value) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(worksheet_name);
  var range = sheet.getRange(1, getColumnIndex(worksheet_name, column_name), sheet.getLastRow(), 1);
  var values = range.getValues().flat();
  return values.indexOf(value) + 1;
}

// 彈跳視窗
function alert(message){
  var ui = SpreadsheetApp.getUi();
  ui.alert(message);
}
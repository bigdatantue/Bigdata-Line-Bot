// 需在設定 => 指令碼屬性 設定以下參數
const scriptProperties = PropertiesService.getScriptProperties();
const CHANNEL_ACCESS_TOKEN = scriptProperties.getProperty('CHANNEL_ACCESS_TOKEN');
const LINE_NOTIFY_TOKEN = scriptProperties.getProperty('LINE_NOTIFY_TOKEN');

// 建立試算表menu
function onOpen(e) {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu("Line Messaging API")
    .addItem('更新使用者資訊', 'updateUserInfo')
    .addToUi();
  ui.createMenu("Line Notify")
    .addItem("建立觸發條件", "createTrigger")
    .addSeparator()
    .addItem("偵測訂閱者狀態", "checkStatus")
    .addItem("移除斷線訂閱者資料", "deleteDisconnectUsers")
    .addSeparator()
    .addItem("移除「可刪除」訂閱者", "deleteUsers")
    .addToUi();
}

// 更新使用者資訊
function updateUserInfo() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('user_info');
  var lastRow = sheet.getLastRow();
  for (var i = 2; i <= lastRow; i++) {
    var userId = sheet.getRange(i, getColumnIndex('user_info', 'user_id')).getValue();
    var newUserInfo = getUserInfo(userId);
    if (newUserInfo) {
      sheet.getRange(i, getColumnIndex('user_info', 'display_name')).setValue(newUserInfo.displayName);
      sheet.getRange(i, getColumnIndex('user_info', 'picture_url')).setValue(newUserInfo.pictureUrl);
      sheet.getRange(i, getColumnIndex('user_info', 'language')).setValue(newUserInfo.language);
      sheet.getRange(i, getColumnIndex('user_info', 'status_message')).setValue(newUserInfo.statusMessage);
    }
  }
}
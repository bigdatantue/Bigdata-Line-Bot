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
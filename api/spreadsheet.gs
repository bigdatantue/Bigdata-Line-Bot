// 需在設定 => 指令碼屬性 設定CHANNEL_ACCESS_TOKEN
const scriptProperties = PropertiesService.getScriptProperties();
const CHANNEL_ACCESS_TOKEN = scriptProperties.getProperty('CHANNEL_ACCESS_TOKEN');

// 在試算表打開時自動運行此函數，並添加自訂選單
function onOpen(e) {
  SpreadsheetApp.getUi()
  .createMenu('手動更新')
  .addItem('更新使用者資訊', 'updateUserInfo') // 這個選項對應於 updateUserInfo 函數
  .addToUi(); // 將選單添加到用戶界面
}

// 獲取特定欄位名稱的欄位索引
function get_column_index(worksheet_name, column_name) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(worksheet_name);
  var range = sheet.getRange(1, 1, 1, sheet.getLastColumn());
  var values = range.getValues()[0];
  return values.indexOf(column_name) + 1;
}

// 更新使用者資訊
function updateUserInfo() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('user_info');
  var lastRow = sheet.getLastRow();
  for (var i = 2; i <= lastRow; i++) {
    var userId = sheet.getRange(i, get_column_index('user_info', 'user_id')).getValue();
    var newUserInfo = getUserInfo(userId);
    if (newUserInfo) {
      sheet.getRange(i, get_column_index('user_info', 'display_name')).setValue(newUserInfo.displayName);
      sheet.getRange(i, get_column_index('user_info', 'picture_url')).setValue(newUserInfo.pictureUrl);
      sheet.getRange(i, get_column_index('user_info', 'language')).setValue(newUserInfo.language);
      sheet.getRange(i, get_column_index('user_info', 'status_message')).setValue(newUserInfo.statusMessage);
    }
  }
}

// 取得使用者資訊
function getUserInfo(userId) {
  var url = "https://api.line.me/v2/bot/profile/" + userId;
  var headers = {
    "Authorization": `Bearer ${CHANNEL_ACCESS_TOKEN}`
  };
  var options = {
    "method": "GET",
    "headers": headers,
    "muteHttpExceptions": true
  };
  try {
    var response = UrlFetchApp.fetch(url, options);
    var data = JSON.parse(response.getContentText());
    return {
      displayName: data.displayName,
      pictureUrl: data.pictureUrl,
      language: data.language,
      statusMessage: data.statusMessage
    };
  } catch (e) {
    Logger.log("Error fetching user info: " + e.message);
    Logger.log(e.response.getContentText());
    return null;
  }
}
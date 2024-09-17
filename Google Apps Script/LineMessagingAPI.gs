// 更新使用者資訊
function updateUserInfo() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('user_info');
  var lastRow = sheet.getLastRow();
  for(var i = 2; i <= lastRow; i++) {
    var userId = sheet.getRange(i, getColumnIndex('user_info', 'user_id')).getValue();
    var response = getUserInfo(userId);
    if(response.getResponseCode() == 200){
      userInfo = JSON.parse(response.getContentText());
      sheet.getRange(i, getColumnIndex('user_info', 'display_name')).setValue(userInfo.displayName);
      sheet.getRange(i, getColumnIndex('user_info', 'picture_url')).setValue(userInfo.pictureUrl);
      sheet.getRange(i, getColumnIndex('user_info', 'language')).setValue(userInfo.language);
      sheet.getRange(i, getColumnIndex('user_info', 'status_message')).setValue(userInfo.statusMessage);      
    }else{
      continue;
    }
  }
  alert("使用者資訊更新完成");
}

// 取得使用者資訊
function getUserInfo(userId) {
  var url = `https://api.line.me/v2/bot/profile/${userId}`;
  var headers = {
    "Authorization": `Bearer ${CHANNEL_ACCESS_TOKEN}`
  };
  var options = {
    "method": "GET",
    "headers": headers,
    "muteHttpExceptions": true
  };
  return UrlFetchApp.fetch(url, options);
}
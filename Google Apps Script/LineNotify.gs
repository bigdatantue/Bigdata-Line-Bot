var sheetLineNotifyTokens = SpreadsheetApp.getActive().getSheetByName("notify_info");
var sheetLineNotifyTokenslastRow = sheetLineNotifyTokens.getLastRow();
var sheetLineNotifyTokenslastColumn = sheetLineNotifyTokens.getLastColumn();

var tokenColumn = getColumnIndex('notify_info', 'token');
var tokenTargetTypeColumn = getColumnIndex('notify_info', 'type');
var tokenTargetColumn = getColumnIndex('notify_info', 'name');
var tokenDisconnectColumn = getColumnIndex('notify_info', '斷線');
var tokenDeleteColumn = getColumnIndex('notify_info', '可刪除');

//檢查訂閱者狀態
function checkStatus(){
  var sheetLineNotifyTokensRange = sheetLineNotifyTokens.getRange(2, 1, sheetLineNotifyTokenslastRow - 1, sheetLineNotifyTokenslastColumn);
  var sheetLineNotifyTokensData = sheetLineNotifyTokensRange.getValues();
  for (var i = 0; i < sheetLineNotifyTokensData.length; i++) {
    var token = sheetLineNotifyTokensData[i][tokenColumn - 1];
    var urlfetchResult = checkSubscriptionStatus(token);
    //將偵測不到狀態的 Line Notify Token 標示為斷線
    updateDisconnectStatus(token, urlfetchResult,"check");
  }
  alert("檢查完成");
}

//將斷線的訂閱者資料移除
function deleteDisconnectUsers() {
  var sheetLineNotifyTokensRange = sheetLineNotifyTokens.getRange(2, 1, sheetLineNotifyTokenslastRow - 1, sheetLineNotifyTokenslastColumn);
  var sheetLineNotifyTokensData = sheetLineNotifyTokensRange.getValues();
  for (var i = 0; i < sheetLineNotifyTokensData.length; i++) {
    if (sheetLineNotifyTokensData[i][tokenDisconnectColumn - 1] === "斷線") {
      sheetLineNotifyTokensData.splice(i, 1);  //把 Index 值為 i 的陣列元素移除
      i--; 
    }
  }
  
  //把「Line Notify Tokens」工作表內的舊資料清除，並將移除斷線訂閱者後的新資料表填回去
  sheetLineNotifyTokensRange.clearContent();
  if (sheetLineNotifyTokensData.length > 0) {
    sheetLineNotifyTokens.getRange(2, 1, sheetLineNotifyTokensData.length, sheetLineNotifyTokenslastColumn).setValues(sheetLineNotifyTokensData);
  }
  alert("已移除斷線者資料");
}

//移除「可刪除」欄位被打勾的訂閱者
function deleteUsers() {
  var sheetLineNotifyTokensRange = sheetLineNotifyTokens.getRange(2, 1, sheetLineNotifyTokenslastRow - 1, sheetLineNotifyTokenslastColumn);
  var sheetLineNotifyTokensData = sheetLineNotifyTokensRange.getValues();
  for (var i = 0; i < sheetLineNotifyTokensData.length; i++) {
    token = sheetLineNotifyTokensData[i][tokenColumn - 1]
    if (sheetLineNotifyTokensData[i][tokenDeleteColumn - 1] == true) {
      revokeUsers(token);
      sheetLineNotifyTokensData.splice(i, 1);
      i--;
    }
  }

  // //把「Line Notify Tokens」工作表內的舊資料清除，並將移除訂閱者後的新資料表填回去
  sheetLineNotifyTokensRange.clearContent();
  if (sheetLineNotifyTokensData.length > 0) {
    sheetLineNotifyTokens.getRange(2, 1, sheetLineNotifyTokensData.length, sheetLineNotifyTokenslastColumn).setValues(sheetLineNotifyTokensData);
  }
  alert("已移除可刪除使用者資料")
}

//更新訂閱者狀態
function updateDisconnectStatus(token, urlfetchResult, action) {
  var sheetLineNotifyTokensRange = sheetLineNotifyTokens.getRange(getRowIndex("notify_info", "token", token), 1, 1, sheetLineNotifyTokenslastColumn);
  var sheetLineNotifyTokensData = sheetLineNotifyTokensRange.getValues()[0];
  var lineUserStatus;
  lineUserStatus = JSON.parse(urlfetchResult);
  if (lineUserStatus.status == 200) {
    if (action == "check") {
      sheetLineNotifyTokensData[tokenTargetTypeColumn - 1] = lineUserStatus.targetType;
      sheetLineNotifyTokensData[tokenTargetColumn - 1] = lineUserStatus.target;
    }
    sheetLineNotifyTokensData[tokenDisconnectColumn - 1] = null;
  }
  else {
    sheetLineNotifyTokensData[tokenDisconnectColumn - 1] = "斷線";
  }
  sheetLineNotifyTokensRange.setValues([sheetLineNotifyTokensData]);
}

// 發送 notify 通知
function sendNotify(token, message, image){
  var options = {
    "muteHttpExceptions" : true,
    "method"  : "post",
    "payload" : {
      "message" : message,
      "imageThumbnail":image,
      "imageFullsize":image
    },
    "headers" : {"Authorization" : "Bearer " + token}
  };
  return UrlFetchApp.fetch("https://notify-api.line.me/api/notify", options);
}

// 檢查訂閱者狀態
function checkSubscriptionStatus(token){
  var options = {
    "muteHttpExceptions" : true,
    "method"  : "get",
    "headers" : {"Authorization" : "Bearer " + token}
  };
  return UrlFetchApp.fetch("https://notify-api.line.me/api/status", options);
}

// 將指定 ID 的訂閱者強制解除連動
function revokeUsers(token) {
  var options = {
    "muteHttpExceptions" : true,
    "method"  : "post",
    "headers" : {"Authorization" : "Bearer " + token}
  };
  return UrlFetchApp.fetch("https://notify-api.line.me/api/revoke", options);
}
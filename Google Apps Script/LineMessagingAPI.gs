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
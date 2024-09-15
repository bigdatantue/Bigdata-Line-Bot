// 取得表單資料
function getFormData(e){
  var formData = e.namedValues; //在試算表內利用 Event Object 取得表單送出的回應。

  //製作訊息內容
  var feature = formData['何種功能發生問題？'];
  var display_name = formData['LINE帳號名稱'];
  var description = formData['問題描述及操作流程'];
  var image_url = formData['問題截圖上傳'][0].replace(/\/open/g, "/uc"); //把網址的 open 改成 uc，這樣才能直接下載檔案;

  var message = `LINE名稱: ${display_name}\n發生問題功能: ${feature}\n問題描述: ${description}`;
  //將訊息傳送給訂閱者
  sendNotify('VHIcjUdfkVG4ngnhW1LmX1HjgPVcezTIUtuzaBkmbtk', message, image_url);
}

//建立觸發條件
function createTrigger() {
  var allTriggers = ScriptApp.getProjectTriggers();

  var checkTemp = allTriggers.filter(function(item, index, array){
    return item.getHandlerFunction() == "getFormData";
  });
  if (checkTemp.length == 0) {
    ScriptApp.newTrigger("getFormData")
      .forSpreadsheet(SpreadsheetApp.getActive())
      .onFormSubmit()
      .create();
  }
  alert("觸發條件已建立完成");
}
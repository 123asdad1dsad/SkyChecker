// SkyChecker — скрипт для Google Таблицы (Apps Script).
// Колонки листа: A=Номер, B=HWID, C=Статус, D=Добавлен
// Статусы, которые ставит модератор:
//   "ожидание"          — игрок ждет начала проверки на экране блокировки
//   "проверка"          — игроку открывается доступ к программе (Разрешить)
//   "запрещено"         — доступ заблокирован, программа закрывается (Запретить)
//   "проверка окончена" — строка удаляется, программа у игрока закрывается

var SHEET_NAME = "Проверки";

function doGet(e) {
  var action = (e.parameter.action || "").toLowerCase();
  var hwid = e.parameter.hwid || "";
  
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var sheet = getSheet();
    
    // Новые действия для веб-панели управления
    if (action === "list") return reply(listRows(sheet));
    if (action === "update") {
      var statusVal = e.parameter.status || "";
      return reply(updateStatus(sheet, hwid, statusVal));
    }
    
    // Действия для клиента
    if (!hwid) return reply({ ok: false, error: "no hwid" });
    if (action === "register") return reply(register(sheet, hwid));
    if (action === "status") return reply(status(sheet, hwid));
    
    return reply({ ok: false, error: "bad action" });
  } finally {
    lock.releaseLock();
  }
}

function getSheet() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
    sheet.appendRow(["Номер", "HWID", "Статус", "Добавлен"]);
    sheet.setFrozenRows(1);
  }
  return sheet;
}

function findRow(sheet, hwid) {
  var values = sheet.getDataRange().getValues();
  for (var i = 1; i < values.length; i++) {
    if (String(values[i][1]) === hwid) {
      return { row: i + 1, number: values[i][0], status: String(values[i][2]).toLowerCase().trim() };
    }
  }
  return null;
}

function listRows(sheet) {
  var values = sheet.getDataRange().getValues();
  var rows = [];
  for (var i = 1; i < values.length; i++) {
    rows.push({
      number: values[i][0],
      hwid: values[i][1],
      status: String(values[i][2]).trim(),
      added: values[i][3]
    });
  }
  return { ok: true, data: rows };
}

function updateStatus(sheet, hwid, newStatus) {
  if (!hwid) return { ok: false, error: "no hwid" };
  var found = findRow(sheet, hwid);
  if (!found) return { ok: false, error: "hwid not found" };
  
  // Обновляем статус в колонке C (индекс 3 в Excel-координатах)
  sheet.getRange(found.row, 3).setValue(newStatus);
  return { ok: true, hwid: hwid, status: newStatus };
}

function register(sheet, hwid) {
  var found = findRow(sheet, hwid);
  if (found) {
    return { ok: true, number: found.number, status: mapStatus(found.status) };
  }
  var props = PropertiesService.getScriptProperties();
  var number = Number(props.getProperty("next_number") || "1");
  props.setProperty("next_number", String(number + 1));
  sheet.appendRow([number, hwid, "ожидание", new Date()]);
  return { ok: true, number: number, status: "waiting" };
}

function status(sheet, hwid) {
  var found = findRow(sheet, hwid);
  if (!found) return { ok: true, status: "finished" };
  if (found.status === "проверка окончена") {
    sheet.deleteRow(found.row);
    return { ok: true, status: "finished" };
  }
  return { ok: true, number: found.number, status: mapStatus(found.status) };
}

function mapStatus(s) {
  if (s === "проверка") return "checking";
  if (s === "проверка окончена") return "finished";
  if (s === "запрещено" || s === "отклонено" || s === "denied") return "denied";
  return "waiting";
}

function reply(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

APP_NAME = "SkyChecker"
APP_VERSION = "1.0"

# URL веб-приложения Google Apps Script (деплой скрипта таблицы).
# Пока пусто — программа работает без проверки доступа.
SHEET_API_URL = "https://script.google.com/macros/s/AKfycbxNhStf1vUoQ6ibQDv6eiCppZr4BRBNQGfRveXAKqnLfeROrEFa50AbwFWxI1QLh-0J/exec"

# name — что видит проверяющий, exe — файл в папке tools/
TOOLS = [
    {"name": "Everything",          "exe": "Everything.exe",          "desc": "Мгновенный поиск по всем файлам диска"},
    {"name": "Shellbag",            "exe": "Shellbag.exe",            "desc": "История открытых и удалённых папок"},
    {"name": "LastActivityView",    "exe": "LastActivityView.exe",    "desc": "Хронология действий в системе"},
    {"name": "CachedProgramsList",  "exe": "CachedProgramsList.exe",  "desc": "Кэш запускавшихся программ"},
    {"name": "JournalTrace",        "exe": "JournalTrace.exe",        "desc": "Журнал USN — выберите диск C в окне программы"},
    {"name": "System Informer",     "exe": "System Informer.lnk",     "desc": "Процессы, драйверы, инжекты"},
    {"name": "WinPrefetchView",     "exe": "WinPrefetchView.exe",     "desc": "Prefetch: что и когда запускалось"},
    {"name": "BrowserDownloadsView", "exe": "BrowserDownloadsView.exe", "desc": "Загрузки во всех браузерах"},
    {"name": "USBDriveLog",         "exe": "USBDriveLog.exe",         "desc": "История подключённых USB-накопителей"},
    {"name": "Luyten",              "exe": "Luyten.exe",              "desc": "Декомпилятор Java (.jar / .class)"},
    {"name": "HxD",                 "exe": "HxD.lnk",                 "desc": "HEX-редактор, анализ дампов"},
]

# Папки, которые открываются в один клик. {user} = папка пользователя
GAME_FOLDERS = [
    {"name": ".minecraft",   "path": r"%APPDATA%\.minecraft"},
    {"name": "PulseVisuals", "path": r"%APPDATA%\PulseVisuals"},
    {"name": "versions",     "path": r"%APPDATA%\.minecraft\versions"},
    {"name": "mods",         "path": r"%APPDATA%\.minecraft\mods"},
    {"name": "logs",         "path": r"%APPDATA%\.minecraft\logs"},
    {"name": "screenshots",  "path": r"%APPDATA%\.minecraft\screenshots"},
]
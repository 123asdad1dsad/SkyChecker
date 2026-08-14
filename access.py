"""Доступ по номеру через Google Таблицу (веб-приложение Apps Script)."""
import json
import urllib.parse
import urllib.request

from config import SHEET_API_URL


def configured():
    """URL веб-приложения задан в config.py."""
    return SHEET_API_URL.startswith("https://script.google.com/")


def get_hwid():
    """Стабильный идентификатор ПК (MachineGuid из реестра Windows)."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as k:
            return winreg.QueryValueEx(k, "MachineGuid")[0]
    except OSError:
        import uuid
        return f"node-{uuid.getnode():x}"


def _call(action, hwid):
    query = urllib.parse.urlencode({"action": action, "hwid": hwid})
    with urllib.request.urlopen(f"{SHEET_API_URL}?{query}", timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


def register(hwid):
    """Добавляет ПК в таблицу (или возвращает уже выданный номер): {ok, number, status}."""
    return _call("register", hwid)


def status(hwid):
    """Текущий статус: waiting / checking / finished."""
    return _call("status", hwid)

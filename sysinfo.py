import os
import sys
import platform
import socket
import getpass
import string
import ctypes
from datetime import datetime

import psutil


def _fmt(ts):
    if not ts:
        return "нет данных"
    return datetime.fromtimestamp(ts).strftime("%d.%m.%Y  %H:%M:%S")


def _os_name():
    """platform.release() не отличает Windows 11 от 10 — смотрим номер сборки."""
    try:
        build = sys.getwindowsversion().build
        name = "Windows 11" if build >= 22000 else f"Windows {platform.release()}"
        return f"{name} (build {build})"
    except AttributeError:
        return f"{platform.system()} {platform.release()}"


def _cpu_name():
    """Реальное имя процессора из реестра (platform.processor() даёт техническую строку)."""
    try:
        import winreg
        key = r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key) as k:
            return winreg.QueryValueEx(k, "ProcessorNameString")[0].strip()
    except OSError:
        return platform.processor() or "нет данных"


def recycle_bin_last_cleared():
    """Время последнего изменения корзины на всех дисках = последняя очистка/удаление."""
    newest = None
    where = None
    for letter in string.ascii_uppercase:
        root = f"{letter}:\\$Recycle.Bin"
        if not os.path.isdir(root):
            continue
        try:
            for sid in os.listdir(root):
                folder = os.path.join(root, sid)
                if not os.path.isdir(folder):
                    continue
                ts = os.path.getmtime(folder)
                if newest is None or ts > newest:
                    newest = ts
                    where = f"{letter}:\\"
        except (PermissionError, OSError):
            continue
    return newest, where


def recycle_bin_items():
    """Сколько объектов сейчас лежит в корзине (Shell API — те же цифры, что в проводнике)."""
    try:
        class SHQUERYRBINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", ctypes.c_ulong),
                ("i64Size", ctypes.c_longlong),
                ("i64NumItems", ctypes.c_longlong),
            ]

        info = SHQUERYRBINFO()
        info.cbSize = ctypes.sizeof(SHQUERYRBINFO)
        if ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(info)) == 0:
            return int(info.i64NumItems), int(info.i64Size)
    except (OSError, AttributeError):
        pass

    # запасной вариант — прямой подсчёт по дискам
    count = 0
    for letter in string.ascii_uppercase:
        root = f"{letter}:\\$Recycle.Bin"
        if not os.path.isdir(root):
            continue
        try:
            sids = os.listdir(root)
        except OSError:
            continue
        for sid in sids:
            folder = os.path.join(root, sid)
            try:
                if os.path.isdir(folder):
                    count += len([f for f in os.listdir(folder) if f.startswith("$R")])
            except OSError:
                continue
    return count, None


def collect():
    ts, drive = recycle_bin_last_cleared()
    bin_count, bin_size = recycle_bin_items()
    bin_str = str(bin_count)
    if bin_size:
        mb = bin_size / 1024 ** 2
        bin_str += f"   ({mb / 1024:.2f} ГБ)" if mb >= 1024 else f"   ({mb:.1f} МБ)"

    boot = psutil.boot_time()
    uptime = datetime.now() - datetime.fromtimestamp(boot)
    days, rem = divmod(int(uptime.total_seconds()), 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    uptime_str = (f"{days} д " if days else "") + f"{hours} ч {minutes} мин"

    cores = psutil.cpu_count(logical=False)
    threads = psutil.cpu_count()

    return [
        ("Последняя очистка корзины", _fmt(ts) + (f"   ({drive})" if drive else ""), True),
        ("Объектов в корзине сейчас", bin_str, False),
        ("Система запущена", _fmt(boot), False),
        ("Аптайм", uptime_str, False),
        ("Пользователь", getpass.getuser(), False),
        ("Имя ПК", socket.gethostname(), False),
        ("ОС", _os_name(), False),
        ("Процессор", _cpu_name(), False),
        ("Ядер / потоков", f"{cores or '?'} / {threads or '?'}", False),
        ("ОЗУ", f"{round(psutil.virtual_memory().total / 1024 ** 3)} ГБ", False),
        ("Локальное время", datetime.now().strftime("%d.%m.%Y  %H:%M:%S"), False),
    ]


def get_drives_info():
    """Сбор информации обо всех дисках в системе (буква, тип, файловая система, метка, серийный номер)."""
    DRIVE_TYPES = {
        0: ("Неизвестно", False),
        1: ("Некорректный путь", False),
        2: ("Съемный диск (USB / Flash)", True),
        3: ("Локальный диск (HDD / SSD)", False),
        4: ("Сетевой диск", True),
        5: ("CD-ROM дисковод", False),
        6: ("RAM виртуальный диск", True),
    }

    drives = []
    for letter in string.ascii_uppercase:
        drive_path = f"{letter}:\\"
        # Проверяем, отвечает ли диск (быстрый вызов без зависания)
        try:
            # GetDriveTypeW возвращает 1 (DRIVE_NO_ROOT_DIR), если диска нет
            type_code = ctypes.windll.kernel32.GetDriveTypeW(drive_path)
            if type_code <= 1:
                continue
        except Exception:
            continue

        type_str, highlight = DRIVE_TYPES.get(type_code, ("Неизвестно", False))

        # Чтение информации о томе
        volume_name = ctypes.create_unicode_buffer(260)
        fs_name = ctypes.create_unicode_buffer(260)
        serial_num = ctypes.c_ulong(0)
        max_component_len = ctypes.c_ulong(0)
        fs_flags = ctypes.c_ulong(0)

        # Вызов GetVolumeInformationW
        r = ctypes.windll.kernel32.GetVolumeInformationW(
            drive_path,
            volume_name,
            ctypes.sizeof(volume_name),
            ctypes.byref(serial_num),
            ctypes.byref(max_component_len),
            ctypes.byref(fs_flags),
            fs_name,
            ctypes.sizeof(fs_name)
        )

        label = volume_name.value if r else ""
        fs_type = fs_name.value if r else "нет данных"
        serial = f"{serial_num.value:08X}" if r else "нет данных"

        # Сбор информации о размере
        try:
            usage = psutil.disk_usage(drive_path)
            total_gb = usage.total / (1024 ** 3)
            used_gb = usage.used / (1024 ** 3)
            free_gb = usage.free / (1024 ** 3)
            pct = usage.percent
        except (PermissionError, OSError):
            total_gb, used_gb, free_gb, pct = 0.0, 0.0, 0.0, 0.0

        drives.append({
            "letter": letter,
            "path": drive_path,
            "type_str": type_str,
            "type_code": type_code,
            "highlight": highlight,
            "label": label or "Без названия",
            "fs_type": fs_type,
            "serial": serial,
            "total_gb": total_gb,
            "used_gb": used_gb,
            "free_gb": free_gb,
            "pct": pct
        })
    return drives

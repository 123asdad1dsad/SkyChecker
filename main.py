import os
import sys
import subprocess
import threading
import ctypes
from datetime import datetime

import customtkinter as ctk
from tkinter import messagebox

import theme as T
from config import APP_NAME, APP_VERSION, TOOLS, GAME_FOLDERS
import sysinfo
import access

ctk.set_appearance_mode("dark")


def base_dir():
    """Работает и в исходниках, и внутри собранного .exe (PyInstaller)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def tools_dir():
    """Папка tools: рядом с exe, а если нет — на уровень выше."""
    near = os.path.join(base_dir(), "tools")
    if os.path.isdir(near):
        return near
    parent = os.path.join(os.path.dirname(base_dir()), "tools")
    if os.path.isdir(parent):
        return parent
    return near


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME}  v{APP_VERSION}  —  Профессиональный сканер")
        self.geometry("1120x720")
        self.minsize(1000, 640)
        self.configure(fg_color=T.BG_DEEP)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Переменные поиска и данных
        self.current_page_key = "tools"
        self.strings_search_query = ""
        self.strings_data = self._load_strings_data()

        self.lock = None
        if access.configured():
            self._build_lock()
        else:
            self._unlock()

    def _unlock(self):
        self._build_sidebar()
        self._build_content()
        self.show("tools")

    # ---------- экран блокировки (доступ через Google Таблицу) ----------
    def _build_lock(self):
        self.hwid = access.get_hwid()
        self.lock = ctk.CTkFrame(self, fg_color=T.BG_DEEP)
        self.lock.grid(row=0, column=0, columnspan=2, sticky="nsew")

        box = ctk.CTkFrame(self.lock, fg_color="transparent")
        box.place(relx=0.5, rely=0.45, anchor="center")
        
        ctk.CTkLabel(box, text=APP_NAME, font=("Segoe UI Semibold", 32), text_color=T.TEXT).pack()
        ctk.CTkLabel(box, text="СИСТЕМА ПРОВЕРКИ НА ЧИТЫ", font=T.FONT_SUB, text_color=T.TEXT_MUTED).pack(pady=(4, 20))
        
        # Красивая карточка с кодом
        code_card = ctk.CTkFrame(box, fg_color=T.BG_CARD, border_width=1, border_color=T.BORDER, corner_radius=16)
        code_card.pack(pady=10, padx=20)
        
        ctk.CTkLabel(code_card, text="Ваш номер для проверки", font=T.FONT_SUB, text_color=T.TEXT_MUTED).pack(pady=(16, 0), padx=30)
        
        self.lock_number = ctk.CTkLabel(code_card, text="…", font=("Segoe UI Semibold", 80), text_color=T.ACCENT)
        self.lock_number.pack(pady=(4, 16), padx=30)
        
        self.lock_info = ctk.CTkLabel(box, text="Получение номера доступа…", font=T.FONT_SUB, text_color=T.TEXT_MUTED)
        self.lock_info.pack(pady=10)

        threading.Thread(target=self._lock_register, daemon=True).start()

    def _lock_register(self):
        try:
            r = access.register(self.hwid)
            self.after(0, self._lock_registered, r)
        except Exception:
            self.after(0, lambda: self.lock_info.configure(
                text="Нет связи с сервером — повторный запрос через 5 сек…"))
            self.after(5000, lambda: threading.Thread(
                target=self._lock_register, daemon=True).start())

    def _lock_registered(self, r):
        self.lock_number.configure(text=str(r.get("number", "?")))
        self.lock_info.configure(text="Сообщите номер модератору и ожидайте начала проверки")
        self._lock_apply(r)

    def _lock_poll_schedule(self):
        self.after(4000, lambda: threading.Thread(
            target=self._lock_poll, daemon=True).start())

    def _lock_poll(self):
        try:
            r = access.status(self.hwid)
        except Exception:
            self.after(0, self._lock_poll_schedule)
            return
        self.after(0, self._lock_apply, r)

    def _lock_apply(self, r):
        st = r.get("status")
        if st == "finished":
            messagebox.showinfo("Проверка завершена", "Проверка окончена. Программа будет закрыта.")
            self.destroy()
            return
        if st == "denied":
            messagebox.showerror("Доступ запрещен", "Вам отказано в прохождении проверки. Программа закрывается.")
            self.destroy()
            return
        if st == "checking" and self.lock is not None:
            self.lock.destroy()
            self.lock = None
            self._unlock()
        self._lock_poll_schedule()

    # ---------- левая панель ----------
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color=T.BG_SIDEBAR)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(9, weight=1)

        ctk.CTkLabel(self.sidebar, text=APP_NAME, font=("Segoe UI Semibold", 24), text_color=T.TEXT)\
            .grid(row=0, column=0, padx=24, pady=(24, 2), sticky="w")
        ctk.CTkLabel(self.sidebar, text="проверка на читы", font=T.FONT_SMALL, text_color=T.TEXT_MUTED)\
            .grid(row=1, column=0, padx=24, pady=(0, 24), sticky="w")

        self.nav = {}
        items = [
            ("tools", "Программы", "🛠️"),
            ("folders", "Игровые папки", "📁"),
            ("strings", "База ниток", "🧵"),
            ("disks", "Диски и тома", "💾"),
            ("apps", "Поиск следов", "🔎"),
            ("system", "Система", "💻"),
            ("settings", "Дизайн", "🎨"),
        ]
        
        for i, (key, label, icon) in enumerate(items):
            b = ctk.CTkButton(
                self.sidebar, text=f"  {icon}  {label}", anchor="w", height=42,
                corner_radius=10, font=T.FONT_ITEM,
                fg_color="transparent", hover_color=T.BG_CARD_HOV,
                text_color=T.TEXT_MUTED,
                command=lambda k=key: self.show(k),
            )
            b.grid(row=2 + i, column=0, padx=14, pady=3, sticky="ew")
            self.nav[key] = b

        # красная кнопка внизу
        ctk.CTkButton(
            self.sidebar, text="Завершить проверку", width=220, height=44, corner_radius=10,
            font=T.FONT_ITEM, fg_color=T.DANGER, hover_color=T.DANGER_HOVER,
            text_color=T.TEXT, command=self.finish,
        ).grid(row=10, column=0, pady=(10, 24), sticky="s")

    def _build_content(self):
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color=T.BG_DEEP)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)

    def show(self, key):
        self.current_page_key = key
        for k, b in self.nav.items():
            active = k == key
            b.configure(
                fg_color=T.ACCENT if active else "transparent",
                text_color=T.TEXT if active else T.TEXT_MUTED,
                hover_color=T.ACCENT_HOVER if active else T.BG_CARD_HOV,
            )
        for w in self.content.winfo_children():
            w.destroy()
        
        pages = {
            "tools": self.page_tools,
            "folders": self.page_folders,
            "strings": self.page_strings,
            "disks": self.page_disks,
            "apps": self.page_apps,
            "system": self.page_system,
            "settings": self.page_settings
        }
        pages[key]()

    def _header(self, title, subtitle):
        box = ctk.CTkFrame(self.content, fg_color="transparent")
        box.grid(row=0, column=0, sticky="ew", padx=30, pady=(24, 12))
        ctk.CTkLabel(box, text=title, font=T.FONT_TITLE, text_color=T.TEXT).pack(anchor="w")
        ctk.CTkLabel(box, text=subtitle, font=T.FONT_SUB, text_color=T.TEXT_MUTED).pack(anchor="w", pady=(2, 0))

    # ---------- раздел: Программы ----------
    def page_tools(self):
        self._header("Программы", f"Запуск утилит для проверки — файлы ({len(TOOLS)} шт.) лежат в папке tools")
        
        grid = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        grid.grid(row=1, column=0, sticky="nsew", padx=22, pady=(0, 22))
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)

        for i, tool in enumerate(TOOLS):
            card = ctk.CTkFrame(grid, fg_color=T.BG_CARD, corner_radius=14,
                                border_width=1, border_color=T.BORDER)
            card.grid(row=i // 2, column=i % 2, padx=10, pady=10, sticky="nsew")
            card.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(card, text=tool["name"], font=T.FONT_ITEM, text_color=T.TEXT)\
                .grid(row=0, column=0, sticky="w", padx=18, pady=(16, 0))
            
            ctk.CTkLabel(card, text=tool["desc"], font=T.FONT_SMALL, text_color=T.TEXT_MUTED,
                         wraplength=320, justify="left")\
                .grid(row=1, column=0, sticky="w", padx=18, pady=(4, 16))

            exists = os.path.isfile(os.path.join(tools_dir(), tool["exe"]))
            
            ctk.CTkButton(
                card, text="Запустить" if exists else "Файл не найден", height=34, width=140,
                corner_radius=8, font=T.FONT_SMALL,
                fg_color=T.ACCENT if exists else T.BG_CARD_HOV,
                hover_color=T.ACCENT_HOVER if exists else T.BG_CARD_HOV,
                text_color=T.TEXT if exists else T.TEXT_MUTED,
                state="normal" if exists else "disabled",
                command=lambda t=tool: self.run_tool(t),
            ).grid(row=2, column=0, sticky="w", padx=18, pady=(0, 16))

    def run_tool(self, tool):
        path = os.path.join(tools_dir(), tool["exe"])
        try:
            if path.lower().endswith(".jar"):
                subprocess.Popen(["java", "-jar", path], cwd=os.path.dirname(path))
            elif tool.get("args") and path.lower().endswith(".exe"):
                subprocess.Popen([path] + tool["args"], cwd=os.path.dirname(path))
            else:
                os.startfile(path)
        except Exception as e:
            messagebox.showerror("Ошибка запуска", f"{tool['name']}\n\n{e}")

    # ---------- раздел: Игровые папки ----------
    def page_folders(self):
        self._header("Игровые папки", "Открытие директорий клиента игры в один клик")
        
        box = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        box.grid(row=1, column=0, sticky="nsew", padx=22, pady=(0, 22))
        box.grid_columnconfigure(0, weight=1)

        for i, f in enumerate(GAME_FOLDERS):
            real = os.path.expandvars(f["path"])
            exists = os.path.isdir(real)

            row = ctk.CTkFrame(box, fg_color=T.BG_CARD, corner_radius=14,
                               border_width=1, border_color=T.BORDER)
            row.grid(row=i, column=0, sticky="ew", padx=10, pady=8)
            row.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(row, text=f["name"], font=T.FONT_ITEM, text_color=T.TEXT)\
                .grid(row=0, column=0, sticky="w", padx=20, pady=(14, 0))
            
            ctk.CTkLabel(row, text=real, font=T.FONT_SMALL,
                         text_color=T.ACCENT_SOFT if exists else T.TEXT_MUTED)\
                .grid(row=1, column=0, sticky="w", padx=20, pady=(4, 14))

            ctk.CTkButton(
                row, text="Открыть" if exists else "Папка отсутствует", width=140, height=36,
                corner_radius=8, font=T.FONT_SMALL,
                fg_color=T.ACCENT if exists else T.BG_CARD_HOV,
                hover_color=T.ACCENT_HOVER if exists else T.BG_CARD_HOV,
                text_color=T.TEXT if exists else T.TEXT_MUTED,
                state="normal" if exists else "disabled",
                command=lambda p=real: os.startfile(p),
            ).grid(row=0, column=1, rowspan=2, padx=20, pady=10)

    # ---------- раздел: База ниток (Проводник по Нитки.txt) ----------
    def page_strings(self):
        self._header("База ниток для поиска", "Быстрый поиск и копирование ключевых строк для Everything / System Informer")
        
        # Поиск
        search_box = ctk.CTkFrame(self.content, fg_color="transparent")
        search_box.grid(row=1, column=0, sticky="ew", padx=30, pady=(0, 12))
        search_box.grid_columnconfigure(0, weight=1)
        
        self.str_search_var = ctk.StringVar(value=self.strings_search_query)
        self.str_search_var.trace_add("write", self._on_strings_search_changed)
        
        search_entry = ctk.CTkEntry(
            search_box, placeholder_text="🔍 Введите ключевое слово или размер для фильтрации...",
            font=T.FONT_SUB, fg_color=T.BG_CARD, border_color=T.BORDER,
            text_color=T.TEXT, placeholder_text_color=T.TEXT_MUTED,
            height=40, corner_radius=10
        )
        search_entry.grid(row=0, column=0, sticky="ew")
        
        # Скролл контейнер для результатов
        self.strings_scroll = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        self.strings_scroll.grid(row=2, column=0, sticky="nsew", padx=22, pady=(0, 22))
        self.content.grid_rowconfigure(2, weight=1)
        
        self._render_strings()

    def _load_strings_data(self):
        """Парсинг файла Нитки.txt на разделы и элементы."""
        path = os.path.join(base_dir(), "Нитки.txt")
        if not os.path.isfile(path):
            return []
        
        sections = []
        current_section = None
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception:
            return []
            
        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue
                
            # Проверяем заголовок секции
            if line_clean.startswith("===") or (line_clean.startswith("==") and line_clean.endswith("==")):
                title = line_clean.replace("=", "").strip()
                if title:
                    if current_section:
                        sections.append(current_section)
                    current_section = {"title": title, "items": []}
                continue
                
            if current_section is None:
                current_section = {"title": "Общие строки", "items": []}
                
            # Разделение элементов
            if "|" in line_clean and not line_clean.startswith("size:"):
                # Ключевые слова через пайп
                parts = [p.strip() for p in line_clean.split("|") if p.strip()]
                current_section["items"].append({
                    "type": "keywords",
                    "parts": parts,
                    "raw": line_clean
                })
            else:
                # Обычный текст или поисковый паттерн
                current_section["items"].append({
                    "type": "text",
                    "text": line_clean
                })
                
        if current_section:
            sections.append(current_section)
            
        return sections

    def _on_strings_search_changed(self, *args):
        self.strings_search_query = self.str_search_var.get().strip().lower()
        self._render_strings()

    def _render_strings(self):
        for w in self.strings_scroll.winfo_children():
            w.destroy()
            
        self.strings_scroll.grid_columnconfigure(0, weight=1)
        row_idx = 0
        
        for sec in self.strings_data:
            # Фильтруем элементы секции
            filtered_items = []
            for item in sec["items"]:
                if not self.strings_search_query:
                    filtered_items.append(item)
                else:
                    if item["type"] == "text" and self.strings_search_query in item["text"].lower():
                        filtered_items.append(item)
                    elif item["type"] == "keywords":
                        matching_parts = [p for p in item["parts"] if self.strings_search_query in p.lower()]
                        if matching_parts or self.strings_search_query in item["raw"].lower():
                            filtered_items.append(item)
            
            if not filtered_items:
                continue
                
            # Заголовок секции
            sec_lbl = ctk.CTkLabel(self.strings_scroll, text=sec["title"], font=("Segoe UI Semibold", 16), text_color=T.ACCENT_SOFT)
            sec_lbl.grid(row=row_idx, column=0, sticky="w", padx=12, pady=(16, 6))
            row_idx += 1
            
            for item in filtered_items:
                card = ctk.CTkFrame(self.strings_scroll, fg_color=T.BG_CARD, corner_radius=10, border_width=1, border_color=T.BORDER)
                card.grid(row=row_idx, column=0, sticky="ew", padx=10, pady=5)
                card.grid_columnconfigure(0, weight=1)
                row_idx += 1
                
                if item["type"] == "text":
                    lbl = ctk.CTkLabel(card, text=item["text"], font=T.FONT_SMALL, text_color=T.TEXT, justify="left", wraplength=600)
                    lbl.grid(row=0, column=0, sticky="w", padx=16, pady=12)
                    
                    # Кнопка копирования
                    btn = ctk.CTkButton(
                        card, text="Копировать", width=110, height=28, corner_radius=6, font=T.FONT_SMALL,
                        fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
                        command=lambda txt=item["text"]: self._copy_to_clipboard(txt)
                    )
                    btn.grid(row=0, column=1, padx=16, pady=12)
                    
                elif item["type"] == "keywords":
                    # Сетка для чипсов/кнопок
                    chips_frame = ctk.CTkFrame(card, fg_color="transparent")
                    chips_frame.grid(row=0, column=0, sticky="w", padx=12, pady=10)
                    
                    # Кнопки для каждого ключевого слова
                    col, r = 0, 0
                    for part in item["parts"]:
                        # Проверяем, совпадает ли с поиском
                        match = self.strings_search_query and self.strings_search_query in part.lower()
                        p_btn = ctk.CTkButton(
                            chips_frame, text=part, height=26, corner_radius=6, font=T.FONT_SMALL,
                            fg_color=T.ACCENT_SOFT if match else T.BG_CARD_HOV,
                            hover_color=T.ACCENT,
                            text_color=T.TEXT if match else T.TEXT_MUTED,
                            command=lambda p=part: self._copy_to_clipboard(p)
                        )
                        p_btn.grid(row=r, column=col, padx=4, pady=4, sticky="w")
                        col += 1
                        if col > 4:
                            col = 0
                            r += 1
                            
                    # Кнопка копирования всей строки
                    btn = ctk.CTkButton(
                        card, text="Копировать всё", width=120, height=28, corner_radius=6, font=T.FONT_SMALL,
                        fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
                        command=lambda txt=item["raw"]: self._copy_to_clipboard(txt)
                    )
                    btn.grid(row=0, column=1, padx=16, pady=12, sticky="ne" if r > 0 else "center")

    def _copy_to_clipboard(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update() # Обновляем буфер обмена системы
        
        # Всплывающее уведомление
        notification = ctk.CTkToplevel(self)
        notification.geometry("240x70")
        notification.overrideredirect(True)
        notification.configure(fg_color=T.BG_CARD)
        
        # Центрируем поверх главного окна
        x = self.winfo_x() + (self.winfo_width() // 2) - 120
        y = self.winfo_y() + (self.winfo_height() // 2) - 35
        notification.geometry(f"+{x}+{y}")
        
        lbl = ctk.CTkLabel(notification, text="✔️ Скопировано в буфер!", font=T.FONT_ITEM, text_color=T.ACCENT_SOFT)
        lbl.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Тень / рамка для всплывающего окна
        notification.lift()
        self.after(1000, notification.destroy)

    # ---------- раздел: Диски и тома (найти тумс/тома) ----------
    def page_disks(self):
        self._header("Диски и системные тома", "Сканирование дисков, USB-накопителей и RAM-дисков")
        
        box = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        box.grid(row=1, column=0, sticky="nsew", padx=22, pady=(0, 22))
        box.grid_columnconfigure(0, weight=1)
        
        drives = sysinfo.get_drives_info()
        
        if not drives:
            ctk.CTkLabel(box, text="Диски не обнаружены", font=T.FONT_TITLE, text_color=T.TEXT_MUTED).pack(pady=40)
            return

        for i, d in enumerate(drives):
            # Рамка для диска
            row = ctk.CTkFrame(
                box, fg_color=T.BG_CARD, corner_radius=14,
                border_width=2 if d["highlight"] else 1,
                border_color=T.ACCENT if d["highlight"] else T.BORDER
            )
            row.grid(row=i, column=0, sticky="ew", padx=10, pady=8)
            row.grid_columnconfigure(0, weight=1)
            
            # Заголовок диска
            header_frame = ctk.CTkFrame(row, fg_color="transparent")
            header_frame.grid(row=0, column=0, sticky="w", padx=18, pady=(14, 2))
            
            ctk.CTkLabel(header_frame, text=f"Диск {d['letter']}:  ", font=("Segoe UI Semibold", 16), text_color=T.TEXT).pack(side="left")
            ctk.CTkLabel(header_frame, text=f"[{d['label']}]", font=T.FONT_ITEM, text_color=T.ACCENT_SOFT if d["highlight"] else T.TEXT_MUTED).pack(side="left")
            
            # Тип и ФС
            type_text = f"Тип: {d['type_str']}  |  ФС: {d['fs_type']}"
            ctk.CTkLabel(row, text=type_text, font=T.FONT_SMALL, text_color=T.ACCENT_SOFT if d["highlight"] else T.TEXT_MUTED)\
                .grid(row=1, column=0, sticky="w", padx=18, pady=(0, 10))
                
            # Прогресс бар
            progress_frame = ctk.CTkFrame(row, fg_color="transparent")
            progress_frame.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 14))
            progress_frame.grid_columnconfigure(0, weight=1)
            
            if d["total_gb"] > 0:
                used_text = f"Занято: {d['used_gb']:.1f} ГБ  /  {d['total_gb']:.1f} ГБ  ({d['pct']}%)"
                ctk.CTkLabel(progress_frame, text=used_text, font=T.FONT_SMALL, text_color=T.TEXT_MUTED).grid(row=0, column=0, sticky="w")
                
                # Сам прогресс-бар
                pb = ctk.CTkProgressBar(progress_frame, fg_color=T.BG_DEEP, progress_color=T.ACCENT)
                pb.grid(row=1, column=0, sticky="ew", pady=(4, 0))
                pb.set(d["pct"] / 100.0)
            else:
                ctk.CTkLabel(progress_frame, text="Диск не готов или заблокирован", font=T.FONT_SMALL, text_color=T.DANGER).grid(row=0, column=0, sticky="w")
            
            # Серийный номер
            serial_text = f"Серийный номер тома: {d['serial']}"
            ctk.CTkLabel(row, text=serial_text, font=T.FONT_SMALL, text_color=T.TEXT_MUTED)\
                .grid(row=3, column=0, sticky="w", padx=18, pady=(0, 14))

            # Кнопка открытия диска
            ctk.CTkButton(
                row, text="Открыть диск", width=130, height=36, corner_radius=8, font=T.FONT_SMALL,
                fg_color=T.ACCENT if not d["highlight"] else T.BG_CARD_HOV,
                hover_color=T.ACCENT_HOVER if not d["highlight"] else T.ACCENT,
                text_color=T.TEXT,
                command=lambda p=d["path"]: os.startfile(p)
            ).grid(row=0, column=1, rowspan=4, padx=18, pady=10)

        # Кнопка обновления дисков
        ctk.CTkButton(box, text="Обновить список дисков", height=40, corner_radius=10,
                      fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER, font=T.FONT_ITEM,
                      command=lambda: self.show("disks")).grid(row=999, column=0, pady=20)

    # ---------- раздел: Поиск следов (включая Teams/Тумс) ----------
    def page_apps(self):
        self._header("Поиск следов мессенджеров и софта", "Сканирование запущенных процессов, папок установки и истории активности")
        
        box = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        box.grid(row=1, column=0, sticky="nsew", padx=22, pady=(0, 22))
        box.grid_columnconfigure(0, weight=1)
        
        # Получаем данные о приложениях
        scanned_apps = self._scan_apps_data()
        
        for i, app in enumerate(scanned_apps):
            card = ctk.CTkFrame(box, fg_color=T.BG_CARD, corner_radius=14, border_width=1, border_color=T.BORDER)
            card.grid(row=i, column=0, sticky="ew", padx=10, pady=8)
            card.grid_columnconfigure(0, weight=1)
            
            # Название программы и статус
            title_frame = ctk.CTkFrame(card, fg_color="transparent")
            title_frame.grid(row=0, column=0, sticky="w", padx=18, pady=(14, 2))
            
            ctk.CTkLabel(title_frame, text=app["name"], font=("Segoe UI Semibold", 16), text_color=T.TEXT).pack(side="left")
            
            # Метка статуса
            status_colors = {
                "accent": T.ACCENT_SOFT,
                "text": T.TEXT,
                "muted": T.TEXT_MUTED,
                "danger": T.DANGER
            }
            lbl_color = status_colors.get(app["status_color"], T.TEXT_MUTED)
            ctk.CTkLabel(title_frame, text=f"  ({app['status']})", font=T.FONT_ITEM, text_color=lbl_color).pack(side="left")
            
            # Описание
            ctk.CTkLabel(card, text=app["desc"], font=T.FONT_SMALL, text_color=T.TEXT_MUTED)\
                .grid(row=1, column=0, sticky="w", padx=18, pady=(0, 6))
                
            # Путь установки
            path_lbl = ctk.CTkLabel(card, text=f"Путь: {app['path']}", font=T.FONT_SMALL, text_color=T.TEXT_MUTED, justify="left", wraplength=550)
            path_lbl.grid(row=2, column=0, sticky="w", padx=18, pady=(0, 6))
            
            # Последнее изменение папки
            mtime_lbl = ctk.CTkLabel(card, text=f"Активность директории: {app['last_modified']}", font=T.FONT_SMALL, text_color=T.TEXT_MUTED)
            mtime_lbl.grid(row=3, column=0, sticky="w", padx=18, pady=(0, 14))
            
            # Кнопки действий справа
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.grid(row=0, column=1, rowspan=4, padx=18, pady=10)
            
            # Кнопка открыть папку
            exists = app["path"] != "нет данных"
            ctk.CTkButton(
                btn_frame, text="Открыть папку", width=130, height=32, corner_radius=8, font=T.FONT_SMALL,
                fg_color=T.ACCENT if exists else T.BG_CARD_HOV,
                hover_color=T.ACCENT_HOVER if exists else T.BG_CARD_HOV,
                text_color=T.TEXT if exists else T.TEXT_MUTED,
                state="normal" if exists else "disabled",
                command=lambda p=app["path"]: os.startfile(p)
            ).pack(pady=4)
            
            # Кнопка завершить процесс (если запущен)
            if app["is_running"]:
                ctk.CTkButton(
                    btn_frame, text="Закрыть процесс", width=130, height=32, corner_radius=8, font=T.FONT_SMALL,
                    fg_color=T.DANGER, hover_color=T.DANGER_HOVER,
                    text_color=T.TEXT,
                    command=lambda p=app["process"]: self._kill_process(p)
                ).pack(pady=4)

        # Кнопка обновления
        ctk.CTkButton(box, text="Обновить статус приложений", height=40, corner_radius=10,
                      fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER, font=T.FONT_ITEM,
                      command=lambda: self.show("apps")).grid(row=999, column=0, pady=20)

    def _scan_apps_data(self):
        """Сканирование установленного софта на ПК."""
        import winreg
        import psutil
        
        apps = [
            {
                "name": "Discord",
                "process": "Discord.exe",
                "paths": [r"%LOCALAPPDATA%\Discord", r"%APPDATA%\Discord"],
                "desc": "Голосовой мессенджер. Чат-логи и файлы кэша передаваемых медиа."
            },
            {
                "name": "Telegram",
                "process": "Telegram.exe",
                "paths": [r"%APPDATA%\Telegram Desktop"],
                "desc": "Проверка загрузок (Telegram Desktop\\tdata), медиа и последних сессий."
            },
            {
                "name": "Microsoft Teams (Тумс/Тимс)",
                "process": "Teams.exe",
                "paths": [
                    r"%LOCALAPPDATA%\Microsoft\Teams", 
                    r"%APPDATA%\Microsoft\Teams",
                    r"%LOCALAPPDATA%\Packages\MSTeams_8wekyb3d8bbwe",
                    r"%LOCALAPPDATA%\Microsoft\MSTeams"
                ],
                "desc": "Корпоративный мессенджер (Тумс), хранит кэш файлов, переписки и запущенные модули."
            },
            {
                "name": "Steam",
                "process": "steam.exe",
                "paths": [r"C:\Program Files (x86)\Steam", r"C:\Program Files\Steam"],
                "desc": "Игровой клиент. История запусков игр и библиотек (.dll)."
            },
            {
                "name": "TLauncher",
                "process": "TLauncher.exe",
                "paths": [r"%APPDATA%\.tlauncher", r"%APPDATA%\LegacyLauncher"],
                "desc": "Minecraft Лаунчер. Логи авторизации, пути к Java и запущенные версии."
            },
            {
                "name": "Feather Launcher",
                "process": "Feather.exe",
                "paths": [r"%APPDATA%\.feather"],
                "desc": "Профессиональный игровой клиент с модами и скрытыми инжектами."
            },
            {
                "name": "CurseForge",
                "process": "CurseForge.exe",
                "paths": [r"%LOCALAPPDATA%\CurseForge"],
                "desc": "Управление модами. Позволяет быстро загружать сторонние аддоны."
            }
        ]
        
        # Чтение Steam из реестра
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as k:
                steam_path = winreg.QueryValueEx(k, "SteamPath")[0]
                if steam_path and os.path.isdir(steam_path):
                    apps[3]["paths"].insert(0, steam_path.replace("/", "\\"))
        except OSError:
            pass
            
        # Сбор запущенных процессов
        running_processes = {}
        for p in psutil.process_iter(attrs=['pid', 'name']):
            try:
                name = p.info['name']
                if name:
                    running_processes[name.lower()] = p.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        results = []
        for app in apps:
            status = "Не найден"
            status_color = "muted"
            real_path = "нет данных"
            is_running = False
            pid = None
            
            proc_lower = app["process"].lower()
            if proc_lower in running_processes:
                is_running = True
                pid = running_processes[proc_lower]
                status = f"Запущен (PID: {pid})"
                status_color = "accent"
                
            found_path = None
            last_modified = None
            for p in app["paths"]:
                expanded = os.path.expandvars(p)
                if os.path.isdir(expanded):
                    found_path = expanded
                    try:
                        mtime = os.path.getmtime(expanded)
                        last_modified = datetime.fromtimestamp(mtime).strftime("%d.%m.%Y  %H:%M:%S")
                    except OSError:
                        pass
                    break
                    
            if found_path:
                real_path = found_path
                if not is_running:
                    status = "Установлен"
                    status_color = "text"
            else:
                status = "Не установлен"
                status_color = "muted"
                
            results.append({
                "name": app["name"],
                "process": app["process"],
                "desc": app["desc"],
                "status": status,
                "status_color": status_color,
                "path": real_path,
                "is_running": is_running,
                "pid": pid,
                "last_modified": last_modified or "нет данных"
            })
            
        return results

    def _kill_process(self, process_name):
        import psutil
        if messagebox.askyesno("Подтверждение", f"Вы действительно хотите принудительно закрыть все процессы {process_name}?"):
            killed = False
            for proc in psutil.process_iter(attrs=['name']):
                try:
                    if proc.info['name'] and proc.info['name'].lower() == process_name.lower():
                        proc.terminate()
                        killed = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            if killed:
                messagebox.showinfo("Процесс завершен", f"Процессы {process_name} были завершены.")
                self.show("apps")
            else:
                messagebox.showerror("Ошибка", f"Не удалось завершить процессы {process_name}.")

    # ---------- раздел: Системная информация ----------
    def page_system(self):
        self._header("Системная информация", "Данные системы, важные маркеры времени очистки корзины и аптайма")
        
        box = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        box.grid(row=1, column=0, sticky="nsew", padx=22, pady=(0, 22))
        box.grid_columnconfigure(0, weight=1)

        for i, (label, value, highlight) in enumerate(sysinfo.collect()):
            row = ctk.CTkFrame(
                box, fg_color=T.BG_CARD, corner_radius=14,
                border_width=2 if highlight else 1,
                border_color=T.ACCENT if highlight else T.BORDER,
            )
            row.grid(row=i, column=0, sticky="ew", padx=10, pady=6)
            row.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(row, text=label, font=T.FONT_SMALL, text_color=T.TEXT_MUTED, width=250, anchor="w")\
                .grid(row=0, column=0, sticky="w", padx=20, pady=14)
            
            ctk.CTkLabel(row, text=value, font=T.FONT_ITEM,
                         text_color=T.ACCENT_SOFT if highlight else T.TEXT, anchor="w")\
                .grid(row=0, column=1, sticky="w", pady=14)

        ctk.CTkButton(box, text="Обновить системные данные", height=40, corner_radius=10,
                      fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER, font=T.FONT_SMALL,
                      command=lambda: self.show("system")).grid(row=999, column=0, pady=20)

    # ---------- раздел: Настройки (Выбор тем/дизайна) ----------
    def page_settings(self):
        self._header("Настройки дизайна приложения", "Выберите оформление интерфейса, настройте цветовые схемы и проверьте HWID")
        
        box = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        box.grid(row=1, column=0, sticky="nsew", padx=22, pady=(0, 22))
        box.grid_columnconfigure(0, weight=1)
        
        # Карточка выбора темы
        card_theme = ctk.CTkFrame(box, fg_color=T.BG_CARD, corner_radius=14, border_width=1, border_color=T.BORDER)
        card_theme.grid(row=0, column=0, sticky="ew", padx=10, pady=8)
        card_theme.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(card_theme, text="Тема оформления интерфейса", font=("Segoe UI Semibold", 16), text_color=T.TEXT)\
            .grid(row=0, column=0, sticky="w", padx=20, pady=(16, 2))
            
        ctk.CTkLabel(card_theme, text="Выберите цветовую схему для изменения оттенков карточек, кнопок и шрифтов.", font=T.FONT_SMALL, text_color=T.TEXT_MUTED)\
            .grid(row=1, column=0, sticky="w", padx=20, pady=(0, 16))
            
        # Dropdown выбора темы
        theme_menu = ctk.CTkOptionMenu(
            card_theme, values=T.get_themes(),
            fg_color=T.BG_DEEP, button_color=T.ACCENT, button_hover_color=T.ACCENT_HOVER,
            dropdown_fg_color=T.BG_CARD, dropdown_hover_color=T.BG_CARD_HOV,
            font=T.FONT_ITEM, dropdown_font=T.FONT_SMALL,
            height=36, width=200, corner_radius=8,
            command=self._change_theme
        )
        theme_menu.grid(row=0, column=1, rowspan=2, padx=20, pady=16)
        theme_menu.set(T.get_current_theme())
        
        # Карточка системных метаданных
        card_meta = ctk.CTkFrame(box, fg_color=T.BG_CARD, corner_radius=14, border_width=1, border_color=T.BORDER)
        card_meta.grid(row=1, column=0, sticky="ew", padx=10, pady=8)
        card_meta.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(card_meta, text="Идентификатор компьютера (HWID)", font=("Segoe UI Semibold", 16), text_color=T.TEXT)\
            .grid(row=0, column=0, sticky="w", padx=20, pady=(16, 2))
            
        hwid_str = access.get_hwid()
        ctk.CTkLabel(card_meta, text=f"HWID: {hwid_str}", font=T.FONT_SMALL, text_color=T.ACCENT_SOFT)\
            .grid(row=1, column=0, sticky="w", padx=20, pady=(0, 16))
            
        ctk.CTkButton(
            card_meta, text="Копировать HWID", width=150, height=34, corner_radius=8, font=T.FONT_SMALL,
            fg_color=T.BG_DEEP, hover_color=T.BG_CARD_HOV, text_color=T.TEXT,
            command=lambda: self._copy_to_clipboard(hwid_str)
        ).grid(row=0, column=1, rowspan=2, padx=20, pady=16)

    def _change_theme(self, new_theme_name):
        """Смена цветовой темы оформления на лету."""
        if T.apply_theme(new_theme_name):
            # Перенастраиваем главное окно и боковую панель
            self.configure(fg_color=T.BG_DEEP)
            self.sidebar.configure(fg_color=T.BG_SIDEBAR)
            
            # Обновляем все кнопки в боковой панели
            for key, btn in self.nav.items():
                active = key == self.current_page_key
                btn.configure(
                    fg_color=T.ACCENT if active else "transparent",
                    text_color=T.TEXT if active else T.TEXT_MUTED,
                    hover_color=T.ACCENT_HOVER if active else T.BG_CARD_HOV,
                )
                
            # Перерисовываем текущую активную страницу
            self.show(self.current_page_key)

    # ---------- завершение ----------
    def finish(self):
        if messagebox.askyesno("Завершить проверку", "Закрыть клиент и завершить проверку?"):
            self.destroy()


if __name__ == "__main__":
    App().mainloop()

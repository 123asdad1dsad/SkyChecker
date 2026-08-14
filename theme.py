# Текущая активная тема и её палитра
# По умолчанию используется тёмно-синяя Space Blue

THEMES = {
    "Space Blue": {
        "BG_DEEP": "#0B1220",
        "BG_SIDEBAR": "#0F1A2E",
        "BG_CARD": "#152238",
        "BG_CARD_HOV": "#1D2E4A",
        "ACCENT": "#2D6CFF",
        "ACCENT_HOVER": "#1B54D6",
        "ACCENT_SOFT": "#3B82F6",
        "BORDER": "#22304D",
        "TEXT": "#FFFFFF",
        "TEXT_MUTED": "#9BB0D0",
    },
    "Cyber Violet": {
        "BG_DEEP": "#0D0814",
        "BG_SIDEBAR": "#140D24",
        "BG_CARD": "#1C1231",
        "BG_CARD_HOV": "#261947",
        "ACCENT": "#A855F7",
        "ACCENT_HOVER": "#9333EA",
        "ACCENT_SOFT": "#C084FC",
        "BORDER": "#311C53",
        "TEXT": "#FFFFFF",
        "TEXT_MUTED": "#C0A9DF",
    },
    "Emerald Dragon": {
        "BG_DEEP": "#060F0E",
        "BG_SIDEBAR": "#0B1A18",
        "BG_CARD": "#112624",
        "BG_CARD_HOV": "#193633",
        "ACCENT": "#10B981",
        "ACCENT_HOVER": "#059669",
        "ACCENT_SOFT": "#34D399",
        "BORDER": "#1D423F",
        "TEXT": "#FFFFFF",
        "TEXT_MUTED": "#99F6E4",
    },
    "Volcano Red": {
        "BG_DEEP": "#120707",
        "BG_SIDEBAR": "#1C0D0D",
        "BG_CARD": "#281414",
        "BG_CARD_HOV": "#361D1D",
        "ACCENT": "#EF4444",
        "ACCENT_HOVER": "#DC2626",
        "ACCENT_SOFT": "#F87171",
        "BORDER": "#441D1D",
        "TEXT": "#FFFFFF",
        "TEXT_MUTED": "#FCA5A5",
    },
    "Absolute Dark": {
        "BG_DEEP": "#09090B",
        "BG_SIDEBAR": "#18181B",
        "BG_CARD": "#222225",
        "BG_CARD_HOV": "#2D2D30",
        "ACCENT": "#D4D4D8",
        "ACCENT_HOVER": "#A1A1AA",
        "ACCENT_SOFT": "#71717A",
        "BORDER": "#2D2D30",
        "TEXT": "#FFFFFF",
        "TEXT_MUTED": "#A1A1AA",
    }
}

# Инициализируем переменные первой темой по умолчанию
_current_theme = "Space Blue"
_t = THEMES[_current_theme]

BG_DEEP      = _t["BG_DEEP"]
BG_SIDEBAR   = _t["BG_SIDEBAR"]
BG_CARD      = _t["BG_CARD"]
BG_CARD_HOV  = _t["BG_CARD_HOV"]
ACCENT       = _t["ACCENT"]
ACCENT_HOVER = _t["ACCENT_HOVER"]
ACCENT_SOFT  = _t["ACCENT_SOFT"]
TEXT         = _t["TEXT"]
TEXT_MUTED   = _t["TEXT_MUTED"]
BORDER       = _t["BORDER"]

DANGER       = "#E03131"   # кнопка «Завершить проверку»
DANGER_HOVER = "#B02525"

FONT_TITLE   = ("Segoe UI Semibold", 20)
FONT_SUB     = ("Segoe UI", 12)
FONT_ITEM    = ("Segoe UI Semibold", 13)
FONT_SMALL   = ("Segoe UI", 11)


def get_current_theme():
    return _current_theme


def get_themes():
    return list(THEMES.keys())


def apply_theme(name):
    global BG_DEEP, BG_SIDEBAR, BG_CARD, BG_CARD_HOV, ACCENT, ACCENT_HOVER, ACCENT_SOFT, BORDER, TEXT, TEXT_MUTED, _current_theme
    if name in THEMES:
        _current_theme = name
        _t = THEMES[name]
        BG_DEEP      = _t["BG_DEEP"]
        BG_SIDEBAR   = _t["BG_SIDEBAR"]
        BG_CARD      = _t["BG_CARD"]
        BG_CARD_HOV  = _t["BG_CARD_HOV"]
        ACCENT       = _t["ACCENT"]
        ACCENT_HOVER = _t["ACCENT_HOVER"]
        ACCENT_SOFT  = _t["ACCENT_SOFT"]
        BORDER       = _t["BORDER"]
        TEXT         = _t["TEXT"]
        TEXT_MUTED   = _t["TEXT_MUTED"]
        return True
    return False

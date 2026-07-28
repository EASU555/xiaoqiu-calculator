from __future__ import annotations

import ctypes
import json
import os
import re
import sys
import tkinter as tk
import tkinter.font as tkfont
from decimal import (
    Decimal,
    DecimalException,
    InvalidOperation,
    ROUND_HALF_UP,
    localcontext,
)
from pathlib import Path

import customtkinter as ctk


DEFAULT_DIVISOR = "475"
DEFAULT_COEFFICIENT = "475"
DEFAULT_FIXED_VALUE = "475"
DEFAULT_COUNTER_HOTKEY = "space"
DEFAULT_COUNTER_HOTKEY_CODE = 32
MAX_INPUT_LENGTH = 64
MAX_RESULT_LENGTH = 24
CALCULATION_PRECISION = MAX_INPUT_LENGTH * 3
NUMBER_PATTERN = re.compile(r"-?(?:\d+(?:\.\d*)?|\.\d+)$")
EDITING_PATTERN = re.compile(r"^-?(?:\d*(?:\.\d*)?)?$")
HOTKEY_PATTERN = re.compile(r"^[^\s<>]{1,64}$", re.UNICODE)

RESERVED_HOTKEYS = frozenset(
    {
        "return",
        "kp_enter",
        "escape",
        "tab",
        "iso_left_tab",
        "shift_l",
        "shift_r",
        "control_l",
        "control_r",
        "alt_l",
        "alt_r",
        "meta_l",
        "meta_r",
        "super_l",
        "super_r",
        "win_l",
        "win_r",
        "caps_lock",
        "num_lock",
        "scroll_lock",
        "menu",
    }
)

# Windows virtual-key codes reserved for navigation or existing app commands.
RESERVED_KEYCODES = frozenset(
    {
        9,   # Tab
        13,  # Enter
        16,  # Shift
        17,  # Ctrl
        18,  # Alt
        20,  # Caps Lock
        27,  # Escape
        91,  # Left Windows
        92,  # Right Windows
        93,  # Menu
        144, # Num Lock
        145, # Scroll Lock
    }
)

HOTKEY_DISPLAY_NAMES = {
    "space": "Space",
    "backspace": "Backspace",
    "delete": "Delete",
    "insert": "Insert",
    "home": "Home",
    "end": "End",
    "prior": "Page Up",
    "next": "Page Down",
    "left": "←",
    "right": "→",
    "up": "↑",
    "down": "↓",
    "kp_add": "Num +",
    "kp_subtract": "Num −",
    "kp_multiply": "Num ×",
    "kp_divide": "Num ÷",
    "kp_decimal": "Num .",
}

KEYCODE_DISPLAY_NAMES = {
    8: "Backspace",
    19: "Pause",
    32: "Space",
    33: "Page Up",
    34: "Page Down",
    35: "End",
    36: "Home",
    37: "←",
    38: "↑",
    39: "→",
    40: "↓",
    45: "Insert",
    46: "Delete",
    106: "Num ×",
    107: "Num +",
    109: "Num −",
    110: "Num .",
    111: "Num ÷",
    186: ";",
    187: "=",
    188: ",",
    189: "−",
    190: ".",
    191: "/",
    192: "`",
    219: "[",
    220: "\\",
    221: "]",
    222: "'",
}
KEYCODE_DISPLAY_NAMES.update({code: chr(code) for code in range(48, 58)})
KEYCODE_DISPLAY_NAMES.update({code: chr(code) for code in range(65, 91)})
KEYCODE_DISPLAY_NAMES.update(
    {code: f"Num {code - 96}" for code in range(96, 106)}
)
KEYCODE_DISPLAY_NAMES.update(
    {code: f"F{code - 111}" for code in range(112, 136)}
)

WINDOW_WIDTH = 500
WINDOW_HEIGHT = 660

# Neutral graphite surfaces with a restrained burnt-orange accent.
APP_BG = "#0D0F12"
SURFACE = "#171A1F"
SURFACE_ALT = "#1E2228"
BORDER = "#303640"
TEXT = "#F4F6F8"
MUTED = "#A8B0BA"
FAINT = "#7D8792"
ACCENT = "#F28C28"
ACCENT_HOVER = "#FFA44F"
ACCENT_TEXT = "#19120C"
ACCENT_SOFT = "#211C17"
ACCENT_BORDER = "#704624"
SUCCESS = "#74D18A"
SUCCESS_SOFT = "#112419"
ERROR = "#FF9191"
ERROR_SOFT = "#351619"


class InputValidationError(ValueError):
    """A validation failure tied to one user-editable field."""

    def __init__(self, message: str, field: str) -> None:
        super().__init__(message)
        self.field = field


class CalculationRangeError(ValueError):
    """A valid calculation whose display would be unsafe or impractical."""


def resource_path(filename: str) -> Path:
    """Resolve a bundled PyInstaller asset or a source-tree asset."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / filename


def parse_number(value: str, label: str) -> Decimal:
    """Parse one user-entered signed integer or decimal."""
    value = value.strip()
    field_name = f"{label} 数据" if label in {"A", "B"} else label
    if not value:
        if label in {"A", "B"}:
            raise InputValidationError(f"请输入 {field_name}。", label)
        raise InputValidationError(f"请输入{field_name}。", label)
    if len(value) > MAX_INPUT_LENGTH:
        raise InputValidationError(
            f"{field_name}最多输入 {MAX_INPUT_LENGTH} 个字符。",
            label,
        )
    if not NUMBER_PATTERN.fullmatch(value):
        raise InputValidationError(
            f"{field_name}必须是数字（支持整数和小数）。",
            label,
        )
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise InputValidationError(
            f"{field_name}必须是数字（支持整数和小数）。",
            label,
        ) from exc


def format_result(value: Decimal) -> str:
    """Round to two decimal places, then remove insignificant zeroes."""
    try:
        integer_places = max(value.adjusted() + 1, 1) if value else 1
        with localcontext() as context:
            context.prec = max(
                len(value.as_tuple().digits),
                integer_places,
                28,
            ) + 4
            rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except DecimalException as exc:
        raise CalculationRangeError("数值超出可计算范围，请缩小输入值。") from exc
    if rounded == 0:
        rounded = Decimal("0")
    text = format(rounded, "f").rstrip("0").rstrip(".")
    text = text or "0"
    if len(text) > MAX_RESULT_LENGTH:
        raise CalculationRangeError(
            "计算结果过长，请缩小输入值或增大除数。"
        )
    return text


def calculate_values(
    a_text: str,
    b_text: str,
    divisor_text: str = DEFAULT_DIVISOR,
) -> tuple[str, str]:
    """Return the two display values for the calculator."""
    a_value = parse_number(a_text, "A")
    b_value = parse_number(b_text, "B")
    divisor = parse_number(divisor_text, "除数")
    if divisor == 0:
        raise InputValidationError("除数不能为 0。", "除数")
    try:
        with localcontext() as context:
            context.prec = CALCULATION_PRECISION
            total = a_value + b_value
            divided = b_value / divisor
    except DecimalException as exc:
        raise CalculationRangeError("数值超出可计算范围，请调整输入。") from exc
    return format_result(total), format_result(divided)


def calculate_multiply_add_value(
    coefficient_text: str,
    multiplier_text: str,
    addend_text: str,
) -> str:
    """Return the display value for coefficient × multiplier + addend."""
    coefficient = parse_number(coefficient_text, "系数")
    multiplier = parse_number(multiplier_text, "乘数")
    addend = parse_number(addend_text, "加数")
    try:
        with localcontext() as context:
            context.prec = CALCULATION_PRECISION
            result = coefficient * multiplier + addend
    except DecimalException as exc:
        raise CalculationRangeError("数值超出可计算范围，请调整输入。") from exc
    return format_result(result)


def calculate_fixed_value_operation(
    fixed_value_text: str,
    operation_value_text: str,
    operation: str,
) -> str:
    """Return one result for fixed value (+, -, ×, ÷) operation value."""
    fixed_value = parse_number(fixed_value_text, "固定值")
    operation_value = parse_number(operation_value_text, "运算值")
    if operation not in {"+", "-", "×", "÷"}:
        raise ValueError("不支持的运算符。")
    if operation == "÷" and operation_value == 0:
        raise InputValidationError("进行除法时，运算值不能为 0。", "运算值")

    try:
        with localcontext() as context:
            context.prec = CALCULATION_PRECISION
            if operation == "+":
                result = fixed_value + operation_value
            elif operation == "-":
                result = fixed_value - operation_value
            elif operation == "×":
                result = fixed_value * operation_value
            else:
                result = fixed_value / operation_value
    except DecimalException as exc:
        raise CalculationRangeError("数值超出可计算范围，请调整输入。") from exc
    return format_result(result)


def increment_counter_value(current: int) -> int:
    """Return the next counter value for one click or shortcut press."""
    return current + 1


def normalize_hotkey(keysym: str) -> str | None:
    """Validate and normalize one Tk key symbol for counter binding."""
    if not isinstance(keysym, str):
        return None
    candidate = keysym.strip()
    if not HOTKEY_PATTERN.fullmatch(candidate):
        return None
    if candidate.lower() in RESERVED_HOTKEYS:
        return None
    return candidate.lower() if len(candidate) == 1 else candidate


def normalize_keycode(keycode: object) -> int | None:
    """Return a usable Windows/Tk keycode without treating it as text."""
    try:
        normalized = int(keycode)
    except (TypeError, ValueError, OverflowError):
        return None
    if not 1 <= normalized <= 65535:
        return None
    return normalized


def hotkey_is_reserved(keysym: str, keycode: object = None) -> bool:
    """Protect app commands and system navigation from being overwritten."""
    lowered = keysym.strip().lower() if isinstance(keysym, str) else ""
    normalized_code = normalize_keycode(keycode)
    return lowered in RESERVED_HOTKEYS or normalized_code in RESERVED_KEYCODES


def hotkey_display_name(keysym: str, keycode: object = None) -> str:
    """Return a compact user-facing name for a normalized key symbol."""
    normalized_code = normalize_keycode(keycode)
    if normalized_code in KEYCODE_DISPLAY_NAMES:
        return KEYCODE_DISPLAY_NAMES[normalized_code]

    normalized = normalize_hotkey(keysym)
    if normalized is None or normalized.lower().startswith("keycode_"):
        if normalized_code is not None:
            return f"按键 {normalized_code}"
        normalized = DEFAULT_COUNTER_HOTKEY
    lowered = normalized.lower()
    if lowered in HOTKEY_DISPLAY_NAMES:
        return HOTKEY_DISPLAY_NAMES[lowered]
    if len(normalized) == 1:
        return normalized.upper()
    if lowered.startswith("kp_"):
        return "Num " + normalized[3:].replace("_", " ").title()
    return normalized.replace("_", " ").title()


def hotkey_matches_event(
    saved_keysym: str,
    saved_keycode: object,
    event_keysym: str,
    event_keycode: object,
) -> bool:
    """Match by keycode first, with a keysym fallback for legacy settings."""
    expected_code = normalize_keycode(saved_keycode)
    actual_code = normalize_keycode(event_keycode)
    if expected_code is not None and actual_code is not None:
        return expected_code == actual_code

    expected_symbol = normalize_hotkey(saved_keysym)
    actual_symbol = normalize_hotkey(event_keysym)
    return (
        expected_symbol is not None
        and actual_symbol is not None
        and expected_symbol.casefold() == actual_symbol.casefold()
    )


def settings_file_path() -> Path:
    """Return the per-user settings file path without touching the filesystem."""
    app_data = os.environ.get("APPDATA")
    base = Path(app_data) if app_data else Path.home() / ".config"
    return base / "XiaoqiuCalculator" / "settings.json"


def load_counter_hotkey_binding(
    path: Path | None = None,
) -> tuple[str, int | None]:
    """Load a saved keysym/keycode pair and migrate legacy settings safely."""
    target = path or settings_file_path()
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
        normalized = normalize_hotkey(payload.get("counter_hotkey", ""))
        keycode = normalize_keycode(payload.get("counter_hotkey_code"))
    except (OSError, ValueError, AttributeError):
        normalized = None
        keycode = None

    if hotkey_is_reserved(normalized or "", keycode):
        normalized = None
        keycode = None
    if normalized is None and keycode is not None:
        normalized = f"keycode_{keycode}"
    if normalized is None:
        return DEFAULT_COUNTER_HOTKEY, DEFAULT_COUNTER_HOTKEY_CODE
    return normalized, keycode


def load_counter_hotkey(path: Path | None = None) -> str:
    """Load the saved hotkey symbol for callers using the legacy API."""
    return load_counter_hotkey_binding(path)[0]


def save_counter_hotkey(
    keysym: str,
    path: Path | None = None,
    *,
    keycode: object = None,
) -> str:
    """Atomically persist one validated counter hotkey."""
    normalized = normalize_hotkey(keysym)
    normalized_code = normalize_keycode(keycode)
    if hotkey_is_reserved(keysym, normalized_code):
        raise ValueError("该按键不能用作计数快捷键。")
    if normalized is None and normalized_code is not None:
        normalized = f"keycode_{normalized_code}"
    if normalized is None:
        raise ValueError("未能识别该按键，请换一个按键重试。")

    target = path or settings_file_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    payload: dict[str, str | int] = {"counter_hotkey": normalized}
    if normalized_code is not None:
        payload["counter_hotkey_code"] = normalized_code
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)
    return normalized


class CalculatorApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("小秋计算器")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(460, 640)
        self.resizable(True, False)
        self.configure(fg_color=APP_BG)

        self.font_family = self._choose_font_family()
        self._current_page = "calculator"
        self._current_calculation_mode = "standard"
        self.a_value = tk.StringVar()
        self.b_value = tk.StringVar()
        self.divisor_value = tk.StringVar(value=DEFAULT_DIVISOR)
        self.total_result = tk.StringVar(value="—")
        self.divide_result = tk.StringVar(value="—")
        self.divide_formula = tk.StringVar(value=f"B ÷ {DEFAULT_DIVISOR}")
        self.coefficient_value = tk.StringVar(value=DEFAULT_COEFFICIENT)
        self.multiply_value = tk.StringVar()
        self.addend_value = tk.StringVar()
        self.multiply_add_result = tk.StringVar(value="—")
        self.multiply_add_formula = tk.StringVar(
            value=f"{DEFAULT_COEFFICIENT} × — + — ="
        )
        self.basic_fixed_value = tk.StringVar(value=DEFAULT_FIXED_VALUE)
        self.basic_operation_value = tk.StringVar()
        self.basic_operation = "+"
        self.basic_result = tk.StringVar(value="—")
        self.basic_formula = tk.StringVar(value=f"{DEFAULT_FIXED_VALUE} + — =")
        self.counter_value = tk.IntVar(value=0)
        (
            self.counter_hotkey,
            self.counter_hotkey_code,
        ) = load_counter_hotkey_binding()
        self.page_subtitle = tk.StringVar(value="双结果计算")
        self.shortcut_text = tk.StringVar(value=self._shortcut_summary())
        self._page_status: dict[str, tuple[str, str]] = {
            "standard": (
                "输入 A、B，结果会实时更新；可按需修改除数。",
                "neutral",
            ),
            "multiply_add": (
                "系数默认 475；输入完整后结果会实时更新。",
                "neutral",
            ),
            "basic": (
                "固定值默认 475；选择运算符后结果会实时更新。",
                "neutral",
            ),
            "counter": ("按 +1 或已绑定快捷键开始计数。", "neutral"),
        }
        self.status_text = tk.StringVar(value=self._page_status["standard"][0])
        self._invalid_entries: set[ctk.CTkEntry] = set()
        self._focused_entry: ctk.CTkEntry | None = None
        self._capturing_hotkey = False

        self._create_app_icon()
        self._create_fonts()
        self._build_ui()
        self._bind_interactions()
        self._center_window()
        self._apply_windows_titlebar()

    def _choose_font_family(self) -> str:
        families = set(tkfont.families(self))
        for candidate in (
            "Microsoft YaHei UI",
            "Microsoft YaHei",
            "Segoe UI Variable",
            "Segoe UI",
        ):
            if candidate in families:
                return candidate
        return str(tkfont.nametofont("TkDefaultFont").actual("family"))

    def _create_fonts(self) -> None:
        self.title_font = ctk.CTkFont(self.font_family, 20, "bold")
        self.subtitle_font = ctk.CTkFont(self.font_family, 10)
        self.section_font = ctk.CTkFont(self.font_family, 11, "bold")
        self.label_font = ctk.CTkFont(self.font_family, 10, "bold")
        self.body_font = ctk.CTkFont(self.font_family, 10)
        self.caption_font = ctk.CTkFont(self.font_family, 9)
        self.input_font = ctk.CTkFont(self.font_family, 14)
        self.button_font = ctk.CTkFont(self.font_family, 11, "bold")
        self.result_font = ctk.CTkFont(self.font_family, 23, "bold")
        self.result_medium_font = ctk.CTkFont(self.font_family, 18, "bold")
        self.result_compact_font = ctk.CTkFont(self.font_family, 14, "bold")
        self.counter_font = ctk.CTkFont(self.font_family, 54, "bold")
        self.counter_medium_font = ctk.CTkFont(self.font_family, 42, "bold")
        self.counter_compact_font = ctk.CTkFont(self.font_family, 30, "bold")

    def _create_app_icon(self) -> None:
        try:
            self.iconbitmap(default=str(resource_path("app_icon.ico")))
            return
        except tk.TclError:
            pass

        icon = tk.PhotoImage(width=32, height=32)
        orange = ACCENT
        for y in range(4, 28):
            inset = 2 if y in (4, 5, 26, 27) else 1 if y in (6, 25) else 0
            icon.put(orange, to=(4 + inset, y, 28 - inset, y + 1))
        icon.put(ACCENT_TEXT, to=(9, 14, 23, 18))
        icon.put(ACCENT_TEXT, to=(14, 9, 18, 23))
        self.iconphoto(True, icon)
        self._app_icon = icon

    def _apply_windows_titlebar(self) -> None:
        """Match the native Windows title bar to the graphite app palette."""
        if sys.platform != "win32":
            return

        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            if not hwnd:
                hwnd = self.winfo_id()

            def colorref(hex_color: str) -> int:
                red, green, blue = (
                    int(hex_color[index : index + 2], 16) for index in (1, 3, 5)
                )
                return red | (green << 8) | (blue << 16)

            dark_mode = ctypes.c_int(1)
            caption = ctypes.c_int(colorref(APP_BG))
            caption_text = ctypes.c_int(colorref(TEXT))
            border = ctypes.c_int(colorref(BORDER))
            dwm = ctypes.windll.dwmapi.DwmSetWindowAttribute

            dwm(hwnd, 20, ctypes.byref(dark_mode), ctypes.sizeof(dark_mode))
            dwm(hwnd, 35, ctypes.byref(caption), ctypes.sizeof(caption))
            dwm(hwnd, 36, ctypes.byref(caption_text), ctypes.sizeof(caption_text))
            dwm(hwnd, 34, ctypes.byref(border), ctypes.sizeof(border))
        except (AttributeError, OSError):
            pass

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=0, sticky="nsew", padx=24, pady=(22, 18))
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)

        self._build_header(content)
        page_host = ctk.CTkFrame(content, fg_color="transparent")
        page_host.grid(row=1, column=0, sticky="nsew")
        page_host.grid_columnconfigure(0, weight=1)
        page_host.grid_rowconfigure(0, weight=1)

        self.calculator_page = ctk.CTkFrame(page_host, fg_color="transparent")
        self.calculator_page.grid(row=0, column=0, sticky="nsew")
        self.calculator_page.grid_columnconfigure(0, weight=1)
        self.calculator_page.grid_rowconfigure(1, weight=1)
        self._build_calculation_mode_switch(self.calculator_page)

        calculation_host = ctk.CTkFrame(
            self.calculator_page,
            fg_color="transparent",
        )
        calculation_host.grid(row=1, column=0, sticky="nsew")
        calculation_host.grid_columnconfigure(0, weight=1)
        calculation_host.grid_rowconfigure(0, weight=1)

        self.standard_calculator_panel = ctk.CTkFrame(
            calculation_host,
            fg_color="transparent",
        )
        self.standard_calculator_panel.grid(row=0, column=0, sticky="nsew")
        self.standard_calculator_panel.grid_columnconfigure(0, weight=1)
        self._build_input_card(self.standard_calculator_panel)
        self._build_actions(self.standard_calculator_panel)
        self._build_results(self.standard_calculator_panel)

        self.multiply_add_panel = ctk.CTkFrame(
            calculation_host,
            fg_color="transparent",
        )
        self.multiply_add_panel.grid(row=0, column=0, sticky="nsew")
        self.multiply_add_panel.grid_columnconfigure(0, weight=1)
        self._build_multiply_add_panel(self.multiply_add_panel)
        self.standard_calculator_panel.tkraise()

        self.basic_page = ctk.CTkFrame(page_host, fg_color="transparent")
        self.basic_page.grid(row=0, column=0, sticky="nsew")
        self.basic_page.grid_columnconfigure(0, weight=1)
        self._build_basic_arithmetic_page(self.basic_page)

        self.counter_page = ctk.CTkFrame(page_host, fg_color="transparent")
        self.counter_page.grid(row=0, column=0, sticky="nsew")
        self.counter_page.grid_columnconfigure(0, weight=1)
        self._build_counter_page(self.counter_page)

        self.calculator_page.tkraise()
        self._build_status(content)

    def _build_header(self, parent: ctk.CTkFrame) -> None:
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        header.grid_columnconfigure(1, weight=1)

        badge = ctk.CTkFrame(
            header,
            width=44,
            height=44,
            corner_radius=13,
            fg_color=ACCENT_SOFT,
            border_width=1,
            border_color=ACCENT_BORDER,
        )
        badge.grid(row=0, column=0, rowspan=2, sticky="nw", padx=(0, 12))
        badge.grid_propagate(False)
        ctk.CTkLabel(
            badge,
            text="Σ",
            font=ctk.CTkFont(self.font_family, 21, "bold"),
            text_color=ACCENT,
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            header,
            text="小秋计算器",
            font=self.title_font,
            text_color=TEXT,
            anchor="w",
        ).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(
            header,
            textvariable=self.page_subtitle,
            font=self.subtitle_font,
            text_color=MUTED,
            anchor="w",
        ).grid(row=1, column=1, sticky="w", pady=(1, 0))

        navigation = ctk.CTkFrame(
            header,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
            fg_color=SURFACE_ALT,
        )
        navigation.grid(
            row=0,
            column=2,
            rowspan=2,
            sticky="e",
            padx=(10, 0),
        )

        self.calculator_nav_button = ctk.CTkButton(
            navigation,
            text="计算器",
            width=66,
            height=32,
            corner_radius=8,
            border_width=1,
            border_color=ACCENT_BORDER,
            fg_color=ACCENT_SOFT,
            hover_color=ACCENT_BORDER,
            text_color=ACCENT,
            font=self.caption_font,
            command=self.show_calculator_page,
        )
        self.calculator_nav_button.grid(row=0, column=0, padx=3, pady=3)

        self.basic_nav_button = ctk.CTkButton(
            navigation,
            text="基础运算",
            width=76,
            height=32,
            corner_radius=8,
            border_width=0,
            fg_color="transparent",
            hover_color=BORDER,
            text_color=MUTED,
            font=self.caption_font,
            command=self.show_basic_arithmetic_page,
        )
        self.basic_nav_button.grid(row=0, column=1, pady=3)

        self.counter_nav_button = ctk.CTkButton(
            navigation,
            text="快捷计数",
            width=76,
            height=32,
            corner_radius=8,
            border_width=0,
            fg_color="transparent",
            hover_color=BORDER,
            text_color=MUTED,
            font=self.caption_font,
            command=self.show_counter_page,
        )
        self.counter_nav_button.grid(
            row=0,
            column=2,
            padx=(0, 3),
            pady=3,
        )

    def _build_calculation_mode_switch(self, parent: ctk.CTkFrame) -> None:
        mode_row = ctk.CTkFrame(parent, fg_color="transparent")
        mode_row.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        mode_row.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            mode_row,
            text="计算模式",
            font=self.label_font,
            text_color=TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        selector = ctk.CTkFrame(
            mode_row,
            corner_radius=10,
            fg_color=SURFACE_ALT,
            border_width=1,
            border_color=BORDER,
        )
        selector.grid(row=0, column=1, sticky="e")

        self.standard_mode_button = ctk.CTkButton(
            selector,
            text="双结果",
            width=88,
            height=32,
            corner_radius=8,
            border_width=1,
            border_color=ACCENT_BORDER,
            fg_color=ACCENT_SOFT,
            hover_color=ACCENT_BORDER,
            text_color=ACCENT,
            font=self.caption_font,
            command=self.show_standard_mode,
        )
        self.standard_mode_button.grid(row=0, column=0, padx=3, pady=3)

        self.multiply_add_mode_button = ctk.CTkButton(
            selector,
            text="乘加计算",
            width=96,
            height=32,
            corner_radius=8,
            border_width=0,
            fg_color="transparent",
            hover_color=BORDER,
            text_color=MUTED,
            font=self.caption_font,
            command=self.show_multiply_add_mode,
        )
        self.multiply_add_mode_button.grid(
            row=0,
            column=1,
            padx=(0, 3),
            pady=3,
        )

    def _build_input_card(self, parent: ctk.CTkFrame) -> None:
        card = ctk.CTkFrame(
            parent,
            corner_radius=16,
            fg_color=SURFACE,
            border_width=1,
            border_color=BORDER,
        )
        card.grid(row=0, column=0, sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        card_header = ctk.CTkFrame(card, fg_color="transparent")
        card_header.grid(row=0, column=0, sticky="ew", padx=18, pady=(15, 10))
        card_header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            card_header,
            text="输入数据",
            font=self.section_font,
            text_color=TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        divisor_control = ctk.CTkFrame(card_header, fg_color="transparent")
        divisor_control.grid(row=0, column=1, sticky="e")
        ctk.CTkLabel(
            divisor_control,
            text="除数",
            font=self.caption_font,
            text_color=FAINT,
        ).grid(row=0, column=0, padx=(0, 7))
        self.divisor_entry = ctk.CTkEntry(
            divisor_control,
            width=82,
            height=29,
            corner_radius=8,
            border_width=1,
            border_color=BORDER,
            fg_color=SURFACE_ALT,
            text_color=TEXT,
            placeholder_text=DEFAULT_DIVISOR,
            placeholder_text_color=FAINT,
            textvariable=self.divisor_value,
            font=self.body_font,
            justify="center",
            validate="key",
            validatecommand=(self.register(self._validate_input), "%P"),
        )
        self.divisor_entry.grid(row=0, column=1)

        fields = ctk.CTkFrame(card, fg_color="transparent")
        fields.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 17))
        fields.grid_columnconfigure(0, weight=1)
        fields.grid_columnconfigure(1, weight=1)

        self.a_entry = self._add_input_field(
            fields,
            column=0,
            label="A 数据",
            variable=self.a_value,
            placeholder="例如 120.5",
            hint="例：120.5",
            padx=(0, 6),
        )
        self.b_entry = self._add_input_field(
            fields,
            column=1,
            label="B 数据",
            variable=self.b_value,
            placeholder="例如 475",
            hint="例：475",
            padx=(6, 0),
        )

    def _add_input_field(
        self,
        parent: ctk.CTkFrame,
        column: int,
        label: str,
        variable: tk.StringVar,
        placeholder: str,
        hint: str,
        padx: tuple[int, int],
    ) -> ctk.CTkEntry:
        field = ctk.CTkFrame(parent, fg_color="transparent")
        field.grid(row=0, column=column, sticky="ew", padx=padx)
        field.grid_columnconfigure(0, weight=1)

        field_header = ctk.CTkFrame(field, fg_color="transparent")
        field_header.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        field_header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            field_header,
            text=label,
            font=self.label_font,
            text_color=TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            field_header,
            text=hint,
            font=self.caption_font,
            text_color=FAINT,
            anchor="e",
        ).grid(row=0, column=1, sticky="e")

        entry = ctk.CTkEntry(
            field,
            height=44,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
            fg_color=SURFACE_ALT,
            text_color=TEXT,
            placeholder_text=placeholder,
            placeholder_text_color=FAINT,
            textvariable=variable,
            font=self.input_font,
            justify="right",
            validate="key",
            validatecommand=(self.register(self._validate_input), "%P"),
        )
        entry.grid(row=1, column=0, sticky="ew")
        return entry

    def _build_actions(self, parent: ctk.CTkFrame) -> None:
        actions = ctk.CTkFrame(parent, fg_color="transparent")
        actions.grid(row=1, column=0, sticky="ew", pady=(14, 17))
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=2)

        self.clear_button = ctk.CTkButton(
            actions,
            text="清空",
            height=43,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
            fg_color=SURFACE,
            hover_color=SURFACE_ALT,
            text_color=TEXT,
            font=self.body_font,
            command=self.clear,
        )
        self.clear_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self.calculate_button = ctk.CTkButton(
            actions,
            text="计算结果",
            height=43,
            corner_radius=10,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color=ACCENT_TEXT,
            font=self.button_font,
            command=self.calculate,
        )
        self.calculate_button.grid(row=0, column=1, sticky="ew", padx=(5, 0))

    def _build_multiply_add_panel(self, parent: ctk.CTkFrame) -> None:
        card = ctk.CTkFrame(
            parent,
            corner_radius=16,
            fg_color=SURFACE,
            border_width=1,
            border_color=BORDER,
        )
        card.grid(row=0, column=0, sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        card_header = ctk.CTkFrame(card, fg_color="transparent")
        card_header.grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 8))
        card_header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            card_header,
            text="乘加公式",
            font=self.section_font,
            text_color=TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        coefficient_control = ctk.CTkFrame(
            card_header,
            height=36,
            corner_radius=9,
            fg_color=SURFACE_ALT,
            border_width=1,
            border_color=BORDER,
        )
        coefficient_control.grid(row=0, column=1, sticky="e")
        ctk.CTkLabel(
            coefficient_control,
            text="系数",
            text_color=MUTED,
            font=self.caption_font,
        ).grid(row=0, column=0, padx=(10, 6), pady=3)
        self.coefficient_entry = ctk.CTkEntry(
            coefficient_control,
            width=88,
            height=30,
            corner_radius=7,
            border_width=1,
            border_color=BORDER,
            fg_color=SURFACE,
            text_color=TEXT,
            placeholder_text=DEFAULT_COEFFICIENT,
            placeholder_text_color=FAINT,
            textvariable=self.coefficient_value,
            font=self.body_font,
            justify="center",
            validate="key",
            validatecommand=(self.register(self._validate_input), "%P"),
        )
        self.coefficient_entry.grid(row=0, column=1, padx=(0, 3), pady=3)

        formula_strip = ctk.CTkFrame(
            card,
            height=38,
            corner_radius=9,
            fg_color=SURFACE_ALT,
        )
        formula_strip.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 10))
        formula_strip.grid_propagate(False)
        ctk.CTkLabel(
            formula_strip,
            textvariable=self.multiply_add_formula,
            font=self.body_font,
            text_color=MUTED,
        ).place(relx=0.5, rely=0.5, anchor="center")

        fields = ctk.CTkFrame(card, fg_color="transparent")
        fields.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 16))
        fields.grid_columnconfigure(0, weight=1)
        fields.grid_columnconfigure(1, weight=1)
        self.multiply_entry = self._add_input_field(
            fields,
            column=0,
            label="乘数",
            variable=self.multiply_value,
            placeholder="例如 2",
            hint="系数要乘的数",
            padx=(0, 6),
        )
        self.addend_entry = self._add_input_field(
            fields,
            column=1,
            label="加数",
            variable=self.addend_value,
            placeholder="例如 25",
            hint="最后加上的数",
            padx=(6, 0),
        )

        actions = ctk.CTkFrame(parent, fg_color="transparent")
        actions.grid(row=1, column=0, sticky="ew", pady=(14, 17))
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=2)
        self.multiply_add_clear_button = ctk.CTkButton(
            actions,
            text="清空",
            height=43,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
            fg_color=SURFACE,
            hover_color=SURFACE_ALT,
            text_color=TEXT,
            font=self.body_font,
            command=self.clear_multiply_add,
        )
        self.multiply_add_clear_button.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 5),
        )
        self.multiply_add_calculate_button = ctk.CTkButton(
            actions,
            text="计算等于",
            height=43,
            corner_radius=10,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color=ACCENT_TEXT,
            font=self.button_font,
            command=self.calculate_multiply_add,
        )
        self.multiply_add_calculate_button.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(5, 0),
        )

        result_header = ctk.CTkFrame(parent, fg_color="transparent")
        result_header.grid(row=2, column=0, sticky="ew", pady=(0, 7))
        result_header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            result_header,
            text="计算结果",
            font=self.section_font,
            text_color=TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            result_header,
            text="实时更新 · 最多 2 位",
            font=self.caption_font,
            text_color=FAINT,
            anchor="e",
        ).grid(row=0, column=1, sticky="e")

        (
            self.multiply_add_result_card,
            self.multiply_add_result_label,
        ) = self._add_result_card(
            parent,
            row=3,
            title="等于",
            formula=self.multiply_add_formula,
            variable=self.multiply_add_result,
            featured=True,
        )

    def _build_basic_arithmetic_page(self, parent: ctk.CTkFrame) -> None:
        intro = ctk.CTkFrame(parent, fg_color="transparent")
        intro.grid(row=0, column=0, sticky="ew", pady=(1, 12))
        intro.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            intro,
            text="固定值基础运算",
            font=self.section_font,
            text_color=TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            intro,
            text="每次只选择一个运算符",
            font=self.caption_font,
            text_color=FAINT,
            anchor="e",
        ).grid(row=0, column=1, sticky="e")

        card = ctk.CTkFrame(
            parent,
            corner_radius=16,
            fg_color=SURFACE,
            border_width=1,
            border_color=BORDER,
        )
        card.grid(row=1, column=0, sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        formula_strip = ctk.CTkFrame(
            card,
            height=42,
            corner_radius=9,
            fg_color=SURFACE_ALT,
        )
        formula_strip.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 12))
        formula_strip.grid_propagate(False)
        ctk.CTkLabel(
            formula_strip,
            textvariable=self.basic_formula,
            font=self.body_font,
            text_color=MUTED,
        ).place(relx=0.5, rely=0.5, anchor="center")

        fields = ctk.CTkFrame(card, fg_color="transparent")
        fields.grid(row=1, column=0, sticky="ew", padx=18)
        fields.grid_columnconfigure(0, weight=1)
        fields.grid_columnconfigure(1, weight=1)
        self.basic_fixed_entry = self._add_input_field(
            fields,
            column=0,
            label="固定值",
            variable=self.basic_fixed_value,
            placeholder=DEFAULT_FIXED_VALUE,
            hint="默认 475，可修改",
            padx=(0, 6),
        )
        self.basic_value_entry = self._add_input_field(
            fields,
            column=1,
            label="运算值",
            variable=self.basic_operation_value,
            placeholder="例如 25",
            hint="参与本次运算",
            padx=(6, 0),
        )

        operation_header = ctk.CTkFrame(card, fg_color="transparent")
        operation_header.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=18,
            pady=(15, 7),
        )
        operation_header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            operation_header,
            text="选择运算",
            font=self.label_font,
            text_color=TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            operation_header,
            text="加 / 减 / 乘 / 除四选一",
            font=self.caption_font,
            text_color=FAINT,
            anchor="e",
        ).grid(row=0, column=1, sticky="e")

        operation_selector = ctk.CTkFrame(
            card,
            corner_radius=10,
            fg_color=SURFACE_ALT,
            border_width=1,
            border_color=BORDER,
        )
        operation_selector.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=18,
            pady=(0, 16),
        )
        for column in range(4):
            operation_selector.grid_columnconfigure(column, weight=1)

        self.basic_operation_buttons: dict[str, ctk.CTkButton] = {}
        operation_labels = {
            "+": "＋",
            "-": "－",
            "×": "×",
            "÷": "÷",
        }
        for column, (operation, label) in enumerate(operation_labels.items()):
            active = operation == self.basic_operation
            button = ctk.CTkButton(
                operation_selector,
                text=label,
                width=70,
                height=38,
                corner_radius=8,
                border_width=1 if active else 0,
                border_color=ACCENT_BORDER,
                fg_color=ACCENT_SOFT if active else "transparent",
                hover_color=ACCENT_BORDER if active else BORDER,
                text_color=ACCENT if active else MUTED,
                font=self.button_font,
                command=lambda value=operation: self.select_basic_operation(value),
            )
            button.grid(
                row=0,
                column=column,
                sticky="ew",
                padx=(3 if column == 0 else 1, 3 if column == 3 else 1),
                pady=3,
            )
            self.basic_operation_buttons[operation] = button

        actions = ctk.CTkFrame(parent, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", pady=(14, 17))
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=2)
        self.basic_clear_button = ctk.CTkButton(
            actions,
            text="清空",
            height=43,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
            fg_color=SURFACE,
            hover_color=SURFACE_ALT,
            text_color=TEXT,
            font=self.body_font,
            command=self.clear_basic_arithmetic,
        )
        self.basic_clear_button.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 5),
        )
        self.basic_calculate_button = ctk.CTkButton(
            actions,
            text="计算结果",
            height=43,
            corner_radius=10,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color=ACCENT_TEXT,
            font=self.button_font,
            command=self.calculate_basic_arithmetic,
        )
        self.basic_calculate_button.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(5, 0),
        )

        result_header = ctk.CTkFrame(parent, fg_color="transparent")
        result_header.grid(row=3, column=0, sticky="ew", pady=(0, 7))
        result_header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            result_header,
            text="计算结果",
            font=self.section_font,
            text_color=TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            result_header,
            text="实时更新 · 最多 2 位",
            font=self.caption_font,
            text_color=FAINT,
            anchor="e",
        ).grid(row=0, column=1, sticky="e")

        (
            self.basic_result_card,
            self.basic_result_label,
        ) = self._add_result_card(
            parent,
            row=4,
            title="等于",
            formula=self.basic_formula,
            variable=self.basic_result,
            featured=True,
        )

    def _build_counter_page(self, parent: ctk.CTkFrame) -> None:
        intro = ctk.CTkFrame(parent, fg_color="transparent")
        intro.grid(row=0, column=0, sticky="ew", pady=(1, 12))
        intro.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            intro,
            text="快捷计数",
            font=self.section_font,
            text_color=TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            intro,
            text="每按一次快捷键，计数增加 1",
            font=self.caption_font,
            text_color=FAINT,
            anchor="e",
        ).grid(row=0, column=1, sticky="e")

        counter = ctk.CTkFrame(
            parent,
            height=220,
            corner_radius=16,
            fg_color=SURFACE,
            border_width=1,
            border_color=ACCENT_BORDER,
        )
        counter.grid(row=1, column=0, sticky="ew")
        counter.grid_columnconfigure(0, weight=1)
        counter.grid_propagate(False)

        ctk.CTkLabel(
            counter,
            text="当前计数",
            font=self.caption_font,
            text_color=FAINT,
        ).grid(row=0, column=0, pady=(22, 0))

        self.counter_value_label = ctk.CTkLabel(
            counter,
            textvariable=self.counter_value,
            font=self.counter_font,
            text_color=ACCENT,
            anchor="center",
        )
        self.counter_value_label.grid(row=1, column=0, sticky="ew", pady=(3, 10))

        counter_actions = ctk.CTkFrame(counter, fg_color="transparent")
        counter_actions.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 22))
        counter_actions.grid_columnconfigure(0, weight=1)
        counter_actions.grid_columnconfigure(1, weight=2)

        self.counter_reset_button = ctk.CTkButton(
            counter_actions,
            text="清零",
            height=48,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
            fg_color=SURFACE_ALT,
            hover_color=BORDER,
            text_color=TEXT,
            font=self.body_font,
            command=self.reset_counter,
        )
        self.counter_reset_button.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 6),
        )

        self.counter_increment_button = ctk.CTkButton(
            counter_actions,
            text="计数 +1",
            height=48,
            corner_radius=10,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color=ACCENT_TEXT,
            font=self.button_font,
            command=self.increment_counter,
        )
        self.counter_increment_button.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(6, 0),
        )

        hotkey_card = ctk.CTkFrame(
            parent,
            height=76,
            corner_radius=14,
            fg_color=SURFACE,
            border_width=1,
            border_color=BORDER,
        )
        hotkey_card.grid(row=2, column=0, sticky="ew", pady=(14, 0))
        hotkey_card.grid_columnconfigure(0, weight=1)
        hotkey_card.grid_propagate(False)

        hotkey_description = ctk.CTkFrame(
            hotkey_card,
            fg_color="transparent",
        )
        hotkey_description.grid(row=0, column=0, sticky="w", padx=(18, 8))
        ctk.CTkLabel(
            hotkey_description,
            text="计数快捷键",
            font=self.label_font,
            text_color=TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            hotkey_description,
            text="点击右侧按钮后，按下目标键",
            font=self.caption_font,
            text_color=FAINT,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(3, 0))

        self.hotkey_button = ctk.CTkButton(
            hotkey_card,
            text=self._hotkey_button_text(),
            width=154,
            height=40,
            corner_radius=9,
            border_width=1,
            border_color=BORDER,
            fg_color=SURFACE_ALT,
            hover_color=BORDER,
            font=self.caption_font,
            text_color=MUTED,
            command=self.start_hotkey_capture,
        )
        self.hotkey_button.grid(
            row=0,
            column=1,
            sticky="e",
            padx=(8, 18),
        )

    def _build_results(self, parent: ctk.CTkFrame) -> None:
        section_header = ctk.CTkFrame(parent, fg_color="transparent")
        section_header.grid(row=2, column=0, sticky="ew", pady=(0, 7))
        section_header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            section_header,
            text="计算结果",
            font=self.section_font,
            text_color=TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            section_header,
            text="实时更新 · 最多 2 位",
            font=self.caption_font,
            text_color=FAINT,
            anchor="e",
        ).grid(row=0, column=1, sticky="e")

        results = ctk.CTkFrame(parent, fg_color="transparent")
        results.grid(row=3, column=0, sticky="ew")
        results.grid_columnconfigure(0, weight=1)

        self.total_card, self.total_value_label = self._add_result_card(
            results,
            row=0,
            title="总数",
            formula="A + B",
            variable=self.total_result,
            featured=True,
        )
        self.divide_card, self.divide_value_label = self._add_result_card(
            results,
            row=1,
            title="单列结果",
            formula=self.divide_formula,
            variable=self.divide_result,
            featured=False,
        )

    def _add_result_card(
        self,
        parent: ctk.CTkFrame,
        row: int,
        title: str,
        formula: str | tk.StringVar,
        variable: tk.StringVar,
        featured: bool,
    ) -> tuple[ctk.CTkFrame, ctk.CTkLabel]:
        card = ctk.CTkFrame(
            parent,
            height=71,
            corner_radius=14,
            fg_color=SURFACE,
            border_width=1,
            border_color=ACCENT_BORDER if featured else BORDER,
        )
        card.grid(row=row, column=0, sticky="ew", pady=(0, 7 if row == 0 else 0))
        card.grid_propagate(False)

        if featured:
            accent_rail = ctk.CTkFrame(
                card,
                width=4,
                height=47,
                corner_radius=2,
                fg_color=ACCENT,
            )
            accent_rail.grid(
                row=0,
                column=0,
                rowspan=2,
                sticky="ns",
                padx=(12, 0),
                pady=12,
            )
            text_column = 1
            value_column = 2
            text_padx = (12, 0)
        else:
            text_column = 0
            value_column = 1
            text_padx = (16, 0)

        card.grid_columnconfigure(text_column, weight=1)

        ctk.CTkLabel(
            card,
            text=title,
            font=self.label_font,
            text_color=TEXT,
            anchor="w",
        ).grid(
            row=0,
            column=text_column,
            sticky="sw",
            padx=text_padx,
            pady=(10, 0),
        )
        formula_options: dict[str, object]
        if isinstance(formula, tk.StringVar):
            formula_options = {"textvariable": formula}
        else:
            formula_options = {"text": formula}

        ctk.CTkLabel(
            card,
            font=self.caption_font,
            text_color=MUTED,
            anchor="w",
            **formula_options,
        ).grid(
            row=1,
            column=text_column,
            sticky="nw",
            padx=text_padx,
            pady=(0, 10),
        )

        value_label = ctk.CTkLabel(
            card,
            textvariable=variable,
            font=self.result_font,
            text_color=FAINT,
            anchor="e",
        )
        value_label.grid(
            row=0,
            column=value_column,
            rowspan=2,
            sticky="e",
            padx=(18, 16),
        )
        return card, value_label

    def _build_status(self, parent: ctk.CTkFrame) -> None:
        self.status_frame = ctk.CTkFrame(
            parent,
            height=34,
            corner_radius=10,
            fg_color=SURFACE_ALT,
        )
        self.status_frame.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        self.status_frame.grid_columnconfigure(1, weight=1)
        self.status_frame.grid_propagate(False)

        self.status_dot = ctk.CTkLabel(
            self.status_frame,
            text="●",
            width=22,
            font=ctk.CTkFont(self.font_family, 8),
            text_color=MUTED,
        )
        self.status_dot.grid(row=0, column=0, padx=(8, 0))
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            textvariable=self.status_text,
            font=self.caption_font,
            text_color=MUTED,
            anchor="w",
        )
        self.status_label.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        ctk.CTkLabel(
            parent,
            textvariable=self.shortcut_text,
            font=self.caption_font,
            text_color=FAINT,
            anchor="e",
        ).grid(row=3, column=0, sticky="e", pady=(6, 0))

    def _bind_interactions(self) -> None:
        self.a_value.trace_add("write", self._on_input_change)
        self.b_value.trace_add("write", self._on_input_change)
        self.divisor_value.trace_add("write", self._on_input_change)
        self.coefficient_value.trace_add(
            "write",
            self._on_multiply_add_input_change,
        )
        self.multiply_value.trace_add("write", self._on_multiply_add_input_change)
        self.addend_value.trace_add("write", self._on_multiply_add_input_change)
        self.basic_fixed_value.trace_add("write", self._on_basic_input_change)
        self.basic_operation_value.trace_add("write", self._on_basic_input_change)
        self.bind("<KeyPress>", self._handle_keypress)

        for entry in (
            self.a_entry,
            self.b_entry,
            self.divisor_entry,
            self.coefficient_entry,
            self.multiply_entry,
            self.addend_entry,
            self.basic_fixed_entry,
            self.basic_value_entry,
        ):
            entry.bind("<FocusIn>", lambda _event, item=entry: self._focus_entry(item))
            entry.bind("<FocusOut>", lambda _event, item=entry: self._blur_entry(item))

        self.a_entry.bind("<Tab>", self._focus_b_from_keyboard)
        self.a_entry.bind(
            "<Shift-Tab>",
            lambda _event: self._focus_widget(self.multiply_add_mode_button),
        )
        self.b_entry.bind("<Tab>", self._focus_divisor_from_keyboard)
        self.b_entry.bind("<Shift-Tab>", self._focus_a_from_keyboard)
        self.divisor_entry.bind("<Tab>", self._focus_navigation_from_keyboard)
        self.divisor_entry.bind("<Shift-Tab>", self._focus_b_from_keyboard)

        self.coefficient_entry.bind(
            "<Tab>",
            lambda _event: self._focus_widget(self.multiply_entry),
        )
        self.coefficient_entry.bind(
            "<Shift-Tab>",
            lambda _event: self._focus_widget(self.multiply_add_mode_button),
        )
        self.multiply_entry.bind(
            "<Tab>",
            lambda _event: self._focus_widget(self.addend_entry),
        )
        self.multiply_entry.bind(
            "<Shift-Tab>",
            lambda _event: self._focus_widget(self.coefficient_entry),
        )
        self.addend_entry.bind("<Tab>", self._focus_navigation_from_keyboard)
        self.addend_entry.bind(
            "<Shift-Tab>",
            lambda _event: self._focus_widget(self.multiply_entry),
        )

        self.standard_mode_button.bind(
            "<Tab>",
            lambda _event: self._focus_widget(self.multiply_add_mode_button),
        )
        self.standard_mode_button.bind(
            "<Shift-Tab>",
            lambda _event: self._focus_widget(self.counter_nav_button),
        )
        self.multiply_add_mode_button.bind(
            "<Tab>",
            self._focus_active_calculation_start,
        )
        self.multiply_add_mode_button.bind(
            "<Shift-Tab>",
            lambda _event: self._focus_widget(self.standard_mode_button),
        )

        self.calculator_nav_button.bind(
            "<Tab>",
            lambda _event: self._focus_widget(self.basic_nav_button),
        )
        self.calculator_nav_button.bind(
            "<Shift-Tab>",
            self._focus_page_end_from_keyboard,
        )
        self.basic_nav_button.bind(
            "<Tab>",
            lambda _event: self._focus_widget(self.counter_nav_button),
        )
        self.basic_nav_button.bind(
            "<Shift-Tab>",
            lambda _event: self._focus_widget(self.calculator_nav_button),
        )
        self.counter_nav_button.bind(
            "<Tab>",
            self._focus_page_start_from_keyboard,
        )
        self.counter_nav_button.bind(
            "<Shift-Tab>",
            lambda _event: self._focus_widget(self.basic_nav_button),
        )

        self.basic_fixed_entry.bind(
            "<Tab>",
            lambda _event: self._focus_widget(self.basic_value_entry),
        )
        self.basic_fixed_entry.bind(
            "<Shift-Tab>",
            lambda _event: self._focus_widget(self.counter_nav_button),
        )
        self.basic_value_entry.bind(
            "<Tab>",
            lambda _event: self._focus_widget(self.basic_operation_buttons["+"]),
        )
        self.basic_value_entry.bind(
            "<Shift-Tab>",
            lambda _event: self._focus_widget(self.basic_fixed_entry),
        )

        operation_order = ("+", "-", "×", "÷")
        for index, operation in enumerate(operation_order):
            button = self.basic_operation_buttons[operation]
            if index == len(operation_order) - 1:
                button.bind("<Tab>", self._focus_navigation_from_keyboard)
            else:
                next_button = self.basic_operation_buttons[operation_order[index + 1]]
                button.bind(
                    "<Tab>",
                    lambda _event, target=next_button: self._focus_widget(target),
                )
            if index == 0:
                button.bind(
                    "<Shift-Tab>",
                    lambda _event: self._focus_widget(self.basic_value_entry),
                )
            else:
                previous_button = self.basic_operation_buttons[
                    operation_order[index - 1]
                ]
                button.bind(
                    "<Shift-Tab>",
                    lambda _event, target=previous_button: self._focus_widget(target),
                )

        self.counter_reset_button.bind(
            "<Tab>",
            lambda _event: self._focus_widget(self.counter_increment_button),
        )
        self.counter_reset_button.bind(
            "<Shift-Tab>",
            lambda _event: self._focus_widget(self.counter_nav_button),
        )
        self.counter_increment_button.bind(
            "<Tab>",
            lambda _event: self._focus_widget(self.hotkey_button),
        )
        self.counter_increment_button.bind(
            "<Shift-Tab>",
            lambda _event: self._focus_widget(self.counter_reset_button),
        )
        self.hotkey_button.bind("<Tab>", self._focus_navigation_from_keyboard)
        self.hotkey_button.bind(
            "<Shift-Tab>",
            lambda _event: self._focus_widget(self.counter_increment_button),
        )

        self.a_entry.focus_set()

    def show_standard_mode(self) -> None:
        self._current_calculation_mode = "standard"
        self.standard_calculator_panel.tkraise()
        self._style_calculation_mode_buttons()
        if self._current_page == "calculator":
            self.page_subtitle.set("双结果计算")
            self._restore_page_status()
            self.a_entry.focus_set()

    def show_multiply_add_mode(self) -> None:
        self._current_calculation_mode = "multiply_add"
        self.multiply_add_panel.tkraise()
        self._style_calculation_mode_buttons()
        if self._current_page == "calculator":
            self.page_subtitle.set("自定义系数乘加")
            self._restore_page_status()
            self.coefficient_entry.focus_set()

    def _style_calculation_mode_buttons(self) -> None:
        active_options = {
            "border_width": 1,
            "border_color": ACCENT_BORDER,
            "fg_color": ACCENT_SOFT,
            "text_color": ACCENT,
        }
        inactive_options = {
            "border_width": 0,
            "fg_color": "transparent",
            "text_color": MUTED,
        }
        standard_options = (
            active_options
            if self._current_calculation_mode == "standard"
            else inactive_options
        )
        multiply_options = (
            active_options
            if self._current_calculation_mode == "multiply_add"
            else inactive_options
        )
        self.standard_mode_button.configure(**standard_options)
        self.multiply_add_mode_button.configure(**multiply_options)

    def _style_page_navigation(self) -> None:
        active_options = {
            "border_width": 1,
            "border_color": ACCENT_BORDER,
            "fg_color": ACCENT_SOFT,
            "hover_color": ACCENT_BORDER,
            "text_color": ACCENT,
        }
        inactive_options = {
            "border_width": 0,
            "fg_color": "transparent",
            "hover_color": BORDER,
            "text_color": MUTED,
        }
        page_buttons = {
            "calculator": self.calculator_nav_button,
            "basic": self.basic_nav_button,
            "counter": self.counter_nav_button,
        }
        for page, button in page_buttons.items():
            button.configure(
                **(active_options if page == self._current_page else inactive_options)
            )

    def show_calculator_page(self) -> None:
        if self._capturing_hotkey:
            self.cancel_hotkey_capture()
        self._current_page = "calculator"
        self.calculator_page.tkraise()
        if self._current_calculation_mode == "multiply_add":
            self.multiply_add_panel.tkraise()
            self.page_subtitle.set("自定义系数乘加")
        else:
            self.standard_calculator_panel.tkraise()
            self.page_subtitle.set("双结果计算")
        self._style_page_navigation()
        self.shortcut_text.set(self._shortcut_summary())
        self._restore_page_status()
        self._focus_active_calculation_entry()

    def show_basic_arithmetic_page(self) -> None:
        if self._capturing_hotkey:
            self.cancel_hotkey_capture()
        self._current_page = "basic"
        self.basic_page.tkraise()
        self.page_subtitle.set("固定值基础运算")
        self._style_page_navigation()
        self.shortcut_text.set(self._shortcut_summary())
        self._restore_page_status()
        self.basic_fixed_entry.focus_set()

    def show_counter_page(self) -> None:
        self._current_page = "counter"
        self.counter_page.tkraise()
        self.page_subtitle.set("独立快捷计数")
        self._style_page_navigation()
        self.shortcut_text.set(self._shortcut_summary())
        self._restore_page_status()
        self.counter_increment_button.focus_set()

    def _handle_keypress(self, event: tk.Event) -> str | None:
        keysym = str(event.keysym)
        keycode = normalize_keycode(event.keycode)
        lowered = keysym.lower()

        if self._capturing_hotkey:
            if lowered == "escape" or keycode == 27:
                self.cancel_hotkey_capture()
                return "break"
            if hotkey_is_reserved(keysym, keycode):
                self._show_invalid_hotkey_prompt()
                return "break"

            normalized = normalize_hotkey(keysym)
            if normalized is None and keycode is not None:
                normalized = f"keycode_{keycode}"
            if normalized is None:
                self._show_invalid_hotkey_prompt()
                return "break"
            self._apply_counter_hotkey(normalized, keycode)
            return "break"

        if lowered in {"return", "kp_enter"}:
            if self._focus_is_within(self.calculator_nav_button):
                self.show_calculator_page()
                return "break"
            if self._focus_is_within(self.basic_nav_button):
                self.show_basic_arithmetic_page()
                return "break"
            if self._focus_is_within(self.counter_nav_button):
                self.show_counter_page()
                return "break"

        if self._current_page == "calculator":
            if lowered in {"return", "kp_enter"}:
                if self._focus_is_within(self.standard_mode_button):
                    self.show_standard_mode()
                elif self._focus_is_within(self.multiply_add_mode_button):
                    self.show_multiply_add_mode()
                else:
                    self.calculate()
                return "break"
            if lowered == "escape":
                self.clear()
                return "break"
            return None

        if self._current_page == "basic":
            focused_operation = self._focused_basic_operation()
            if lowered in {"left", "right"} and focused_operation is not None:
                self._move_basic_operation(focused_operation, lowered)
                return "break"
            if lowered in {"return", "kp_enter"}:
                if focused_operation is not None:
                    self.select_basic_operation(focused_operation)
                else:
                    self.calculate_basic_arithmetic()
                return "break"
            if lowered == "escape":
                self.clear_basic_arithmetic()
                return "break"
            return None

        if lowered == "escape":
            self.show_calculator_page()
            return "break"

        if lowered in {"return", "kp_enter"}:
            if self._focus_is_within(self.counter_reset_button):
                self.reset_counter()
            elif self._focus_is_within(self.hotkey_button):
                self.start_hotkey_capture()
            else:
                self.increment_counter()
            return "break"

        if (
            hotkey_matches_event(
                self.counter_hotkey,
                self.counter_hotkey_code,
                keysym,
                keycode,
            )
            and not self._focus_is_text_input()
        ):
            self.increment_counter()
            return "break"
        return None

    def _focus_is_text_input(self) -> bool:
        focused = self.focus_get()
        return focused is not None and focused.winfo_class() in {
            "Entry",
            "Text",
            "TEntry",
        }

    def _focus_is_within(self, widget: tk.Misc) -> bool:
        focused = self.focus_get()
        while focused is not None:
            if focused is widget:
                return True
            focused = getattr(focused, "master", None)
        return False

    def _focused_basic_operation(self) -> str | None:
        for operation, button in self.basic_operation_buttons.items():
            if self._focus_is_within(button):
                return operation
        return None

    def _move_basic_operation(self, current: str, direction: str) -> None:
        operation_order = ("+", "-", "×", "÷")
        current_index = operation_order.index(current)
        offset = -1 if direction == "left" else 1
        next_operation = operation_order[
            (current_index + offset) % len(operation_order)
        ]
        self.select_basic_operation(next_operation)
        self.basic_operation_buttons[next_operation].focus_set()

    def _hotkey_button_text(self) -> str:
        display = hotkey_display_name(
            self.counter_hotkey,
            self.counter_hotkey_code,
        )
        return f"快捷键：{display}"

    def _shortcut_summary(self) -> str:
        display = hotkey_display_name(
            self.counter_hotkey,
            self.counter_hotkey_code,
        )
        if self._current_page == "counter":
            return f"{display} +1   ·   Esc 返回计算器"
        return "Enter 计算   ·   Esc 清空"

    def start_hotkey_capture(self) -> None:
        self._capturing_hotkey = True
        self.hotkey_button.configure(
            text="请按一个键（Esc 取消）",
            border_color=ACCENT_BORDER,
            fg_color=ACCENT_SOFT,
            text_color=ACCENT,
        )
        self.hotkey_button.focus_set()

    def cancel_hotkey_capture(self) -> None:
        self._capturing_hotkey = False
        self._restore_hotkey_button()
        self.hotkey_button.focus_set()

    def _show_invalid_hotkey_prompt(self) -> None:
        self.hotkey_button.configure(text="此键用于系统操作，请换一个")
        self.after(1200, self._restore_capture_prompt)

    def _restore_capture_prompt(self) -> None:
        if self._capturing_hotkey:
            self.hotkey_button.configure(text="请按一个键（Esc 取消）")

    def _apply_counter_hotkey(
        self,
        keysym: str,
        keycode: int | None,
    ) -> None:
        self.counter_hotkey = keysym
        self.counter_hotkey_code = keycode
        self._capturing_hotkey = False
        self.shortcut_text.set(self._shortcut_summary())
        self._restore_hotkey_button()

        display = hotkey_display_name(keysym, keycode)
        try:
            save_counter_hotkey(keysym, keycode=keycode)
        except (OSError, ValueError):
            self._set_status(
                f"快捷键 {display} 已生效，但无法保存到本机。",
                tone="error",
            )
        else:
            self._set_status(
                f"计数快捷键已设置为 {display}，并已自动保存。",
                tone="success",
            )
        self.counter_increment_button.focus_set()

    def _restore_hotkey_button(self) -> None:
        self.hotkey_button.configure(
            text=self._hotkey_button_text(),
            border_color=BORDER,
            fg_color=SURFACE_ALT,
            text_color=FAINT,
        )

    def increment_counter(self) -> None:
        value = increment_counter_value(self.counter_value.get())
        self.counter_value.set(value)
        self._style_counter_label(value)
        self.counter_increment_button.focus_set()

    def reset_counter(self) -> None:
        self.counter_value.set(0)
        self._style_counter_label(0)
        self._set_status("计数器已清零，可以重新开始计数。", tone="neutral")
        self.counter_reset_button.focus_set()

    def _style_counter_label(self, value: int) -> None:
        length = len(str(value))
        if length <= 6:
            font = self.counter_font
        elif length <= 10:
            font = self.counter_medium_font
        else:
            font = self.counter_compact_font
        self.counter_value_label.configure(font=font)

    def _validate_input(self, proposed: str) -> bool:
        return (
            len(proposed) <= MAX_INPUT_LENGTH
            and (proposed == "" or EDITING_PATTERN.fullmatch(proposed) is not None)
        )

    def _focus_b_from_keyboard(self, _event: tk.Event) -> str:
        self.b_entry.focus_set()
        return "break"

    def _focus_a_from_keyboard(self, _event: tk.Event) -> str:
        self.a_entry.focus_set()
        return "break"

    def _focus_divisor_from_keyboard(self, _event: tk.Event) -> str:
        self.divisor_entry.focus_set()
        return "break"

    def _focus_navigation_from_keyboard(self, _event: tk.Event) -> str:
        return self._focus_widget(self.calculator_nav_button)

    def _focus_page_start_from_keyboard(self, _event: tk.Event) -> str:
        if self._current_page == "calculator":
            return self._focus_widget(self.standard_mode_button)
        if self._current_page == "basic":
            return self._focus_widget(self.basic_fixed_entry)
        return self._focus_widget(self.counter_reset_button)

    def _focus_page_end_from_keyboard(self, _event: tk.Event) -> str:
        if self._current_page == "calculator":
            if self._current_calculation_mode == "multiply_add":
                return self._focus_widget(self.addend_entry)
            return self._focus_widget(self.divisor_entry)
        if self._current_page == "basic":
            return self._focus_widget(self.basic_operation_buttons["÷"])
        return self._focus_widget(self.hotkey_button)

    def _focus_active_calculation_start(self, _event: tk.Event) -> str:
        self._focus_active_calculation_entry()
        return "break"

    def _focus_active_calculation_entry(self) -> None:
        if self._current_calculation_mode == "multiply_add":
            self.coefficient_entry.focus_set()
        else:
            self.a_entry.focus_set()

    @staticmethod
    def _focus_widget(widget: tk.Misc) -> str:
        widget.focus_set()
        return "break"

    def _focus_entry(self, entry: ctk.CTkEntry) -> None:
        self._focused_entry = entry
        if entry not in self._invalid_entries:
            entry.configure(border_color=ACCENT, border_width=2)

    def _blur_entry(self, entry: ctk.CTkEntry) -> None:
        if self._focused_entry is entry:
            self._focused_entry = None
        if entry not in self._invalid_entries:
            entry.configure(border_color=BORDER, border_width=1)

    def _reset_entries(self) -> None:
        self._invalid_entries.clear()
        for entry in (
            self.a_entry,
            self.b_entry,
            self.divisor_entry,
            self.coefficient_entry,
            self.multiply_entry,
            self.addend_entry,
            self.basic_fixed_entry,
            self.basic_value_entry,
        ):
            if entry is self._focused_entry:
                entry.configure(border_color=ACCENT, border_width=2)
            else:
                entry.configure(border_color=BORDER, border_width=1)

    def _on_input_change(self, *_args: object) -> None:
        self._reset_entries()
        divisor_text = self.divisor_value.get().strip()
        self.divide_formula.set(f"B ÷ {divisor_text or '—'}")
        self.total_result.set("—")
        self.divide_result.set("—")
        self._reset_result_labels()
        self._set_status_for(
            "standard",
            "输入 A、B，结果会实时更新；可按需修改除数。",
            tone="neutral",
        )
        try:
            total, divided = calculate_values(
                self.a_value.get(),
                self.b_value.get(),
                self.divisor_value.get(),
            )
        except InputValidationError:
            return
        except CalculationRangeError as exc:
            self._set_status_for("standard", str(exc), tone="error")
            return

        self.total_result.set(total)
        self.divide_result.set(divided)
        self._style_result_label(self.total_value_label, total, ACCENT)
        self._style_result_label(self.divide_value_label, divided, TEXT)
        self._set_status_for(
            "standard",
            f"结果已实时更新；当前除数为 {divisor_text}。",
            tone="success",
        )

    def _on_multiply_add_input_change(self, *_args: object) -> None:
        self._reset_entries()
        coefficient = self._formula_preview_value(self.coefficient_value.get())
        multiplier = self._formula_preview_value(self.multiply_value.get())
        addend = self._formula_preview_value(self.addend_value.get())
        self.multiply_add_formula.set(
            f"{coefficient} × {multiplier} + {addend} ="
        )
        self.multiply_add_result.set("—")
        self.multiply_add_result_label.configure(
            text_color=FAINT,
            font=self.result_font,
        )
        self._set_status_for(
            "multiply_add",
            "系数默认 475；输入完整后结果会实时更新。",
            tone="neutral",
        )
        try:
            result = calculate_multiply_add_value(
                self.coefficient_value.get(),
                self.multiply_value.get(),
                self.addend_value.get(),
            )
        except InputValidationError:
            return
        except CalculationRangeError as exc:
            self._set_status_for("multiply_add", str(exc), tone="error")
            return

        self.multiply_add_result.set(result)
        self._style_result_label(self.multiply_add_result_label, result, ACCENT)
        self._set_status_for(
            "multiply_add",
            "乘加结果已实时更新。",
            tone="success",
        )

    def _on_basic_input_change(self, *_args: object) -> None:
        self._reset_entries()
        fixed_value = self._formula_preview_value(self.basic_fixed_value.get())
        operation_value = self._formula_preview_value(
            self.basic_operation_value.get()
        )
        self.basic_formula.set(
            f"{fixed_value} {self.basic_operation} {operation_value} ="
        )
        self.basic_result.set("—")
        self._reset_basic_result_label()
        self._set_status_for(
            "basic",
            "固定值默认 475；选择运算符后结果会实时更新。",
            tone="neutral",
        )
        try:
            result = calculate_fixed_value_operation(
                self.basic_fixed_value.get(),
                self.basic_operation_value.get(),
                self.basic_operation,
            )
        except InputValidationError:
            return
        except CalculationRangeError as exc:
            self._set_status_for("basic", str(exc), tone="error")
            return

        self.basic_result.set(result)
        self._style_result_label(self.basic_result_label, result, ACCENT)
        self._set_status_for(
            "basic",
            "基础运算结果已实时更新。",
            tone="success",
        )

    def select_basic_operation(self, operation: str) -> None:
        if operation not in self.basic_operation_buttons:
            return
        self.basic_operation = operation
        self._style_basic_operation_buttons()
        self._on_basic_input_change()

    def _style_basic_operation_buttons(self) -> None:
        active_options = {
            "border_width": 1,
            "border_color": ACCENT_BORDER,
            "fg_color": ACCENT_SOFT,
            "hover_color": ACCENT_BORDER,
            "text_color": ACCENT,
        }
        inactive_options = {
            "border_width": 0,
            "fg_color": "transparent",
            "hover_color": BORDER,
            "text_color": MUTED,
        }
        for operation, button in self.basic_operation_buttons.items():
            button.configure(
                **(
                    active_options
                    if operation == self.basic_operation
                    else inactive_options
                )
            )

    @staticmethod
    def _formula_preview_value(value: str) -> str:
        value = value.strip()
        if not value:
            return "—"
        return value if len(value) <= 10 else f"{value[:9]}…"

    def _set_status(self, message: str, tone: str) -> None:
        self._set_status_for(self._status_context(), message, tone)

    def _set_status_for(self, context: str, message: str, tone: str) -> None:
        self._page_status[context] = (message, tone)
        if self._status_context() == context:
            self._render_status(message, tone)

    def _status_context(self) -> str:
        if self._current_page == "calculator":
            return self._current_calculation_mode
        return self._current_page

    def _restore_page_status(self) -> None:
        message, tone = self._page_status[self._status_context()]
        self._render_status(message, tone)

    def _render_status(self, message: str, tone: str) -> None:
        palette = {
            "neutral": (SURFACE_ALT, MUTED),
            "success": (SUCCESS_SOFT, SUCCESS),
            "error": (ERROR_SOFT, ERROR),
        }
        background, foreground = palette[tone]
        self.status_text.set(message)
        self.status_frame.configure(fg_color=background)
        self.status_dot.configure(text_color=foreground)
        self.status_label.configure(text_color=foreground)

    def calculate(self) -> None:
        if self._current_calculation_mode == "multiply_add":
            self.calculate_multiply_add()
            return

        try:
            total, divided = calculate_values(
                self.a_value.get(),
                self.b_value.get(),
                self.divisor_value.get(),
            )
        except InputValidationError as exc:
            self.total_result.set("—")
            self.divide_result.set("—")
            self._reset_result_labels()
            invalid_entry = self._entry_for_field(exc.field)
            self._invalid_entries.add(invalid_entry)
            invalid_entry.configure(border_color=ERROR, border_width=2)
            invalid_entry.focus_set()
            self._set_status(str(exc), tone="error")
            return
        except CalculationRangeError as exc:
            self.total_result.set("—")
            self.divide_result.set("—")
            self._reset_result_labels()
            self._reset_entries()
            self._set_status(str(exc), tone="error")
            return

        self._reset_entries()
        self.total_result.set(total)
        self.divide_result.set(divided)
        self._style_result_label(self.total_value_label, total, ACCENT)
        self._style_result_label(self.divide_value_label, divided, TEXT)
        divisor_text = self.divisor_value.get().strip()
        self._set_status(
            f"计算完成，已使用除数 {divisor_text}，结果保留 2 位小数。",
            tone="success",
        )

    def calculate_multiply_add(self) -> None:
        try:
            result = calculate_multiply_add_value(
                self.coefficient_value.get(),
                self.multiply_value.get(),
                self.addend_value.get(),
            )
        except InputValidationError as exc:
            self.multiply_add_result.set("—")
            self._reset_multiply_add_result_label()
            invalid_entry = self._entry_for_field(exc.field)
            self._invalid_entries.add(invalid_entry)
            invalid_entry.configure(border_color=ERROR, border_width=2)
            invalid_entry.focus_set()
            self._set_status(str(exc), tone="error")
            return
        except CalculationRangeError as exc:
            self.multiply_add_result.set("—")
            self._reset_multiply_add_result_label()
            self._reset_entries()
            self._set_status(str(exc), tone="error")
            return

        self._reset_entries()
        self.multiply_add_result.set(result)
        self._style_result_label(self.multiply_add_result_label, result, ACCENT)
        coefficient_text = self.coefficient_value.get().strip()
        self._set_status(
            f"乘加计算完成：已使用系数 {coefficient_text}。",
            tone="success",
        )

    def calculate_basic_arithmetic(self) -> None:
        try:
            result = calculate_fixed_value_operation(
                self.basic_fixed_value.get(),
                self.basic_operation_value.get(),
                self.basic_operation,
            )
        except InputValidationError as exc:
            self.basic_result.set("—")
            self._reset_basic_result_label()
            invalid_entry = self._entry_for_field(exc.field)
            self._invalid_entries.add(invalid_entry)
            invalid_entry.configure(border_color=ERROR, border_width=2)
            invalid_entry.focus_set()
            self._set_status(str(exc), tone="error")
            return
        except CalculationRangeError as exc:
            self.basic_result.set("—")
            self._reset_basic_result_label()
            self._reset_entries()
            self._set_status(str(exc), tone="error")
            return

        self._reset_entries()
        self.basic_result.set(result)
        self._style_result_label(self.basic_result_label, result, ACCENT)
        fixed_value = self.basic_fixed_value.get().strip()
        operation_value = self.basic_operation_value.get().strip()
        self._set_status(
            f"计算完成：{fixed_value} {self.basic_operation} "
            f"{operation_value} = {result}。",
            tone="success",
        )

    def _entry_for_field(self, field: str) -> ctk.CTkEntry:
        return {
            "A": self.a_entry,
            "B": self.b_entry,
            "除数": self.divisor_entry,
            "系数": self.coefficient_entry,
            "乘数": self.multiply_entry,
            "加数": self.addend_entry,
            "固定值": self.basic_fixed_entry,
            "运算值": self.basic_value_entry,
        }[field]

    def _style_result_label(
        self,
        label: ctk.CTkLabel,
        value: str,
        color: str,
    ) -> None:
        if len(value) <= 12:
            font = self.result_font
        elif len(value) <= 18:
            font = self.result_medium_font
        else:
            font = self.result_compact_font
        label.configure(text_color=color, font=font)

    def _reset_result_labels(self) -> None:
        self.total_value_label.configure(text_color=FAINT, font=self.result_font)
        self.divide_value_label.configure(text_color=FAINT, font=self.result_font)

    def _reset_multiply_add_result_label(self) -> None:
        self.multiply_add_result_label.configure(
            text_color=FAINT,
            font=self.result_font,
        )

    def _reset_basic_result_label(self) -> None:
        self.basic_result_label.configure(
            text_color=FAINT,
            font=self.result_font,
        )

    def clear(self) -> None:
        if self._current_calculation_mode == "multiply_add":
            self.clear_multiply_add()
            return

        self.a_value.set("")
        self.b_value.set("")
        divisor_text = self.divisor_value.get().strip()
        if not NUMBER_PATTERN.fullmatch(divisor_text) or Decimal(divisor_text) == 0:
            self.divisor_value.set(DEFAULT_DIVISOR)
            divisor_text = DEFAULT_DIVISOR
        self._reset_entries()
        self.total_result.set("—")
        self.divide_result.set("—")
        self._reset_result_labels()
        self._set_status(
            f"已清空 A 和 B；除数保持为 {divisor_text}。",
            tone="neutral",
        )
        self.a_entry.focus_set()

    def clear_multiply_add(self) -> None:
        self.multiply_value.set("")
        self.addend_value.set("")
        coefficient_text = self.coefficient_value.get().strip()
        if not NUMBER_PATTERN.fullmatch(coefficient_text):
            self.coefficient_value.set(DEFAULT_COEFFICIENT)
            coefficient_text = DEFAULT_COEFFICIENT
        self._reset_entries()
        self.multiply_add_result.set("—")
        self._reset_multiply_add_result_label()
        self._set_status(
            f"已清空乘数和加数；系数保持为 {coefficient_text}。",
            tone="neutral",
        )
        self.multiply_entry.focus_set()

    def clear_basic_arithmetic(self) -> None:
        self.basic_operation_value.set("")
        fixed_value_text = self.basic_fixed_value.get().strip()
        if not NUMBER_PATTERN.fullmatch(fixed_value_text):
            self.basic_fixed_value.set(DEFAULT_FIXED_VALUE)
            fixed_value_text = DEFAULT_FIXED_VALUE
        self._reset_entries()
        self.basic_result.set("—")
        self._reset_basic_result_label()
        self._set_status(
            f"已清空运算值；固定值保持为 {fixed_value_text}。",
            tone="neutral",
        )
        self.basic_value_entry.focus_set()

    def _center_window(self) -> None:
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = max((screen_width - WINDOW_WIDTH) // 2, 0)
        y = max((screen_height - WINDOW_HEIGHT) // 2, 0)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")


def main() -> None:
    ctk.set_appearance_mode("dark")
    app = CalculatorApp()
    app.mainloop()


if __name__ == "__main__":
    main()

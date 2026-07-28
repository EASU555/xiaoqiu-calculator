from __future__ import annotations

import ctypes
import json
import os
import re
import sys
import tkinter as tk
import tkinter.font as tkfont
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import (
    Decimal,
    DecimalException,
    InvalidOperation,
    ROUND_HALF_UP,
    localcontext,
)
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk


DEFAULT_DIVISOR = "475"
DEFAULT_COEFFICIENT = "475"
DEFAULT_FIXED_VALUE = "475"
DEFAULT_COUNTER_HOTKEY = "space"
DEFAULT_COUNTER_HOTKEY_CODE = 32
DEFAULT_APPEARANCE_MODE = "light"
APPEARANCE_MODES = frozenset({"light", "dark"})
MAX_INPUT_LENGTH = 64
MAX_RESULT_LENGTH = 24
CALCULATION_PRECISION = MAX_INPUT_LENGTH * 3
HISTORY_LIMIT = 50
HISTORY_KINDS = ("standard", "multiply_add", "basic")
HISTORY_ROWS_BEFORE_SCROLL = 1
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

WINDOW_WIDTH = 680
WINDOW_HEIGHT = 780

# Light keeps the current warm-neutral template; dark restores the original
# graphite-and-orange template. CustomTkinter selects the matching tuple item.
ColorValue = str | tuple[str, str]
APP_BG: ColorValue = ("#F3F4F6", "#0D0F12")
SURFACE: ColorValue = ("#FFFFFF", "#171A1F")
SURFACE_ALT: ColorValue = ("#F7F7F5", "#1E2228")
BORDER: ColorValue = ("#E0E3E7", "#303640")
CONTROL_BG: ColorValue = ("#F7F8F9", "#1D2126")
CONTROL_HOVER: ColorValue = ("#ECEFF2", "#292E35")
DIVIDER: ColorValue = ("#ECEEF1", "#292E35")
SCROLLBAR: ColorValue = ("#D2D7DD", "#3A414B")
SCROLLBAR_HOVER: ColorValue = ("#B6BDC6", "#555E69")
TEXT: ColorValue = ("#1B1D21", "#F4F6F8")
MUTED: ColorValue = ("#646A73", "#A8B0BA")
FAINT: ColorValue = ("#9298A1", "#7D8792")
ACCENT: ColorValue = ("#F57C00", "#F28C28")
ACCENT_HOVER: ColorValue = ("#DC6E00", "#FFA44F")
ACCENT_TEXT: ColorValue = ("#FFFFFF", "#19120C")
ACCENT_SOFT: ColorValue = ("#FFF1E5", "#211C17")
ACCENT_SOFT_HOVER: ColorValue = ("#FFE4CF", "#332318")
ACCENT_BORDER: ColorValue = ("#F5C69F", "#704624")
SUCCESS: ColorValue = ("#2F7D55", "#74D18A")
SUCCESS_SOFT: ColorValue = ("#EAF6EF", "#112419")
ERROR: ColorValue = ("#C54444", "#FF9191")
ERROR_SOFT: ColorValue = ("#FCEDED", "#351619")

PANEL_RADIUS = 14
CONTROL_RADIUS = 9
BUTTON_RADIUS = 10


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


def counter_shortcut_matches(
    saved_keysym: str,
    saved_keycode: object,
    event_keysym: str,
    event_keycode: object,
) -> bool:
    """Keep Space available while also honoring the user-defined shortcut."""
    actual_code = normalize_keycode(event_keycode)
    if actual_code == DEFAULT_COUNTER_HOTKEY_CODE:
        return True
    if isinstance(event_keysym, str) and event_keysym.casefold() == "space":
        return True
    return hotkey_matches_event(
        saved_keysym,
        saved_keycode,
        event_keysym,
        event_keycode,
    )


def settings_file_path() -> Path:
    """Return the per-user settings file path without touching the filesystem."""
    app_data = os.environ.get("APPDATA")
    base = Path(app_data) if app_data else Path.home() / ".config"
    return base / "XiaoqiuCalculator" / "settings.json"


def appearance_file_path() -> Path:
    """Return the per-user appearance path without touching the filesystem."""
    return settings_file_path().with_name("appearance.json")


def resolve_appearance_color(color: ColorValue, mode: str) -> str:
    """Resolve one light/dark color tuple for Tk and native Windows APIs."""
    if isinstance(color, tuple):
        return color[1] if mode == "dark" else color[0]
    return color


def load_appearance_mode(path: Path | None = None) -> str:
    """Load the saved app appearance, falling back to the light template."""
    target = path or appearance_file_path()
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
        mode = payload.get("appearance_mode")
    except (OSError, ValueError, AttributeError):
        return DEFAULT_APPEARANCE_MODE
    return mode if mode in APPEARANCE_MODES else DEFAULT_APPEARANCE_MODE


def save_appearance_mode(
    mode: str,
    path: Path | None = None,
) -> str:
    """Atomically persist an explicitly selected light or dark template."""
    if mode not in APPEARANCE_MODES:
        raise ValueError("不支持的外观模式。")
    target = path or appearance_file_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(
            {"appearance_mode": mode},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)
    return mode


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


@dataclass(frozen=True)
class CalculationHistoryEntry:
    """One explicit, successful calculation saved for a single mode."""

    kind: str
    expression: str
    primary_result: str
    secondary_result: str | None
    created_at: str


def history_file_path() -> Path:
    """Return the per-user history path without touching the filesystem."""
    return settings_file_path().with_name("history.json")


def empty_calculation_history() -> dict[str, list[CalculationHistoryEntry]]:
    """Create an isolated history bucket for every calculation mode."""
    return {kind: [] for kind in HISTORY_KINDS}


def history_scrollbar_needed(entry_count: int) -> bool:
    """Decide scrollbar emphasis without observing live widget geometry."""
    return entry_count > HISTORY_ROWS_BEFORE_SCROLL


def append_calculation_history(
    histories: dict[str, list[CalculationHistoryEntry]],
    entry: CalculationHistoryEntry,
    *,
    limit: int = HISTORY_LIMIT,
) -> None:
    """Insert newest-first and enforce the limit independently per mode."""
    if entry.kind not in HISTORY_KINDS:
        raise ValueError("不支持的历史记录类型。")
    if limit < 1:
        raise ValueError("历史记录上限必须大于 0。")
    bucket = histories.setdefault(entry.kind, [])
    bucket.insert(0, entry)
    del bucket[limit:]


def clear_calculation_history(
    histories: dict[str, list[CalculationHistoryEntry]],
    kind: str,
) -> None:
    """Clear only the requested mode while preserving every other mode."""
    if kind not in HISTORY_KINDS:
        raise ValueError("不支持的历史记录类型。")
    histories[kind] = []


def load_calculation_history(
    path: Path | None = None,
) -> dict[str, list[CalculationHistoryEntry]]:
    """Load versioned history data, safely ignoring malformed records."""
    histories = empty_calculation_history()
    target = path or history_file_path()
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
        stored_histories = payload.get("histories", {})
        if not isinstance(stored_histories, dict):
            return histories
        for kind in HISTORY_KINDS:
            records = stored_histories.get(kind, [])
            if not isinstance(records, list):
                continue
            for record in records:
                if not isinstance(record, dict):
                    continue
                expression = record.get("expression")
                primary_result = record.get("primary_result")
                secondary_result = record.get("secondary_result")
                created_at = record.get("created_at")
                if not all(
                    isinstance(value, str)
                    for value in (expression, primary_result, created_at)
                ):
                    continue
                if secondary_result is not None and not isinstance(
                    secondary_result,
                    str,
                ):
                    continue
                histories[kind].append(
                    CalculationHistoryEntry(
                        kind=kind,
                        expression=expression,
                        primary_result=primary_result,
                        secondary_result=secondary_result,
                        created_at=created_at,
                    )
                )
                if len(histories[kind]) >= HISTORY_LIMIT:
                    break
    except (OSError, ValueError, AttributeError):
        return histories
    return histories


def save_calculation_history(
    histories: dict[str, list[CalculationHistoryEntry]],
    path: Path | None = None,
) -> None:
    """Atomically persist isolated calculation histories."""
    target = path or history_file_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    payload = {
        "version": 1,
        "histories": {
            kind: [asdict(entry) for entry in histories.get(kind, [])[:HISTORY_LIMIT]]
            for kind in HISTORY_KINDS
        },
    }
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)


def enable_windows_dpi_awareness() -> None:
    """Ask Windows for per-monitor DPI scaling before Tk creates a window."""
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except (AttributeError, OSError):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            pass


class CalculatorApp(ctk.CTk):
    def __init__(self) -> None:
        appearance_mode = load_appearance_mode()
        ctk.set_appearance_mode(appearance_mode)
        super().__init__()
        self.appearance_mode = appearance_mode
        self.title("小秋计算器")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(440, 400)
        self.resizable(True, True)
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
        self.calculation_history = load_calculation_history()
        self._history_views: dict[str, ctk.CTkScrollableFrame] = {}
        self._history_count_labels: dict[str, ctk.CTkLabel] = {}
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
            "counter": ("按 +1、Space 或已绑定快捷键开始计数。", "neutral"),
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
        self.subtitle_font = ctk.CTkFont(self.font_family, 11)
        self.section_font = ctk.CTkFont(self.font_family, 13, "bold")
        self.label_font = ctk.CTkFont(self.font_family, 12, "bold")
        self.body_font = ctk.CTkFont(self.font_family, 11)
        self.caption_font = ctk.CTkFont(self.font_family, 10)
        self.input_font = ctk.CTkFont(self.font_family, 15)
        self.button_font = ctk.CTkFont(self.font_family, 12, "bold")
        self.result_font = ctk.CTkFont(self.font_family, 22, "bold")
        self.result_medium_font = ctk.CTkFont(self.font_family, 18, "bold")
        self.result_compact_font = ctk.CTkFont(self.font_family, 14, "bold")
        self.history_result_font = ctk.CTkFont(self.font_family, 12, "bold")
        self.counter_font = ctk.CTkFont(self.font_family, 68, "bold")
        self.counter_medium_font = ctk.CTkFont(self.font_family, 52, "bold")
        self.counter_compact_font = ctk.CTkFont(self.font_family, 36, "bold")

    def _create_app_icon(self) -> None:
        try:
            self.iconbitmap(default=str(resource_path("app_icon.ico")))
            return
        except tk.TclError:
            pass

        icon = tk.PhotoImage(width=32, height=32)
        orange = resolve_appearance_color(ACCENT, self.appearance_mode)
        icon_text = resolve_appearance_color(
            ACCENT_TEXT,
            self.appearance_mode,
        )
        for y in range(4, 28):
            inset = 2 if y in (4, 5, 26, 27) else 1 if y in (6, 25) else 0
            icon.put(orange, to=(4 + inset, y, 28 - inset, y + 1))
        icon.put(icon_text, to=(9, 14, 23, 18))
        icon.put(icon_text, to=(14, 9, 18, 23))
        self.iconphoto(True, icon)
        self._app_icon = icon

    def _apply_windows_titlebar(self) -> None:
        """Match the native Windows title bar to the light app palette."""
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

            dark_mode = ctypes.c_int(1 if self.appearance_mode == "dark" else 0)
            caption = ctypes.c_int(
                colorref(
                    resolve_appearance_color(
                        APP_BG,
                        self.appearance_mode,
                    )
                )
            )
            caption_text = ctypes.c_int(
                colorref(resolve_appearance_color(TEXT, self.appearance_mode))
            )
            border = ctypes.c_int(
                colorref(resolve_appearance_color(BORDER, self.appearance_mode))
            )
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
        content.grid(row=0, column=0, sticky="nsew", padx=20, pady=(18, 14))
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)

        self._build_header(content)
        page_host = ctk.CTkFrame(content, fg_color="transparent")
        page_host.grid(row=1, column=0, sticky="nsew")
        page_host.grid_columnconfigure(0, weight=1)
        page_host.grid_rowconfigure(0, weight=1)

        page_options = {
            "fg_color": "transparent",
            "corner_radius": 0,
            "scrollbar_fg_color": "transparent",
            "scrollbar_button_color": SCROLLBAR,
            "scrollbar_button_hover_color": SCROLLBAR_HOVER,
        }
        self.calculator_page_container = ctk.CTkFrame(
            page_host,
            fg_color="transparent",
        )
        self.calculator_page_container.grid(row=0, column=0, sticky="nsew")
        self.calculator_page_container.grid_columnconfigure(0, weight=1)
        self.calculator_page_container.grid_rowconfigure(0, weight=1)
        self.calculator_page = ctk.CTkScrollableFrame(
            self.calculator_page_container,
            **page_options,
        )
        self.calculator_page.grid(row=0, column=0, sticky="nsew")
        self.calculator_page.grid_columnconfigure(0, weight=1)
        self._polish_scrollbar(self.calculator_page)
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
        self._build_history_panel(
            self.standard_calculator_panel,
            "standard",
            row=0,
        )
        self._build_input_card(self.standard_calculator_panel)

        self.multiply_add_panel = ctk.CTkFrame(
            calculation_host,
            fg_color="transparent",
        )
        self.multiply_add_panel.grid(row=0, column=0, sticky="nsew")
        self.multiply_add_panel.grid_columnconfigure(0, weight=1)
        self._build_history_panel(
            self.multiply_add_panel,
            "multiply_add",
            row=0,
        )
        self._build_multiply_add_panel(self.multiply_add_panel)
        self.standard_calculator_panel.tkraise()

        self.basic_page_container = ctk.CTkFrame(
            page_host,
            fg_color="transparent",
        )
        self.basic_page_container.grid(row=0, column=0, sticky="nsew")
        self.basic_page_container.grid_columnconfigure(0, weight=1)
        self.basic_page_container.grid_rowconfigure(0, weight=1)
        self.basic_page = ctk.CTkScrollableFrame(
            self.basic_page_container,
            **page_options,
        )
        self.basic_page.grid(row=0, column=0, sticky="nsew")
        self.basic_page.grid_columnconfigure(0, weight=1)
        self._polish_scrollbar(self.basic_page)
        self._build_basic_arithmetic_page(self.basic_page)

        self.counter_page_container = ctk.CTkFrame(
            page_host,
            fg_color="transparent",
        )
        self.counter_page_container.grid(row=0, column=0, sticky="nsew")
        self.counter_page_container.grid_columnconfigure(0, weight=1)
        self.counter_page_container.grid_rowconfigure(0, weight=1)
        self.counter_page = ctk.CTkScrollableFrame(
            self.counter_page_container,
            **page_options,
        )
        self.counter_page.grid(row=0, column=0, sticky="nsew")
        self.counter_page.grid_columnconfigure(0, weight=1)
        self._polish_scrollbar(self.counter_page)
        self._build_counter_page(self.counter_page)

        self.calculator_page_container.tkraise()
        self._build_status(content)
        for kind in HISTORY_KINDS:
            self._render_history(kind)

    def _build_header(self, parent: ctk.CTkFrame) -> None:
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        header.grid_columnconfigure(1, weight=1)

        badge = ctk.CTkFrame(
            header,
            width=42,
            height=42,
            corner_radius=12,
            fg_color=ACCENT_SOFT,
            border_width=0,
        )
        badge.grid(row=0, column=0, rowspan=2, sticky="nw", padx=(0, 12))
        badge.grid_propagate(False)
        ctk.CTkLabel(
            badge,
            text="Σ",
            font=ctk.CTkFont(self.font_family, 22, "bold"),
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
            corner_radius=CONTROL_RADIUS,
            border_width=1,
            border_color=BORDER,
            fg_color=SURFACE,
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
            width=52,
            height=32,
            corner_radius=7,
            border_width=0,
            fg_color=ACCENT_SOFT,
            hover_color=ACCENT_SOFT_HOVER,
            text_color=ACCENT,
            font=self.caption_font,
            command=self.show_calculator_page,
        )
        self.calculator_nav_button.grid(row=0, column=0, padx=3, pady=3)

        self.basic_nav_button = ctk.CTkButton(
            navigation,
            text="基础运算",
            width=60,
            height=32,
            corner_radius=7,
            border_width=0,
            fg_color="transparent",
            hover_color=CONTROL_HOVER,
            text_color=MUTED,
            font=self.caption_font,
            command=self.show_basic_arithmetic_page,
        )
        self.basic_nav_button.grid(row=0, column=1, pady=3)

        self.counter_nav_button = ctk.CTkButton(
            navigation,
            text="快捷计数",
            width=60,
            height=32,
            corner_radius=7,
            border_width=0,
            fg_color="transparent",
            hover_color=CONTROL_HOVER,
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

        self.theme_button = ctk.CTkButton(
            navigation,
            text=self._theme_button_text(),
            width=34,
            height=32,
            corner_radius=7,
            border_width=0,
            fg_color="transparent",
            hover_color=CONTROL_HOVER,
            text_color=MUTED,
            font=ctk.CTkFont(self.font_family, 14, "bold"),
            command=self.toggle_appearance_mode,
        )
        self.theme_button.grid(
            row=0,
            column=3,
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
            corner_radius=CONTROL_RADIUS,
            fg_color=SURFACE,
            border_width=1,
            border_color=BORDER,
        )
        selector.grid(row=0, column=1, sticky="e")

        self.standard_mode_button = ctk.CTkButton(
            selector,
            text="双结果",
            width=88,
            height=32,
            corner_radius=7,
            border_width=0,
            fg_color=ACCENT_SOFT,
            hover_color=ACCENT_SOFT_HOVER,
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
            corner_radius=7,
            border_width=0,
            fg_color="transparent",
            hover_color=CONTROL_HOVER,
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

    def _create_shadowed_panel(
        self,
        parent: ctk.CTkFrame,
        *,
        row: int,
        pady: tuple[int, int] = (0, 0),
    ) -> ctk.CTkFrame:
        """Create a clean tonal work surface without aliased fake shadows."""
        card = ctk.CTkFrame(
            parent,
            corner_radius=PANEL_RADIUS,
            fg_color=SURFACE,
            border_width=0,
        )
        card.grid(
            row=row,
            column=0,
            sticky="ew",
            pady=pady,
        )
        card.grid_columnconfigure(0, weight=1)
        return card

    @staticmethod
    def _polish_scrollbar(
        scrollable: ctk.CTkScrollableFrame,
        *,
        height: int | None = None,
    ) -> None:
        options: dict[str, object] = {
            "width": 10,
            "corner_radius": 5,
            "border_spacing": 2,
        }
        if height is not None:
            options["height"] = height
        scrollable._scrollbar.configure(**options)

    def _build_history_panel(
        self,
        parent: ctk.CTkFrame,
        kind: str,
        *,
        row: int,
    ) -> None:
        card = self._create_shadowed_panel(parent, row=row)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=18, pady=(13, 8))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header,
            text="历史记录",
            font=self.section_font,
            text_color=TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        count_label = ctk.CTkLabel(
            header,
            text=f"0 / {HISTORY_LIMIT}",
            font=self.caption_font,
            text_color=FAINT,
        )
        count_label.grid(row=0, column=1, padx=(8, 10))
        self._history_count_labels[kind] = count_label

        ctk.CTkButton(
            header,
            text="清空历史",
            width=80,
            height=28,
            corner_radius=7,
            border_width=0,
            fg_color=CONTROL_BG,
            hover_color=ERROR_SOFT,
            text_color=MUTED,
            font=self.caption_font,
            command=lambda value=kind: self._confirm_clear_history(value),
        ).grid(row=0, column=2, sticky="e")

        ledger = ctk.CTkScrollableFrame(
            card,
            height=72,
            corner_radius=10,
            fg_color=CONTROL_BG,
            scrollbar_fg_color="transparent",
            scrollbar_button_color=SCROLLBAR,
            scrollbar_button_hover_color=SCROLLBAR_HOVER,
        )
        # CustomTkinter 6.0 gives vertical scrollbars a 200 px minimum;
        # constrain this bounded ledger so high-DPI windows stay compact.
        self._polish_scrollbar(ledger, height=72)
        ledger.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=18,
            pady=(0, 16),
        )
        ledger.grid_columnconfigure(0, weight=1)
        self._history_views[kind] = ledger

    @staticmethod
    def _history_time_label(created_at: str) -> str:
        try:
            return datetime.fromisoformat(created_at).strftime("%m-%d %H:%M")
        except ValueError:
            return ""

    def _render_history(self, kind: str) -> None:
        ledger = self._history_views.get(kind)
        count_label = self._history_count_labels.get(kind)
        if ledger is None or count_label is None:
            return
        for child in ledger.winfo_children():
            child.destroy()

        entries = self.calculation_history.get(kind, [])
        count_label.configure(text=f"{len(entries)} / {HISTORY_LIMIT}")
        show_scrollbar = history_scrollbar_needed(len(entries))
        ledger._scrollbar.configure(
            button_color=SCROLLBAR if show_scrollbar else CONTROL_BG,
            button_hover_color=(
                SCROLLBAR_HOVER if show_scrollbar else CONTROL_BG
            ),
        )
        if not entries:
            empty = ctk.CTkFrame(ledger, fg_color="transparent")
            empty.grid(row=0, column=0, sticky="ew", padx=12, pady=13)
            empty.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                empty,
                text="暂无计算记录",
                font=self.label_font,
                text_color=MUTED,
            ).grid(row=0, column=0)
            ctk.CTkLabel(
                empty,
                text="点击“计算结果”或按 Enter 后会保存在这里",
                font=self.caption_font,
                text_color=FAINT,
            ).grid(row=1, column=0, pady=(4, 0))
            return

        for index, entry in enumerate(entries):
            row = ctk.CTkFrame(ledger, fg_color="transparent")
            row.grid(
                row=index * 2,
                column=0,
                sticky="ew",
                padx=10,
                pady=(8 if index == 0 else 6, 5),
            )
            row.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                row,
                text=entry.expression,
                font=self.body_font,
                text_color=TEXT,
                anchor="w",
            ).grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(
                row,
                text=self._history_time_label(entry.created_at),
                font=self.caption_font,
                text_color=FAINT,
                anchor="e",
            ).grid(row=0, column=1, sticky="e", padx=(10, 0))
            ctk.CTkLabel(
                row,
                text=entry.primary_result,
                font=self.history_result_font,
                text_color=ACCENT,
                anchor="w",
            ).grid(row=1, column=0, sticky="w", pady=(3, 0))
            if entry.secondary_result:
                ctk.CTkLabel(
                    row,
                    text=entry.secondary_result,
                    font=self.caption_font,
                    text_color=MUTED,
                    anchor="e",
                ).grid(
                    row=1,
                    column=1,
                    sticky="e",
                    padx=(10, 0),
                    pady=(3, 0),
                )
            if index < len(entries) - 1:
                ctk.CTkFrame(
                    ledger,
                    height=1,
                    corner_radius=0,
                    fg_color=DIVIDER,
                ).grid(
                    row=index * 2 + 1,
                    column=0,
                    sticky="ew",
                    padx=10,
                )

    def _confirm_clear_history(self, kind: str) -> None:
        if not self.calculation_history.get(kind):
            self._set_status("本页还没有历史记录。", tone="neutral")
            return
        kind_name = {
            "standard": "双结果",
            "multiply_add": "乘加计算",
            "basic": "基础运算",
        }[kind]
        confirmed = messagebox.askyesno(
            "清空历史",
            f"确定清空“{kind_name}”的全部历史记录吗？\n"
            "其他计算模式的历史不会受影响。",
            parent=self,
            icon="warning",
            default=messagebox.NO,
        )
        if not confirmed:
            return

        previous = list(self.calculation_history[kind])
        clear_calculation_history(self.calculation_history, kind)
        try:
            save_calculation_history(self.calculation_history)
        except OSError:
            self.calculation_history[kind] = previous
            self._set_status("历史记录清空失败，请稍后重试。", tone="error")
            return
        self._render_history(kind)
        self._set_status("本页历史记录已清空。", tone="neutral")

    def _record_history(
        self,
        kind: str,
        expression: str,
        primary_result: str,
        secondary_result: str | None = None,
    ) -> bool:
        entry = CalculationHistoryEntry(
            kind=kind,
            expression=expression,
            primary_result=primary_result,
            secondary_result=secondary_result,
            created_at=datetime.now().astimezone().isoformat(timespec="seconds"),
        )
        previous = list(self.calculation_history.get(kind, []))
        append_calculation_history(self.calculation_history, entry)
        try:
            save_calculation_history(self.calculation_history)
        except OSError:
            self.calculation_history[kind] = previous
            return False
        self._render_history(kind)
        return True

    def _add_inline_result(
        self,
        parent: ctk.CTkFrame,
        *,
        column: int,
        title: str,
        formula: str | tk.StringVar,
        variable: tk.StringVar,
        featured: bool,
        padx: tuple[int, int],
    ) -> tuple[ctk.CTkFrame, ctk.CTkLabel]:
        result = ctk.CTkFrame(
            parent,
            corner_radius=10,
            fg_color=ACCENT_SOFT if featured else CONTROL_BG,
            border_width=0,
        )
        result.grid(row=0, column=column, sticky="ew", padx=padx)
        result.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            result,
            text=title,
            font=self.label_font,
            text_color=TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=(13, 8), pady=(9, 0))
        formula_options: dict[str, object]
        if isinstance(formula, tk.StringVar):
            formula_options = {"textvariable": formula}
        else:
            formula_options = {"text": formula}
        ctk.CTkLabel(
            result,
            font=self.caption_font,
            text_color=MUTED,
            anchor="w",
            **formula_options,
        ).grid(row=1, column=0, sticky="w", padx=(13, 8), pady=(0, 9))

        value_label = ctk.CTkLabel(
            result,
            textvariable=variable,
            font=self.result_font,
            text_color=FAINT,
            anchor="e",
        )
        value_label.grid(
            row=0,
            column=1,
            rowspan=2,
            sticky="e",
            padx=(10, 13),
        )
        return result, value_label

    def _build_input_card(self, parent: ctk.CTkFrame) -> None:
        card = self._create_shadowed_panel(
            parent,
            row=1,
            pady=(12, 2),
        )

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
            corner_radius=CONTROL_RADIUS,
            border_width=1,
            border_color=BORDER,
            fg_color=CONTROL_BG,
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

        results = ctk.CTkFrame(card, fg_color="transparent")
        results.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 13))
        results.grid_columnconfigure(0, weight=1)
        results.grid_columnconfigure(1, weight=1)
        self.total_card, self.total_value_label = self._add_inline_result(
            results,
            column=0,
            title="总数",
            formula="A + B",
            variable=self.total_result,
            featured=True,
            padx=(0, 6),
        )
        self.divide_card, self.divide_value_label = self._add_inline_result(
            results,
            column=1,
            title="单列结果",
            formula=self.divide_formula,
            variable=self.divide_result,
            featured=False,
            padx=(6, 0),
        )
        self._build_actions(card, row=3)

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
            corner_radius=CONTROL_RADIUS,
            border_width=1,
            border_color=BORDER,
            fg_color=CONTROL_BG,
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

    def _build_actions(self, parent: ctk.CTkFrame, *, row: int) -> None:
        actions = ctk.CTkFrame(parent, fg_color="transparent")
        actions.grid(
            row=row,
            column=0,
            sticky="ew",
            padx=18,
            pady=(0, 16),
        )
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=2)

        self.clear_button = ctk.CTkButton(
            actions,
            text="清空",
            height=43,
            corner_radius=BUTTON_RADIUS,
            border_width=0,
            fg_color=CONTROL_BG,
            hover_color=CONTROL_HOVER,
            text_color=TEXT,
            font=self.body_font,
            command=self.clear,
        )
        self.clear_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self.calculate_button = ctk.CTkButton(
            actions,
            text="计算结果",
            height=43,
            corner_radius=BUTTON_RADIUS,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color=ACCENT_TEXT,
            font=self.button_font,
            command=self.calculate,
        )
        self.calculate_button.grid(row=0, column=1, sticky="ew", padx=(5, 0))

    def _build_multiply_add_panel(self, parent: ctk.CTkFrame) -> None:
        card = self._create_shadowed_panel(
            parent,
            row=1,
            pady=(12, 2),
        )

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
            corner_radius=0,
            fg_color="transparent",
            border_width=0,
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
            corner_radius=CONTROL_RADIUS,
            border_width=1,
            border_color=BORDER,
            fg_color=CONTROL_BG,
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
            corner_radius=CONTROL_RADIUS,
            fg_color=CONTROL_BG,
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

        result_area = ctk.CTkFrame(card, fg_color="transparent")
        result_area.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=18,
            pady=(0, 13),
        )
        result_area.grid_columnconfigure(0, weight=1)
        (
            self.multiply_add_result_card,
            self.multiply_add_result_label,
        ) = self._add_inline_result(
            result_area,
            column=0,
            title="计算结果",
            formula=self.multiply_add_formula,
            variable=self.multiply_add_result,
            featured=True,
            padx=(0, 0),
        )

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.grid(
            row=4,
            column=0,
            sticky="ew",
            padx=18,
            pady=(0, 16),
        )
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=2)
        self.multiply_add_clear_button = ctk.CTkButton(
            actions,
            text="清空",
            height=43,
            corner_radius=BUTTON_RADIUS,
            border_width=0,
            fg_color=CONTROL_BG,
            hover_color=CONTROL_HOVER,
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
            corner_radius=BUTTON_RADIUS,
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

    def _build_basic_arithmetic_page(self, parent: ctk.CTkFrame) -> None:
        self._build_history_panel(parent, "basic", row=0)
        card = self._create_shadowed_panel(
            parent,
            row=1,
            pady=(12, 2),
        )

        formula_strip = ctk.CTkFrame(
            card,
            height=42,
            corner_radius=CONTROL_RADIUS,
            fg_color=CONTROL_BG,
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
            corner_radius=CONTROL_RADIUS,
            fg_color=CONTROL_BG,
            border_width=0,
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
                corner_radius=7,
                border_width=0,
                fg_color=ACCENT_SOFT if active else "transparent",
                hover_color=(
                    ACCENT_SOFT_HOVER if active else CONTROL_HOVER
                ),
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

        result_area = ctk.CTkFrame(card, fg_color="transparent")
        result_area.grid(
            row=4,
            column=0,
            sticky="ew",
            padx=18,
            pady=(0, 13),
        )
        result_area.grid_columnconfigure(0, weight=1)
        self.basic_result_card, self.basic_result_label = self._add_inline_result(
            result_area,
            column=0,
            title="计算结果",
            formula=self.basic_formula,
            variable=self.basic_result,
            featured=True,
            padx=(0, 0),
        )

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.grid(
            row=5,
            column=0,
            sticky="ew",
            padx=18,
            pady=(0, 16),
        )
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=2)
        self.basic_clear_button = ctk.CTkButton(
            actions,
            text="清空",
            height=43,
            corner_radius=BUTTON_RADIUS,
            border_width=0,
            fg_color=CONTROL_BG,
            hover_color=CONTROL_HOVER,
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
            corner_radius=BUTTON_RADIUS,
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

        counter = self._create_shadowed_panel(
            parent,
            row=1,
            pady=(0, 2),
        )

        ctk.CTkLabel(
            counter,
            text="当前计数",
            font=self.caption_font,
            text_color=FAINT,
        ).grid(row=0, column=0, pady=(20, 0))

        self.counter_value_label = ctk.CTkLabel(
            counter,
            textvariable=self.counter_value,
            font=self.counter_font,
            text_color=ACCENT,
            anchor="center",
        )
        self.counter_value_label.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=22,
            pady=(2, 20),
        )

        counter_actions = ctk.CTkFrame(counter, fg_color="transparent")
        counter_actions.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=22,
            pady=(0, 20),
        )
        counter_actions.grid_columnconfigure(0, weight=1)

        self.counter_increment_button = ctk.CTkButton(
            counter_actions,
            text="＋  加 1",
            height=68,
            corner_radius=12,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color=ACCENT_TEXT,
            font=ctk.CTkFont(self.font_family, 18, "bold"),
            command=self.increment_counter,
        )
        self.counter_increment_button.grid(
            row=0,
            column=0,
            sticky="ew",
        )

        self.counter_reset_button = ctk.CTkButton(
            counter_actions,
            text="清零",
            height=40,
            corner_radius=BUTTON_RADIUS,
            border_width=0,
            fg_color=CONTROL_BG,
            hover_color=CONTROL_HOVER,
            text_color=MUTED,
            font=self.body_font,
            command=self.reset_counter,
        )
        self.counter_reset_button.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(10, 0),
        )

        hotkey_card = ctk.CTkFrame(
            parent,
            height=76,
            corner_radius=PANEL_RADIUS,
            fg_color=SURFACE,
            border_width=0,
        )
        hotkey_card.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        hotkey_card.grid_columnconfigure(0, weight=1)
        hotkey_card.grid_propagate(False)

        hotkey_description = ctk.CTkFrame(
            hotkey_card,
            fg_color="transparent",
        )
        hotkey_description.grid(row=0, column=0, sticky="ew", padx=(18, 8))
        hotkey_description.grid_columnconfigure(0, weight=1)
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
            corner_radius=CONTROL_RADIUS,
            border_width=0,
            fg_color=CONTROL_BG,
            hover_color=CONTROL_HOVER,
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

    def _build_status(self, parent: ctk.CTkFrame) -> None:
        self.status_frame = ctk.CTkFrame(
            parent,
            height=34,
            corner_radius=CONTROL_RADIUS,
            fg_color=CONTROL_BG,
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
            lambda _event: self._focus_widget(self.theme_button),
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
            lambda _event: self._focus_widget(self.theme_button),
        )
        self.counter_nav_button.bind(
            "<Shift-Tab>",
            lambda _event: self._focus_widget(self.basic_nav_button),
        )
        self.theme_button.bind("<Tab>", self._focus_page_start_from_keyboard)
        self.theme_button.bind(
            "<Shift-Tab>",
            lambda _event: self._focus_widget(self.counter_nav_button),
        )

        self.basic_fixed_entry.bind(
            "<Tab>",
            lambda _event: self._focus_widget(self.basic_value_entry),
        )
        self.basic_fixed_entry.bind(
            "<Shift-Tab>",
            lambda _event: self._focus_widget(self.theme_button),
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

        self.counter_increment_button.bind(
            "<Tab>",
            lambda _event: self._focus_widget(self.counter_reset_button),
        )
        self.counter_increment_button.bind(
            "<Shift-Tab>",
            lambda _event: self._focus_widget(self.theme_button),
        )
        self.counter_reset_button.bind(
            "<Tab>",
            lambda _event: self._focus_widget(self.hotkey_button),
        )
        self.counter_reset_button.bind(
            "<Shift-Tab>",
            lambda _event: self._focus_widget(self.counter_increment_button),
        )
        self.hotkey_button.bind("<Tab>", self._focus_navigation_from_keyboard)
        self.hotkey_button.bind(
            "<Shift-Tab>",
            lambda _event: self._focus_widget(self.counter_reset_button),
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
            "border_width": 0,
            "fg_color": ACCENT_SOFT,
            "hover_color": ACCENT_SOFT_HOVER,
            "text_color": ACCENT,
        }
        inactive_options = {
            "border_width": 0,
            "fg_color": "transparent",
            "hover_color": CONTROL_HOVER,
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
            "border_width": 0,
            "fg_color": ACCENT_SOFT,
            "hover_color": ACCENT_SOFT_HOVER,
            "text_color": ACCENT,
        }
        inactive_options = {
            "border_width": 0,
            "fg_color": "transparent",
            "hover_color": CONTROL_HOVER,
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

    def _theme_button_text(self) -> str:
        return "☀" if self.appearance_mode == "dark" else "☾"

    def toggle_appearance_mode(self) -> None:
        next_mode = "dark" if self.appearance_mode == "light" else "light"
        self.appearance_mode = next_mode
        ctk.set_appearance_mode(next_mode)
        self.theme_button.configure(text=self._theme_button_text())
        self.update_idletasks()
        self._apply_windows_titlebar()

        mode_name = "深色" if next_mode == "dark" else "浅色"
        try:
            save_appearance_mode(next_mode)
        except OSError:
            self._set_status(
                f"已切换为{mode_name}模式，但无法保存外观设置。",
                tone="error",
            )
        else:
            self._set_status(
                f"已切换为{mode_name}模式，下次启动会自动保持。",
                tone="success",
            )

    def show_calculator_page(self) -> None:
        if self._capturing_hotkey:
            self.cancel_hotkey_capture()
        self._current_page = "calculator"
        self.calculator_page_container.tkraise()
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
        self.basic_page_container.tkraise()
        self.page_subtitle.set("固定值基础运算")
        self._style_page_navigation()
        self.shortcut_text.set(self._shortcut_summary())
        self._restore_page_status()
        self.basic_fixed_entry.focus_set()

    def show_counter_page(self) -> None:
        self._current_page = "counter"
        self.counter_page_container.tkraise()
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
            if self._focus_is_within(self.theme_button):
                self.toggle_appearance_mode()
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
            counter_shortcut_matches(
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
            shortcut = "Space" if display == "Space" else f"Space / {display}"
            return f"{shortcut} +1   ·   Esc 返回计算器"
        return "Enter 计算   ·   Esc 清空"

    def start_hotkey_capture(self) -> None:
        self._capturing_hotkey = True
        self.hotkey_button.configure(
            text="请按一个键（Esc 取消）",
            border_width=1,
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
            border_width=0,
            border_color=BORDER,
            fg_color=CONTROL_BG,
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
        return self._focus_widget(self.counter_increment_button)

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
            entry.configure(border_color=ACCENT, border_width=1)

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
                entry.configure(border_color=ACCENT, border_width=1)
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
            "border_width": 0,
            "fg_color": ACCENT_SOFT,
            "hover_color": ACCENT_SOFT_HOVER,
            "text_color": ACCENT,
        }
        inactive_options = {
            "border_width": 0,
            "fg_color": "transparent",
            "hover_color": CONTROL_HOVER,
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
        a_text = self.a_value.get().strip()
        b_text = self.b_value.get().strip()
        divisor_text = self.divisor_value.get().strip()
        history_saved = self._record_history(
            "standard",
            f"A {a_text} + B {b_text}",
            f"总数 {total}",
            f"B {b_text} ÷ {divisor_text} = {divided}",
        )
        self._set_status(
            (
                f"计算完成，已使用除数 {divisor_text}，并写入历史。"
                if history_saved
                else "计算完成，但历史记录暂时无法保存。"
            ),
            tone="success" if history_saved else "error",
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
        multiplier_text = self.multiply_value.get().strip()
        addend_text = self.addend_value.get().strip()
        history_saved = self._record_history(
            "multiply_add",
            f"{coefficient_text} × {multiplier_text} + {addend_text}",
            f"结果 {result}",
        )
        self._set_status(
            (
                f"乘加计算完成，已使用系数 {coefficient_text} 并写入历史。"
                if history_saved
                else "乘加计算完成，但历史记录暂时无法保存。"
            ),
            tone="success" if history_saved else "error",
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
        history_saved = self._record_history(
            "basic",
            f"{fixed_value} {self.basic_operation} {operation_value}",
            f"结果 {result}",
        )
        self._set_status(
            (
                f"计算完成：{fixed_value} {self.basic_operation} "
                f"{operation_value} = {result}，已写入历史。"
                if history_saved
                else "计算完成，但历史记录暂时无法保存。"
            ),
            tone="success" if history_saved else "error",
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
        color: ColorValue,
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
        rendered_width = self.winfo_width()
        rendered_height = self.winfo_height()
        x = max((screen_width - rendered_width) // 2, 0)
        y = max((screen_height - rendered_height) // 2, 0)
        self.geometry(f"+{x}+{y}")


def main() -> None:
    enable_windows_dpi_awareness()
    app = CalculatorApp()
    app.mainloop()


if __name__ == "__main__":
    main()

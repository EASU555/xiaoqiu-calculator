from __future__ import annotations

import ctypes
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
MAX_INPUT_LENGTH = 64
MAX_RESULT_LENGTH = 24
CALCULATION_PRECISION = MAX_INPUT_LENGTH * 3
NUMBER_PATTERN = re.compile(r"-?(?:\d+(?:\.\d*)?|\.\d+)$")
EDITING_PATTERN = re.compile(r"^-?(?:\d*(?:\.\d*)?)?$")

WINDOW_WIDTH = 500
WINDOW_HEIGHT = 600

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


class CalculatorApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("A+B 计算器")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(460, 590)
        self.resizable(True, False)
        self.configure(fg_color=APP_BG)

        self.font_family = self._choose_font_family()
        self.a_value = tk.StringVar()
        self.b_value = tk.StringVar()
        self.divisor_value = tk.StringVar(value=DEFAULT_DIVISOR)
        self.total_result = tk.StringVar(value="—")
        self.divide_result = tk.StringVar(value="—")
        self.divide_formula = tk.StringVar(value=f"B ÷ {DEFAULT_DIVISOR}")
        self.status_text = tk.StringVar(value="输入 A、B，可按需修改右上角除数。")
        self._invalid_entries: set[ctk.CTkEntry] = set()
        self._focused_entry: ctk.CTkEntry | None = None

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

        self._build_header(content)
        self._build_input_card(content)
        self._build_actions(content)
        self._build_results(content)
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
            text="双结果计算器",
            font=self.title_font,
            text_color=TEXT,
            anchor="w",
        ).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(
            header,
            text="一次输入，同时得到总数与除法结果",
            font=self.subtitle_font,
            text_color=MUTED,
            anchor="w",
        ).grid(row=1, column=1, sticky="w", pady=(1, 0))

        divisor_control = ctk.CTkFrame(header, fg_color="transparent")
        divisor_control.grid(
            row=0,
            column=2,
            rowspan=2,
            sticky="e",
            padx=(10, 0),
        )
        ctk.CTkLabel(
            divisor_control,
            text="可调除数",
            height=13,
            text_color=FAINT,
            font=self.caption_font,
        ).grid(row=0, column=0, sticky="e", pady=(0, 2))
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
        self.divisor_entry.grid(row=1, column=0, sticky="e")

    def _build_input_card(self, parent: ctk.CTkFrame) -> None:
        card = ctk.CTkFrame(
            parent,
            corner_radius=16,
            fg_color=SURFACE,
            border_width=1,
            border_color=BORDER,
        )
        card.grid(row=1, column=0, sticky="ew")
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
        ctk.CTkLabel(
            card_header,
            text="支持正负整数与小数",
            font=self.caption_font,
            text_color=FAINT,
            anchor="e",
        ).grid(row=0, column=1, sticky="e")

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
        actions.grid(row=2, column=0, sticky="ew", pady=(14, 17))
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

    def _build_results(self, parent: ctk.CTkFrame) -> None:
        section_header = ctk.CTkFrame(parent, fg_color="transparent")
        section_header.grid(row=3, column=0, sticky="ew", pady=(0, 7))
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
            text="自动四舍五入至 2 位",
            font=self.caption_font,
            text_color=FAINT,
            anchor="e",
        ).grid(row=0, column=1, sticky="e")

        results = ctk.CTkFrame(parent, fg_color="transparent")
        results.grid(row=4, column=0, sticky="ew")
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
        self.status_frame.grid(row=5, column=0, sticky="ew", pady=(12, 0))
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
            text="Enter 计算   ·   Esc 清空",
            font=self.caption_font,
            text_color=FAINT,
            anchor="e",
        ).grid(row=6, column=0, sticky="e", pady=(6, 0))

    def _bind_interactions(self) -> None:
        self.a_value.trace_add("write", self._on_input_change)
        self.b_value.trace_add("write", self._on_input_change)
        self.divisor_value.trace_add("write", self._on_input_change)
        self.bind("<Return>", lambda _event: self.calculate())
        self.bind("<Escape>", lambda _event: self.clear())

        for entry in (self.a_entry, self.b_entry, self.divisor_entry):
            entry.bind("<FocusIn>", lambda _event, item=entry: self._focus_entry(item))
            entry.bind("<FocusOut>", lambda _event, item=entry: self._blur_entry(item))

        self.a_entry.bind("<Tab>", self._focus_b_from_keyboard)
        self.a_entry.bind("<Shift-Tab>", self._focus_divisor_from_keyboard)
        self.b_entry.bind("<Tab>", self._focus_divisor_from_keyboard)
        self.b_entry.bind("<Shift-Tab>", self._focus_a_from_keyboard)
        self.divisor_entry.bind("<Tab>", self._focus_a_from_keyboard)
        self.divisor_entry.bind("<Shift-Tab>", self._focus_b_from_keyboard)

        self.a_entry.focus_set()

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
        for entry in (self.a_entry, self.b_entry, self.divisor_entry):
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
        self._set_status(
            "输入 A、B，可按需修改右上角除数。",
            tone="neutral",
        )

    def _set_status(self, message: str, tone: str) -> None:
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

    def _entry_for_field(self, field: str) -> ctk.CTkEntry:
        return {
            "A": self.a_entry,
            "B": self.b_entry,
            "除数": self.divisor_entry,
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

    def clear(self) -> None:
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

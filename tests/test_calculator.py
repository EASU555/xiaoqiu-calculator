from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from calculator import (
    ACCENT,
    APP_BG,
    SURFACE,
    DEFAULT_APPEARANCE_MODE,
    DEFAULT_COUNTER_HOTKEY,
    DEFAULT_COUNTER_HOTKEY_CODE,
    HISTORY_LIMIT,
    MAX_INPUT_LENGTH,
    CalculationHistoryEntry,
    CalculationRangeError,
    InputValidationError,
    append_calculation_history,
    calculate_fixed_value_operation,
    calculate_multiply_add_value,
    calculate_values,
    clear_calculation_history,
    counter_shortcut_matches,
    empty_calculation_history,
    format_result,
    history_scrollbar_needed,
    hotkey_display_name,
    hotkey_is_reserved,
    hotkey_matches_event,
    increment_counter_value,
    load_appearance_mode,
    load_calculation_history,
    load_counter_hotkey,
    load_counter_hotkey_binding,
    normalize_hotkey,
    normalize_keycode,
    parse_number,
    resolve_appearance_color,
    save_appearance_mode,
    save_calculation_history,
    save_counter_hotkey,
)
from decimal import Decimal


class CalculatorLogicTests(unittest.TestCase):
    @staticmethod
    def history_entry(kind: str, index: int) -> CalculationHistoryEntry:
        return CalculationHistoryEntry(
            kind=kind,
            expression=f"expression-{index}",
            primary_result=f"result-{index}",
            secondary_result=None,
            created_at=f"2026-07-28T10:{index % 60:02d}:00+08:00",
        )

    def test_default_divisor(self) -> None:
        self.assertEqual(calculate_values("592", "3325"), ("3917", "7"))

    def test_custom_decimal_divisor(self) -> None:
        self.assertEqual(calculate_values("1.25", "5", "2.5"), ("6.25", "2"))

    def test_default_475_multiply_add_mode(self) -> None:
        self.assertEqual(calculate_multiply_add_value("475", "2", "25"), "975")
        self.assertEqual(
            calculate_multiply_add_value("475", "1.5", "0.25"),
            "712.75",
        )
        self.assertEqual(calculate_multiply_add_value("475", "-2", "25"), "-925")

    def test_custom_coefficient_multiply_add_mode(self) -> None:
        self.assertEqual(calculate_multiply_add_value("500", "2", "25"), "1025")
        self.assertEqual(calculate_multiply_add_value("1.5", "4", "2"), "8")
        self.assertEqual(calculate_multiply_add_value("-3", "2", "1"), "-5")

    def test_multiply_add_mode_validates_all_inputs(self) -> None:
        with self.assertRaisesRegex(InputValidationError, "请输入系数"):
            calculate_multiply_add_value("", "2", "10")
        with self.assertRaisesRegex(InputValidationError, "请输入乘数"):
            calculate_multiply_add_value("475", "", "10")
        with self.assertRaisesRegex(InputValidationError, "加数必须是数字"):
            calculate_multiply_add_value("475", "2", "bad")

    def test_fixed_value_basic_operations(self) -> None:
        self.assertEqual(calculate_fixed_value_operation("475", "25", "+"), "500")
        self.assertEqual(calculate_fixed_value_operation("475", "25", "-"), "450")
        self.assertEqual(calculate_fixed_value_operation("12", "2.5", "×"), "30")
        self.assertEqual(calculate_fixed_value_operation("10", "4", "÷"), "2.5")

    def test_fixed_value_operations_support_negative_values(self) -> None:
        self.assertEqual(calculate_fixed_value_operation("-10", "2.5", "+"), "-7.5")
        self.assertEqual(calculate_fixed_value_operation("-10", "-2", "×"), "20")

    def test_fixed_value_operation_validates_inputs_and_zero_division(self) -> None:
        with self.assertRaisesRegex(InputValidationError, "请输入固定值"):
            calculate_fixed_value_operation("", "2", "+")
        with self.assertRaisesRegex(InputValidationError, "运算值必须是数字"):
            calculate_fixed_value_operation("475", "bad", "-")
        with self.assertRaisesRegex(InputValidationError, "运算值不能为 0"):
            calculate_fixed_value_operation("475", "0", "÷")
        with self.assertRaisesRegex(ValueError, "不支持的运算符"):
            calculate_fixed_value_operation("475", "2", "%")

    def test_negative_values(self) -> None:
        self.assertEqual(calculate_values("-10.5", "5", "-2"), ("-5.5", "-2.5"))

    def test_round_half_up_and_trim_zeroes(self) -> None:
        self.assertEqual(format_result(Decimal("1.005")), "1.01")
        self.assertEqual(format_result(Decimal("3.00")), "3")

    def test_empty_and_malformed_input(self) -> None:
        with self.assertRaisesRegex(InputValidationError, "请输入 A 数据"):
            parse_number("", "A")
        with self.assertRaisesRegex(InputValidationError, "必须是数字"):
            parse_number("1e3", "B")

    def test_zero_divisor_is_rejected(self) -> None:
        with self.assertRaisesRegex(InputValidationError, "除数不能为 0"):
            calculate_values("1", "5", "-0.0")

    def test_overlong_input_is_rejected(self) -> None:
        with self.assertRaisesRegex(InputValidationError, "最多输入"):
            calculate_values("9" * (MAX_INPUT_LENGTH + 1), "1")

    def test_huge_result_is_rejected_without_decimal_crash(self) -> None:
        tiny_divisor = "0." + "0" * 60 + "1"
        with self.assertRaisesRegex(CalculationRangeError, "计算结果过长"):
            calculate_values("1", "9" * 18, tiny_divisor)

    def test_counter_increments_exactly_once(self) -> None:
        self.assertEqual(increment_counter_value(0), 1)
        self.assertEqual(increment_counter_value(41), 42)

    def test_counter_hotkey_normalization(self) -> None:
        self.assertEqual(normalize_hotkey("A"), "a")
        self.assertEqual(normalize_hotkey("7"), "7")
        self.assertEqual(normalize_hotkey("space"), "space")
        self.assertEqual(normalize_hotkey("F8"), "F8")

    def test_reserved_or_malformed_hotkeys_are_rejected(self) -> None:
        for keysym in ("Return", "KP_Enter", "Escape", "Tab", "Control_L"):
            with self.subTest(keysym=keysym):
                self.assertIsNone(normalize_hotkey(keysym))
        self.assertIsNone(normalize_hotkey(""))
        self.assertIsNone(normalize_hotkey("bad key"))
        self.assertTrue(hotkey_is_reserved("unrecognized", 13))
        self.assertFalse(hotkey_is_reserved("a", 65))

    def test_windows_keycode_normalization_and_matching(self) -> None:
        self.assertEqual(normalize_keycode("65"), 65)
        self.assertIsNone(normalize_keycode(0))
        self.assertIsNone(normalize_keycode("not-a-code"))
        self.assertTrue(hotkey_matches_event("a", 65, "??", 65))
        self.assertFalse(hotkey_matches_event("a", 65, "a", 66))
        self.assertTrue(hotkey_matches_event("F8", None, "f8", None))

    def test_space_remains_available_with_a_custom_counter_shortcut(self) -> None:
        self.assertTrue(counter_shortcut_matches("F8", 119, "space", 32))
        self.assertTrue(counter_shortcut_matches("F8", 119, "F8", 119))
        self.assertFalse(counter_shortcut_matches("F8", 119, "a", 65))

    def test_hotkey_display_names_are_compact(self) -> None:
        self.assertEqual(hotkey_display_name("space"), "Space")
        self.assertEqual(hotkey_display_name("a"), "A")
        self.assertEqual(hotkey_display_name("F8"), "F8")
        self.assertEqual(hotkey_display_name("Left"), "←")
        self.assertEqual(hotkey_display_name("??", 65), "A")
        self.assertEqual(hotkey_display_name("keycode_226", 226), "按键 226")

    def test_counter_hotkey_settings_round_trip(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            self.assertEqual(
                load_counter_hotkey_binding(path),
                (DEFAULT_COUNTER_HOTKEY, DEFAULT_COUNTER_HOTKEY_CODE),
            )
            self.assertEqual(save_counter_hotkey("F8", path, keycode=119), "F8")
            self.assertEqual(load_counter_hotkey(path), "F8")
            self.assertEqual(load_counter_hotkey_binding(path), ("F8", 119))

    def test_unusual_keysym_uses_keycode_fallback(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            self.assertEqual(save_counter_hotkey("", path, keycode=226), "keycode_226")
            self.assertEqual(load_counter_hotkey_binding(path), ("keycode_226", 226))

    def test_invalid_settings_fall_back_to_space(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text("not json", encoding="utf-8")
            self.assertEqual(load_counter_hotkey(path), DEFAULT_COUNTER_HOTKEY)
            with self.assertRaises(ValueError):
                save_counter_hotkey("Escape", path)

    def test_appearance_mode_settings_round_trip(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "appearance.json"
            self.assertEqual(
                load_appearance_mode(path),
                DEFAULT_APPEARANCE_MODE,
            )
            self.assertEqual(save_appearance_mode("dark", path), "dark")
            self.assertEqual(load_appearance_mode(path), "dark")
            self.assertEqual(save_appearance_mode("light", path), "light")
            self.assertEqual(load_appearance_mode(path), "light")
            with self.assertRaises(ValueError):
                save_appearance_mode("system", path)

    def test_invalid_appearance_settings_fall_back_to_light(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "appearance.json"
            path.write_text('{"appearance_mode": "unknown"}', encoding="utf-8")
            self.assertEqual(
                load_appearance_mode(path),
                DEFAULT_APPEARANCE_MODE,
            )
            path.write_text("not json", encoding="utf-8")
            self.assertEqual(
                load_appearance_mode(path),
                DEFAULT_APPEARANCE_MODE,
            )

    def test_dark_palette_restores_original_graphite_template(self) -> None:
        self.assertEqual(resolve_appearance_color(APP_BG, "light"), "#F3F4F6")
        self.assertEqual(resolve_appearance_color(APP_BG, "dark"), "#0D0F12")
        self.assertEqual(resolve_appearance_color(SURFACE, "dark"), "#171A1F")
        self.assertEqual(resolve_appearance_color(ACCENT, "dark"), "#F28C28")

    def test_history_limit_is_enforced_per_mode(self) -> None:
        histories = empty_calculation_history()
        for index in range(HISTORY_LIMIT + 5):
            append_calculation_history(
                histories,
                self.history_entry("standard", index),
            )
        for index in range(HISTORY_LIMIT + 2):
            append_calculation_history(
                histories,
                self.history_entry("multiply_add", index),
            )

        self.assertEqual(len(histories["standard"]), HISTORY_LIMIT)
        self.assertEqual(len(histories["multiply_add"]), HISTORY_LIMIT)
        self.assertEqual(histories["standard"][0].expression, "expression-54")
        self.assertEqual(histories["standard"][-1].expression, "expression-5")
        self.assertEqual(
            histories["multiply_add"][0].expression,
            "expression-51",
        )
        self.assertEqual(
            histories["multiply_add"][-1].expression,
            "expression-2",
        )
        self.assertEqual(histories["basic"], [])

    def test_history_scrollbar_rule_is_geometry_independent(self) -> None:
        self.assertFalse(history_scrollbar_needed(0))
        self.assertFalse(history_scrollbar_needed(1))
        self.assertTrue(history_scrollbar_needed(2))
        self.assertTrue(history_scrollbar_needed(HISTORY_LIMIT))

    def test_history_persists_across_reload(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "history.json"
            histories = empty_calculation_history()
            standard = self.history_entry("standard", 1)
            multiply_add = self.history_entry("multiply_add", 2)
            append_calculation_history(histories, standard)
            append_calculation_history(histories, multiply_add)

            save_calculation_history(histories, path)
            restored = load_calculation_history(path)

            self.assertEqual(restored["standard"], [standard])
            self.assertEqual(restored["multiply_add"], [multiply_add])
            self.assertEqual(restored["basic"], [])

    def test_clearing_history_preserves_other_modes_and_persists(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "history.json"
            histories = empty_calculation_history()
            append_calculation_history(
                histories,
                self.history_entry("standard", 1),
            )
            multiply_add = self.history_entry("multiply_add", 2)
            basic = self.history_entry("basic", 3)
            append_calculation_history(histories, multiply_add)
            append_calculation_history(histories, basic)

            clear_calculation_history(histories, "standard")
            save_calculation_history(histories, path)
            restored = load_calculation_history(path)

            self.assertEqual(restored["standard"], [])
            self.assertEqual(restored["multiply_add"], [multiply_add])
            self.assertEqual(restored["basic"], [basic])

    def test_malformed_history_falls_back_to_isolated_empty_buckets(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "history.json"
            path.write_text("{not-json", encoding="utf-8")

            self.assertEqual(
                load_calculation_history(path),
                empty_calculation_history(),
            )


if __name__ == "__main__":
    unittest.main()

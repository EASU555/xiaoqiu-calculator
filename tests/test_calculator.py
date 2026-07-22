from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from calculator import (
    DEFAULT_COUNTER_HOTKEY,
    DEFAULT_COUNTER_HOTKEY_CODE,
    MAX_INPUT_LENGTH,
    CalculationRangeError,
    InputValidationError,
    calculate_multiply_add_value,
    calculate_values,
    format_result,
    hotkey_display_name,
    hotkey_is_reserved,
    hotkey_matches_event,
    increment_counter_value,
    load_counter_hotkey,
    load_counter_hotkey_binding,
    normalize_hotkey,
    normalize_keycode,
    parse_number,
    save_counter_hotkey,
)
from decimal import Decimal


class CalculatorLogicTests(unittest.TestCase):
    def test_default_divisor(self) -> None:
        self.assertEqual(calculate_values("592", "3325"), ("3917", "7"))

    def test_custom_decimal_divisor(self) -> None:
        self.assertEqual(calculate_values("1.25", "5", "2.5"), ("6.25", "2"))

    def test_fixed_475_multiply_add_mode(self) -> None:
        self.assertEqual(calculate_multiply_add_value("2", "25"), "975")
        self.assertEqual(calculate_multiply_add_value("1.5", "0.25"), "712.75")
        self.assertEqual(calculate_multiply_add_value("-2", "25"), "-925")

    def test_fixed_multiply_add_mode_validates_both_inputs(self) -> None:
        with self.assertRaisesRegex(InputValidationError, "请输入乘数"):
            calculate_multiply_add_value("", "10")
        with self.assertRaisesRegex(InputValidationError, "加数必须是数字"):
            calculate_multiply_add_value("2", "bad")

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


if __name__ == "__main__":
    unittest.main()

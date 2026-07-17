from __future__ import annotations

import unittest

from calculator import (
    MAX_INPUT_LENGTH,
    CalculationRangeError,
    InputValidationError,
    calculate_values,
    format_result,
    parse_number,
)
from decimal import Decimal


class CalculatorLogicTests(unittest.TestCase):
    def test_default_divisor(self) -> None:
        self.assertEqual(calculate_values("592", "3325"), ("3917", "7"))

    def test_custom_decimal_divisor(self) -> None:
        self.assertEqual(calculate_values("1.25", "5", "2.5"), ("6.25", "2"))

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


if __name__ == "__main__":
    unittest.main()

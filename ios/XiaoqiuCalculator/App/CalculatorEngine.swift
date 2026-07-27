import Foundation

enum CalculatorField: String, Hashable {
    case a
    case b
    case divisor
}

enum CalculatorIssue: Error, Equatable {
    case input(message: String, field: CalculatorField)
    case range(message: String)

    var message: String {
        switch self {
        case let .input(message, _), let .range(message):
            return message
        }
    }

    var field: CalculatorField? {
        guard case let .input(_, field) = self else {
            return nil
        }
        return field
    }
}

struct CalculationResult: Equatable {
    let total: String
    let divided: String
}

enum CalculatorEngine {
    static let defaultDivisor = "475"
    static let maxInputLength = 64
    static let maxResultLength = 24

    private static let numberPattern =
        #"^-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)$"#
    private static let editingPattern =
        #"^-?(?:[0-9]*(?:\.[0-9]*)?)?$"#

    static func isEditingTextValid(_ value: String) -> Bool {
        value.count <= maxInputLength && matches(value, pattern: editingPattern)
    }

    static func isValidNonZeroDivisor(_ value: String) -> Bool {
        guard
            let parsed = try? parseNumber(
                value,
                label: "除数",
                field: .divisor
            )
        else {
            return false
        }
        return !parsed.isZero
    }

    static func calculate(
        aText: String,
        bText: String,
        divisorText: String = defaultDivisor
    ) throws -> CalculationResult {
        let aValue = try parseNumber(aText, label: "A", field: .a)
        let bValue = try parseNumber(bText, label: "B", field: .b)
        let divisor = try parseNumber(
            divisorText,
            label: "除数",
            field: .divisor
        )

        guard !divisor.isZero else {
            throw CalculatorIssue.input(
                message: "除数不能为 0。",
                field: .divisor
            )
        }

        let total = aValue.adding(bValue).roundedString(
            fractionDigits: 2
        )
        let divided = ArbitraryDecimal.dividing(
            bValue,
            by: divisor,
            fractionDigits: 2
        )

        guard
            total.count <= maxResultLength,
            divided.count <= maxResultLength
        else {
            throw CalculatorIssue.range(
                message: "计算结果过长，请缩小输入值或增大除数。"
            )
        }

        return CalculationResult(total: total, divided: divided)
    }

    private static func parseNumber(
        _ rawValue: String,
        label: String,
        field: CalculatorField
    ) throws -> ArbitraryDecimal {
        let value = rawValue.trimmingCharacters(in: .whitespacesAndNewlines)
        let displayName = label == "A" || label == "B"
            ? "\(label) 数据"
            : label

        guard !value.isEmpty else {
            let message = label == "A" || label == "B"
                ? "请输入 \(displayName)。"
                : "请输入\(displayName)。"
            throw CalculatorIssue.input(message: message, field: field)
        }
        guard value.count <= maxInputLength else {
            throw CalculatorIssue.input(
                message: "\(displayName)最多输入 \(maxInputLength) 个字符。",
                field: field
            )
        }
        guard matches(value, pattern: numberPattern) else {
            throw CalculatorIssue.input(
                message: "\(displayName)必须是数字（支持整数和小数）。",
                field: field
            )
        }

        return ArbitraryDecimal(value)
    }

    private static func matches(_ value: String, pattern: String) -> Bool {
        value.range(of: pattern, options: .regularExpression) != nil
    }
}

private struct ArbitraryDecimal: Equatable {
    let sign: Int
    let digits: String
    let scale: Int

    var isZero: Bool {
        digits == "0"
    }

    init(_ value: String) {
        var body = value
        let sign = body.first == "-" ? -1 : 1
        if sign < 0 {
            body.removeFirst()
        }

        let parts = body.split(
            separator: ".",
            maxSplits: 1,
            omittingEmptySubsequences: false
        )
        let integerPart = parts.first.map(String.init) ?? "0"
        let fractionPart = parts.count == 2 ? String(parts[1]) : ""
        self.init(
            sign: sign,
            digits: (integerPart.isEmpty ? "0" : integerPart) + fractionPart,
            scale: fractionPart.count
        )
    }

    init(sign: Int, digits: String, scale: Int) {
        var normalizedDigits = BigInteger.stripLeadingZeroes(digits)
        var normalizedScale = max(scale, 0)

        while
            normalizedScale > 0,
            normalizedDigits.count > 1,
            normalizedDigits.last == "0"
        {
            normalizedDigits.removeLast()
            normalizedScale -= 1
        }

        if normalizedDigits == "0" {
            self.sign = 1
            self.digits = "0"
            self.scale = 0
        } else {
            self.sign = sign < 0 ? -1 : 1
            self.digits = normalizedDigits
            self.scale = normalizedScale
        }
    }

    func adding(_ other: ArbitraryDecimal) -> ArbitraryDecimal {
        let commonScale = max(scale, other.scale)
        let left = digits + String(
            repeating: "0",
            count: commonScale - scale
        )
        let right = other.digits + String(
            repeating: "0",
            count: commonScale - other.scale
        )

        if sign == other.sign {
            return ArbitraryDecimal(
                sign: sign,
                digits: BigInteger.add(left, right),
                scale: commonScale
            )
        }

        switch BigInteger.compare(left, right) {
        case .orderedSame:
            return ArbitraryDecimal(sign: 1, digits: "0", scale: 0)
        case .orderedDescending:
            return ArbitraryDecimal(
                sign: sign,
                digits: BigInteger.subtract(left, right),
                scale: commonScale
            )
        case .orderedAscending:
            return ArbitraryDecimal(
                sign: other.sign,
                digits: BigInteger.subtract(right, left),
                scale: commonScale
            )
        }
    }

    func roundedString(fractionDigits: Int) -> String {
        let roundedInteger: String

        if scale <= fractionDigits {
            roundedInteger = digits + String(
                repeating: "0",
                count: fractionDigits - scale
            )
        } else {
            let removedCount = scale - fractionDigits
            let padded = String(
                repeating: "0",
                count: max(removedCount - digits.count, 0)
            ) + digits
            let splitIndex = max(padded.count - removedCount, 0)
            let split = padded.index(padded.startIndex, offsetBy: splitIndex)
            var whole = String(padded[..<split])
            let removed = String(padded[split...])
            whole = BigInteger.stripLeadingZeroes(whole)

            if removed.first.map({ $0 >= "5" }) == true {
                whole = BigInteger.add(whole, "1")
            }
            roundedInteger = whole
        }

        return Self.formatScaledInteger(
            roundedInteger,
            sign: sign,
            fractionDigits: fractionDigits
        )
    }

    static func dividing(
        _ numeratorValue: ArbitraryDecimal,
        by denominatorValue: ArbitraryDecimal,
        fractionDigits: Int
    ) -> String {
        let numerator = numeratorValue.digits + String(
            repeating: "0",
            count: denominatorValue.scale + fractionDigits
        )
        let denominator = denominatorValue.digits + String(
            repeating: "0",
            count: numeratorValue.scale
        )

        let division = BigInteger.divide(
            numerator,
            by: denominator
        )
        var quotient = division.quotient
        let remainder = division.remainder
        if BigInteger.compare(
            BigInteger.multiply(remainder, by: 2),
            denominator
        ) != .orderedAscending {
            quotient = BigInteger.add(quotient, "1")
        }

        return formatScaledInteger(
            quotient,
            sign: numeratorValue.sign * denominatorValue.sign,
            fractionDigits: fractionDigits
        )
    }

    private static func formatScaledInteger(
        _ rawDigits: String,
        sign: Int,
        fractionDigits: Int
    ) -> String {
        var digits = BigInteger.stripLeadingZeroes(rawDigits)
        guard digits != "0" else {
            return "0"
        }

        if fractionDigits > 0 {
            let minimumCount = fractionDigits + 1
            if digits.count < minimumCount {
                digits = String(
                    repeating: "0",
                    count: minimumCount - digits.count
                ) + digits
            }

            let decimalIndex = digits.index(
                digits.endIndex,
                offsetBy: -fractionDigits
            )
            digits.insert(".", at: decimalIndex)
            while digits.last == "0" {
                digits.removeLast()
            }
            if digits.last == "." {
                digits.removeLast()
            }
        }

        return sign < 0 ? "-\(digits)" : digits
    }
}

private enum BigInteger {
    static func stripLeadingZeroes(_ value: String) -> String {
        let stripped = value.drop(while: { $0 == "0" })
        return stripped.isEmpty ? "0" : String(stripped)
    }

    static func compare(_ left: String, _ right: String) -> ComparisonResult {
        let left = stripLeadingZeroes(left)
        let right = stripLeadingZeroes(right)
        if left.count != right.count {
            return left.count < right.count
                ? .orderedAscending
                : .orderedDescending
        }
        if left == right {
            return .orderedSame
        }
        return left < right ? .orderedAscending : .orderedDescending
    }

    static func add(_ left: String, _ right: String) -> String {
        let leftDigits = Array(left.utf8)
        let rightDigits = Array(right.utf8)
        var leftIndex = leftDigits.count - 1
        var rightIndex = rightDigits.count - 1
        var carry = 0
        var output: [UInt8] = []

        while leftIndex >= 0 || rightIndex >= 0 || carry > 0 {
            let leftValue = leftIndex >= 0
                ? Int(leftDigits[leftIndex] - 48)
                : 0
            let rightValue = rightIndex >= 0
                ? Int(rightDigits[rightIndex] - 48)
                : 0
            let sum = leftValue + rightValue + carry
            output.append(UInt8(sum % 10 + 48))
            carry = sum / 10
            leftIndex -= 1
            rightIndex -= 1
        }

        return String(bytes: output.reversed(), encoding: .utf8) ?? "0"
    }

    static func subtract(_ left: String, _ right: String) -> String {
        let leftDigits = Array(left.utf8)
        let rightDigits = Array(right.utf8)
        var leftIndex = leftDigits.count - 1
        var rightIndex = rightDigits.count - 1
        var borrow = 0
        var output: [UInt8] = []

        while leftIndex >= 0 {
            var value = Int(leftDigits[leftIndex] - 48) - borrow
            let rightValue = rightIndex >= 0
                ? Int(rightDigits[rightIndex] - 48)
                : 0
            if value < rightValue {
                value += 10
                borrow = 1
            } else {
                borrow = 0
            }
            output.append(UInt8(value - rightValue + 48))
            leftIndex -= 1
            rightIndex -= 1
        }

        let result = String(
            bytes: output.reversed(),
            encoding: .utf8
        ) ?? "0"
        return stripLeadingZeroes(result)
    }

    static func multiply(_ value: String, by digit: Int) -> String {
        guard digit > 0, value != "0" else {
            return "0"
        }

        let digits = Array(value.utf8)
        var index = digits.count - 1
        var carry = 0
        var output: [UInt8] = []

        while index >= 0 || carry > 0 {
            let current = index >= 0 ? Int(digits[index] - 48) : 0
            let product = current * digit + carry
            output.append(UInt8(product % 10 + 48))
            carry = product / 10
            index -= 1
        }

        return String(bytes: output.reversed(), encoding: .utf8) ?? "0"
    }

    static func divide(
        _ numerator: String,
        by denominator: String
    ) -> (quotient: String, remainder: String) {
        precondition(denominator != "0")
        var remainder = "0"
        var quotient: [UInt8] = []

        for digit in stripLeadingZeroes(numerator).utf8 {
            remainder = stripLeadingZeroes(
                (remainder == "0" ? "" : remainder)
                    + (String(bytes: [digit], encoding: .utf8) ?? "0")
            )

            var quotientDigit = 0
            if compare(remainder, denominator) != .orderedAscending {
                for candidate in stride(from: 9, through: 1, by: -1) {
                    let product = multiply(denominator, by: candidate)
                    if compare(product, remainder) != .orderedDescending {
                        quotientDigit = candidate
                        remainder = subtract(remainder, product)
                        break
                    }
                }
            }
            quotient.append(UInt8(quotientDigit + 48))
        }

        return (
            stripLeadingZeroes(
                String(bytes: quotient, encoding: .utf8) ?? "0"
            ),
            stripLeadingZeroes(remainder)
        )
    }
}

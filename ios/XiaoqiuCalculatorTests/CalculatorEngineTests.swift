import XCTest
@testable import XiaoqiuCalculator

final class CalculatorEngineTests: XCTestCase {
    func testDefaultDivisor() throws {
        XCTAssertEqual(
            try CalculatorEngine.calculate(aText: "592", bText: "3325"),
            CalculationResult(total: "3917", divided: "7")
        )
    }

    func testCustomDecimalDivisor() throws {
        XCTAssertEqual(
            try CalculatorEngine.calculate(
                aText: "1.25",
                bText: "5",
                divisorText: "2.5"
            ),
            CalculationResult(total: "6.25", divided: "2")
        )
    }

    func testNegativeValues() throws {
        XCTAssertEqual(
            try CalculatorEngine.calculate(
                aText: "-10.5",
                bText: "5",
                divisorText: "-2"
            ),
            CalculationResult(total: "-5.5", divided: "-2.5")
        )
    }

    func testRoundHalfUp() throws {
        XCTAssertEqual(
            try CalculatorEngine.calculate(
                aText: "0",
                bText: "1.005",
                divisorText: "1"
            ),
            CalculationResult(total: "1.01", divided: "1.01")
        )
    }

    func testZeroDivisorIsRejected() {
        XCTAssertThrowsError(
            try CalculatorEngine.calculate(
                aText: "1",
                bText: "5",
                divisorText: "-0.0"
            )
        ) { error in
            XCTAssertEqual(
                error as? CalculatorIssue,
                .input(message: "除数不能为 0。", field: .divisor)
            )
        }
    }

    func testOverlongInputIsRejected() {
        XCTAssertThrowsError(
            try CalculatorEngine.calculate(
                aText: String(
                    repeating: "9",
                    count: CalculatorEngine.maxInputLength + 1
                ),
                bText: "1"
            )
        )
    }

    func testHugeResultIsRejected() {
        let tinyDivisor = "0." + String(repeating: "0", count: 60) + "1"
        XCTAssertThrowsError(
            try CalculatorEngine.calculate(
                aText: "1",
                bText: String(repeating: "9", count: 18),
                divisorText: tinyDivisor
            )
        )
    }
}

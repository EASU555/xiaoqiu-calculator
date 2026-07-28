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

    func testMultiplyAddWithDefaultAndCustomCoefficient() throws {
        XCTAssertEqual(
            try CalculatorEngine.calculateMultiplyAdd(
                coefficientText: "475",
                multiplierText: "2",
                addendText: "25"
            ),
            "975"
        )
        XCTAssertEqual(
            try CalculatorEngine.calculateMultiplyAdd(
                coefficientText: "1.5",
                multiplierText: "4",
                addendText: "2"
            ),
            "8"
        )
        XCTAssertEqual(
            try CalculatorEngine.calculateMultiplyAdd(
                coefficientText: "-3",
                multiplierText: "2",
                addendText: "1"
            ),
            "-5"
        )
    }

    func testMultiplyAddRoundsHalfUp() throws {
        XCTAssertEqual(
            try CalculatorEngine.calculateMultiplyAdd(
                coefficientText: "1.005",
                multiplierText: "1",
                addendText: "0"
            ),
            "1.01"
        )
    }

    func testBasicOperations() throws {
        XCTAssertEqual(
            try CalculatorEngine.calculateBasic(
                fixedValueText: "475",
                operationValueText: "25",
                operation: .add
            ),
            "500"
        )
        XCTAssertEqual(
            try CalculatorEngine.calculateBasic(
                fixedValueText: "475",
                operationValueText: "25",
                operation: .subtract
            ),
            "450"
        )
        XCTAssertEqual(
            try CalculatorEngine.calculateBasic(
                fixedValueText: "12",
                operationValueText: "2.5",
                operation: .multiply
            ),
            "30"
        )
        XCTAssertEqual(
            try CalculatorEngine.calculateBasic(
                fixedValueText: "10",
                operationValueText: "4",
                operation: .divide
            ),
            "2.5"
        )
    }

    func testBasicOperationSupportsNegativeValues() throws {
        XCTAssertEqual(
            try CalculatorEngine.calculateBasic(
                fixedValueText: "-10",
                operationValueText: "2.5",
                operation: .add
            ),
            "-7.5"
        )
        XCTAssertEqual(
            try CalculatorEngine.calculateBasic(
                fixedValueText: "-10",
                operationValueText: "-2",
                operation: .multiply
            ),
            "20"
        )
    }

    func testBasicDivisionByZeroIsRejected() {
        XCTAssertThrowsError(
            try CalculatorEngine.calculateBasic(
                fixedValueText: "475",
                operationValueText: "-0.0",
                operation: .divide
            )
        ) { error in
            XCTAssertEqual(
                error as? CalculatorIssue,
                .input(
                    message: "进行除法时，运算值不能为 0。",
                    field: .operationValue
                )
            )
        }
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

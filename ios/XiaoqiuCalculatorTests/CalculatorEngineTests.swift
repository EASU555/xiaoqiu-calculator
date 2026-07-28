import Foundation
import XCTest
@testable import XiaoqiuCalculator

final class CalculatorEngineTests: XCTestCase {
    func testKeypadHeightAdaptsToPhoneAndTabletViewports() {
        XCTAssertEqual(
            CalculatorLayoutMetrics.keypadKeyHeight(
                availableHeight: 650,
                availableWidth: 357,
                useWideLayout: false
            ),
            56.425,
            accuracy: 0.001
        )
        XCTAssertEqual(
            CalculatorLayoutMetrics.keypadKeyHeight(
                availableHeight: 800,
                availableWidth: 357,
                useWideLayout: false
            ),
            56.425,
            accuracy: 0.001
        )
        XCTAssertEqual(
            CalculatorLayoutMetrics.keypadKeyHeight(
                availableHeight: 800,
                availableWidth: 960,
                useWideLayout: true
            ),
            52,
            accuracy: 0.001
        )
        XCTAssertEqual(
            CalculatorLayoutMetrics.keypadKeyHeight(
                availableHeight: 1_200,
                availableWidth: 960,
                useWideLayout: true
            ),
            84,
            accuracy: 0.001
        )
        XCTAssertEqual(
            CalculatorLayoutMetrics.keypadKeyHeight(
                availableHeight: 720,
                availableWidth: 1_300,
                useWideLayout: true
            ),
            52,
            accuracy: 0.001
        )
    }

    func testKeypadUsesRemainingPageHeightInsteadOfWholeScreenHeight() {
        XCTAssertEqual(
            CalculatorLayoutMetrics.keypadKeyHeight(
                availableHeight: 960,
                availableWidth: 960,
                useWideLayout: true
            ),
            72.5,
            accuracy: 0.001
        )
        XCTAssertEqual(
            CalculatorLayoutMetrics.keypadKeyHeight(
                availableHeight: 960,
                availableWidth: 960,
                useWideLayout: true,
                stackedReservedHeight: CalculatorLayoutMetrics
                    .basicStackedReservedHeight
            ),
            84,
            accuracy: 0.001
        )
    }

    func testSideBySideKeypadUsesLandscapeHeightAndWidth() {
        XCTAssertEqual(
            CalculatorLayoutMetrics.keypadKeyHeight(
                availableHeight: 720,
                availableWidth: 560,
                useWideLayout: true,
                isSideBySide: true
            ),
            76.26,
            accuracy: 0.001
        )
        XCTAssertTrue(
            CalculatorLayoutMetrics.usesSideBySidePageLayout(
                availableHeight: 720,
                availableWidth: 1_300,
                useWideLayout: true
            )
        )
        XCTAssertFalse(
            CalculatorLayoutMetrics.usesSideBySidePageLayout(
                availableHeight: 1_100,
                availableWidth: 960,
                useWideLayout: true
            )
        )
    }

    func testSmallIPadPortraitKeypadFitsWithinAvailableHeight() {
        let availableHeight: CGFloat = 878
        let keyHeight = CalculatorLayoutMetrics.keypadKeyHeight(
            availableHeight: availableHeight,
            availableWidth: 746,
            useWideLayout: true
        )

        XCTAssertLessThanOrEqual(
            CalculatorLayoutMetrics.calculatorStackedReservedHeight
                + keyHeight * 4,
            availableHeight
        )
        XCTAssertGreaterThanOrEqual(keyHeight, 52)
    }

    func testKeypadGridStaysProportionalAcrossPhoneAndTabletWidths() {
        XCTAssertEqual(
            CalculatorLayoutMetrics.keypadGridWidth(
                availableWidth: 357,
                useWideLayout: false
            ),
            329,
            accuracy: 0.001
        )
        XCTAssertEqual(
            CalculatorLayoutMetrics.keypadGridWidth(
                availableWidth: 960,
                useWideLayout: true
            ),
            720,
            accuracy: 0.001
        )
        XCTAssertEqual(
            CalculatorLayoutMetrics.keypadGridWidth(
                availableWidth: 1_300,
                useWideLayout: true
            ),
            720,
            accuracy: 0.001
        )
    }

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

    @MainActor
    func testKeypadEditsSelectedFieldWithoutSystemKeyboard() throws {
        let suiteName = "CalculatorKeypadTests.\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suiteName))
        defer { defaults.removePersistentDomain(forName: suiteName) }
        let model = CalculatorViewModel(userDefaults: defaults)

        XCTAssertTrue(model.applyKeypadInput(.digit("1"), to: .a))
        XCTAssertTrue(model.applyKeypadInput(.digit("2"), to: .a))
        XCTAssertTrue(model.applyKeypadInput(.decimal, to: .a))
        XCTAssertTrue(model.applyKeypadInput(.digit("5"), to: .a))
        XCTAssertEqual(model.text(for: .a), "12.5")

        XCTAssertFalse(model.applyKeypadInput(.decimal, to: .a))
        XCTAssertTrue(model.applyKeypadInput(.toggleSign, to: .a))
        XCTAssertEqual(model.text(for: .a), "-12.5")

        XCTAssertTrue(model.applyKeypadInput(.delete, to: .a))
        XCTAssertEqual(model.text(for: .a), "-12.")

        XCTAssertTrue(model.applyKeypadInput(.clear, to: .a))
        XCTAssertEqual(model.text(for: .a), "")
    }

    @MainActor
    func testKeypadCanReplaceDefaultsAndCompleteCalculation() throws {
        let suiteName = "CalculatorKeypadTests.\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suiteName))
        defer { defaults.removePersistentDomain(forName: suiteName) }
        let model = CalculatorViewModel(userDefaults: defaults)

        XCTAssertTrue(
            model.applyKeypadInput(
                .digit("2"),
                to: .divisor,
                replacingExisting: true
            )
        )
        XCTAssertEqual(model.text(for: .divisor), "2")

        XCTAssertTrue(model.applyKeypadInput(.digit("1"), to: .a))
        XCTAssertTrue(model.applyKeypadInput(.digit("5"), to: .a))
        XCTAssertTrue(model.applyKeypadInput(.digit("5"), to: .b))
        model.calculate()

        XCTAssertEqual(model.totalResult, "20")
        XCTAssertEqual(model.dividedResult, "2.5")
        XCTAssertEqual(model.visibleHistoryEntries.count, 1)
    }

    @MainActor
    func testHistoryRecordsOnlyExplicitSuccessfulCalculations() throws {
        let suiteName = "CalculatorHistoryTests.\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suiteName))
        defer { defaults.removePersistentDomain(forName: suiteName) }
        let model = CalculatorViewModel(userDefaults: defaults)

        model.update("592", for: .a)
        model.update("3325", for: .b)
        XCTAssertTrue(model.visibleHistoryEntries.isEmpty)

        model.calculate()

        XCTAssertEqual(model.visibleHistoryEntries.count, 1)
        XCTAssertEqual(
            model.visibleHistoryEntries.first?.expression,
            "A 592 + B 3325"
        )
        XCTAssertEqual(
            model.visibleHistoryEntries.first?.primaryResult,
            "总数 3917"
        )
        XCTAssertEqual(
            model.visibleHistoryEntries.first?.secondaryResult,
            "B 3325 ÷ 475 = 7"
        )
    }

    @MainActor
    func testHistoryPersistsAndCanBeCleared() throws {
        let suiteName = "CalculatorHistoryTests.\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suiteName))
        defer { defaults.removePersistentDomain(forName: suiteName) }

        let firstModel = CalculatorViewModel(userDefaults: defaults)
        firstModel.page = .basic
        firstModel.update("25", for: .operationValue)
        firstModel.calculate()

        let restoredModel = CalculatorViewModel(userDefaults: defaults)
        restoredModel.page = .basic
        XCTAssertEqual(restoredModel.visibleHistoryEntries.count, 1)
        XCTAssertEqual(
            restoredModel.visibleHistoryEntries.first?.expression,
            "475 + 25"
        )
        XCTAssertEqual(
            restoredModel.visibleHistoryEntries.first?.primaryResult,
            "500"
        )

        restoredModel.clearHistory()
        XCTAssertTrue(restoredModel.visibleHistoryEntries.isEmpty)

        let clearedModel = CalculatorViewModel(userDefaults: defaults)
        clearedModel.page = .basic
        XCTAssertTrue(clearedModel.visibleHistoryEntries.isEmpty)
    }
}

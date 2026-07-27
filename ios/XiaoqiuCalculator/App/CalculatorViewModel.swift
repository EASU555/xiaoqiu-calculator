import Combine
import Foundation

@MainActor
final class CalculatorViewModel: ObservableObject {
    enum StatusTone {
        case neutral
        case success
        case error
    }

    @Published private(set) var aText = ""
    @Published private(set) var bText = ""
    @Published private(set) var divisorText = CalculatorEngine.defaultDivisor
    @Published private(set) var totalResult = "—"
    @Published private(set) var dividedResult = "—"
    @Published private(set) var status =
        "输入 A、B，可按需修改除数。"
    @Published private(set) var statusTone: StatusTone = .neutral
    @Published private(set) var invalidField: CalculatorField?

    var divideFormula: String {
        let trimmed = divisorText.trimmingCharacters(
            in: .whitespacesAndNewlines
        )
        return "B ÷ \(trimmed.isEmpty ? "—" : trimmed)"
    }

    func text(for field: CalculatorField) -> String {
        switch field {
        case .a:
            return aText
        case .b:
            return bText
        case .divisor:
            return divisorText
        }
    }

    func update(_ value: String, for field: CalculatorField) {
        guard CalculatorEngine.isEditingTextValid(value) else {
            return
        }

        switch field {
        case .a:
            guard value != aText else { return }
            aText = value
        case .b:
            guard value != bText else { return }
            bText = value
        case .divisor:
            guard value != divisorText else { return }
            divisorText = value
        }
        resetForInputChange()
    }

    func calculate() {
        do {
            let result = try CalculatorEngine.calculate(
                aText: aText,
                bText: bText,
                divisorText: divisorText
            )
            invalidField = nil
            totalResult = result.total
            dividedResult = result.divided
            statusTone = .success
            status =
                "计算完成，已使用除数 \(divisorText)，结果保留 2 位小数。"
        } catch let issue as CalculatorIssue {
            invalidField = issue.field
            totalResult = "—"
            dividedResult = "—"
            statusTone = .error
            status = issue.message
        } catch {
            invalidField = nil
            totalResult = "—"
            dividedResult = "—"
            statusTone = .error
            status = "计算失败，请检查输入后重试。"
        }
    }

    func clear() {
        aText = ""
        bText = ""
        if !CalculatorEngine.isValidNonZeroDivisor(divisorText) {
            divisorText = CalculatorEngine.defaultDivisor
        }

        invalidField = nil
        totalResult = "—"
        dividedResult = "—"
        statusTone = .neutral
        status = "已清空 A 和 B；除数保持为 \(divisorText)。"
    }

    private func resetForInputChange() {
        invalidField = nil
        totalResult = "—"
        dividedResult = "—"
        statusTone = .neutral
        status = "输入 A、B，可按需修改除数。"
    }
}

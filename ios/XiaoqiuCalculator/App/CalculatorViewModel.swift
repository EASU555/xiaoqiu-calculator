import Combine
import Foundation

enum AppPage: String, CaseIterable, Identifiable, Hashable {
    case calculator = "计算器"
    case basic = "基础运算"
    case counter = "快捷计算"

    var id: String { rawValue }
}

enum CalculatorMode: String, CaseIterable, Identifiable, Hashable {
    case standard = "双结果"
    case multiplyAdd = "乘加计算"

    var id: String { rawValue }
}

enum CalculationHistoryKind: String, Codable {
    case standard
    case multiplyAdd
    case basic
}

struct CalculationHistoryEntry: Identifiable, Codable, Equatable {
    let id: UUID
    let kind: CalculationHistoryKind
    let expression: String
    let primaryResult: String
    let secondaryResult: String?
    let createdAt: Date
}

@MainActor
final class CalculatorViewModel: ObservableObject {
    enum StatusTone {
        case neutral
        case success
        case error
    }

    @Published var page: AppPage = .calculator {
        didSet { restoreStatus() }
    }
    @Published var mode: CalculatorMode = .standard {
        didSet { restoreStatus() }
    }
    @Published var basicOperation: BasicOperation = .add {
        didSet {
            refreshBasicLive()
            if page == .basic {
                restoreStatus()
            }
        }
    }

    @Published private(set) var aText = ""
    @Published private(set) var bText = ""
    @Published private(set) var divisorText = CalculatorEngine.defaultDivisor
    @Published private(set) var totalResult = "—"
    @Published private(set) var dividedResult = "—"

    @Published private(set) var coefficientText =
        CalculatorEngine.defaultCoefficient
    @Published private(set) var multiplierText = ""
    @Published private(set) var addendText = ""
    @Published private(set) var multiplyAddResult = "—"

    @Published private(set) var fixedValueText =
        CalculatorEngine.defaultFixedValue
    @Published private(set) var operationValueText = ""
    @Published private(set) var basicResult = "—"

    @Published private(set) var counter = 0
    @Published private(set) var status =
        "输入 A、B，结果会实时更新；可按需修改除数。"
    @Published private(set) var statusTone: StatusTone = .neutral
    @Published private(set) var invalidField: CalculatorField?
    @Published private(set) var historyEntries: [CalculationHistoryEntry] = []

    private let historyDefaultsKey = "xiaoqiu.calculationHistory.v1"
    private let historyLimit = 50
    private let userDefaults: UserDefaults
    private var statusStore: [String: (String, StatusTone)] = [
        "standard": (
            "输入 A、B，结果会实时更新；可按需修改除数。",
            .neutral
        ),
        "multiplyAdd": (
            "系数默认 475；输入完整后结果会实时更新。",
            .neutral
        ),
        "basic": (
            "固定值默认 475；选择运算符后结果会实时更新。",
            .neutral
        ),
        "counter": (
            "点按 +1 开始计数；iPad 外接键盘也可按空格。",
            .neutral
        )
    ]

    init(userDefaults: UserDefaults = .standard) {
        self.userDefaults = userDefaults
        loadHistory()
    }

    var subtitle: String {
        switch page {
        case .calculator:
            return mode == .standard
                ? "一次输入，同时得到总数与除法结果"
                : "系数 × 乘数 + 加数"
        case .basic:
            return "固定值与运算值的四则运算"
        case .counter:
            return "触屏快速加一，随时清零"
        }
    }

    var divideFormula: String {
        "B ÷ \(preview(divisorText))"
    }

    var multiplyAddFormula: String {
        "\(preview(coefficientText)) × \(preview(multiplierText))"
            + " + \(preview(addendText)) ="
    }

    var basicFormula: String {
        "\(preview(fixedValueText)) \(basicOperation.rawValue)"
            + " \(preview(operationValueText)) ="
    }

    var visibleHistoryEntries: [CalculationHistoryEntry] {
        historyEntries.filter { $0.kind == currentHistoryKind }
    }

    func text(for field: CalculatorField) -> String {
        switch field {
        case .a:
            return aText
        case .b:
            return bText
        case .divisor:
            return divisorText
        case .coefficient:
            return coefficientText
        case .multiplier:
            return multiplierText
        case .addend:
            return addendText
        case .fixedValue:
            return fixedValueText
        case .operationValue:
            return operationValueText
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
            refreshStandardLive()
        case .b:
            guard value != bText else { return }
            bText = value
            refreshStandardLive()
        case .divisor:
            guard value != divisorText else { return }
            divisorText = value
            refreshStandardLive()
        case .coefficient:
            guard value != coefficientText else { return }
            coefficientText = value
            refreshMultiplyAddLive()
        case .multiplier:
            guard value != multiplierText else { return }
            multiplierText = value
            refreshMultiplyAddLive()
        case .addend:
            guard value != addendText else { return }
            addendText = value
            refreshMultiplyAddLive()
        case .fixedValue:
            guard value != fixedValueText else { return }
            fixedValueText = value
            refreshBasicLive()
        case .operationValue:
            guard value != operationValueText else { return }
            operationValueText = value
            refreshBasicLive()
        }
    }

    func calculate() {
        switch page {
        case .calculator:
            if mode == .standard {
                calculateStandard(explicit: true)
            } else {
                calculateMultiplyAdd(explicit: true)
            }
        case .basic:
            calculateBasic(explicit: true)
        case .counter:
            incrementCounter()
        }
    }

    func clear() {
        switch page {
        case .calculator:
            mode == .standard ? clearStandard() : clearMultiplyAdd()
        case .basic:
            clearBasic()
        case .counter:
            resetCounter()
        }
    }

    func clearHistory() {
        let kind = currentHistoryKind
        guard historyEntries.contains(where: { $0.kind == kind }) else {
            return
        }
        historyEntries.removeAll { $0.kind == kind }
        saveHistory()
        setStatus(
            "本页历史记录已清空。",
            tone: .neutral,
            key: statusKey
        )
    }

    func incrementCounter() {
        counter += 1
        setStatus(
            "当前计数为 \(counter)。",
            tone: .success,
            key: "counter"
        )
    }

    func resetCounter() {
        counter = 0
        setStatus(
            "计数已清零。",
            tone: .neutral,
            key: "counter"
        )
    }

    private func refreshStandardLive() {
        invalidField = nil
        calculateStandard(explicit: false)
    }

    private func refreshMultiplyAddLive() {
        invalidField = nil
        calculateMultiplyAdd(explicit: false)
    }

    private func refreshBasicLive() {
        invalidField = nil
        calculateBasic(explicit: false)
    }

    private func calculateStandard(explicit: Bool) {
        do {
            let result = try CalculatorEngine.calculate(
                aText: aText,
                bText: bText,
                divisorText: divisorText
            )
            invalidField = nil
            totalResult = result.total
            dividedResult = result.divided
            if explicit {
                appendHistory(
                    CalculationHistoryEntry(
                        id: UUID(),
                        kind: .standard,
                        expression: "A \(aText) + B \(bText)",
                        primaryResult: "总数 \(result.total)",
                        secondaryResult:
                            "B \(bText) ÷ \(divisorText) = \(result.divided)",
                        createdAt: Date()
                    )
                )
            }
            setStatus(
                explicit ? "计算完成，已使用除数 \(divisorText)。" : "双结果已实时更新。",
                tone: .success,
                key: "standard"
            )
        } catch let issue as CalculatorIssue {
            totalResult = "—"
            dividedResult = "—"
            handle(issue, explicit: explicit, key: "standard")
        } catch {
            failUnknown(key: "standard")
        }
    }

    private func calculateMultiplyAdd(explicit: Bool) {
        do {
            let result = try CalculatorEngine.calculateMultiplyAdd(
                coefficientText: coefficientText,
                multiplierText: multiplierText,
                addendText: addendText
            )
            multiplyAddResult = result
            invalidField = nil
            if explicit {
                appendHistory(
                    CalculationHistoryEntry(
                        id: UUID(),
                        kind: .multiplyAdd,
                        expression:
                            "\(coefficientText) × \(multiplierText) + \(addendText)",
                        primaryResult: result,
                        secondaryResult: nil,
                        createdAt: Date()
                    )
                )
            }
            setStatus(
                explicit ? "乘加计算完成。" : "乘加结果已实时更新。",
                tone: .success,
                key: "multiplyAdd"
            )
        } catch let issue as CalculatorIssue {
            multiplyAddResult = "—"
            handle(issue, explicit: explicit, key: "multiplyAdd")
        } catch {
            failUnknown(key: "multiplyAdd")
        }
    }

    private func calculateBasic(explicit: Bool) {
        do {
            let result = try CalculatorEngine.calculateBasic(
                fixedValueText: fixedValueText,
                operationValueText: operationValueText,
                operation: basicOperation
            )
            basicResult = result
            invalidField = nil
            if explicit {
                appendHistory(
                    CalculationHistoryEntry(
                        id: UUID(),
                        kind: .basic,
                        expression:
                            "\(fixedValueText) \(basicOperation.rawValue) \(operationValueText)",
                        primaryResult: result,
                        secondaryResult: nil,
                        createdAt: Date()
                    )
                )
            }
            setStatus(
                explicit ? "基础运算完成。" : "基础运算结果已实时更新。",
                tone: .success,
                key: "basic"
            )
        } catch let issue as CalculatorIssue {
            basicResult = "—"
            handle(issue, explicit: explicit, key: "basic")
        } catch {
            failUnknown(key: "basic")
        }
    }

    private func clearStandard() {
        aText = ""
        bText = ""
        if !CalculatorEngine.isValidNonZeroDivisor(divisorText) {
            divisorText = CalculatorEngine.defaultDivisor
        }
        totalResult = "—"
        dividedResult = "—"
        invalidField = nil
        setStatus(
            "已清空 A 和 B；除数保持为 \(divisorText)。",
            tone: .neutral,
            key: "standard"
        )
    }

    private func clearMultiplyAdd() {
        multiplierText = ""
        addendText = ""
        if !CalculatorEngine.isValidNumber(
            coefficientText,
            field: .coefficient
        ) {
            coefficientText = CalculatorEngine.defaultCoefficient
        }
        multiplyAddResult = "—"
        invalidField = nil
        setStatus(
            "已清空乘数和加数；系数保持为 \(coefficientText)。",
            tone: .neutral,
            key: "multiplyAdd"
        )
    }

    private func clearBasic() {
        operationValueText = ""
        if !CalculatorEngine.isValidNumber(
            fixedValueText,
            field: .fixedValue
        ) {
            fixedValueText = CalculatorEngine.defaultFixedValue
        }
        basicResult = "—"
        invalidField = nil
        setStatus(
            "已清空运算值；固定值保持为 \(fixedValueText)。",
            tone: .neutral,
            key: "basic"
        )
    }

    private func handle(
        _ issue: CalculatorIssue,
        explicit: Bool,
        key: String
    ) {
        if explicit {
            invalidField = issue.field
            setStatus(issue.message, tone: .error, key: key)
        } else {
            invalidField = nil
            let message: String
            switch key {
            case "multiplyAdd":
                message = "系数默认 475；输入完整后结果会实时更新。"
            case "basic":
                message = "固定值默认 475；选择运算符后结果会实时更新。"
            default:
                message = "输入 A、B，结果会实时更新；可按需修改除数。"
            }
            setStatus(message, tone: .neutral, key: key)
        }
    }

    private func failUnknown(key: String) {
        invalidField = nil
        setStatus(
            "计算失败，请检查输入后重试。",
            tone: .error,
            key: key
        )
    }

    private func setStatus(
        _ message: String,
        tone: StatusTone,
        key: String
    ) {
        statusStore[key] = (message, tone)
        if statusKey == key {
            status = message
            statusTone = tone
        }
    }

    private func restoreStatus() {
        let stored = statusStore[statusKey] ?? ("可以开始了。", .neutral)
        status = stored.0
        statusTone = stored.1
        invalidField = nil
    }

    private var statusKey: String {
        switch page {
        case .calculator:
            return mode == .standard ? "standard" : "multiplyAdd"
        case .basic:
            return "basic"
        case .counter:
            return "counter"
        }
    }

    private var currentHistoryKind: CalculationHistoryKind {
        switch page {
        case .calculator:
            return mode == .standard ? .standard : .multiplyAdd
        case .basic:
            return .basic
        case .counter:
            return .standard
        }
    }

    private func appendHistory(_ entry: CalculationHistoryEntry) {
        historyEntries.insert(entry, at: 0)
        if historyEntries.count > historyLimit {
            historyEntries.removeLast(historyEntries.count - historyLimit)
        }
        saveHistory()
    }

    private func loadHistory() {
        guard
            let data = userDefaults.data(forKey: historyDefaultsKey),
            let stored = try? JSONDecoder().decode(
                [CalculationHistoryEntry].self,
                from: data
            )
        else {
            return
        }
        historyEntries = Array(stored.prefix(historyLimit))
    }

    private func saveHistory() {
        guard let data = try? JSONEncoder().encode(historyEntries) else {
            return
        }
        userDefaults.set(data, forKey: historyDefaultsKey)
    }

    private func preview(_ text: String) -> String {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return "—" }
        return trimmed.count > 10
            ? String(trimmed.prefix(9)) + "…"
            : trimmed
    }
}

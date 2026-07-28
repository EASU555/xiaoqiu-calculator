import SwiftUI
import UIKit

struct CalculatorView: View {
    @StateObject private var model = CalculatorViewModel()
    @State private var showHistoryClearConfirmation = false
    @State private var activeField: CalculatorField?
    @State private var replaceActiveValue = false
    @State private var isHistoryExpanded = false
    @Environment(\.accessibilityReduceTransparency)
    private var reduceTransparency

    private let pageMaxWidth: CGFloat = 1_100

    var body: some View {
        TabView(selection: $model.page) {
            NavigationStack {
                pageCanvas { useWideLayout, minHeight in
                    calculatorPage(
                        useWideLayout: useWideLayout,
                        minHeight: minHeight
                    )
                }
                .navigationTitle("计算器")
                .navigationBarTitleDisplayMode(.large)
                .toolbar {
                    navigationToolbar(for: .calculator)
                }
            }
            .tabItem {
                Label("计算器", systemImage: "function")
            }
            .tag(AppPage.calculator)

            NavigationStack {
                pageCanvas { useWideLayout, minHeight in
                    basicPage(
                        useWideLayout: useWideLayout,
                        minHeight: minHeight
                    )
                }
                .navigationTitle("基础运算")
                .navigationBarTitleDisplayMode(.large)
                .toolbar {
                    navigationToolbar(for: .basic)
                }
            }
            .tabItem {
                Label("基础运算", systemImage: "plus.forwardslash.minus")
            }
            .tag(AppPage.basic)

            NavigationStack {
                pageCanvas { useWideLayout, minHeight in
                    counterPage(
                        useWideLayout: useWideLayout,
                        minHeight: minHeight
                    )
                }
                .navigationTitle("快捷计算")
                .navigationBarTitleDisplayMode(.large)
                .toolbar {
                    navigationToolbar(for: .counter)
                }
            }
            .tabItem {
                Label("快捷计算", systemImage: "plus.circle")
            }
            .tag(AppPage.counter)
        }
        .tint(Color.appAccent)
        .animation(
            .spring(response: 0.3, dampingFraction: 0.84),
            value: model.mode
        )
        .confirmationDialog(
            "清空当前模式的历史记录？",
            isPresented: $showHistoryClearConfirmation,
            titleVisibility: .visible
        ) {
            Button("清空历史记录", role: .destructive) {
                withAnimation(.easeOut(duration: 0.18)) {
                    model.clearHistory()
                }
            }
            Button("取消", role: .cancel) {}
        } message: {
            Text("清空后无法恢复，其他计算模式的记录不会受影响。")
        }
        .onChange(of: model.invalidField) { field in
            if let field {
                activeField = field
                replaceActiveValue = false
            }
        }
        .onChange(of: model.page) { _ in
            resetActiveField()
            isHistoryExpanded = false
        }
        .onChange(of: model.mode) { _ in
            resetActiveField()
            isHistoryExpanded = false
        }
        .onAppear {
            resetActiveField()
        }
    }

    @ViewBuilder
    private func pageCanvas<Content: View>(
        @ViewBuilder content: @escaping (Bool, CGFloat) -> Content
    ) -> some View {
        GeometryReader { geometry in
            let useWideLayout = geometry.size.width >= 760
            let horizontalPadding: CGFloat = useWideLayout ? 32 : 18
            let verticalPadding: CGFloat = useWideLayout ? 24 : 16
            let minHeight = max(
                0,
                geometry.size.height - verticalPadding * 2
            )

            ZStack {
                CalculatorBackdrop(
                    reduceTransparency: reduceTransparency
                )

                ScrollView {
                    content(useWideLayout, minHeight)
                        .frame(maxWidth: pageMaxWidth)
                        .frame(
                            minHeight: minHeight,
                            alignment: .top
                        )
                        .padding(.horizontal, horizontalPadding)
                        .padding(.vertical, verticalPadding)
                        .frame(maxWidth: .infinity)
                }
            }
        }
    }

    @ToolbarContentBuilder
    private func navigationToolbar(
        for page: AppPage
    ) -> some ToolbarContent {
        ToolbarItem(placement: .navigationBarTrailing) {
            Button {
                model.clear()
            } label: {
                Label(
                    page == .counter ? "清零" : "清空输入",
                    systemImage: page == .counter
                        ? "arrow.counterclockwise"
                        : "eraser"
                )
            }
            .accessibilityHint(
                page == .counter
                    ? "将当前计数归零"
                    : "清空当前页面的输入和结果"
            )
        }
    }

    private func calculatorPage(
        useWideLayout: Bool,
        minHeight: CGFloat
    ) -> some View {
        VStack(spacing: useWideLayout ? 20 : 16) {
            modePicker
                .frame(maxWidth: useWideLayout ? 460 : .infinity)

            historyPanel(useWideLayout: useWideLayout)

            if model.mode == .standard {
                standardWorkspace(useWideLayout: useWideLayout)
            } else {
                multiplyAddWorkspace(useWideLayout: useWideLayout)
            }

            inlineStatus
            numericKeypad(useWideLayout: useWideLayout)
        }
        .frame(
            maxWidth: .infinity,
            minHeight: minHeight,
            alignment: .top
        )
    }

    private var modePicker: some View {
        Picker("计算模式", selection: $model.mode) {
            ForEach(CalculatorMode.allCases) { mode in
                Text(mode.rawValue)
                    .tag(mode)
            }
        }
        .pickerStyle(.segmented)
        .accessibilityHint("在双结果和乘加计算之间切换")
    }

    @ViewBuilder
    private func standardWorkspace(useWideLayout: Bool) -> some View {
        if useWideLayout {
            HStack(alignment: .top, spacing: 16) {
                standardInputPanel
                standardResults
            }
        } else {
            VStack(spacing: 14) {
                standardInputPanel
                standardResults
            }
        }
    }

    private var standardInputPanel: some View {
        VStack(alignment: .leading, spacing: 18) {
            sectionHeader(
                title: "输入数据",
                detail: "输入后实时计算"
            )

            VStack(spacing: 14) {
                numericInput(
                    field: .divisor,
                    title: "可调除数",
                    placeholder: CalculatorEngine.defaultDivisor
                )
                numericInput(
                    field: .a,
                    title: "A 数据",
                    placeholder: "120.5"
                )
                numericInput(
                    field: .b,
                    title: "B 数据",
                    placeholder: "475"
                )
            }
        }
        .frame(maxWidth: .infinity, alignment: .topLeading)
        .contentCard()
    }

    private var standardResults: some View {
        VStack(alignment: .leading, spacing: 14) {
            sectionHeader(
                title: "计算结果",
                detail: "最多保留 2 位小数"
            )

            VStack(spacing: 12) {
                resultCard(
                    title: "总数",
                    formula: "A + B",
                    value: model.totalResult,
                    featured: true
                )
                resultCard(
                    title: "单独结果",
                    formula: model.divideFormula,
                    value: model.dividedResult,
                    featured: false
                )
            }
        }
        .frame(maxWidth: .infinity, alignment: .topLeading)
        .contentCard()
    }

    @ViewBuilder
    private func multiplyAddWorkspace(useWideLayout: Bool) -> some View {
        if useWideLayout {
            HStack(alignment: .top, spacing: 16) {
                multiplyAddInputPanel
                multiplyAddResults
            }
        } else {
            VStack(spacing: 14) {
                multiplyAddInputPanel
                multiplyAddResults
            }
        }
    }

    private var multiplyAddInputPanel: some View {
        VStack(alignment: .leading, spacing: 18) {
            sectionHeader(
                title: "输入数据",
                detail: "系数默认 475"
            )

            VStack(spacing: 14) {
                numericInput(
                    field: .coefficient,
                    title: "系数",
                    placeholder: CalculatorEngine.defaultCoefficient
                )
                numericInput(
                    field: .multiplier,
                    title: "乘数",
                    placeholder: "2"
                )
                numericInput(
                    field: .addend,
                    title: "加数",
                    placeholder: "25"
                )
            }
        }
        .frame(maxWidth: .infinity, alignment: .topLeading)
        .contentCard()
    }

    private var multiplyAddResults: some View {
        VStack(alignment: .leading, spacing: 14) {
            sectionHeader(
                title: "乘加结果",
                detail: "实时更新"
            )

            resultCard(
                title: "计算结果",
                formula: model.multiplyAddFormula,
                value: model.multiplyAddResult,
                featured: true
            )
        }
        .frame(maxWidth: .infinity, alignment: .topLeading)
        .contentCard()
    }

    private func basicPage(
        useWideLayout: Bool,
        minHeight: CGFloat
    ) -> some View {
        VStack(spacing: useWideLayout ? 20 : 16) {
            historyPanel(useWideLayout: useWideLayout)
            basicWorkspace(useWideLayout: useWideLayout)
            inlineStatus
            numericKeypad(useWideLayout: useWideLayout)
        }
        .frame(
            maxWidth: .infinity,
            minHeight: minHeight,
            alignment: .top
        )
    }

    @ViewBuilder
    private func basicWorkspace(useWideLayout: Bool) -> some View {
        if useWideLayout {
            HStack(alignment: .top, spacing: 16) {
                basicInputPanel
                basicResults
            }
        } else {
            VStack(spacing: 14) {
                basicInputPanel
                basicResults
            }
        }
    }

    private var basicInputPanel: some View {
        VStack(alignment: .leading, spacing: 18) {
            sectionHeader(
                title: "运算设置",
                detail: "固定值默认 475"
            )

            VStack(spacing: 14) {
                numericInput(
                    field: .fixedValue,
                    title: "固定值",
                    placeholder: CalculatorEngine.defaultFixedValue
                )
                operationControl
                numericInput(
                    field: .operationValue,
                    title: "运算值",
                    placeholder: "25"
                )
            }
        }
        .frame(maxWidth: .infinity, alignment: .topLeading)
        .contentCard()
    }

    private var operationControl: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("运算符")
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(Color.primaryText)

            Picker("运算符", selection: $model.basicOperation) {
                ForEach(BasicOperation.allCases) { operation in
                    Text(operation.rawValue)
                        .tag(operation)
                }
            }
            .pickerStyle(.segmented)
            .labelsHidden()
        }
        .frame(maxWidth: .infinity)
    }

    private var basicResults: some View {
        VStack(alignment: .leading, spacing: 14) {
            sectionHeader(
                title: "运算结果",
                detail: "实时更新"
            )

            resultCard(
                title: "计算结果",
                formula: model.basicFormula,
                value: model.basicResult,
                featured: true
            )
        }
        .frame(maxWidth: .infinity, alignment: .topLeading)
        .contentCard()
    }

    private func historyPanel(useWideLayout: Bool) -> some View {
        VStack(spacing: 0) {
            HStack(spacing: 10) {
                Button {
                    guard !model.visibleHistoryEntries.isEmpty else { return }
                    withAnimation(.easeInOut(duration: 0.2)) {
                        isHistoryExpanded.toggle()
                    }
                } label: {
                    HStack(spacing: 10) {
                        Image(systemName: "clock.arrow.circlepath")
                            .font(.subheadline.weight(.semibold))
                            .foregroundStyle(Color.appAccent)
                            .accessibilityHidden(true)

                        Text("历史")
                            .font(.subheadline.weight(.semibold))
                            .foregroundStyle(Color.primaryText)

                        if let latestEntry = model.visibleHistoryEntries.first {
                            Text(latestEntry.expression)
                                .font(.subheadline)
                                .foregroundStyle(Color.mutedText)
                                .lineLimit(1)

                            Spacer(minLength: 4)

                            Text(latestEntry.primaryResult)
                                .font(
                                    .system(
                                        .subheadline,
                                        design: .rounded,
                                        weight: .semibold
                                    )
                                )
                                .foregroundStyle(Color.appAccent)
                                .monospacedDigit()
                                .lineLimit(1)
                                .minimumScaleFactor(0.7)

                            Image(
                                systemName: isHistoryExpanded
                                    ? "chevron.up"
                                    : "chevron.down"
                            )
                            .font(.caption.weight(.bold))
                            .foregroundStyle(Color.faintText)
                            .accessibilityHidden(true)
                        } else {
                            Text("暂无记录，点击“计算”后自动保存")
                                .font(.caption)
                                .foregroundStyle(Color.faintText)
                                .lineLimit(1)

                            Spacer(minLength: 4)
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
                .buttonStyle(.plain)
                .disabled(model.visibleHistoryEntries.isEmpty)
                .accessibilityLabel(
                    isHistoryExpanded ? "收起历史记录" : "展开历史记录"
                )

                Button {
                    if !model.visibleHistoryEntries.isEmpty {
                        showHistoryClearConfirmation = true
                    }
                } label: {
                    Image(systemName: "trash")
                        .font(.subheadline.weight(.semibold))
                        .frame(width: 30, height: 30)
                }
                .buttonStyle(.plain)
                .foregroundStyle(Color.mutedText)
                .disabled(model.visibleHistoryEntries.isEmpty)
                .accessibilityLabel("清空历史记录")
            }
            .padding(.horizontal, useWideLayout ? 18 : 14)
            .frame(height: useWideLayout ? 58 : 54)

            if isHistoryExpanded && !model.visibleHistoryEntries.isEmpty {
                panelDivider
                    .padding(.horizontal, useWideLayout ? 18 : 14)

                ScrollView {
                    LazyVStack(spacing: 0) {
                        ForEach(model.visibleHistoryEntries) { entry in
                            historyRow(entry)

                            if entry.id
                                != model.visibleHistoryEntries.last?.id {
                                panelDivider
                                    .padding(.vertical, 10)
                            }
                        }
                    }
                    .padding(useWideLayout ? 18 : 14)
                }
                .frame(height: useWideLayout ? 160 : 136)
                .scrollIndicators(.visible)
            }
        }
        .frame(maxWidth: .infinity)
        .background(Color.surface)
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay {
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke(Color.border, lineWidth: 1)
        }
        .shadow(color: Color.shadowTint, radius: 8, x: 0, y: 3)
        .accessibilityElement(children: .contain)
    }

    private func historyRow(_ entry: CalculationHistoryEntry) -> some View {
        HStack(alignment: .firstTextBaseline, spacing: 14) {
            VStack(alignment: .leading, spacing: 6) {
                Text(entry.expression)
                    .font(.subheadline.weight(.medium))
                    .foregroundStyle(Color.primaryText)
                    .lineLimit(1)
                    .minimumScaleFactor(0.75)

                if let secondaryResult = entry.secondaryResult {
                    Text(secondaryResult)
                        .font(.caption)
                        .foregroundStyle(Color.mutedText)
                        .lineLimit(1)
                        .minimumScaleFactor(0.75)
                }
            }

            Spacer(minLength: 12)

            VStack(alignment: .trailing, spacing: 5) {
                Text(entry.primaryResult)
                    .font(.system(.title3, design: .rounded, weight: .semibold))
                    .foregroundStyle(Color.appAccent)
                    .monospacedDigit()
                    .lineLimit(1)
                    .minimumScaleFactor(0.7)

                Text(entry.createdAt, style: .time)
                    .font(.caption2)
                    .foregroundStyle(Color.faintText)
            }
        }
        .padding(.horizontal, 2)
        .accessibilityElement(children: .combine)
    }

    private func counterPage(
        useWideLayout: Bool,
        minHeight: CGFloat
    ) -> some View {
        VStack(spacing: useWideLayout ? 22 : 16) {
            counterDisplay(useWideLayout: useWideLayout)

            Spacer(minLength: useWideLayout ? 36 : 22)

            Button {
                model.incrementCounter()
            } label: {
                VStack(spacing: useWideLayout ? 14 : 9) {
                    Image(systemName: "plus")
                        .font(
                            .system(
                                size: useWideLayout ? 46 : 34,
                                weight: .semibold
                            )
                        )
                    Text("加 1")
                        .font(useWideLayout ? .largeTitle.bold() : .title.bold())
                    Text("点击按钮或按下空格键")
                        .font(.subheadline)
                        .opacity(0.82)
                }
                .frame(maxWidth: .infinity)
            }
            .adaptivePrimaryAction(
                height: useWideLayout ? 190 : 138,
                reduceTransparency: reduceTransparency
            )
            .keyboardShortcut(.space, modifiers: [])
            .accessibilityHint("每次点击使当前计数增加一")

            inlineStatus
        }
        .frame(maxWidth: useWideLayout ? 900 : 620)
        .frame(
            maxWidth: .infinity,
            minHeight: minHeight,
            alignment: .top
        )
    }

    private func counterDisplay(useWideLayout: Bool) -> some View {
        VStack(spacing: useWideLayout ? 18 : 12) {
            HStack {
                VStack(alignment: .leading, spacing: 3) {
                    Text("当前计数")
                        .font(.headline)
                        .foregroundStyle(Color.primaryText)
                    Text("每次点击增加 1")
                        .font(.caption)
                        .foregroundStyle(Color.faintText)
                }

                Spacer()

                Button {
                    model.resetCounter()
                } label: {
                    Label("清零", systemImage: "arrow.counterclockwise")
                }
                .adaptiveSecondaryAction(
                    height: 44,
                    reduceTransparency: reduceTransparency
                )
                .frame(maxWidth: 130)
            }

            panelDivider

            Text("\(model.counter)")
                .font(
                    .system(
                        size: useWideLayout ? 118 : 82,
                        weight: .medium,
                        design: .rounded
                    )
                )
                .foregroundStyle(Color.appAccent)
                .monospacedDigit()
                .minimumScaleFactor(0.35)
                .lineLimit(1)
                .frame(maxWidth: .infinity)
        }
        .frame(maxWidth: .infinity)
        .contentCard()
    }

    private var panelDivider: some View {
        Rectangle()
            .fill(Color.border)
            .frame(height: 1)
            .accessibilityHidden(true)
    }

    private func numericInput(
        field: CalculatorField,
        title: String,
        placeholder: String
    ) -> some View {
        let value = model.text(for: field)

        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(Color.primaryText)

            Button {
                if activeField != field {
                    activeField = field
                    replaceActiveValue = true
                }
            } label: {
                HStack(spacing: 10) {
                    if activeField == field {
                        Circle()
                            .fill(Color.appAccent)
                            .frame(width: 7, height: 7)
                            .accessibilityHidden(true)
                    }

                    Spacer(minLength: 0)

                    Text(value.isEmpty ? placeholder : value)
                        .font(
                            .system(
                                .title3,
                                design: .rounded,
                                weight: .medium
                            )
                        )
                        .foregroundStyle(
                            value.isEmpty
                                ? Color.faintText
                                : Color.primaryText
                        )
                        .monospacedDigit()
                        .lineLimit(1)
                        .minimumScaleFactor(0.65)
                }
                .padding(.horizontal, 15)
                .frame(maxWidth: .infinity, minHeight: 54)
                .background(Color.surfaceAlt)
                .clipShape(
                    RoundedRectangle(cornerRadius: 15, style: .continuous)
                )
                .overlay {
                    RoundedRectangle(cornerRadius: 15, style: .continuous)
                        .stroke(
                            fieldBorderColor(field),
                            lineWidth: fieldBorderWidth(field)
                        )
                }
            }
            .buttonStyle(.plain)
            .accessibilityLabel(title)
            .accessibilityValue(
                model.text(for: field).isEmpty
                    ? "空"
                    : model.text(for: field)
            )
            .accessibilityHint("选择后使用下方数字键盘输入")
        }
        .frame(maxWidth: .infinity)
    }

    private func numericKeypad(useWideLayout: Bool) -> some View {
        VStack(spacing: useWideLayout ? 12 : 10) {
            HStack(spacing: 8) {
                Text("数字键盘")
                    .font(.headline)
                    .foregroundStyle(Color.primaryText)

                Spacer()

                HStack(spacing: 6) {
                    Circle()
                        .fill(Color.appAccent)
                        .frame(width: 6, height: 6)
                    Text("正在输入：\(activeFieldTitle)")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(Color.mutedText)
                }
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
                .background(Color.accentSoft)
                .clipShape(Capsule())
            }

            ForEach(keypadRows.indices, id: \.self) { rowIndex in
                HStack(spacing: useWideLayout ? 10 : 8) {
                    ForEach(keypadRows[rowIndex]) { key in
                        Button {
                            handleKeypadKey(key)
                        } label: {
                            Group {
                                if let systemImage = key.systemImage {
                                    Image(systemName: systemImage)
                                } else {
                                    Text(key.title)
                                }
                            }
                            .font(
                                key.isPrimary
                                    ? .headline
                                    : .title3.weight(.semibold)
                            )
                            .frame(maxWidth: .infinity)
                            .frame(height: useWideLayout ? 52 : 48)
                        }
                        .buttonStyle(
                            CalculatorKeyButtonStyle(
                                isPrimary: key.isPrimary
                            )
                        )
                        .accessibilityLabel(key.accessibilityLabel)
                    }
                }
            }
        }
        .padding(useWideLayout ? 16 : 14)
        .frame(maxWidth: .infinity)
        .background(Color.surface)
        .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
        .overlay {
            RoundedRectangle(cornerRadius: 22, style: .continuous)
                .stroke(Color.border, lineWidth: 1)
        }
        .shadow(color: Color.shadowTint, radius: 10, x: 0, y: 4)
    }

    private func resultCard(
        title: String,
        formula: String,
        value: String,
        featured: Bool
    ) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .firstTextBaseline, spacing: 10) {
                if featured {
                    Circle()
                        .fill(Color.appAccent)
                        .frame(width: 8, height: 8)
                        .accessibilityHidden(true)
                }

                Text(title)
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(Color.primaryText)
                Spacer(minLength: 8)
                Text(formula)
                    .font(.caption)
                    .foregroundStyle(Color.mutedText)
                    .lineLimit(1)
            }

            Text(value)
                .font(resultFont(for: value))
                .foregroundStyle(
                    value == "—"
                        ? Color.faintText
                        : (featured ? Color.appAccent : Color.primaryText)
                )
                .lineLimit(1)
                .minimumScaleFactor(0.45)
                .monospacedDigit()
                .frame(maxWidth: .infinity, alignment: .trailing)
        }
        .padding(18)
        .frame(maxWidth: .infinity, minHeight: 112)
        .background(Color.surfaceAlt)
        .clipShape(RoundedRectangle(cornerRadius: 19, style: .continuous))
        .overlay {
            RoundedRectangle(cornerRadius: 19, style: .continuous)
                .stroke(
                    featured ? Color.accentBorder : Color.border,
                    lineWidth: featured ? 1.5 : 1
                )
        }
        .accessibilityElement(children: .combine)
    }

    private var inlineStatus: some View {
        HStack(spacing: 10) {
            Image(systemName: statusSymbol)
                .foregroundStyle(statusForeground)
                .accessibilityHidden(true)
            Text(model.status)
                .font(.footnote)
                .foregroundStyle(statusForeground)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(.horizontal, 15)
        .padding(.vertical, 12)
        .background(statusBackground)
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
        .overlay {
            RoundedRectangle(cornerRadius: 14, style: .continuous)
                .stroke(statusForeground.opacity(0.16), lineWidth: 1)
        }
        .animation(.easeOut(duration: 0.18), value: model.status)
        .accessibilityLabel("状态：\(model.status)")
    }

    private func sectionHeader(
        title: String,
        detail: String
    ) -> some View {
        HStack(alignment: .firstTextBaseline) {
            Text(title)
                .font(.headline)
                .foregroundStyle(Color.primaryText)
            Spacer()
            Text(detail)
                .font(.caption)
                .foregroundStyle(Color.faintText)
        }
    }

    private func fieldBorderColor(_ field: CalculatorField) -> Color {
        if model.invalidField == field {
            return .errorText
        }
        return activeField == field ? .appAccent : .border
    }

    private func fieldBorderWidth(_ field: CalculatorField) -> CGFloat {
        model.invalidField == field || activeField == field ? 2 : 1
    }

    private var keypadRows: [[CalculatorKey]] {
        [
            [.digit("1"), .digit("2"), .digit("3"), .clear, .delete],
            [.digit("4"), .digit("5"), .digit("6"), .toggleSign, .decimal],
            [.digit("7"), .digit("8"), .digit("9"), .digit("0"), .calculate]
        ]
    }

    private var activeFieldTitle: String {
        guard let activeField else { return "请选择输入项" }

        switch activeField {
        case .a:
            return "A 数据"
        case .b:
            return "B 数据"
        case .divisor:
            return "可调除数"
        case .coefficient:
            return "系数"
        case .multiplier:
            return "乘数"
        case .addend:
            return "加数"
        case .fixedValue:
            return "固定值"
        case .operationValue:
            return "运算值"
        }
    }

    private func resetActiveField() {
        switch model.page {
        case .calculator:
            activeField = model.mode == .standard ? .a : .multiplier
        case .basic:
            activeField = .operationValue
        case .counter:
            activeField = nil
        }
        replaceActiveValue = false
    }

    private func handleKeypadKey(_ key: CalculatorKey) {
        if key == .calculate {
            model.calculate()
            replaceActiveValue = false
            return
        }

        guard
            let activeField,
            let input = key.input
        else {
            return
        }

        let shouldReplace =
            replaceActiveValue
            && (key.isDigit || key == .decimal)
        let didChange = model.applyKeypadInput(
            input,
            to: activeField,
            replacingExisting: shouldReplace
        )

        if didChange {
            replaceActiveValue = false
        }
    }

    private func resultFont(for value: String) -> Font {
        if value.count <= 12 {
            return .system(size: 40, weight: .medium, design: .rounded)
        }
        if value.count <= 18 {
            return .system(size: 31, weight: .medium, design: .rounded)
        }
        return .system(size: 23, weight: .medium, design: .rounded)
    }

    private var statusSymbol: String {
        switch model.statusTone {
        case .neutral:
            return "info.circle.fill"
        case .success:
            return "checkmark.circle.fill"
        case .error:
            return "exclamationmark.triangle.fill"
        }
    }

    private var statusForeground: Color {
        switch model.statusTone {
        case .neutral:
            return .mutedText
        case .success:
            return .successText
        case .error:
            return .errorText
        }
    }

    private var statusBackground: Color {
        switch model.statusTone {
        case .neutral:
            return .surface
        case .success:
            return .successSoft
        case .error:
            return .errorSoft
        }
    }
}

private enum CalculatorKey: Identifiable, Equatable {
    case digit(String)
    case decimal
    case clear
    case delete
    case toggleSign
    case calculate

    var id: String {
        switch self {
        case let .digit(value):
            return "digit-\(value)"
        case .decimal:
            return "decimal"
        case .clear:
            return "clear"
        case .delete:
            return "delete"
        case .toggleSign:
            return "toggle-sign"
        case .calculate:
            return "calculate"
        }
    }

    var title: String {
        switch self {
        case let .digit(value):
            return value
        case .decimal:
            return "."
        case .clear:
            return "C"
        case .delete:
            return ""
        case .toggleSign:
            return "±"
        case .calculate:
            return "计算"
        }
    }

    var systemImage: String? {
        self == .delete ? "delete.left" : nil
    }

    var accessibilityLabel: String {
        switch self {
        case let .digit(value):
            return value
        case .decimal:
            return "小数点"
        case .clear:
            return "清空当前输入"
        case .delete:
            return "删除一位"
        case .toggleSign:
            return "切换正负号"
        case .calculate:
            return "计算"
        }
    }

    var input: CalculatorKeypadInput? {
        switch self {
        case let .digit(value):
            return .digit(value)
        case .decimal:
            return .decimal
        case .clear:
            return .clear
        case .delete:
            return .delete
        case .toggleSign:
            return .toggleSign
        case .calculate:
            return nil
        }
    }

    var isDigit: Bool {
        if case .digit = self {
            return true
        }
        return false
    }

    var isPrimary: Bool {
        self == .calculate
    }
}

private struct CalculatorKeyButtonStyle: ButtonStyle {
    let isPrimary: Bool

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .foregroundStyle(isPrimary ? Color.white : Color.primaryText)
            .background(
                isPrimary
                    ? Color.appAccent
                    : (
                        configuration.isPressed
                            ? Color.accentSoft
                            : Color.surfaceAlt
                    )
            )
            .clipShape(RoundedRectangle(cornerRadius: 15, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: 15, style: .continuous)
                    .stroke(
                        isPrimary ? Color.accentBorder : Color.border,
                        lineWidth: 1
                    )
            }
            .scaleEffect(configuration.isPressed ? 0.97 : 1)
            .animation(
                .easeOut(duration: 0.12),
                value: configuration.isPressed
            )
    }
}

private struct CalculatorBackdrop: View {
    let reduceTransparency: Bool

    var body: some View {
        GeometryReader { geometry in
            ZStack {
                LinearGradient(
                    colors: [
                        Color.backdropTop,
                        Color.appBackground,
                        Color.backdropBottom
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )

                if !reduceTransparency {
                    Circle()
                        .fill(
                            RadialGradient(
                                colors: [
                                    Color.appAccent.opacity(0.22),
                                    Color.appAccent.opacity(0)
                                ],
                                center: .center,
                                startRadius: 0,
                                endRadius: geometry.size.width * 0.42
                            )
                        )
                        .frame(
                            width: geometry.size.width * 0.9,
                            height: geometry.size.width * 0.9
                        )
                        .offset(
                            x: geometry.size.width * 0.38,
                            y: -geometry.size.height * 0.34
                        )
                        .blur(radius: 28)

                    Circle()
                        .fill(
                            RadialGradient(
                                colors: [
                                    Color.coolGlow.opacity(0.18),
                                    Color.coolGlow.opacity(0)
                                ],
                                center: .center,
                                startRadius: 0,
                                endRadius: geometry.size.width * 0.38
                            )
                        )
                        .frame(
                            width: geometry.size.width * 0.84,
                            height: geometry.size.width * 0.84
                        )
                        .offset(
                            x: -geometry.size.width * 0.4,
                            y: geometry.size.height * 0.28
                        )
                        .blur(radius: 32)
                }
            }
        }
        .ignoresSafeArea()
        .accessibilityHidden(true)
    }
}

private struct PrimaryActionButtonStyle: ButtonStyle {
    var height: CGFloat

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.headline)
            .foregroundStyle(Color.accentButtonText)
            .padding(.horizontal, 16)
            .frame(maxWidth: .infinity, minHeight: height)
            .background(
                configuration.isPressed
                    ? Color.accentHover
                    : Color.appAccent
            )
            .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
            .shadow(
                color: Color.accentShadow,
                radius: configuration.isPressed ? 4 : 10,
                x: 0,
                y: configuration.isPressed ? 2 : 6
            )
            .scaleEffect(configuration.isPressed ? 0.985 : 1)
            .animation(.easeOut(duration: 0.12), value: configuration.isPressed)
    }
}

private struct SecondaryActionButtonStyle: ButtonStyle {
    var height: CGFloat

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.headline)
            .foregroundStyle(Color.primaryText)
            .padding(.horizontal, 16)
            .frame(maxWidth: .infinity, minHeight: height)
            .background(
                configuration.isPressed ? Color.surfaceAlt : Color.surface
            )
            .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .stroke(Color.border, lineWidth: 1)
            }
            .shadow(
                color: Color.shadowTint,
                radius: configuration.isPressed ? 3 : 8,
                x: 0,
                y: configuration.isPressed ? 1 : 4
            )
            .scaleEffect(configuration.isPressed ? 0.985 : 1)
            .animation(.easeOut(duration: 0.12), value: configuration.isPressed)
    }
}

private extension View {
    @ViewBuilder
    func adaptivePrimaryAction(
        height: CGFloat,
        reduceTransparency: Bool
    ) -> some View {
        if #available(iOS 26.0, *), !reduceTransparency {
            font(.headline)
                .frame(minHeight: height)
                .buttonStyle(.glassProminent)
                .tint(Color.appAccent)
        } else {
            buttonStyle(PrimaryActionButtonStyle(height: height))
        }
    }

    @ViewBuilder
    func adaptiveSecondaryAction(
        height: CGFloat,
        reduceTransparency: Bool
    ) -> some View {
        if #available(iOS 26.0, *), !reduceTransparency {
            font(.headline)
                .frame(minHeight: height)
                .buttonStyle(.glass)
                .tint(Color.primaryText)
        } else {
            buttonStyle(SecondaryActionButtonStyle(height: height))
        }
    }

    func contentCard() -> some View {
        padding(22)
            .background(Color.surface)
            .clipShape(RoundedRectangle(cornerRadius: 26, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: 26, style: .continuous)
                    .stroke(Color.border, lineWidth: 1)
            }
            .shadow(color: Color.shadowTint, radius: 12, x: 0, y: 5)
    }
}

private extension Color {
    static let appBackground = Color(light: 0xF4F3F0, dark: 0x121314)
    static let backdropTop = Color(light: 0xFFF8F1, dark: 0x211A16)
    static let backdropBottom = Color(light: 0xEFF4F6, dark: 0x10191D)
    static let coolGlow = Color(light: 0x7CCDE3, dark: 0x3E91A9)
    static let surface = Color(light: 0xFDFDFC, dark: 0x252628)
    static let surfaceAlt = Color(light: 0xF5F4F1, dark: 0x303134)
    static let border = Color(light: 0xDEDDD8, dark: 0x45474A)
    static let primaryText = Color(light: 0x171717, dark: 0xF6F4F1)
    static let mutedText = Color(light: 0x6F7074, dark: 0xB6B7BA)
    static let faintText = Color(light: 0x96979B, dark: 0x86878B)
    static let appAccent = Color(hex: 0xFF7500)
    static let accentHover = Color(hex: 0xE96900)
    static let accentButtonText = Color.white
    static let accentBorder = Color(light: 0xFFC68F, dark: 0x955426)
    static let successText = Color(light: 0x31825B, dark: 0x6ED2A0)
    static let successSoft = Color(light: 0xEAF7EF, dark: 0x173629)
    static let errorText = Color(light: 0xC74B4B, dark: 0xF08A8A)
    static let errorSoft = Color(light: 0xFCEEEE, dark: 0x402222)
    static let shadowTint = Color.black.opacity(0.1)
    static let accentShadow = Color(hex: 0xFF7500).opacity(0.22)

    init(light: UInt32, dark: UInt32) {
        self.init(
            uiColor: UIColor { traits in
                let hex = traits.userInterfaceStyle == .dark ? dark : light
                return UIColor(
                    red: CGFloat((hex >> 16) & 0xFF) / 255,
                    green: CGFloat((hex >> 8) & 0xFF) / 255,
                    blue: CGFloat(hex & 0xFF) / 255,
                    alpha: 1
                )
            }
        )
    }

    init(hex: UInt32) {
        self.init(
            red: Double((hex >> 16) & 0xFF) / 255,
            green: Double((hex >> 8) & 0xFF) / 255,
            blue: Double(hex & 0xFF) / 255
        )
    }
}

#Preview("iPhone") {
    CalculatorView()
        .frame(width: 393, height: 852)
}

#Preview("iPad Portrait") {
    CalculatorView()
        .frame(width: 1_024, height: 1_366)
}

#Preview("iPad Landscape") {
    CalculatorView()
        .frame(width: 1_366, height: 1_024)
}

import SwiftUI
import UIKit

struct CalculatorView: View {
    @StateObject private var model = CalculatorViewModel()
    @FocusState private var focusedField: CalculatorField?
    @Environment(\.accessibilityReduceTransparency)
    private var reduceTransparency

    private let pageMaxWidth: CGFloat = 1_180

    var body: some View {
        GeometryReader { geometry in
            let useWideLayout = geometry.size.width >= 760
            let horizontalPadding: CGFloat = useWideLayout ? 32 : 18
            let verticalPadding: CGFloat = useWideLayout ? 28 : 18
            let pageMinHeight: CGFloat = useWideLayout
                ? max(410, geometry.size.height - 310)
                : 0

            ZStack {
                LiquidGlassBackdrop(
                    reduceTransparency: reduceTransparency
                )

                ScrollView {
                    VStack(spacing: useWideLayout ? 20 : 16) {
                        header
                        pagePicker
                        pageContent(
                            useWideLayout: useWideLayout,
                            minHeight: pageMinHeight
                        )
                        statusBar
                        keyboardHint
                    }
                    .frame(maxWidth: pageMaxWidth)
                    .frame(
                        minHeight: max(
                            0,
                            geometry.size.height - verticalPadding * 2
                        ),
                        alignment: .top
                    )
                    .padding(.horizontal, horizontalPadding)
                    .padding(.vertical, verticalPadding)
                    .frame(maxWidth: .infinity)
                }
                .scrollDismissesKeyboard(.interactively)
            }
        }
        .tint(Color.appAccent)
        .animation(
            .spring(response: 0.34, dampingFraction: 0.82),
            value: model.page
        )
        .animation(
            .spring(response: 0.3, dampingFraction: 0.84),
            value: model.mode
        )
        .toolbar {
            ToolbarItemGroup(placement: .keyboard) {
                Button(model.page == .counter ? "清零" : "清空") {
                    model.clear()
                }
                Spacer()
                if model.page != .counter {
                    Button("计算") {
                        model.calculate()
                    }
                    .fontWeight(.semibold)
                }
                Button("完成") {
                    focusedField = nil
                }
            }
        }
        .onChange(of: model.invalidField) { field in
            if let field {
                focusedField = field
            }
        }
        .onChange(of: model.page) { _ in
            focusedField = nil
        }
        .onChange(of: model.mode) { _ in
            focusedField = nil
        }
    }

    private var header: some View {
        HStack(spacing: 13) {
            ZStack {
                Text(headerSymbol)
                    .font(.system(size: 21, weight: .bold, design: .rounded))
                    .foregroundStyle(Color.appAccent)
            }
            .frame(width: 50, height: 50)
            .adaptiveGlassSurface(
                cornerRadius: 16,
                tint: Color.appAccent.opacity(0.08),
                interactive: false,
                reduceTransparency: reduceTransparency
            )
            .accessibilityHidden(true)

            VStack(alignment: .leading, spacing: 3) {
                Text("小秋计算器")
                    .font(.title2.weight(.bold))
                    .foregroundStyle(Color.primaryText)
                Text(model.subtitle)
                    .font(.subheadline)
                    .foregroundStyle(Color.mutedText)
                    .lineLimit(1)
            }

            Spacer()

            HStack(spacing: 6) {
                Circle()
                    .fill(Color.appAccent)
                    .frame(width: 7, height: 7)
                Text("计算 / 工具")
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(Color.mutedText)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .adaptiveGlassSurface(
                cornerRadius: 18,
                interactive: false,
                reduceTransparency: reduceTransparency
            )
        }
    }

    private var headerSymbol: String {
        switch model.page {
        case .calculator:
            return "Σ"
        case .basic:
            return "±"
        case .counter:
            return "+1"
        }
    }

    private var pagePicker: some View {
        AdaptiveGlassContainer(spacing: 4) {
            HStack(spacing: 4) {
                ForEach(AppPage.allCases) { page in
                    Button {
                        withAnimation(
                            .spring(
                                response: 0.3,
                                dampingFraction: 0.82
                            )
                        ) {
                            model.page = page
                        }
                    } label: {
                        Text(page.rawValue)
                            .font(.subheadline.weight(.semibold))
                            .foregroundStyle(
                                model.page == page
                                    ? Color.primaryText
                                    : Color.mutedText
                            )
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 11)
                            .background {
                                if model.page == page {
                                    RoundedRectangle(
                                        cornerRadius: 14,
                                        style: .continuous
                                    )
                                    .fill(Color.selectionFill)
                                    .shadow(
                                        color: Color.shadowTint,
                                        radius: 7,
                                        x: 0,
                                        y: 3
                                    )
                                }
                            }
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel(page.rawValue)
                    .accessibilityHint("切换到\(page.rawValue)")
                }
            }
        }
        .padding(5)
        .adaptiveGlassSurface(
            cornerRadius: 20,
            interactive: false,
            reduceTransparency: reduceTransparency
        )
        .accessibilityElement(children: .contain)
    }

    @ViewBuilder
    private func pageContent(
        useWideLayout: Bool,
        minHeight: CGFloat
    ) -> some View {
        switch model.page {
        case .calculator:
            calculatorPage(
                useWideLayout: useWideLayout,
                minHeight: minHeight
            )
        case .basic:
            basicPage(
                useWideLayout: useWideLayout,
                minHeight: minHeight
            )
        case .counter:
            counterPage(
                useWideLayout: useWideLayout,
                minHeight: minHeight
            )
        }
    }

    private func calculatorPage(
        useWideLayout: Bool,
        minHeight: CGFloat
    ) -> some View {
        return VStack(spacing: 16) {
            modePicker
                .frame(maxWidth: useWideLayout ? 520 : .infinity)

            historyPanel(useWideLayout: useWideLayout)

            if model.mode == .standard {
                standardWorkspace(useWideLayout: useWideLayout)
            } else {
                multiplyAddWorkspace(useWideLayout: useWideLayout)
            }
        }
        .frame(
            maxWidth: .infinity,
            minHeight: useWideLayout ? minHeight : nil,
            alignment: .top
        )
    }

    private var modePicker: some View {
        AdaptiveGlassContainer(spacing: 4) {
            HStack(spacing: 4) {
                ForEach(CalculatorMode.allCases) { mode in
                    Button {
                        withAnimation(
                            .spring(
                                response: 0.3,
                                dampingFraction: 0.82
                            )
                        ) {
                            model.mode = mode
                        }
                    } label: {
                        Text(mode.rawValue)
                            .font(.subheadline.weight(.semibold))
                            .foregroundStyle(
                                model.mode == mode
                                    ? Color.primaryText
                                    : Color.mutedText
                            )
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 10)
                            .background {
                                if model.mode == mode {
                                    RoundedRectangle(
                                        cornerRadius: 13,
                                        style: .continuous
                                    )
                                    .fill(Color.selectionFill)
                                    .shadow(
                                        color: Color.shadowTint,
                                        radius: 6,
                                        x: 0,
                                        y: 2
                                    )
                                }
                            }
                    }
                    .buttonStyle(.plain)
                }
            }
        }
        .padding(5)
        .adaptiveGlassSurface(
            cornerRadius: 19,
            interactive: false,
            reduceTransparency: reduceTransparency
        )
    }

    @ViewBuilder
    private func standardWorkspace(useWideLayout: Bool) -> some View {
        if useWideLayout {
            HStack(alignment: .bottom, spacing: 16) {
                standardInputPanel(useWideLayout: false)
                standardResults(useWideLayout: false)
            }
        } else {
            VStack(spacing: 14) {
                standardInputPanel(useWideLayout: false)
                standardResults(useWideLayout: false)
            }
        }
    }

    private func standardInputPanel(useWideLayout: Bool) -> some View {
        VStack(alignment: .leading, spacing: 18) {
            sectionHeader(title: "输入数据", detail: "输入后实时计算")

            if useWideLayout {
                HStack(alignment: .top, spacing: 12) {
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
            } else {
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

            panelDivider
            actionButtons(primaryTitle: "计算结果")
        }
        .frame(maxWidth: .infinity, alignment: .topLeading)
        .cardStyle(reduceTransparency: reduceTransparency)
    }

    private func standardResults(useWideLayout: Bool) -> some View {
        VStack(alignment: .leading, spacing: 14) {
            sectionHeader(title: "计算结果", detail: "最多保留 2 位小数")

            if useWideLayout {
                HStack(spacing: 14) {
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
            } else {
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
        }
        .frame(maxWidth: .infinity, alignment: .topLeading)
        .cardStyle(reduceTransparency: reduceTransparency)
    }

    private func multiplyAddInputPanel(useWideLayout: Bool) -> some View {
        VStack(alignment: .leading, spacing: 18) {
            sectionHeader(title: "输入数据", detail: "系数默认 475")

            if useWideLayout {
                HStack(alignment: .top, spacing: 12) {
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
            } else {
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

            panelDivider
            actionButtons(primaryTitle: "计算结果")
        }
        .frame(maxWidth: .infinity, alignment: .topLeading)
        .cardStyle(reduceTransparency: reduceTransparency)
    }

    private var multiplyAddResults: some View {
        VStack(alignment: .leading, spacing: 14) {
            sectionHeader(title: "乘加结果", detail: "实时更新")

            resultCard(
                title: "计算结果",
                formula: model.multiplyAddFormula,
                value: model.multiplyAddResult,
                featured: true
            )
        }
        .frame(maxWidth: .infinity, alignment: .topLeading)
        .cardStyle(reduceTransparency: reduceTransparency)
    }

    @ViewBuilder
    private func multiplyAddWorkspace(useWideLayout: Bool) -> some View {
        if useWideLayout {
            HStack(alignment: .bottom, spacing: 16) {
                multiplyAddInputPanel(useWideLayout: false)
                multiplyAddResults
            }
        } else {
            VStack(spacing: 14) {
                multiplyAddInputPanel(useWideLayout: false)
                multiplyAddResults
            }
        }
    }

    private func basicPage(
        useWideLayout: Bool,
        minHeight: CGFloat
    ) -> some View {
        VStack(spacing: 16) {
            historyPanel(useWideLayout: useWideLayout)
            basicWorkspace(useWideLayout: useWideLayout)
        }
        .frame(
            maxWidth: .infinity,
            minHeight: useWideLayout ? minHeight : nil,
            alignment: .top
        )
    }

    private func basicInputPanel(useWideLayout: Bool) -> some View {
        VStack(alignment: .leading, spacing: 18) {
            sectionHeader(title: "运算设置", detail: "固定值默认 475")

            if useWideLayout {
                HStack(alignment: .bottom, spacing: 12) {
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
            } else {
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

            panelDivider
            actionButtons(primaryTitle: "计算结果")
        }
        .frame(maxWidth: .infinity, alignment: .topLeading)
        .cardStyle(reduceTransparency: reduceTransparency)
    }

    @ViewBuilder
    private func basicWorkspace(useWideLayout: Bool) -> some View {
        if useWideLayout {
            HStack(alignment: .bottom, spacing: 16) {
                basicInputPanel(useWideLayout: false)
                basicResults
            }
        } else {
            VStack(spacing: 14) {
                basicInputPanel(useWideLayout: false)
                basicResults
            }
        }
    }

    private var operationControl: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("运算符")
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(Color.primaryText)
            operationPicker
        }
        .frame(maxWidth: .infinity)
    }

    private var operationPicker: some View {
        HStack(spacing: 4) {
            ForEach(BasicOperation.allCases) { operation in
                Button {
                    withAnimation(.easeInOut(duration: 0.16)) {
                        model.basicOperation = operation
                    }
                } label: {
                    Text(operation.rawValue)
                        .font(.title3.weight(.semibold))
                        .foregroundStyle(
                            model.basicOperation == operation
                                ? Color.appAccent
                                : Color.mutedText
                        )
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 9)
                        .background {
                            if model.basicOperation == operation {
                                RoundedRectangle(
                                    cornerRadius: 12,
                                    style: .continuous
                                )
                                .fill(Color.surface)
                                .shadow(
                                    color: Color.shadowTint,
                                    radius: 5,
                                    x: 0,
                                    y: 2
                                )
                            }
                        }
                }
                .buttonStyle(.plain)
                .accessibilityLabel("运算符\(operation.rawValue)")
            }
        }
        .padding(4)
        .background(Color.controlBackground)
        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
    }

    private var basicResults: some View {
        VStack(alignment: .leading, spacing: 14) {
            sectionHeader(title: "运算结果", detail: "实时更新")

            resultCard(
                title: "计算结果",
                formula: model.basicFormula,
                value: model.basicResult,
                featured: true
            )
        }
        .frame(maxWidth: .infinity, alignment: .topLeading)
        .cardStyle(reduceTransparency: reduceTransparency)
    }

    private func historyPanel(useWideLayout: Bool) -> some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack(alignment: .firstTextBaseline, spacing: 12) {
                Text("历史记录")
                    .font(.headline)
                    .foregroundStyle(Color.primaryText)

                Spacer()

                Label("点击区域清空", systemImage: "trash")
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(
                        model.visibleHistoryEntries.isEmpty
                            ? Color.faintText
                            : Color.appAccent
                    )
            }

            panelDivider

            if model.visibleHistoryEntries.isEmpty {
                VStack(spacing: 8) {
                    Image(systemName: "clock.arrow.circlepath")
                        .font(.system(size: useWideLayout ? 30 : 24))
                        .foregroundStyle(Color.faintText)
                    Text("暂无计算记录")
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(Color.mutedText)
                    Text("点击“计算结果”后会自动保存在这里")
                        .font(.caption)
                        .foregroundStyle(Color.faintText)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                ScrollView {
                    LazyVStack(spacing: 0) {
                        ForEach(model.visibleHistoryEntries) { entry in
                            historyRow(entry)

                            if entry.id != model.visibleHistoryEntries.last?.id {
                                panelDivider
                                    .padding(.vertical, 10)
                            }
                        }
                    }
                }
                .scrollIndicators(.visible)
            }
        }
        .padding(20)
        .frame(
            maxWidth: .infinity,
            minHeight: useWideLayout ? 190 : 160,
            maxHeight: useWideLayout ? .infinity : nil,
            alignment: .topLeading
        )
        .adaptiveGlassSurface(
            cornerRadius: 28,
            tint: Color.historyGlassTint,
            interactive: true,
            reduceTransparency: reduceTransparency
        )
        .contentShape(RoundedRectangle(cornerRadius: 28, style: .continuous))
        .onTapGesture {
            withAnimation(.easeOut(duration: 0.18)) {
                model.clearHistory()
            }
        }
        .accessibilityElement(children: .contain)
        .accessibilityHint("点击可清空当前页面的历史记录")
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

            if useWideLayout {
                Spacer(minLength: 28)
            }

            Button {
                model.incrementCounter()
            } label: {
                VStack(spacing: useWideLayout ? 14 : 9) {
                    Image(systemName: "plus")
                        .font(
                            .system(
                                size: useWideLayout ? 48 : 34,
                                weight: .medium
                            )
                        )
                    Text("加 1")
                        .font(useWideLayout ? .largeTitle.bold() : .title.bold())
                    if useWideLayout {
                        Text("点击按钮或按下空格键")
                            .font(.subheadline)
                            .foregroundStyle(Color.white.opacity(0.82))
                    }
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
            .adaptivePrimaryAction(
                height: useWideLayout ? 210 : 116,
                reduceTransparency: reduceTransparency
            )
            .keyboardShortcut(.space, modifiers: [])
            .accessibilityHint("每次点击使当前计数增加一")
        }
        .frame(maxWidth: useWideLayout ? 900 : 620)
        .frame(
            maxWidth: .infinity,
            minHeight: useWideLayout ? minHeight : nil,
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
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(Color.primaryText)
                        .padding(.horizontal, 14)
                        .frame(height: 42)
                        .background(Color.surfaceAlt)
                        .clipShape(
                            RoundedRectangle(
                                cornerRadius: 14,
                                style: .continuous
                            )
                        )
                        .overlay {
                            RoundedRectangle(
                                cornerRadius: 14,
                                style: .continuous
                            )
                            .stroke(Color.border, lineWidth: 1)
                        }
                }
                .buttonStyle(.plain)
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
        .cardStyle(reduceTransparency: reduceTransparency)
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
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(Color.primaryText)

            TextField(
                placeholder,
                text: Binding(
                    get: { model.text(for: field) },
                    set: { model.update($0, for: field) }
                )
            )
            .font(.system(.title3, design: .rounded, weight: .medium))
            .foregroundStyle(Color.primaryText)
            .multilineTextAlignment(.trailing)
            .keyboardType(.numbersAndPunctuation)
            .textInputAutocapitalization(.never)
            .autocorrectionDisabled()
            .focused($focusedField, equals: field)
            .submitLabel(.done)
            .onSubmit { model.calculate() }
            .padding(.horizontal, 15)
            .frame(height: 54)
            .background(Color.surfaceAlt)
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .stroke(
                        fieldBorderColor(field),
                        lineWidth: fieldBorderWidth(field)
                    )
            }
            .accessibilityLabel(title)
            .accessibilityHint("最多输入 64 个字符，支持负数和小数")
        }
        .frame(maxWidth: .infinity)
    }

    private func actionButtons(primaryTitle: String) -> some View {
        AdaptiveGlassContainer(spacing: 12) {
            HStack(spacing: 12) {
                Button {
                    model.clear()
                } label: {
                    Text("清空")
                        .frame(maxWidth: .infinity)
                }
                .adaptiveSecondaryAction(
                    height: 56,
                    reduceTransparency: reduceTransparency
                )

                Button {
                    model.calculate()
                } label: {
                    Label(primaryTitle, systemImage: "equal")
                        .frame(maxWidth: .infinity)
                }
                .adaptivePrimaryAction(
                    height: 56,
                    reduceTransparency: reduceTransparency
                )
            }
        }
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
        .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
        .overlay {
            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .stroke(
                    featured ? Color.accentBorder : Color.border,
                    lineWidth: featured ? 1.5 : 1
                )
        }
        .accessibilityElement(children: .combine)
    }

    private var statusBar: some View {
        HStack(spacing: 10) {
            Circle()
                .fill(statusForeground)
                .frame(width: 8, height: 8)
                .accessibilityHidden(true)
            Text(model.status)
                .font(.footnote)
                .foregroundStyle(statusForeground)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(.horizontal, 15)
        .padding(.vertical, 12)
        .adaptiveGlassSurface(
            cornerRadius: 16,
            tint: statusGlassTint,
            interactive: false,
            reduceTransparency: reduceTransparency,
            fallbackColor: statusBackground
        )
        .animation(.easeOut(duration: 0.18), value: model.status)
        .accessibilityLabel("状态：\(model.status)")
    }

    private var keyboardHint: some View {
        Text(
            model.page == .counter
                ? "快捷计数仅在此页面响应空格键"
                : "输入完整后会实时计算，也可点按钮明确校验"
        )
        .font(.caption)
        .foregroundStyle(Color.faintText)
        .frame(maxWidth: .infinity, alignment: .trailing)
    }

    private func sectionHeader(title: String, detail: String) -> some View {
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
        return focusedField == field ? .appAccent : .border
    }

    private func fieldBorderWidth(_ field: CalculatorField) -> CGFloat {
        model.invalidField == field || focusedField == field ? 2 : 1
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

    private var statusGlassTint: Color? {
        switch model.statusTone {
        case .neutral:
            return nil
        case .success:
            return .successText.opacity(0.08)
        case .error:
            return .errorText.opacity(0.08)
        }
    }
}

private struct LiquidGlassBackdrop: View {
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
                                    Color.appAccent.opacity(0.26),
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
                                    Color.coolGlow.opacity(0.2),
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

private struct AdaptiveGlassContainer<Content: View>: View {
    let spacing: CGFloat
    let content: Content

    @Environment(\.accessibilityReduceTransparency)
    private var reduceTransparency

    init(
        spacing: CGFloat,
        @ViewBuilder content: () -> Content
    ) {
        self.spacing = spacing
        self.content = content()
    }

    @ViewBuilder
    var body: some View {
        if #available(iOS 26.0, *), !reduceTransparency {
            GlassEffectContainer(spacing: spacing) {
                content
            }
        } else {
            content
        }
    }
}

private struct PrimaryActionButtonStyle: ButtonStyle {
    var height: CGFloat? = 50
    var minHeight: CGFloat? = nil

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.headline)
            .foregroundStyle(Color.accentButtonText)
            .padding(.horizontal, 16)
            .frame(
                maxWidth: .infinity,
                minHeight: minHeight,
                idealHeight: height,
                maxHeight: minHeight == nil ? height : .infinity
            )
            .background(
                configuration.isPressed
                    ? Color.accentHover
                    : Color.appAccent
            )
            .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
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
    var height: CGFloat = 50

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.headline)
            .foregroundStyle(Color.primaryText)
            .padding(.horizontal, 16)
            .frame(height: height)
            .background(
                configuration.isPressed ? Color.surfaceAlt : Color.surface
            )
            .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: 20, style: .continuous)
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
    func adaptiveGlassSurface(
        cornerRadius: CGFloat,
        tint: Color? = nil,
        interactive: Bool,
        reduceTransparency: Bool,
        fallbackColor: Color = .surface
    ) -> some View {
        if #available(iOS 26.0, *), !reduceTransparency {
            if let tint {
                if interactive {
                    glassEffect(
                        .regular.tint(tint).interactive(),
                        in: .rect(cornerRadius: cornerRadius)
                    )
                } else {
                    glassEffect(
                        .regular.tint(tint),
                        in: .rect(cornerRadius: cornerRadius)
                    )
                }
            } else if interactive {
                glassEffect(
                    .regular.interactive(),
                    in: .rect(cornerRadius: cornerRadius)
                )
            } else {
                glassEffect(
                    .regular,
                    in: .rect(cornerRadius: cornerRadius)
                )
            }
        } else {
            background(fallbackColor)
                .clipShape(
                    RoundedRectangle(
                        cornerRadius: cornerRadius,
                        style: .continuous
                    )
                )
                .overlay {
                    RoundedRectangle(
                        cornerRadius: cornerRadius,
                        style: .continuous
                    )
                    .stroke(Color.border, lineWidth: 1)
                }
                .shadow(
                    color: Color.shadowTint,
                    radius: 12,
                    x: 0,
                    y: 5
                )
        }
    }

    @ViewBuilder
    func adaptivePrimaryAction(
        height: CGFloat,
        reduceTransparency: Bool
    ) -> some View {
        if #available(iOS 26.0, *), !reduceTransparency {
            font(.headline)
                .frame(height: height)
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
                .frame(height: height)
                .buttonStyle(.glass)
                .tint(Color.primaryText)
        } else {
            buttonStyle(SecondaryActionButtonStyle(height: height))
        }
    }

    func cardStyle(reduceTransparency: Bool) -> some View {
        padding(22)
            .adaptiveGlassSurface(
                cornerRadius: 28,
                interactive: false,
                reduceTransparency: reduceTransparency
            )
    }
}

private extension Color {
    static let appBackground = Color(light: 0xF4F3F0, dark: 0x121314)
    static let backdropTop = Color(light: 0xFFF8F1, dark: 0x211A16)
    static let backdropBottom = Color(light: 0xEFF4F6, dark: 0x10191D)
    static let coolGlow = Color(light: 0x7CCDE3, dark: 0x3E91A9)
    static let surface = Color(light: 0xFDFDFC, dark: 0x252628)
    static let surfaceAlt = Color(light: 0xF5F4F1, dark: 0x303134)
    static let controlBackground = Color(
        light: 0xE8E7E3,
        dark: 0x2C2D2F
    )
    static let selectionFill = Color(
        light: 0xFFFFFF,
        dark: 0x3A3B3E
    ).opacity(0.82)
    static let historyGlassTint = Color(
        light: 0xFFFFFF,
        dark: 0x202123
    ).opacity(0.12)
    static let border = Color(light: 0xDEDDD8, dark: 0x45474A)
    static let primaryText = Color(light: 0x171717, dark: 0xF6F4F1)
    static let mutedText = Color(light: 0x6F7074, dark: 0xB6B7BA)
    static let faintText = Color(light: 0x96979B, dark: 0x86878B)
    static let appAccent = Color(hex: 0xFF7500)
    static let accentHover = Color(hex: 0xE96900)
    static let accentButtonText = Color.white
    static let accentSoft = Color(light: 0xFFF0E3, dark: 0x432819)
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

import SwiftUI

struct CalculatorView: View {
    @StateObject private var model = CalculatorViewModel()
    @FocusState private var focusedField: CalculatorField?

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
                Color.appBackground.ignoresSafeArea()

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
                RoundedRectangle(cornerRadius: 15, style: .continuous)
                    .fill(Color.surface)
                    .shadow(
                        color: Color.shadowTint,
                        radius: 10,
                        x: 0,
                        y: 4
                    )
                Text(headerSymbol)
                    .font(.system(size: 21, weight: .bold, design: .rounded))
                    .foregroundStyle(Color.appAccent)
            }
            .frame(width: 50, height: 50)
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
            .background(Color.surface)
            .clipShape(Capsule())
            .shadow(
                color: Color.shadowTint,
                radius: 8,
                x: 0,
                y: 3
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
        HStack(spacing: 4) {
            ForEach(AppPage.allCases) { page in
                Button {
                    withAnimation(.easeInOut(duration: 0.18)) {
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
                                    cornerRadius: 13,
                                    style: .continuous
                                )
                                .fill(Color.surface)
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
        .padding(4)
        .background(Color.controlBackground)
        .clipShape(RoundedRectangle(cornerRadius: 17, style: .continuous))
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

            if model.mode == .standard {
                standardResults(useWideLayout: useWideLayout)

                if useWideLayout {
                    Spacer(minLength: 24)
                }

                standardInputPanel(useWideLayout: useWideLayout)
            } else {
                multiplyAddResults

                if useWideLayout {
                    Spacer(minLength: 24)
                }

                multiplyAddInputPanel(useWideLayout: useWideLayout)
            }
        }
        .frame(
            maxWidth: .infinity,
            minHeight: useWideLayout ? minHeight : nil,
            alignment: .top
        )
    }

    private var modePicker: some View {
        HStack(spacing: 4) {
            ForEach(CalculatorMode.allCases) { mode in
                Button {
                    withAnimation(.easeInOut(duration: 0.18)) {
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
                                    cornerRadius: 12,
                                    style: .continuous
                                )
                                .fill(Color.surface)
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
        .padding(4)
        .background(Color.controlBackground)
        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
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
        .cardStyle()
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
        .cardStyle()
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
        .cardStyle()
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
        .cardStyle()
    }

    private func basicPage(
        useWideLayout: Bool,
        minHeight: CGFloat
    ) -> some View {
        VStack(spacing: 16) {
            basicResults

            if useWideLayout {
                Spacer(minLength: 24)
            }

            basicInputPanel(useWideLayout: useWideLayout)
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
        .cardStyle()
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
        .cardStyle()
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
            .buttonStyle(
                PrimaryActionButtonStyle(
                    height: useWideLayout ? 210 : 116
                )
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
        .cardStyle()
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
        HStack(spacing: 12) {
            Button {
                model.clear()
            } label: {
                Text("清空")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(SecondaryActionButtonStyle(height: 56))

            Button {
                model.calculate()
            } label: {
                Label(primaryTitle, systemImage: "equal")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(PrimaryActionButtonStyle(height: 56))
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
        .background(statusBackground)
        .clipShape(RoundedRectangle(cornerRadius: 15, style: .continuous))
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
    func cardStyle() -> some View {
        padding(22)
            .background(Color.surface)
            .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: 24, style: .continuous)
                    .stroke(Color.border, lineWidth: 1)
            }
            .shadow(color: Color.shadowTint, radius: 12, x: 0, y: 5)
    }
}

private extension Color {
    static let appBackground = Color(hex: 0xF5F5F3)
    static let surface = Color(hex: 0xFFFFFF)
    static let surfaceAlt = Color(hex: 0xF6F6F4)
    static let controlBackground = Color(hex: 0xEAEAE7)
    static let border = Color(hex: 0xE1E1DE)
    static let primaryText = Color(hex: 0x171717)
    static let mutedText = Color(hex: 0x6F7074)
    static let faintText = Color(hex: 0x96979B)
    static let appAccent = Color(hex: 0xFF7500)
    static let accentHover = Color(hex: 0xE96900)
    static let accentButtonText = Color.white
    static let accentSoft = Color(hex: 0xFFF0E3)
    static let accentBorder = Color(hex: 0xFFC68F)
    static let successText = Color(hex: 0x31825B)
    static let successSoft = Color(hex: 0xEAF7EF)
    static let errorText = Color(hex: 0xC74B4B)
    static let errorSoft = Color(hex: 0xFCEEEE)
    static let shadowTint = Color.black.opacity(0.07)
    static let accentShadow = Color(hex: 0xFF7500).opacity(0.22)

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

import SwiftUI

struct CalculatorView: View {
    @StateObject private var model = CalculatorViewModel()
    @FocusState private var focusedField: CalculatorField?

    private let pageMaxWidth: CGFloat = 980

    var body: some View {
        GeometryReader { geometry in
            ZStack {
                Color.appBackground.ignoresSafeArea()

                ScrollView {
                    VStack(spacing: 18) {
                        header
                        pagePicker
                        pageContent(useWideLayout: geometry.size.width >= 760)
                        statusBar
                        keyboardHint
                    }
                    .frame(maxWidth: pageMaxWidth)
                    .padding(
                        .horizontal,
                        geometry.size.width >= 760 ? 32 : 20
                    )
                    .padding(.vertical, geometry.size.width >= 760 ? 30 : 20)
                    .frame(maxWidth: .infinity)
                }
                .scrollDismissesKeyboard(.interactively)
            }
        }
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
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .fill(Color.accentSoft)
                    .overlay {
                        RoundedRectangle(cornerRadius: 14, style: .continuous)
                            .stroke(Color.accentBorder, lineWidth: 1)
                    }
                Text(headerSymbol)
                    .font(.system(size: 22, weight: .bold, design: .rounded))
                    .foregroundStyle(Color.appAccent)
            }
            .frame(width: 48, height: 48)
            .accessibilityHidden(true)

            VStack(alignment: .leading, spacing: 3) {
                Text("小秋计算器")
                    .font(.title2.weight(.bold))
                    .foregroundStyle(Color.primaryText)
                Text(model.subtitle)
                    .font(.subheadline)
                    .foregroundStyle(Color.mutedText)
            }
            Spacer()
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
        Picker("功能页面", selection: $model.page) {
            ForEach(AppPage.allCases) { page in
                Text(page.rawValue).tag(page)
            }
        }
        .pickerStyle(.segmented)
        .accessibilityHint("切换计算器、基础运算和快捷计数")
    }

    @ViewBuilder
    private func pageContent(useWideLayout: Bool) -> some View {
        switch model.page {
        case .calculator:
            calculatorPage(useWideLayout: useWideLayout)
        case .basic:
            basicPage(useWideLayout: useWideLayout)
        case .counter:
            counterPage
        }
    }

    private func calculatorPage(useWideLayout: Bool) -> some View {
        VStack(spacing: 16) {
            Picker("计算模式", selection: $model.mode) {
                ForEach(CalculatorMode.allCases) { mode in
                    Text(mode.rawValue).tag(mode)
                }
            }
            .pickerStyle(.segmented)
            .frame(maxWidth: 460)

            if model.mode == .standard {
                standardWorkspace(useWideLayout: useWideLayout)
            } else {
                multiplyAddWorkspace(useWideLayout: useWideLayout)
            }
        }
    }

    @ViewBuilder
    private func standardWorkspace(useWideLayout: Bool) -> some View {
        if useWideLayout {
            HStack(alignment: .top, spacing: 18) {
                VStack(spacing: 16) {
                    standardInputCard
                    actionButtons(primaryTitle: "计算结果")
                }
                .frame(maxWidth: .infinity)
                standardResults.frame(maxWidth: .infinity)
            }
        } else {
            VStack(spacing: 16) {
                standardInputCard
                actionButtons(primaryTitle: "计算结果")
                standardResults
            }
        }
    }

    private var standardInputCard: some View {
        VStack(alignment: .leading, spacing: 16) {
            sectionHeader(title: "双结果输入", detail: "实时计算")
            numericInput(
                field: .divisor,
                title: "可调除数",
                placeholder: CalculatorEngine.defaultDivisor
            )
            ViewThatFits(in: .horizontal) {
                HStack(alignment: .top, spacing: 12) {
                    numericInput(field: .a, title: "A 数据", placeholder: "120.5")
                    numericInput(field: .b, title: "B 数据", placeholder: "475")
                }
                VStack(spacing: 14) {
                    numericInput(field: .a, title: "A 数据", placeholder: "120.5")
                    numericInput(field: .b, title: "B 数据", placeholder: "475")
                }
            }
        }
        .cardStyle()
    }

    private var standardResults: some View {
        VStack(alignment: .leading, spacing: 10) {
            sectionHeader(title: "计算结果", detail: "最多保留 2 位小数")
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

    @ViewBuilder
    private func multiplyAddWorkspace(useWideLayout: Bool) -> some View {
        if useWideLayout {
            HStack(alignment: .top, spacing: 18) {
                VStack(spacing: 16) {
                    multiplyAddInputCard
                    actionButtons(primaryTitle: "计算结果")
                }
                .frame(maxWidth: .infinity)
                multiplyAddResults.frame(maxWidth: .infinity)
            }
        } else {
            VStack(spacing: 16) {
                multiplyAddInputCard
                actionButtons(primaryTitle: "计算结果")
                multiplyAddResults
            }
        }
    }

    private var multiplyAddInputCard: some View {
        VStack(alignment: .leading, spacing: 16) {
            sectionHeader(title: "乘加输入", detail: "系数默认 475")
            numericInput(
                field: .coefficient,
                title: "系数",
                placeholder: CalculatorEngine.defaultCoefficient
            )
            ViewThatFits(in: .horizontal) {
                HStack(alignment: .top, spacing: 12) {
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
                VStack(spacing: 14) {
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
        }
        .cardStyle()
    }

    private var multiplyAddResults: some View {
        VStack(alignment: .leading, spacing: 10) {
            sectionHeader(title: "乘加结果", detail: "实时更新")
            resultCard(
                title: "计算结果",
                formula: model.multiplyAddFormula,
                value: model.multiplyAddResult,
                featured: true
            )
        }
    }

    @ViewBuilder
    private func basicPage(useWideLayout: Bool) -> some View {
        if useWideLayout {
            HStack(alignment: .top, spacing: 18) {
                VStack(spacing: 16) {
                    basicInputCard
                    actionButtons(primaryTitle: "计算结果")
                }
                .frame(maxWidth: .infinity)
                basicResults.frame(maxWidth: .infinity)
            }
        } else {
            VStack(spacing: 16) {
                basicInputCard
                actionButtons(primaryTitle: "计算结果")
                basicResults
            }
        }
    }

    private var basicInputCard: some View {
        VStack(alignment: .leading, spacing: 16) {
            sectionHeader(title: "基础运算", detail: "固定值默认 475")
            numericInput(
                field: .fixedValue,
                title: "固定值",
                placeholder: CalculatorEngine.defaultFixedValue
            )
            Picker("运算符", selection: $model.basicOperation) {
                ForEach(BasicOperation.allCases) { operation in
                    Text(operation.rawValue).tag(operation)
                }
            }
            .pickerStyle(.segmented)
            numericInput(
                field: .operationValue,
                title: "运算值",
                placeholder: "25"
            )
        }
        .cardStyle()
    }

    private var basicResults: some View {
        VStack(alignment: .leading, spacing: 10) {
            sectionHeader(title: "运算结果", detail: "实时更新")
            resultCard(
                title: "计算结果",
                formula: model.basicFormula,
                value: model.basicResult,
                featured: true
            )
        }
    }

    private var counterPage: some View {
        VStack(spacing: 18) {
            VStack(spacing: 8) {
                Text("当前计数")
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(Color.mutedText)
                Text("\(model.counter)")
                    .font(.system(size: 68, weight: .bold, design: .rounded))
                    .foregroundStyle(Color.appAccent)
                    .monospacedDigit()
                    .minimumScaleFactor(0.45)
                    .lineLimit(1)
                    .frame(maxWidth: .infinity, minHeight: 116)
            }
            .cardStyle()

            Button {
                model.incrementCounter()
            } label: {
                Label("加 1", systemImage: "plus")
                    .font(.title2.bold())
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(PrimaryActionButtonStyle(height: 64))
            .keyboardShortcut(.space, modifiers: [])

            Button {
                model.resetCounter()
            } label: {
                Label("清零", systemImage: "arrow.counterclockwise")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(SecondaryActionButtonStyle())

            Text("在 iPad 连接实体键盘时，可按空格快速加一")
                .font(.caption)
                .foregroundStyle(Color.faintText)
        }
        .frame(maxWidth: 620)
    }

    private func numericInput(
        field: CalculatorField,
        title: String,
        placeholder: String
    ) -> some View {
        VStack(alignment: .leading, spacing: 7) {
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
            .padding(.horizontal, 14)
            .frame(height: 48)
            .background(Color.surfaceAlt)
            .clipShape(RoundedRectangle(cornerRadius: 11, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: 11, style: .continuous)
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
        HStack(spacing: 10) {
            Button {
                model.clear()
            } label: {
                Text("清空").frame(maxWidth: .infinity)
            }
            .buttonStyle(SecondaryActionButtonStyle())

            Button {
                model.calculate()
            } label: {
                Label(primaryTitle, systemImage: "equal")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(PrimaryActionButtonStyle())
        }
    }

    private func resultCard(
        title: String,
        formula: String,
        value: String,
        featured: Bool
    ) -> some View {
        HStack(spacing: 14) {
            if featured {
                Capsule()
                    .fill(Color.appAccent)
                    .frame(width: 4, height: 48)
                    .accessibilityHidden(true)
            }

            VStack(alignment: .leading, spacing: 3) {
                Text(title)
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(Color.primaryText)
                Text(formula)
                    .font(.caption)
                    .foregroundStyle(Color.mutedText)
                    .lineLimit(1)
            }
            Spacer(minLength: 12)
            Text(value)
                .font(resultFont(for: value))
                .foregroundStyle(
                    value == "—"
                        ? Color.faintText
                        : (featured ? Color.appAccent : Color.primaryText)
                )
                .lineLimit(1)
                .minimumScaleFactor(0.5)
                .monospacedDigit()
        }
        .padding(.horizontal, 16)
        .frame(minHeight: 84)
        .background(Color.surface)
        .clipShape(RoundedRectangle(cornerRadius: 15, style: .continuous))
        .overlay {
            RoundedRectangle(cornerRadius: 15, style: .continuous)
                .stroke(
                    featured ? Color.accentBorder : Color.border,
                    lineWidth: 1
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
        .padding(.horizontal, 14)
        .padding(.vertical, 11)
        .background(statusBackground)
        .clipShape(RoundedRectangle(cornerRadius: 11, style: .continuous))
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
            return .system(size: 27, weight: .bold, design: .rounded)
        }
        if value.count <= 18 {
            return .system(size: 22, weight: .bold, design: .rounded)
        }
        return .system(size: 17, weight: .bold, design: .rounded)
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
            return .surfaceAlt
        case .success:
            return .successSoft
        case .error:
            return .errorSoft
        }
    }
}

private struct PrimaryActionButtonStyle: ButtonStyle {
    var height: CGFloat = 50

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.headline)
            .foregroundStyle(Color.accentButtonText)
            .padding(.horizontal, 16)
            .frame(height: height)
            .background(
                configuration.isPressed
                    ? Color.accentHover
                    : Color.appAccent
            )
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
            .scaleEffect(configuration.isPressed ? 0.985 : 1)
            .animation(.easeOut(duration: 0.12), value: configuration.isPressed)
    }
}

private struct SecondaryActionButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.headline)
            .foregroundStyle(Color.primaryText)
            .padding(.horizontal, 16)
            .frame(height: 50)
            .background(
                configuration.isPressed ? Color.surfaceAlt : Color.surface
            )
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .stroke(Color.border, lineWidth: 1)
            }
            .scaleEffect(configuration.isPressed ? 0.985 : 1)
            .animation(.easeOut(duration: 0.12), value: configuration.isPressed)
    }
}

private extension View {
    func cardStyle() -> some View {
        padding(18)
            .background(Color.surface)
            .clipShape(RoundedRectangle(cornerRadius: 17, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: 17, style: .continuous)
                    .stroke(Color.border, lineWidth: 1)
            }
    }
}

private extension Color {
    static let appBackground = Color(hex: 0x0D0F12)
    static let surface = Color(hex: 0x171A1F)
    static let surfaceAlt = Color(hex: 0x1E2228)
    static let border = Color(hex: 0x303640)
    static let primaryText = Color(hex: 0xF4F6F8)
    static let mutedText = Color(hex: 0xA8B0BA)
    static let faintText = Color(hex: 0x7D8792)
    static let appAccent = Color(hex: 0xF28C28)
    static let accentHover = Color(hex: 0xFFA44F)
    static let accentButtonText = Color(hex: 0x19120C)
    static let accentSoft = Color(hex: 0x211C17)
    static let accentBorder = Color(hex: 0x704624)
    static let successText = Color(hex: 0x74D18A)
    static let successSoft = Color(hex: 0x112419)
    static let errorText = Color(hex: 0xFF9191)
    static let errorSoft = Color(hex: 0x351619)

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

#Preview("iPad") {
    CalculatorView()
        .frame(width: 1024, height: 768)
}

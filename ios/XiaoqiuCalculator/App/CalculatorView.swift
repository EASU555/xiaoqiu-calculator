import SwiftUI

struct CalculatorView: View {
    @StateObject private var model = CalculatorViewModel()
    @FocusState private var focusedField: CalculatorField?

    private let pageMaxWidth: CGFloat = 940

    var body: some View {
        GeometryReader { geometry in
            ZStack {
                Color.appBackground
                    .ignoresSafeArea()

                ScrollView {
                    VStack(spacing: 18) {
                        header
                        adaptiveWorkspace(
                            useWideLayout: geometry.size.width >= 760
                        )
                        statusBar
                        keyboardHint
                    }
                    .frame(maxWidth: pageMaxWidth)
                    .padding(.horizontal, horizontalPadding(for: geometry.size.width))
                    .padding(.vertical, geometry.size.width >= 760 ? 34 : 22)
                    .frame(maxWidth: .infinity)
                }
                .scrollDismissesKeyboard(.interactively)
            }
        }
        .toolbar {
            ToolbarItemGroup(placement: .keyboard) {
                Button("清空") {
                    model.clear()
                    focusedField = .a
                }
                Spacer()
                Button("计算") {
                    model.calculate()
                }
                .fontWeight(.semibold)
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
    }

    private var header: some View {
        ViewThatFits(in: .horizontal) {
            HStack(alignment: .center, spacing: 14) {
                appIdentity
                Spacer(minLength: 24)
                divisorControl
            }

            VStack(alignment: .leading, spacing: 16) {
                appIdentity
                divisorControl
                    .frame(maxWidth: 260, alignment: .leading)
            }
        }
    }

    private var appIdentity: some View {
        HStack(spacing: 13) {
            ZStack {
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .fill(Color.accentSoft)
                    .overlay {
                        RoundedRectangle(cornerRadius: 14, style: .continuous)
                            .stroke(Color.accentBorder, lineWidth: 1)
                    }

                Text("Σ")
                    .font(.system(size: 23, weight: .bold, design: .rounded))
                    .foregroundStyle(Color.appAccent)
            }
            .frame(width: 48, height: 48)
            .accessibilityHidden(true)

            VStack(alignment: .leading, spacing: 3) {
                Text("小秋计算器")
                    .font(.title2.weight(.bold))
                    .foregroundStyle(Color.primaryText)
                Text("一次输入，同时得到总数与除法结果")
                    .font(.subheadline)
                    .foregroundStyle(Color.mutedText)
            }
        }
    }

    private var divisorControl: some View {
        VStack(alignment: .trailing, spacing: 5) {
            Text("可调除数")
                .font(.caption)
                .foregroundStyle(Color.faintText)
                .frame(maxWidth: .infinity, alignment: .trailing)

            calculatorField(
                field: .divisor,
                placeholder: CalculatorEngine.defaultDivisor,
                alignment: .trailing,
                accessibilityLabel: "自定义除数"
            )
            .frame(width: 150)
        }
    }

    @ViewBuilder
    private func adaptiveWorkspace(useWideLayout: Bool) -> some View {
        if useWideLayout {
            HStack(alignment: .top, spacing: 18) {
                VStack(spacing: 16) {
                    inputCard
                    actionButtons
                }
                .frame(maxWidth: .infinity)

                resultsSection
                    .frame(maxWidth: .infinity)
            }
        } else {
            VStack(spacing: 16) {
                inputCard
                actionButtons
                resultsSection
            }
        }
    }

    private var inputCard: some View {
        VStack(alignment: .leading, spacing: 16) {
            sectionHeader(
                title: "输入数据",
                detail: "支持正负整数与小数"
            )

            ViewThatFits(in: .horizontal) {
                HStack(alignment: .top, spacing: 12) {
                    inputField(
                        field: .a,
                        title: "A 数据",
                        example: "例：120.5"
                    )
                    inputField(
                        field: .b,
                        title: "B 数据",
                        example: "例：475"
                    )
                }

                VStack(spacing: 14) {
                    inputField(
                        field: .a,
                        title: "A 数据",
                        example: "例：120.5"
                    )
                    inputField(
                        field: .b,
                        title: "B 数据",
                        example: "例：475"
                    )
                }
            }
        }
        .cardStyle()
    }

    private func inputField(
        field: CalculatorField,
        title: String,
        example: String
    ) -> some View {
        VStack(alignment: .leading, spacing: 7) {
            HStack {
                Text(title)
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(Color.primaryText)
                Spacer()
                Text(example)
                    .font(.caption)
                    .foregroundStyle(Color.faintText)
            }

            calculatorField(
                field: field,
                placeholder: field == .a ? "例如 120.5" : "例如 475",
                alignment: .trailing,
                accessibilityLabel: title
            )
        }
        .frame(maxWidth: .infinity)
    }

    private func calculatorField(
        field: CalculatorField,
        placeholder: String,
        alignment: TextAlignment,
        accessibilityLabel: String
    ) -> some View {
        TextField(
            placeholder,
            text: Binding(
                get: { model.text(for: field) },
                set: { model.update($0, for: field) }
            )
        )
        .font(.system(.title3, design: .rounded, weight: .medium))
        .foregroundStyle(Color.primaryText)
        .multilineTextAlignment(alignment)
        .keyboardType(.numbersAndPunctuation)
        .textInputAutocapitalization(.never)
        .autocorrectionDisabled()
        .focused($focusedField, equals: field)
        .submitLabel(field == .a ? .next : .done)
        .onSubmit {
            if field == .a {
                focusedField = .b
            } else {
                model.calculate()
            }
        }
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
        .accessibilityLabel(accessibilityLabel)
        .accessibilityHint("最多输入 64 个字符，支持负数和小数")
    }

    private var actionButtons: some View {
        HStack(spacing: 10) {
            Button {
                model.clear()
                focusedField = .a
            } label: {
                Text("清空")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(SecondaryActionButtonStyle())

            Button {
                model.calculate()
            } label: {
                Label("计算结果", systemImage: "equal")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(PrimaryActionButtonStyle())
        }
    }

    private var resultsSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            sectionHeader(
                title: "计算结果",
                detail: "自动四舍五入至 2 位"
            )

            VStack(spacing: 10) {
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
                .minimumScaleFactor(0.55)
                .monospacedDigit()
        }
        .padding(.horizontal, 16)
        .frame(minHeight: 82)
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
        Text("键盘工具栏可直接计算、清空或收起键盘")
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

    private func horizontalPadding(for width: CGFloat) -> CGFloat {
        width >= 760 ? 32 : 20
    }

    private func fieldBorderColor(_ field: CalculatorField) -> Color {
        if model.invalidField == field {
            return .errorText
        }
        if focusedField == field {
            return .appAccent
        }
        return .border
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
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.headline)
            .foregroundStyle(Color.accentButtonText)
            .padding(.horizontal, 16)
            .frame(height: 50)
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
                configuration.isPressed
                    ? Color.surfaceAlt
                    : Color.surface
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

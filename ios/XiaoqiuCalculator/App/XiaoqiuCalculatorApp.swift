import SwiftUI

@main
struct XiaoqiuCalculatorApp: App {
    var body: some Scene {
        WindowGroup {
            CalculatorView()
                .preferredColorScheme(.light)
        }
    }
}

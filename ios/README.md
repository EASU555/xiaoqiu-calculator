# 小秋计算器 iOS

原生 SwiftUI 通用应用，同一个工程同时支持 iPhone 和 iPad。

## 系统要求

- iOS / iPadOS 16.0 或更高版本
- Xcode 16 或兼容版本
- 无第三方运行时依赖

## 工程

打开：

```text
ios/XiaoqiuCalculator.xcodeproj
```

默认 Bundle ID：

```text
com.easu555.xiaoqiucalculator
```

## 功能一致性

- 同时计算 `A + B` 与 `B ÷ 自定义除数`
- 默认除数为 `475`
- 支持正负整数、小数和最多 64 字符输入
- 使用字符串大数运算，避免二进制浮点误差
- 使用 `ROUND_HALF_UP` 规则保留两位小数并移除无意义的末尾 `0`
- 拒绝除数为 `0`、非法输入和超过 24 个显示字符的结果
- iPhone 使用紧凑单栏布局，iPad 宽屏自动切换为双栏布局

## 无签名 IPA

`.github/workflows/build-ios.yml` 会在 GitHub 的 macOS 环境中：

1. 编译 iOS 模拟器版本并运行单元测试。
2. 编译未签名的真机 Release 版本。
3. 将 `.app` 封装为 `XiaoqiuCalculator-unsigned.ipa`。
4. 上传 Actions artifact，并在开发分支生成公开的预发布下载。

该 IPA 需要使用自己的开发者证书重新签名后才能安装。

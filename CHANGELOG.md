# v1.0.0 — 2026-07-17

首个公开版本。

## 功能

- 输入 A、B，同时计算 `A + B` 与 `B ÷ 自定义除数`。
- 除数默认 475，可修改为其他整数或小数。
- 结果四舍五入到 2 位，并省略无意义的末尾 0。
- 支持回车计算、Esc 清空和完整键盘焦点路径。

## 稳定性与安全修复

- 修复超长数字和极小除数触发 `decimal.InvalidOperation` 的崩溃路径。
- 增加输入长度、结果长度和除零保护。
- 使用高精度 Decimal 计算上下文，并为长结果自动调整字号。
- 固定 Python 与 GitHub Actions 依赖版本。
- 添加 8 项边界与回归测试，以及 Windows 自动构建流程。
- 依赖漏洞扫描结果：未发现已知漏洞。

## Windows 可执行文件

- 文件：`ABCalculator.exe`
- SHA-256：`6A4DD5DBC92ABB9DC775F2B9EFF463FD101CC163CCD3F7DBCDB76E7BE985EA1F`

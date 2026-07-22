# 小秋计算器

一个简洁的 Windows 桌面计算与计数工具，提供：

- 总数：`A + B`
- 单独结果：`B ÷ 自定义除数`（默认除数为 `475`）
- 独立快捷计数页：点击 `+1` 或按自定义快捷键加一，并可随时清零

界面使用 CustomTkinter 6，采用中性石墨黑与克制橙色主题，支持高 DPI/显示缩放、圆角控件、悬停与焦点反馈，并优先使用“微软雅黑 UI”显示中文。

结果按 2 位小数进行四舍五入，并省略末尾无意义的 0。例如 `3.00` 会显示为 `3`，`1.50` 会显示为 `1.5`。

## 下载 Windows EXE

从 [GitHub Releases](https://github.com/EASU555/xiaoqiu-calculator/releases/latest) 下载 `ABCalculator.exe`。这是单文件程序，无需安装 Python。

## 直接运行源码

需要 Windows 上安装 Python 3，并确保 Python 自带 Tkinter。双击 `run_calculator.bat` 即可启动；脚本会在缺少 CustomTkinter 时自动安装。

也可以在命令行运行：

```powershell
python calculator.py
```

## 打包为 EXE

双击 `build_exe.bat`。脚本会检查并安装 PyInstaller，然后生成：

```text
dist\ABCalculator.exe
```

生成的 `ABCalculator.exe` 可直接在 Windows 上运行，不需要用户单独打开命令行。

如果希望手动执行打包命令：

```powershell
python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --clean --onefile --windowed --exclude-module numpy --icon app_icon.ico --add-data "app_icon.ico;." --name ABCalculator calculator.py
```

## 输入规则

- 支持整数和小数，例如 `120`、`12.5`、`.5`。
- 支持负数，例如 `-10.25`。
- 右上角除数默认为 `475`，可直接修改为其他整数或小数；除数不能为 `0`。
- 输入为空或不是数字时，界面会在底部显示提示。
- 单个输入最多 64 个字符；过长输入或无法安全显示的超大结果会被拒绝，而不会让程序崩溃。
- 回车键计算，Esc 键清空 A、B；有效的自定义除数会继续保留。
- 计数快捷键默认为 `Space`。点击计数器中的“快捷键”标签，再按一个可用按键即可重新绑定；按 `Esc` 可取消绑定。
- 自定义计数快捷键会自动保存到 `%APPDATA%\XiaoqiuCalculator\settings.json`，下次启动继续使用。
- 字母、数字、标点、方向键、功能键和数字小键盘均支持绑定；程序同时记录 Windows 按键码，以兼容中文输入法和特殊键盘布局。
- 回车、Esc、Tab 和单独的 Ctrl/Alt/Shift 等操作键不会被占用；输入框获得焦点时，绑定键不会误触计数。
- 点击窗口顶部“快捷计数”按钮可进入独立计数页，点击“返回计算”或按 `Esc` 返回；计数快捷键只在计数页生效。

## 测试与稳定性

```powershell
python -m unittest discover -s tests -v
```

- 使用高精度 Decimal 上下文，覆盖超长数字、极小除数、除数为 0、非法格式和四舍五入边界。
- 依赖使用精确版本，GitHub Actions 也固定到具体提交，减少构建结果漂移与供应链风险。
- EXE 本身不联网、不读取无关用户文件，也不会写入注册表；只在 `%APPDATA%\XiaoqiuCalculator` 保存计数快捷键设置。
- 每次推送都会在 Windows 环境运行测试并重新构建 EXE artifact。

## 界面决策

- Surface：轻量 Windows 工具，采用 Fluent 风格的低层级描边、圆角与语义状态反馈。
- 桌面 archetype：command center；主要对象是一次计算任务，主操作是“计算”。
- 布局：固定标题与页面切换 → 独立计算器页 / 独立快捷计数页 → 页面状态提示。
- 视觉锚点：计算器页使用两个独立结果面板；计数页使用大号计数仪表、主计数按钮和单独快捷键设置区。
- 设计约束：使用“微软雅黑 UI”中文字体、中性石墨灰层级与单一焦橙色主操作；橙色仅用于主按钮、焦点和总数强调，成功与错误保留绿/红语义。

# AutoShutdown v1.3.1 EvolveUI/Fluent Polish 设计

## 背景

用户在仓库根目录新增了 `build/` 参考文件夹。该目录包含一个 Qt/QML 打包产物 `appEvolveUI.exe`，以及 Qt Quick Controls 的 Basic、FluentWinUI3 控件资源。虽然这些 QML 组件不能直接在 WPF 项目中复用，但其设计模式可以迁移到 AutoShutdown 的 WPF 主题和控件样式中。

v1.3 已完成透明轻二次元主题和侧边导航布局。v1.3.1 的目标是在不大改业务逻辑的前提下，参考 EvolveUI/Fluent 的组件思路继续打磨 UI 细节，让界面更像成熟组件库驱动的桌面应用。

## 目标

- 发布 v1.3.1，作为 v1.3 的 UI polish 更新。
- 参考 EvolveUI 的 `ETheme` 思路，把更多硬编码颜色提炼到 `DarkTheme.xaml`。
- 参考 FluentWinUI3 的 Button/TextField/ItemDelegate/Switch 交互状态，优化 WPF 控件状态。
- 参考 EBlurCard/EHoverCard，强化玻璃卡片和 hover 卡片样式。
- 参考 EAccordion，将复杂模块内的高级配置做成更清晰的分组或折叠视觉。
- 保留现有业务功能和事件处理逻辑。

## 非目标

- 不把项目从 WPF 迁移到 Qt/QML。
- 不直接依赖或复制 `build/` 里的 Qt DLL/QML 文件。
- 不提交 `build/` 目录或发布产物到 git。
- 不新增新的定时/关机业务功能。

## 参考点

### ETheme

参考中有统一主题对象：

- `primaryColor`
- `secondaryColor`
- `textColor`
- `borderColor`
- `blurOverlayColor`
- `focusColor`
- `shadowColor`
- `isDark`

WPF 对应做法：在 `DarkTheme.xaml` 中增加语义资源，例如：

- `GlassSurfaceBrush`
- `GlassSurfaceHoverBrush`
- `GlassBorderBrush`
- `FocusAccentBrush`
- `NavItemBrush`
- `NavItemHoverBrush`
- `NavIndicatorBrush`
- `InputFocusBrush`

### EButton / Fluent Button

参考特征：

- 按钮状态由 normal/hovered/pressed/disabled 驱动。
- 图标和文字间距统一。
- Hover/Pressed 主要改变背景层和文字透明度，而不是大幅缩放。

WPF 对应做法：

- 更新 Button 模板。
- Hover 时使用轻微背景高亮和边框高亮。
- Pressed 时使用轻微压暗，而不是明显缩放。
- Disabled 状态降低透明度并保持可识别边界。

### TextField / ComboBox

参考特征：

- 输入框聚焦时底部出现 2px accent 线。
- ComboBox 打开/聚焦时突出底部焦点线。

WPF 对应做法：

- TextBox 模板增加底部 FocusStroke。
- ComboBox 增加基础样式，至少保证背景、前景、边框和可编辑文本区域符合主题。

### ItemDelegate / Sidebar

参考特征：

- 选中项左侧有 3px accent 指示条。
- Hover/Pressed/Selected 是不同状态。

WPF 对应做法：

- 侧边导航项不再只靠整块渐变。
- 新增左侧 3px 指示条。
- Active 状态使用透明玻璃底 + accent 指示条 + 字重。
- Hover 状态只轻微高亮。

### EAccordion

参考特征：

- 复杂内容分组，标题栏可突出，内容区可收纳。

WPF 对应做法：

- v1.3.1 不一定实现完整动态折叠。
- 先将“智能触发”页里的网络闲置和进程退出包装成更明显的分组卡片，标题行带 accent 指示。
- 如果实现折叠成本低，可为智能触发分组加入展开/收起按钮；否则先做静态分组视觉。

## 实现范围

### DarkTheme.xaml

- 增加语义色刷。
- 增加/更新：
  - `CardBorder`
  - `GlassPanel`
  - `PrimaryButton`
  - `SecondaryButton`
  - `DangerButton`
  - TextBox 样式
  - ComboBox 样式
- 尽量减少 `MainWindow.xaml` 中散落的硬编码透明色。

### MainWindow.xaml

- 侧边导航项改成带左侧指示条的结构。
- 智能触发页分组更接近组件库风格。
- 卡片标题和副标题间距更一致。
- 保持所有 x:Name 和 Click 事件不变。

### MainWindow.xaml.cs

- `UpdateNavigationUI()` 需要适配新的导航项结构。
- 如果导航项内部加入指示条，需要通过 `FindName` 或单独命名指示条更新颜色/可见性。
- 不改变定时、触发、脚本、发布等业务逻辑。

## 发布

v1.3.1 完成后：

1. 构建 Debug 验证。
2. Publish Release win-x64 single-file。
3. 打包 `AutoShutdown-v1.3.1-win-x64.zip`。
4. 创建 GitHub Release `v1.3.1`。
5. 推送代码到 `main`。

## 验证

- `dotnet build "AutoShutdown/AutoShutdown.csproj"` 必须通过。
- 检查 XAML 编译无命名控件或事件错误。
- 侧边导航切换仍可用。
- ComboBox/TextBox 在深色透明背景下可读。
- 不真实触发关机/重启。

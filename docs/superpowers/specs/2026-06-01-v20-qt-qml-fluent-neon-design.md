# AutoShutdown v2.0-preview Qt/QML Fluent Neon 设计

## 背景

v1.4 的 WPF Neon Command Center 已经比 v1.3.1 更明显，但整体仍受限于 WPF 的视觉上限：布局和交互仍像传统桌面工具，难以达到用户希望的“最好看”效果。用户明确表示“不需要快，就好看的”，并确认可以不继续使用 C#/WPF。

仓库根目录的 `build/` 是 Qt 部署产物，包含 `appEvolveUI.exe`、Qt Quick Controls、FluentWinUI3 样式和 Qt 插件。它不是源码项目：没有 `CMakeLists.txt`、`.cpp`、`.h` 或业务 `Main.qml`。因此不能直接修改 `build/` 变成 AutoShutdown 新版，但它证明目标视觉方向应采用 Qt Quick/QML + FluentWinUI3。

v2.0-preview 将作为一次技术栈和视觉语言预览版：新建源码项目 `AutoShutdownQt/`，使用 C++ Qt 6 + QML + FluentWinUI3 风格重做 AutoShutdown 的高质量桌面前端。

## 目标

- 新建 `AutoShutdownQt/`，作为 Qt/QML 版本源码项目。
- 使用 C++ Qt 6 + QML，而不是 WPF 或 PySide6。
- 视觉方向为 **Fluent Neon Control Deck**：暗色亚克力、Fluent 控件、蓝紫粉高光、流畅动画。
- 第一版优先做“最好看”的核心体验：倒计时、指定时间、动作选择、当前状态、取消任务、立即执行。
- 保留现有 WPF 项目，不删除、不破坏；Qt 版先作为 `v2.0-preview` 并行预览。
- 不提交 `build/` 参考目录或 Qt 部署产物到 git。
- 最终发布 `v2.0-preview` GitHub Release，发布 Qt 版 zip。

## 非目标

- 不直接修改或提交 `build/`。
- 不尝试反编译 `appEvolveUI.exe`。
- 不把现有 WPF XAML 继续打磨成最终 UI。
- 首个 Qt 预览版不要求一次性迁移所有高级功能。
- 首个 Qt 预览版不要求完整迁移：任务中心、网络闲置触发、进程退出触发、执行前脚本、托盘菜单全部高级项。
- 不真实测试关机/重启等 destructive 动作；实现代码要有清晰边界，验证时只做安全路径。

## 技术路线

采用：**C++ Qt 6 + QML + CMake**。

原因：

- Qt Quick/QML 的渲染、动画和状态系统更适合高质量现代 UI。
- C++ 后台适合长期桌面软件，避免 PySide6 打包体积和运行时层级。
- Qt Quick Controls 的 FluentWinUI3 样式可提供更接近 Windows 11 的控件质感。
- CMake 是 Qt 6 标准项目组织方式，后续可用 `windeployqt` 打包。

## 项目结构

新增：

```text
AutoShutdownQt/
  CMakeLists.txt
  src/
    main.cpp
    AppController.h
    AppController.cpp
    PowerService.h
    PowerService.cpp
    CountdownTimer.h
    CountdownTimer.cpp
  qml/
    Main.qml
    Theme.qml
    components/
      AcrylicBackground.qml
      SidebarItem.qml
      NeonCard.qml
      StatusHero.qml
      ActionTile.qml
      TimeInputPanel.qml
      FluentSwitchRow.qml
      StatusPill.qml
```

职责：

- `main.cpp`
  - 初始化 `QGuiApplication`。
  - 设置 Quick Controls 样式为 FluentWinUI3（如果本机 Qt 支持）。
  - 注册 `AppController` 到 QML。
  - 加载 `qml/Main.qml`。

- `AppController`
  - QML 可绑定的应用状态中心。
  - 暴露当前动作、倒计时时间、运行状态、目标时间、强制关闭状态。
  - 提供 QML 可调用方法：启动倒计时、启动指定时间、取消、立即执行、切换动作、切换强制关闭。

- `PowerService`
  - 封装 Windows 电源动作命令。
  - 支持 Shutdown、Sleep、Hibernate、Restart、LogOut、Lock。
  - 提供 dry-run 友好的方法边界，验证阶段不直接调用 destructive 方法。

- `CountdownTimer`
  - 使用 `QTimer` 驱动倒计时。
  - 每秒更新剩余时间。
  - 到点后通知 `AppController` 执行动作。

- `Main.qml`
  - 应用窗口和页面布局。
  - 左侧导航 rail。
  - 首页 Control Deck。
  - 预留高级页面入口。

- `Theme.qml`
  - 语义色、半径、间距、动画时长。
  - 避免 QML 里散落硬编码颜色。

- `components/`
  - 放高复用视觉组件，保持 `Main.qml` 不膨胀。

## 视觉方向：Fluent Neon Control Deck

窗口建议尺寸：`1120 × 760`。

布局：

```text
┌───────────────────────────────────────────────────────────────┐
│ AutoShutdown v2.0-preview        READY / RUNNING       控制按钮 │
├──────────────┬────────────────────────────────────────────────┤
│ Fluent Rail   │  Hero Status Deck                              │
│              │  ┌──────────────────────────────────────────┐  │
│ Overview      │  │  当前动作     00:30:00                   │  │
│ Timer         │  │  大号倒计时 / 状态 / 目标时间             │  │
│ Actions       │  │  Start / Cancel / Execute                 │  │
│ Triggers      │  └──────────────────────────────────────────┘  │
│ Settings      │                                                │
│              │  Action Tiles + Schedule Composer + Summary     │
└──────────────┴────────────────────────────────────────────────┘
```

### 视觉关键词

- 暗色亚克力背景
- 玻璃磨砂卡片
- 蓝紫粉 Neon 高光，但控制用量
- FluentWinUI3 控件质感
- 统一圆角和阴影系统
- 大号倒计时数字，使用 tabular 数字
- 页面切换有淡入和轻微位移
- Hover 使用 reveal 光晕和状态层，不靠粗暴缩放

### 颜色系统

建议语义色：

- `bgDeep`: `#090D1F`
- `bgPanel`: `#172033`
- `surfaceGlass`: `#26FFFFFF`
- `surfaceStrong`: `#38FFFFFF`
- `borderSoft`: `#33DDF7FF`
- `borderStrong`: `#88DDF7FF`
- `primary`: `#79D8FF`
- `secondary`: `#B779FF`
- `accent`: `#FF8ACF`
- `success`: `#7DFFC4`
- `warning`: `#FFD166`
- `danger`: `#FF5C8A`
- `textPrimary`: `#FFF7FF`
- `textSecondary`: `#CDBFEA`

### 动画系统

- 页面切换：180–260ms，opacity + y translation。
- Button press：80–120ms，颜色/透明度变化，不改变布局尺寸。
- Card hover：120–180ms，边框和阴影增强。
- 倒计时 tick：轻微 glow 或 opacity pulse，不能每秒大幅跳动。
- 状态变化：READY/RUNNING/PAUSED 使用 pill 颜色和文字变化。

## 第一版功能范围

v2.0-preview 第一版必须具备：

1. 动作选择
   - Shutdown
   - Sleep
   - Hibernate
   - Restart
   - LogOut
   - Lock

2. 倒计时
   - 小时、分钟、秒输入。
   - 快捷 chips：15 分钟、30 分钟、1 小时、2 小时。
   - 启动、取消。
   - 运行中每秒更新剩余时间。

3. 指定时间
   - 时、分输入。
   - 如果目标时间已过，自动排到明天。

4. 当前状态
   - READY
   - RUNNING
   - COMPLETED 或 CANCELED 的短暂反馈。

5. 立即执行当前动作
   - UI 提供按钮。
   - destructive 动作前要弹出确认对话框。

6. 强制关闭开关
   - 第一版可先只影响 shutdown/restart 命令参数。

7. 安全验证开关
   - 开发/验证阶段可通过 controller 中的 `dryRun` 属性避免真实关机。
   - Release 默认可执行真实动作，但 UI 对 destructive 动作保留确认。

## 后续迁移范围

v2.0 正式版或后续 preview 再迁移：

- 任务中心
- 网络闲置触发
- 进程退出触发
- 执行前脚本
- 开机自启
- 托盘菜单
- 设置持久化
- 多语言/主题切换

## 与现有 WPF 版本关系

- WPF 版本继续保留在 `AutoShutdown/`。
- Qt 版本新增在 `AutoShutdownQt/`。
- 两者互不覆盖。
- v2.0-preview 发布时明确说明：这是全新 Qt/QML UI 预览版，功能先覆盖核心定时与动作执行。

## 打包与发布

构建方式：

```bash
cmake -S AutoShutdownQt -B AutoShutdownQt/build -DCMAKE_BUILD_TYPE=Release
cmake --build AutoShutdownQt/build --config Release
```

Windows 打包建议：

```bash
windeployqt AutoShutdownQt/build/Release/AutoShutdownQt.exe --qmldir AutoShutdownQt/qml
```

发布产物：

```text
AutoShutdownQt-v2.0-preview-win-x64.zip
```

GitHub Release：

- tag: `v2.0-preview`
- title: `AutoShutdown v2.0 Preview`

Release notes：

```text
AutoShutdown v2.0-preview：全新 C++ Qt 6 + QML Fluent Neon 预览版。重做主界面为 Fluent Neon Control Deck，提供核心倒计时、指定时间、动作选择和现代化动画体验。WPF 版本仍保留，Qt 版作为新视觉方向预览。
```

## 风险与约束

- 本机可能没有 Qt SDK/CMake 配置；如缺失，需要先安装 Qt 6 或使用现有 Qt 安装路径。
- `build/` 是参考部署产物，不能作为源码改造。
- Qt 版第一版不等价于 WPF 全功能版，发布时必须写明 preview 范围。
- 电源动作是 destructive 行为，开发验证必须使用 dry-run 或只测试锁屏等较安全动作。
- 如果缺少 Qt FluentWinUI3 style，可先用 Qt Quick Controls Basic + 自定义主题模拟 Fluent Neon；但源码结构仍保持 Qt/QML。

## 验证标准

- `AutoShutdownQt/` 有完整可读源码。
- CMake 配置能生成可执行文件。
- 运行后第一屏视觉明显不同于 WPF：暗色亚克力、Fluent rail、大号倒计时 Hero、动作 tiles。
- 倒计时启动后每秒更新。
- 取消任务能回到 READY。
- 立即执行前出现确认对话框。
- dry-run 模式下不会真实关机/重启。
- `build/` 不出现在 git status 中。
- Qt 构建输出和打包产物不提交到 git。

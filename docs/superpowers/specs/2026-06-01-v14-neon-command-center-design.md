# AutoShutdown v1.4 Neon Command Center UI 设计

## 背景

v1.3.1 已完成 EvolveUI/Fluent 方向的细节 polish，但实际视觉变化太弱：主界面仍显示 `AutoShutdown v1.3` / `v1.3 · Glass Anime`，新增变化主要集中在小型状态层和智能触发页的细线装饰。用户需要的是打开应用第一眼就能感知到的 UI 大改，而不是继续做小修。

v1.4 将从“透明轻二次元卡片页”升级为 **Neon Command Center**：保留 WPF 与现有业务逻辑，重排首页信息架构，强化倒计时状态、当前动作、侧边导航、智能触发分组和组件状态。

## 目标

- 发布 v1.4，作为一次明显的 UI 大改版本。
- 风格采用 **EvolveUI Neon / 酷炫玻璃风格**。
- 允许重排主界面信息架构，但保留现有功能和事件逻辑。
- 打开第一屏必须明显不同于 v1.3/v1.3.1。
- 总览页变成控制中心：大状态 Hero、当前动作、快捷倒计时、配置摘要、电源动作网格。
- 智能触发页做成明显的 EAccordion 风格静态分组，而不是只加细线。
- 发布 `v1.4` GitHub Release，并继续保证 `build/` 只是本地参考，不提交到 GitHub。

## 非目标

- 不迁移到 Qt/QML。
- 不依赖或复制 `build/` 里的 Qt/QML 运行时。
- 不新增关机、触发、任务、脚本等业务能力。
- 不改变网络闲置、进程退出、任务调度、执行前脚本的核心算法。
- 不提交 `build/`、`publish/`、zip 发布产物到 git。
- 不先实现复杂折叠动画；智能触发分组先做静态展开的 Accordion 视觉。

## 设计方向

选定方案：**Neon Command Center**。

窗口仍是单窗口 WPF 应用，但视觉和信息架构重排为：

```text
┌──────────────────────────────────────────────────────────────┐
│ AutoShutdown v1.4 · Neon Command Center / 状态 Badge / 窗口按钮 │
├──────────────┬───────────────────────────────────────────────┤
│ Neon 侧边导航 │ 主控制台首页                                  │
│              │ ┌───────────────────────────────────────────┐ │
│ 总览         │ │ 大型倒计时/状态 Hero Card                  │ │
│ 定时         │ │ 当前动作、剩余时间、启动/取消/暂停按钮       │ │
│ 任务         │ └───────────────────────────────────────────┘ │
│ 智能触发     │ ┌───────────────┬───────────────────────────┐ │
│ 脚本         │ │ 快捷倒计时     │ 当前配置摘要               │ │
│ 设置         │ └───────────────┴───────────────────────────┘ │
│              │ 电源动作 6 宫格 / 发光选中态                  │
└──────────────┴───────────────────────────────────────────────┘
```

## 视觉系统

### 风格关键词

- 深色玻璃背景
- 粉紫蓝 Neon 渐变
- 更强的发光边框和状态光晕
- 大字号倒计时和状态标签
- 明显的 hover / selected / active 状态
- 类 EvolveUI 组件库感，同时保留轻二次元气质

### Theme 资源

在 `DarkTheme.xaml` 中新增或强化 v1.4 语义资源：

- Neon 背景：`CommandBackgroundBrush`
- 主 Hero：`CommandHeroBrush` / `HeroGlowBrush`
- 强化卡片：`CommandCardBrush` / `CommandCardBorderBrush`
- 导航：`NavPillBrush` / `NavPillActiveBrush` / `NavPillIndicatorBrush`
- 状态：`StatusReadyBrush` / `StatusRunningBrush` / `StatusPausedBrush`
- 动作卡：`ActionTileBrush` / `ActionTileActiveBrush`
- Badge/Chip：`BadgeBrush` / `ChipBrush` / `ChipHoverBrush`

现有 `HeroBrush`、`GlassSurfaceBrush`、`GlassBorderBrush`、`ToggleOffBrush` 等资源可以保留，并作为兼容资源继续使用。

## 页面设计

### 顶部 Hero Bar

顶部标题从 `AutoShutdown v1.3` 改为：

- `AutoShutdown v1.4`
- `Neon Command Center`

右侧保留最小化到托盘和隐藏到托盘按钮，但视觉改成 neon icon button。顶部还显示一个状态 badge：

- 未运行：`READY`
- 运行中：`RUNNING`
- 暂停：`PAUSED`

### 侧边导航

侧边栏从普通玻璃面板升级为 Neon Nav：

- 每个导航项是胶囊卡片。
- 选中项有左侧发光指示条、边框高亮和轻微 glow。
- 文字更清晰，建议保留中文标签。
- 可加入 Segoe MDL2 Assets 图标，提升视觉变化。
- 当前版本信息改为 `v1.4 · Neon Center`。

必须保留导航目标：

- 总览
- 定时
- 任务
- 智能触发
- 脚本
- 设置

### 总览页：Command Center

总览页是本次大改核心。

#### 大型状态 Hero Card

未启动时显示：

- 状态：`READY`
- 当前动作：关机 / 睡眠 / 重启等
- 默认倒计时：例如 `00:30:00`
- 主按钮：`启动倒计时`
- 次按钮：`立即执行当前动作`

运行中显示：

- 状态：`RUNNING`
- 大号剩余时间
- 计划执行时间
- 执行动作
- `暂停 1 小时`
- `取消任务计划`

暂停时显示：

- 状态：`PAUSED`
- 恢复后的剩余时间
- 自动恢复时间
- `恢复任务`
- `取消任务计划`

现有 `StatusCard` 可以被改造成 Hero Card，或新增独立控件再让 `UpdateStatusUI()` 同步更新。

#### 电源动作 Neon Grid

保留 6 个动作：

- 关机
- 睡眠
- 休眠
- 重启
- 注销
- 锁定

每个动作变成更大的 action tile：

- 中文主标题
- 英文短标签
- 图标或发光点
- 当前选中项使用 Neon 渐变和 glow

#### 快捷倒计时 Chips

保留：

- 15 分钟
- 30 分钟
- 1 小时
- 2 小时

点击后仍只填入倒计时时间，不直接执行，避免误触发。Hero Card 上应能立即看到默认倒计时变化。

#### 当前配置摘要

新增或强化摘要区：

- 当前动作
- 提醒提前时间
- 强制关闭应用状态
- 默认重复规则
- 执行前脚本状态

摘要区只展示状态，不新增业务逻辑。

### 定时页：高级定时配置

定时页变成详细配置区，不再承担第一屏主视觉。

布局建议：

- 左侧：倒计时模式面板，包含小时/分钟/秒输入。
- 右侧：指定时间模式面板，包含时/分输入。
- 下方：重复规则 chips。
- 保留启动按钮。

现有模式切换逻辑可以保留，但视觉要更像两个高级配置面板。

### 任务页：Neon Task Cards

任务功能不变：

- 保存当前为任务
- 运行最近启用任务
- 启用/禁用
- 应用
- 删除

视觉改成任务卡片：

- 启用任务有 glow 状态点和高亮边框。
- 禁用任务降低透明度。
- 下次执行时间作为 badge 显示。
- 操作按钮统一为 compact neon button。

### 智能触发页：静态 EAccordion 分组

这次必须明显区别于 v1.3.1 的细线 polish。

#### 网络闲置触发分组

标题栏：

- 图标
- `网络闲置触发`
- 状态 badge

内容区：

- 下载阈值
- 上传阈值
- 持续分钟
- 开始监控 / 停止监控
- 当前速度
- 闲置进度

#### 进程退出触发分组

标题栏：

- 图标
- `进程退出触发`
- 状态 badge

内容区：

- 进程选择 ComboBox
- 刷新进程
- 开始监控 / 停止监控
- 自动关闭被监控程序子面板
- 进程状态
- 自动关闭状态

Accordion 视觉要求：标题栏、内容区、内嵌子面板必须明显分层。默认全部展开，不实现折叠动画。

### 脚本页

功能不变，视觉统一：

- 路径输入区
- 选择脚本按钮
- 启用脚本按钮
- 超时秒数输入
- 脚本状态

整体放入一张完整 Neon 面板。

### 设置页

功能不变，视觉统一：

- 提醒提前时间
- 强制关闭应用
- 开机自动启动

开关统一使用 `ApplyToggleVisual(...)` 视觉 helper。

## 实现边界

### 修改文件

- `AutoShutdown/Themes/DarkTheme.xaml`
  - 新增 v1.4 Neon 资源和样式。
- `AutoShutdown/MainWindow.xaml`
  - 重排主窗口和各页面布局。
  - 更新版本显示到 v1.4。
- `AutoShutdown/MainWindow.xaml.cs`
  - 保留现有业务逻辑。
  - 适配新的 UI 控件结构。
  - 必要时新增小型 UI helper。
- `docs/superpowers/plans/2026-06-01-v14-neon-command-center.md`
  - 后续实施计划。

### 控件命名策略

优先保留现有 `x:Name`，包括但不限于：

- `HoursInput` / `MinutesInput` / `SecondsInput`
- `FixedHourInput` / `FixedMinuteInput`
- `ActionShutdown` / `ActionSleep` / `ActionHibernate` / `ActionRestart` / `ActionLogOut` / `ActionLock`
- `StatusCard` / `StatusTitle` / `RemainingLabel` / `RemainingTime`
- `TargetTimeLabel` / `ShutdownModeLabel`
- `PauseResumeButton` / `CancelPlanButton`
- `NetworkDownloadThresholdInput` / `NetworkUploadThresholdInput` / `NetworkIdleMinutesInput`
- `ProcessListCombo` / `ProcessAutoCloseToggle` / `ProcessAutoCloseKnob`
- `ForceCloseToggle` / `ForceCloseKnob`
- `AutoStartToggle` / `AutoStartKnob`
- 所有导航项和导航 indicator

如果新增首页 Hero 控件，需要让现有状态更新方法同步更新，不能让首页显示旧状态。

## 风险控制

1. 保留关键控件名和事件处理器，降低 XAML 编译风险。
2. 分阶段实施和提交：主题资源、总览页、子页面、发布。
3. 每阶段执行 `dotnet build "AutoShutdown/AutoShutdown.csproj"`。
4. 发布前实际启动 exe，确认第一屏显示 v1.4 且视觉明显不同。
5. 不真实触发关机/重启/注销等 destructive 动作。
6. 如果 publish 遇到 exe 被占用，先停止 `AutoShutdown` 进程再重试。

## 验证标准

- Debug build 通过，0 error。
- Release publish 通过。
- 生成 `AutoShutdown-v1.4-win-x64.zip`。
- 实际启动新 exe 后，第一屏显示 `AutoShutdown v1.4` 和 `Neon Command Center`。
- 首页布局明显不同于 v1.3：有大型状态 Hero、快捷 chips、配置摘要和更强 action tile。
- 智能触发页是明显的 Accordion 分组面板。
- 侧边导航选中态明显。
- `build/`、`AutoShutdown/publish/`、zip 均不出现在 git status 中。

## 发布

v1.4 完成后：

1. `dotnet build "AutoShutdown/AutoShutdown.csproj"`
2. `dotnet publish "AutoShutdown/AutoShutdown.csproj" -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:EnableCompressionInSingleFile=true -o "AutoShutdown/publish"`
3. 打包 `AutoShutdown/AutoShutdown-v1.4-win-x64.zip`
4. 创建 GitHub Release `v1.4`
5. 推送 `main`

Release notes 建议：

```text
AutoShutdown v1.4 更新：全新 Neon Command Center 首页，参考 EvolveUI Neon 风格重做主界面；强化倒计时状态 Hero、侧边导航、电源动作网格和智能触发分组视觉，同时保留 v1.3.1 的稳定功能。
```

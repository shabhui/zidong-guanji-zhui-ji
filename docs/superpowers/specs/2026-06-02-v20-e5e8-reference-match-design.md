# AutoShutdownQt v2.0 e5e8 Reference Match UI 设计

## 背景

当前 AutoShutdownQt v2.0 方向已经从 v1.x WPF 进入 PySide6/QML 预览线，并已有 `Starry Glass Control Deck` 设计与实现基础。但用户反馈当前渲染仍不像目标图，要求“学我 e5e8 的图片，更改 UI”。

本次设计明确以 `AutoShutdownQt/e5e8b88f-7acc-4be7-930f-952ad1670984.png` 作为视觉参考，采用 **高度复刻** 策略：尽量贴近参考图的粉紫蓝星空、半透明毛玻璃、右侧 anime 视觉位、霓虹标题和大卡片构图，同时保留 AutoShutdown 的现有功能与安全逻辑。

## 目标

- 将 AutoShutdownQt v2.0 改成第一眼明显接近 e5e8 参考图的 UI。
- 背景从普通深色/灰色控制台升级为粉紫蓝星空渐变。
- 主体使用大圆角半透明玻璃 shell，外边缘有柔和 glow。
- 左侧导航升级为 glass rail，active 项有粉蓝渐变指示条和高亮胶囊。
- 总览页形成“左导航 / 中控制 / 右抽象角色视觉位”的构图。
- 右侧增加明显的抽象 anime 视觉位，但不引入真实人物图片素材。
- 去掉大面积纯灰方块，让卡片、按钮、输入框都采用玻璃与霓虹状态。
- 保留现有 PySide6/QML 技术栈和 controller 业务逻辑。
- 首页必须显示 `AutoShutdown v2.0`，避免用户误以为没有升级。

## 非目标

- 不回到 WPF v1.x 线。
- 不迁移到 Qt/C++。
- 不重写 `controller.py`、`power_service.py` 的业务逻辑。
- 不真实测试关机、重启、注销等破坏性动作。
- 不引入外部真实 anime 人物图片素材。
- 不提交 `build/`、publish 目录、zip 发布产物到 git。
- 不先实现复杂 shader、复杂粒子系统或高成本 Canvas 动画。

## 选定方案

选定方案：**e5e8 高度复刻版**。

方案含义：

- 不是只借鉴颜色。
- 不是只套一层主题皮肤。
- 而是重做主构图，使当前 v2.0 打开后在氛围、层级和视觉重心上接近参考图。

总体布局：

```text
┌──────────────────────────────────────────────────────────────┐
│ 粉紫蓝星空渐变背景 + 柔光星点 + 流光                         │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ 顶部：AutoShutdown v2.0 / Starry Glass / 状态 badge       │ │
│ ├───────────────┬───────────────────────┬──────────────────┤ │
│ │ 玻璃侧边导航   │ 主控制玻璃面板          │ 抽象角色视觉位     │ │
│ │ 总览          │ 大倒计时                │ 发光剪影/星云轮廓  │ │
│ │ 定时          │ 当前动作                │ 不用真实人物素材    │ │
│ │ 任务          │ 主要按钮                │ 但构图像参考图右侧  │ │
│ │ 智能触发      │ 快捷 chips              │                  │ │
│ │ 脚本/设置     │ 电源动作 tiles           │                  │ │
│ └───────────────┴───────────────────────┴──────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

## 视觉系统

### 色彩

新增 e5e8 风格语义 token，建议放入 `AutoShutdownQt/qml/Theme.qml`：

- 背景深色：`#090A1F`、`#111334`、`#1A1044`
- 主粉色：`#FF6FD8`
- 主紫色：`#9B5CFF`
- 主蓝色：`#4CC9FF`
- 星光白：`#F7F2FF`
- 成功绿：`#62F6B5`
- 警告橙：`#FFD166`
- 危险红：`#FF5C8A`
- 玻璃底：半透明深蓝紫，不使用纯灰
- 玻璃边框：粉/紫/蓝低透明描边
- glow：粉紫蓝低透明外发光

### 背景层

`Main.qml` 的背景由四层组成：

1. 深蓝紫基础渐变。
2. 3–5 个大型柔光光球，颜色为粉、紫、蓝，透明度低。
3. 星点层，小圆点错落分布，部分低频闪烁。
4. 大号玻璃 shell，承载标题栏、导航和内容。

动画节奏：

- 光球漂浮周期 8–12 秒。
- 星点闪烁低频且透明度变化小。
- 不做快速、大幅位移动画。

### 玻璃卡片

所有主要卡片都应满足：

- 大圆角。
- 半透明深色底。
- 粉紫蓝边框或顶部高光。
- hover 时边框更亮、底色稍微提升。
- selected 状态必须比 hover 更强。
- 文本区域要有足够深的底层，不能被背景干扰。

### 字体和层级

- 标题更大、更轻、更有 neon 感。
- 倒计时使用最大字号，是总览页第一视觉焦点。
- 正文不小于当前可读尺寸。
- 数字建议使用等宽或 tabular 视觉，避免倒计时变化时跳动。

## 页面设计

### 顶部标题栏

标题栏重做为参考图式轻薄 neon bar：

- 左侧显示：`AutoShutdown`
- 副标题显示：`v2.0 · Starry Glass`
- 中间或右侧显示状态 pill：`READY` / `RUNNING` / `PAUSED`
- 右侧显示 `DRY RUN` pill
- 最右保留窗口按钮

视觉要求：

- 标题不能再像普通工具软件标题。
- pill 使用半透明底和亮色描边。
- 不使用纯灰背景。

### 左侧导航

侧边栏升级为 glass rail：

- 半透明玻璃底。
- 当前导航项为高亮胶囊。
- 左侧有 3px 粉蓝渐变指示条。
- 每项保留中文文字：总览、定时、任务、智能触发、脚本、设置。
- 可使用线性图标或字母标记，但不使用 emoji。
- 导航状态必须明确，不能只靠颜色区分。

### 总览页

总览页是本次 UI 大改核心，采用三列感：

```text
左：导航 rail
中：主控制区
右：抽象角色视觉位
```

#### 主控制区

主控制区包含：

- 大 Hero Card：
  - 状态 `READY` / `RUNNING` / `PAUSED`
  - 大号倒计时
  - 当前动作
  - 主按钮：启动倒计时
  - 次按钮：取消、暂停、立即执行
- 快捷时间 chips：
  - 15 分钟
  - 30 分钟
  - 1 小时
  - 2 小时
- 电源动作 tiles：
  - 关机
  - 睡眠
  - 休眠
  - 重启
  - 注销
  - 锁定

交互层级：

- `启动倒计时` 是总览页唯一最强 CTA。
- `立即执行` 作为次级但带危险语义，不和主按钮抢视觉。
- `取消` / `暂停` 只在状态适用时明显。

#### 抽象角色视觉位

右侧必须有明显视觉区域，但不使用真实人物图。

实现方式：

- 新增 `AnimeSilhouette.qml` 或 `StarryMascot.qml`。
- 用 QML Rectangle、Gradient、圆形、椭圆、线条/光束组合成抽象 anime 角色感。
- 元素包括：
  - 椭圆头部光环
  - 肩部/头发轮廓感
  - 粉紫蓝渐变光束
  - 星点围绕
  - 下方一句短文案：`星空守夜中` 或 `Sleep safely under the stars`

约束：

- 视觉位偏右，接近 e5e8 构图。
- 不能遮挡中间控制区。
- 不增加外部图片依赖。
- 如果 QML Shape/Canvas 风险高，优先用 Rectangle、Gradient、border、opacity、rotation、scale 实现。

### 定时页

定时页使用 e5e8 玻璃分组：

- 倒计时模式卡片。
- 指定时间模式卡片。
- 重复规则 chips。
- 启动按钮保持清晰。
- 输入框改为透明玻璃 input，不再像灰色框。

功能保持不变：

- 倒计时输入。
- 指定时间输入。
- 模式切换。
- 重复规则。
- 启动当前计划。

### 智能触发页

智能触发页改成两张明显 EAccordion 风格玻璃卡：

#### 网络闲置触发

- Header：图标感标记、标题、状态 badge、发光指示。
- 内容：下载阈值、上传阈值、持续分钟。
- 状态：当前速度、闲置进度。
- 操作：开始监控、停止监控。

#### 进程退出触发

- Header：图标感标记、标题、状态 badge、发光指示。
- 内容：进程选择、刷新进程。
- 子面板：自动关闭被监控程序。
- 状态：进程状态、自动关闭状态。

默认全部展开，不先实现折叠逻辑。

### 任务页

任务功能保持不变，但视觉换成任务 glass card：

- 启用任务：亮色边框和状态点。
- 禁用任务：降低透明度，但仍可读。
- 操作按钮使用 compact neon button。

### 脚本页

脚本页放进一张大玻璃卡：

- 脚本路径输入。
- 选择脚本按钮。
- 启用脚本开关。
- 超时秒数输入。
- 脚本状态文本。

### 设置页

设置页改成三张小设置卡：

- 提醒提前时间。
- 强制关闭应用。
- 开机自动启动。

开关使用粉紫蓝发光视觉，并保留可读状态文本。

## 组件修改

### `AutoShutdownQt/qml/Theme.qml`

新增 e5e8 theme token：

- 背景 token。
- glass surface token。
- glass border token。
- neon pink/purple/blue token。
- success/warning/danger token。
- glow opacity 与动画时长 token。

### `AutoShutdownQt/qml/components/NeonCard.qml`

升级为更强玻璃卡：

- 半透明底。
- 边框光。
- 顶部/左上角高光层。
- hover 动画。
- 可选 active/highlight 状态。

### `AutoShutdownQt/qml/components/ActionTile.qml`

强化 action tile：

- selected 状态更明显。
- hover 轻微 scale，持续 150–250ms。
- selected 使用粉蓝渐变感与 glow。
- 不只靠颜色表达 selected，还应有边框、亮度或标记。

### `AutoShutdownQt/qml/components/FluentSwitch.qml`

统一开关视觉：

- on 状态粉紫蓝 glow。
- off 状态仍是玻璃底，不是灰色块。
- knob 可读、可辨认。

### `AutoShutdownQt/qml/components/AnimeSilhouette.qml` 或 `StarryMascot.qml`

新增右侧抽象角色视觉组件：

- 自包含，不依赖业务逻辑。
- 暴露简单属性：`title`、`subtitle`、`accentColor` 可选。
- 不使用外部图片素材。
- 动画可选且轻量。

### `AutoShutdownQt/qml/Main.qml`

主要重排：

- 背景层。
- 玻璃 shell。
- 顶部 neon bar。
- 左侧 glass rail。
- 总览页三列构图。
- 各页面 glass 皮肤统一。

## UI/UX 约束

- 文字对比优先，玻璃和星空不能牺牲可读性。
- 每个页面只强调一个主要动作。
- 危险动作必须用危险语义色和文字提示，不只靠颜色。
- 按钮、导航、tile 都要有 hover/pressed/selected 状态。
- 交互控件视觉尺寸要足够大，避免小到难点。
- 不使用 emoji 作为结构性图标。
- 颜色使用 theme token，不在组件里到处写零散 raw hex。
- 动画只使用 transform/opacity/颜色过渡，避免布局抖动。

## 风险控制

1. 先确认现有 QML 控件名、controller 属性和信号连接。
2. 尽量不改 Python 侧接口。
3. 先做视觉壳，再细化各页面。
4. 右侧角色位优先用简单 QML 元素实现，不先引入复杂 Canvas/Shader。
5. 分阶段运行 QML，发现 `ReferenceError`、`TypeError`、`is not a type`、`Cannot assign` 立即修复。
6. 保持 Dry-run 默认开启，不真实执行关机/重启/注销。

## 验证标准

实现完成后必须验证：

- `python -m py_compile AutoShutdownQt/main.py AutoShutdownQt/controller.py AutoShutdownQt/power_service.py` 通过。
- QML 启动无关键错误：
  - `ReferenceError`
  - `TypeError`
  - `is not a type`
  - `Cannot assign`
- `python AutoShutdownQt/main.py` 可启动。
- 首页显示 `AutoShutdown v2.0`。
- 截图明显接近 `AutoShutdownQt/e5e8b88f-7acc-4be7-930f-952ad1670984.png`：
  - 粉紫蓝星空背景。
  - 大玻璃 shell。
  - 中间主控制区。
  - 右侧抽象 anime 角色视觉位。
  - 无大面积纯灰方块。
- Dry-run 默认开启。
- 主要功能按钮仍可响应：启动倒计时、取消、动作选择、模式选择。

## 发布

如果本轮继续发布，则版本统一为：

- Tag：`v2.0`
- Release title：`AutoShutdownQt v2.0`
- 包名：`AutoShutdownQt-v2.0-win-x64.zip`

Release notes 建议：

```text
AutoShutdownQt v2.0 更新：高度参考 e5e8 视觉图重做 UI，加入粉紫蓝星空背景、大面积毛玻璃控制台、右侧抽象 anime 视觉位与更强的霓虹组件状态；保留现有 Dry-run 与电源动作安全逻辑。
```

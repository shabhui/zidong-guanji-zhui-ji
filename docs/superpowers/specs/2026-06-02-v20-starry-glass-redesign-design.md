# AutoShutdownQt v2.0-preview Starry Glass Control Deck 设计

## 背景

当前 `AutoShutdownQt/` PySide6/QML 预览版已经能启动，并且布局比最初稳定，但视觉仍偏普通工具软件：用户反馈“纯灰色方框很丑”“UI 还是差一点意思”，希望方向更偏二次元、玻璃状、有动画。

本次 redesign 的目标是保留现有稳定信息架构，把视觉层改成 **星空霓虹二次元玻璃风**，让第一眼更梦幻、更通透、更有动效，而不是灰色面板堆叠。

## 目标

- 去掉主要区域的纯灰色方块感。
- 建立二次元星空玻璃视觉：深蓝紫背景、粉蓝紫高光、通透卡片、星点粒子。
- 增加轻量动画：漂浮光球、星点闪烁、玻璃卡 hover、ActionTile hover/selected glow。
- 保留当前清晰布局：顶部标题栏、左侧导航、右侧内容区。
- 保留现有功能和 `controller.py` 逻辑：倒计时、指定时间、动作选择、取消、Dry-run、确认执行。
- 不引入图片素材，先用 QML Rectangle/Gradient/Animation 实现视觉。

## 非目标

- 不迁移技术栈。
- 不重写 controller 业务逻辑。
- 不新增高级触发器功能。
- 不真实测试关机/重启；Dry-run 默认仍开启。
- 不做复杂粒子系统或高性能 shader，避免拖慢启动。

## 视觉方向

选定方案：**Starry Glass Control Deck**。

### 背景

背景由三层组成：

1. 深蓝紫主背景。
2. 3–4 个大型柔和光球，颜色为 cyan / purple / pink，缓慢漂浮。
3. 星点层：小圆点错峰闪烁，分布在背景和内容边缘。

光球动画要慢：单周期约 6–10 秒，避免晃眼。

### 玻璃卡片

所有主要卡片使用玻璃风：

- 半透明底色，不再是纯灰。
- 亮色边框：cyan/pink/purple 之一。
- 顶部或左上角增加高光层。
- hover 时边框和透明度增强。
- selected action tile 使用粉蓝渐变感和 glow。

### Hero 区

首页 Hero 是视觉中心：

- 倒计时数字保持大号。
- READY/RUNNING 状态 pill 使用对应颜色。
- Hero 卡片背景比普通卡片更亮，带微弱呼吸光效。
- 右侧按钮保持清晰，不被装饰遮挡。

### 导航栏

左侧导航继续保留，但改成：

- 背景更像玻璃 rail。
- active item 有亮色竖线、微发光、半透明高光。
- 底部 Dry-run 卡片使用绿色/粉色状态色，不是灰底。

### 动画

- 背景光球：`SequentialAnimation` / `NumberAnimation` 慢速移动。
- 星点：不同 `NumberAnimation` opacity 闪烁。
- 卡片 hover：背景色、边框色、scale 轻微变化。
- ActionTile：hover 1.02 scale，selected 有亮色边框和更高 opacity。
- 页面切换：可先不做复杂 Stack 动画；优先保证稳定和美观。

## 修改文件

- `AutoShutdownQt/qml/Theme.qml`
  - 增加 starry glass 色彩 token。
  - 增加玻璃色、高光色、动画时长。
- `AutoShutdownQt/qml/components/NeonCard.qml`
  - 从普通 Rectangle 卡片升级为 glass card：hover、highlight overlay、border animation。
- `AutoShutdownQt/qml/components/ActionTile.qml`
  - 增强 selected/hover 状态。
- `AutoShutdownQt/qml/components/StatusHero.qml`
  - 如仍使用则增强 hero glass；当前 Main.qml 内联 hero 也可直接增强。
- `AutoShutdownQt/qml/components/FluentSwitch.qml`
  - 微调开关颜色，保持星空玻璃统一。
- `AutoShutdownQt/qml/Main.qml`
  - 替换灰色背景块。
  - 增加光球和星点层。
  - 调整卡片颜色、间距、按钮容器。

## 验证标准

- `python -m py_compile AutoShutdownQt/main.py AutoShutdownQt/controller.py AutoShutdownQt/power_service.py` 通过。
- QML 离屏加载通过，不能有 `ReferenceError`、`TypeError`、`is not a type`、`Cannot assign` 等关键错误。
- `python AutoShutdownQt/main.py` 可启动。
- 打开后视觉上不再出现大面积纯灰方框。
- 首页有明显星空/玻璃/二次元氛围。
- 动画存在但不影响可读性。
- Dry-run 默认开启。

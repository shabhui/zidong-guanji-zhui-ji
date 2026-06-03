# AutoShutdownQt 2.0

AutoShutdownQt 是一个基于 **Python + PySide6/QML** 的 Windows 桌面自动电源动作工具。2.0 版本采用星空玻璃风格界面，支持倒计时、指定时间、任务模板、智能触发、执行前脚本和日志工具。

> 安全提示：AutoShutdownQt 2.0 默认开启 **Dry-run 安全模式**。在 dry-run 下，应用只记录“将要执行”的动作，不会真实关机、重启、注销或运行外部脚本。只有手动关闭 dry-run 后，才会执行真实系统动作。

## 功能特性

- **倒计时任务**：按小时/分钟/秒启动倒计时。
- **指定时间任务**：设定今天或明天的执行时刻。
- **电源动作**：关机、睡眠、休眠、重启、注销、锁定。
- **任务模板**：
  - 15 分钟后关机
  - 30 分钟后关机
  - 1 小时后睡眠
  - 今晚 23:00 关机
- **进程退出触发**：监控指定进程，进程出现后再退出时触发当前电源动作。
- **网络闲置触发**：当下载/上传速度持续低于阈值达到设定秒数后触发当前电源动作。
- **执行前脚本**：真实执行电源动作前可运行脚本；dry-run 下不会启动脚本。
- **配置持久化**：保存 dry-run、动作、脚本、触发器阈值等常用设置。
- **日志工具**：支持清空日志和导出日志。
- **脚本辅助工具**：支持验证脚本路径和打开脚本所在目录。

## 项目结构

```text
AutoShutdownQt/
├── main.py                 # 应用入口
├── controller.py           # QML 控制器和业务状态
├── power_service.py        # Windows 电源动作执行
├── script_service.py       # 执行前脚本服务
├── settings_service.py     # 配置持久化
├── network_service.py      # 网络速度采样与计算
├── package_release.py      # 2.0 打包脚本
├── AutoShutdownQt-2.0.spec # PyInstaller 打包配置
├── qml/                    # QML 界面和组件
└── tests/                  # 单元测试和 QML 静态回归测试
```

## 环境要求

- Windows 10/11
- Python 3.12+
- PySide6
- PyInstaller（仅打包发布时需要）

如果只运行源码，确保 Python 环境中已安装 PySide6。

## 从源码运行

```bash
python AutoShutdownQt/main.py
```

建议验证或演示时保持 dry-run 开启。关闭 dry-run 后，立即执行、倒计时结束、进程退出触发、网络闲置触发都可能执行真实系统动作。

## 运行测试

```bash
python -m unittest discover AutoShutdownQt/tests -v
```

当前 2.0 分支包含控制器、服务、QML wiring、发布打包配置等测试。

## 打包 2.0 发布包

先确保 PyInstaller 可用：

```bash
python -m pip install pyinstaller
```

然后执行：

```bash
python AutoShutdownQt/package_release.py
```

生成产物：

```text
dist/AutoShutdownQt-2.0/
dist/AutoShutdownQt-2.0.zip
```

说明：

- `dist/`、`build/` 和 `*.zip` 已被 `.gitignore` 忽略，不会随源码提交。
- 当前发布包是便携版，不是安装器。
- 当前 exe 未做代码签名，Windows 首次运行时可能出现安全提示。
- zip 内会包含 `release-manifest.json`，用于记录版本、关键文件和安全说明。
- 更多发布说明见 `RELEASE_NOTES_v2.0.md`。

## 安全模式说明

AutoShutdownQt 面向电源动作自动化，默认安全策略是：

1. 默认 `dryRun = true`。
2. dry-run 下不会真实执行关机、重启、注销等系统动作。
3. dry-run 下不会运行外部脚本，只记录将执行的脚本路径。
4. 关闭 dry-run 后，请先确认任务、触发器、脚本路径和未保存工作。

## GitHub 发布状态

当前 2.0 源码和本地发布准备基线在：

```text
main
```

本仓库提交发布配置和源码，不直接提交本地 zip 包。如需正式 GitHub Release，可在确认 README、测试和本地发布包后创建 `v2.0` tag，并上传 `dist/AutoShutdownQt-2.0.zip`。

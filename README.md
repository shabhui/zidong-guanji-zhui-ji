# 定时关机助手 3.2

定时关机助手 是一个基于 **Python + PySide6/QML** 的 Windows 桌面自动电源动作工具。3.2 是正式安装包版本，新增可设置的空闲自动关机，同时继续保留右下角托盘后台、Inno Setup 安装器和便携 zip。

> 安全提示：定时关机助手 3.2 默认开启 **Dry-run 安全模式**。在 dry-run 下，应用只记录“将要执行”的动作，不会真实关机、重启、注销、锁定、睡眠、休眠或运行外部脚本。只有手动关闭 dry-run 后，才会执行真实系统动作。

## Current release

当前版本是 **定时关机助手 3.2**，这是正式安装包版本，新增可设置的空闲自动关机，并继续支持右下角托盘后台运行、开机启动、任务历史和 Windows 原生通知。

- 下载安装器：`定时关机助手-3.2-Setup.exe`
- 便携版 zip：`定时关机助手-3.2.zip`
- 校验文件：`SHA256SUMS.txt`
- 默认开启 Dry-run 安全模式。
- 系统托盘可用时，可为执行前提醒发送 Windows 原生通知。
- 可查看、清空任务历史，并导出 JSON。
- 托盘可用时，点击关闭按钮会隐藏到右下角小图标；双击小图标恢复窗口，右键选择 Quit 才彻底退出。

## 功能特性

- **单页 Command Center**：集中展示安全状态、当前动作、托盘后台预期、队列数量、下一任务、触发器和最近活动。
- **倒计时任务**：按小时/分钟/秒启动倒计时。
- **指定时间任务**：设定今天或明天的执行时刻。
- **电源动作**：关机、睡眠、休眠、重启、注销、锁定。
- **关机前优雅关闭应用**：关机/重启/注销前，像手动关机那样向正在运行的应用发送关闭请求（应用可弹窗保存未完成的工作），并可设置最长等待秒数；超时后再继续执行电源动作。Dry-run 下只列出将要关闭的应用，不会真正关闭。与「强制关闭应用」不同：本功能不强杀进程，保留保存机会。
- **任务模板**：15 分钟后关机、30 分钟后关机、1 小时后睡眠、今晚 23:00 关机等。
- **执行前提醒**：可配置提醒分钟列表，默认 `10,5,1`。
- **首次启动安全说明**：首次运行会说明 Dry-run、真实执行风险、托盘后台运行和彻底退出方式。
- **关闭到托盘提示**：首次关闭窗口到托盘前会提示任务和触发器仍会继续运行。
- **Windows 原生通知**：可在系统托盘可用时为执行前提醒发送原生通知。
- **开机自动启动**：可选择写入当前用户 Windows Run 项，便携版默认不启用。
- **右下角小图标后台运行**：点击右上角关闭按钮会隐藏到右下角小图标；双击小图标恢复窗口，右键小图标选择 Quit 才彻底退出。
- **任务历史**：记录创建、延后、取消和执行事件，支持清空与 JSON 导出。
- **默认延后**：提醒弹窗可按配置的默认分钟数延后当前任务，默认 `15` 分钟。
- **任务队列隔离提醒**：每个队列任务的每个提醒点只提醒一次，延后后会重新计算提醒点。
- **本地音乐播放器**：支持启动自动播放、选择音乐文件夹、歌曲列表、播放/暂停/停止、音量、进度拖动、上一首/下一首、顺序播放/列表循环/单曲循环。
- **进程退出触发**：监控指定进程，进程出现后再退出时触发当前电源动作。
- **网络闲置触发**：当下载/上传速度持续低于阈值达到设定秒数后触发当前电源动作。
- **空闲自动关机**：可设置启用、空闲分钟、轮询秒和触发动作；达到键鼠无操作阈值后加入现有任务队列。
- **执行前脚本**：真实执行电源动作前可运行脚本；dry-run 下不会启动脚本。
- **配置持久化**：保存 dry-run、动作、脚本、触发器阈值、任务队列、提醒、延后和音乐设置等常用设置。
- **日志工具**：支持清空日志、导出日志和导出诊断。

## 项目结构

```text
AutoShutdownQt/
├── main.py                 # 应用入口
├── controller.py           # QML 控制器和业务状态
├── power_service.py        # Windows 电源动作执行
├── app_close_service.py    # 关机前优雅关闭应用（模拟手动关机）
├── script_service.py       # 执行前脚本服务
├── settings_service.py     # 配置持久化
├── network_service.py      # 网络速度采样与计算
├── music_service.py        # 本地音乐播放服务
├── task_model.py           # 任务模型
├── task_scheduler.py       # 任务队列调度
├── tray_service.py         # 系统托盘服务
├── package_release.py      # 打包脚本
├── AutoShutdownQt-3.2.spec # PyInstaller 打包配置
├── AutoShutdownQt-3.2.iss  # Inno Setup 安装器配置
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

Note: controller/QML logic tests use `AutoShutdownQt/tests/qt_test_env.py` as a test-only fallback when PySide6 is not installed in the current Python environment. Running the real app and visual Qt checks still requires PySide6.

## 打包 3.2 发布包

先确保 PyInstaller 可用；如果要生成安装器，还需要安装 Inno Setup 并确保 `ISCC.exe` 在 PATH 中：

```bash
python -m pip install pyinstaller
```

然后执行：

```bash
python AutoShutdownQt/package_release.py
```

生成产物：

```text
dist/定时关机助手-3.2/
dist/定时关机助手-3.2.zip
dist/定时关机助手-3.2-Setup.exe
dist/SHA256SUMS.txt
dist/release-checklist-v3.2.md
```

说明：

- `dist/`、`build/` 和 `*.zip` 已被 `.gitignore` 忽略，不会随源码提交。
- 3.2 同时发布安装器和便携 zip。
- 当前 exe/安装器未做代码签名，Windows 首次运行时可能出现安全提示。
- zip 内会包含 `release-manifest.json`，用于记录版本、关键文件和安全说明。
- 根目录 `.mp3` 文件会被打进发布包。
- 更多发布说明见 `RELEASE_NOTES_v3.2.md`。

## 安全模式说明

定时关机助手 面向电源动作自动化，默认安全策略是：

1. 默认 `dryRun = true`。
2. dry-run 下不会真实执行关机、重启、注销等系统动作。
3. dry-run 下不会运行外部脚本，只记录将执行的脚本路径。
4. 关闭 dry-run 后，请先确认任务、触发器、脚本路径和未保存工作。
5. 执行前提醒会在 dry-run 和真实执行模式下显示，并明确当前模式。

## GitHub 发布状态

当前源码和本地发布准备基线在：

```text
main
```

本仓库提交发布配置和源码，不直接提交本地 zip 或安装器。正式 GitHub Release 使用 `v3.2` tag，并上传 `dist/定时关机助手-3.2-Setup.exe`、`dist/定时关机助手-3.2.zip` 与 `dist/SHA256SUMS.txt`。

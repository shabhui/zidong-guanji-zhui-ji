# AutoShutdownQt 2.4

AutoShutdownQt 是一个基于 **Python + PySide6/QML** 的 Windows 桌面自动电源动作工具。2.4 是 2.3 command center UI polish release 之后的提醒与延后执行版本，重点新增执行前提醒、默认延后、音乐播放器和更完整的本地任务队列体验。

> 安全提示：AutoShutdownQt 2.4 默认开启 **Dry-run 安全模式**。在 dry-run 下，应用只记录“将要执行”的动作，不会真实关机、重启、注销、锁定、睡眠、休眠或运行外部脚本。只有手动关闭 dry-run 后，才会执行真实系统动作。

## Current release

AutoShutdownQt 2.4 is the current reminder, snooze, and local music playback release.

- Download: `AutoShutdownQt-2.4.zip`
- Verify checksum with `SHA256SUMS.txt`
- Dry-run is enabled by default.
- Execution reminders can warn before queued tasks run and use the configured default snooze duration.
- The bundled local music player supports folder selection, playlist switching, seek, volume, previous/next, and playback modes.

## 功能特性

- **单页 Command Center**：集中展示安全状态、当前动作、托盘后台预期、队列数量、下一任务、触发器和最近活动。
- **倒计时任务**：按小时/分钟/秒启动倒计时。
- **指定时间任务**：设定今天或明天的执行时刻。
- **电源动作**：关机、睡眠、休眠、重启、注销、锁定。
- **任务模板**：15 分钟后关机、30 分钟后关机、1 小时后睡眠、今晚 23:00 关机等。
- **执行前提醒**：可配置提醒分钟列表，默认 `10,5,1`。
- **默认延后**：提醒弹窗可按配置的默认分钟数延后当前任务，默认 `15` 分钟。
- **任务队列隔离提醒**：每个队列任务的每个提醒点只提醒一次，延后后会重新计算提醒点。
- **本地音乐播放器**：支持启动自动播放、选择音乐文件夹、歌曲列表、播放/暂停/停止、音量、进度拖动、上一首/下一首、顺序播放/列表循环/单曲循环。
- **进程退出触发**：监控指定进程，进程出现后再退出时触发当前电源动作。
- **网络闲置触发**：当下载/上传速度持续低于阈值达到设定秒数后触发当前电源动作。
- **执行前脚本**：真实执行电源动作前可运行脚本；dry-run 下不会启动脚本。
- **配置持久化**：保存 dry-run、动作、脚本、触发器阈值、任务队列、提醒、延后和音乐设置等常用设置。
- **日志工具**：支持清空日志、导出日志和导出诊断。

## 项目结构

```text
AutoShutdownQt/
├── main.py                 # 应用入口
├── controller.py           # QML 控制器和业务状态
├── power_service.py        # Windows 电源动作执行
├── script_service.py       # 执行前脚本服务
├── settings_service.py     # 配置持久化
├── network_service.py      # 网络速度采样与计算
├── music_service.py        # 本地音乐播放服务
├── task_model.py           # 任务模型
├── task_scheduler.py       # 任务队列调度
├── tray_service.py         # 系统托盘服务
├── package_release.py      # 打包脚本
├── AutoShutdownQt-2.4.spec # PyInstaller 打包配置
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

## 打包 2.4 发布包

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
dist/AutoShutdownQt-2.4/
dist/AutoShutdownQt-2.4.zip
dist/SHA256SUMS.txt
dist/release-checklist-v2.4.md
```

说明：

- `dist/`、`build/` 和 `*.zip` 已被 `.gitignore` 忽略，不会随源码提交。
- 当前发布包是便携版，不是安装器。
- 当前 exe 未做代码签名，Windows 首次运行时可能出现安全提示。
- zip 内会包含 `release-manifest.json`，用于记录版本、关键文件和安全说明。
- 根目录 `.mp3` 文件会被打进发布包。
- 更多发布说明见 `RELEASE_NOTES_v2.4.md`。

## 安全模式说明

AutoShutdownQt 面向电源动作自动化，默认安全策略是：

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

本仓库提交发布配置和源码，不直接提交本地 zip 包。正式 GitHub Release 使用 `v2.4` tag，并上传 `dist/AutoShutdownQt-2.4.zip` 与 `dist/SHA256SUMS.txt`。

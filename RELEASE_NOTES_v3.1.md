# 定时关机助手 3.1 Release Notes

定时关机助手 3.1 是正式安装包版本，同时保留便携 zip。

## Highlights

- 新增可设置的空闲自动关机：可配置启用、空闲分钟、轮询秒和触发动作。
- 空闲阈值达到后会加入现有 task queue，继续复用 Dry-run、提醒、历史、取消和 queue 调度逻辑。
- 智能触发页新增空闲自动关机卡片，并保留进程退出触发、网络闲置触发、Command Center、tray background 等核心体验。
- 新增 Inno Setup 安装器：`dist/定时关机助手-3.1-Setup.exe`。
- 继续保留便携版：`dist/定时关机助手-3.1.zip`。

## Safety

- Dry-run 默认开启，不会真实执行关机、重启、注销、锁定、睡眠、休眠或外部脚本。
- 关闭 Dry-run 后，倒计时、固定时间、进程退出、网络闲置和空闲自动关机都可能执行真实 Windows 电源动作，请先确认未保存工作。
- 当前 exe/安装器未做代码签名，Windows 首次运行时可能出现安全提示。

## Artifacts

- `dist/定时关机助手-3.1-Setup.exe`
- `dist/定时关机助手-3.1.zip`
- `dist/SHA256SUMS.txt`
- `dist/release-checklist-v3.1.md`

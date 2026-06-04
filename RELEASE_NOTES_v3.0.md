# 定时关机助手 3.0 Release Notes

定时关机助手 3.0 是正式安装包版本，同时保留便携 zip。

## Highlights

- 保留 2.x Command Center、queue/task history、tray background 等核心体验。
- 修复关闭窗口隐藏到右下角小图标行为：只有右下角小图标可用时才拦截关闭并隐藏窗口。
- 隐藏到右下角小图标后显示提示，双击小图标可恢复窗口，右键选择 Quit 可彻底退出。
- 新增 Inno Setup 安装器：`dist/AutoShutdownQt-3.0-Setup.exe`。
- 安装器包含开始菜单快捷方式、可选桌面快捷方式、卸载入口和可选安装后启动。
- 继续保留便携版：`dist/AutoShutdownQt-3.0.zip`。

## Safety

- Dry-run 默认开启，不会真实执行关机、重启、注销、锁定、睡眠、休眠或外部脚本。
- 关闭 Dry-run 后会执行真实 Windows 电源动作，请先确认未保存工作。
- 当前 exe/安装器未做代码签名，Windows 首次运行时可能出现安全提示。

## Artifacts

- `dist/AutoShutdownQt-3.0-Setup.exe`
- `dist/AutoShutdownQt-3.0.zip`
- `dist/SHA256SUMS.txt`
- `dist/release-checklist-v3.0.md`

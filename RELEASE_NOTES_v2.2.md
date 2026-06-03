# AutoShutdownQt 2.2 Release Notes

AutoShutdownQt 2.2 是 AutoShutdownQt 2.1 practical scheduler 之后的 stability patch，继续提供 Windows 便携版自动电源动作工具。

## 发布产物

- 便携版目录：`dist/AutoShutdownQt-2.2/`
- 便携版 zip：`dist/AutoShutdownQt-2.2.zip`
- 校验文件：`dist/SHA256SUMS.txt`
- 发布检查清单：`dist/release-checklist-v2.2.md`

## Stability fixes

- Queue rows stay synchronized with process and network trigger monitors.
- Starting a new process or network trigger replaces the previous active trigger row.
- Stopping or deleting trigger rows stops the matching runtime monitor.
- Recurring fixed-time tasks recompute their next run on startup instead of trusting stale saved timestamps.
- Tray Quit explicitly exits instead of behaving like close-to-tray.

## 安全说明

- 默认开启 **Dry-run** 安全模式。
- Dry-run 下不会真实关机、重启、注销、锁定、睡眠或休眠。
- 验证时不要执行真实系统电源动作。
- 当前 exe **未做代码签名**，Windows 首次运行可能提示安全警告。
- 当前发布包是便携版，不是安装器。

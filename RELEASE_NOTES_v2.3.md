# AutoShutdownQt 2.3 Release Notes

AutoShutdownQt 2.3 是 AutoShutdownQt 2.2 stability release 之后的 command center UI polish release。它不改变调度语义，重点提升单页控制台的信息层级、安全状态可见性、任务队列可读性和日志可读性。

## 发布产物

- 便携版目录：`dist/AutoShutdownQt-2.3/`
- 便携版 zip：`dist/AutoShutdownQt-2.3.zip`
- 校验文件：`dist/SHA256SUMS.txt`
- 发布检查清单：`dist/release-checklist-v2.3.md`

## UI polish

- Single-page Command Center replaces the multi-page/sidebar workflow.
- Safety strip shows Dry-run/Live mode, current action, tray/background expectation, and queue count.
- Command cards highlight next task, active triggers, and queue health.
- Task Queue Dashboard improves queue readability without adding new scheduling behavior.
- Recent activity frames existing logs as an operational activity feed.

## 安全说明

- 默认开启 **Dry-run** 安全模式。
- Dry-run 下不会真实关机、重启、注销、锁定、睡眠或休眠。
- 验证时不要执行真实系统电源动作。
- 当前 exe **未做代码签名**，Windows 首次运行可能提示安全警告。
- 当前发布包是便携版，不是安装器。

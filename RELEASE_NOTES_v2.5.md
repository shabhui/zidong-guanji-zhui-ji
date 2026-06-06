# AutoShutdownQt 2.5 Release Notes

AutoShutdownQt 2.5 is the core background-experience release after the 2.4 reminder, snooze, music, and command center updates. It keeps Dry-run as the default safety mode and adds native notification wiring, task history, and opt-in Windows startup behavior.

## 发布产物

- 便携版目录：`dist/AutoShutdownQt-2.5/`
- 便携版 zip：`dist/AutoShutdownQt-2.5.zip`
- 校验文件：`dist/SHA256SUMS.txt`
- 发布检查清单：`dist/release-checklist-v2.5.md`

## Background experience

- Windows native notifications can be enabled for execution reminders when tray support is available.
- Startup settings are opt-in and local to the current Windows user.
- Startup-to-tray lets the app begin hidden when enabled.
- Task history records created, snoozed, cancelled, and executed task events.
- Task history can be cleared or exported as JSON.
- Tray background scheduling remains local-only.

## Command center and queue

- The command center remains the primary single-page status surface.
- Queue health, tray state, reminders, and recent activity remain visible.
- Reminder and snooze behavior from 2.4 is preserved for queued tasks.

## Packaging

- 发布版本更新为 2.5。
- PyInstaller spec 使用 `AutoShutdownQt-2.5.spec`。
- 发布 zip 使用 `AutoShutdownQt-2.5.zip`。
- release manifest 记录 2.5 版本和关键文件检查。
- SHA256SUMS.txt 随 release 资产发布。

## 安全说明

- 默认开启 **Dry-run** 安全模式。
- Dry-run 下不会真实关机、重启、注销、锁定、睡眠或休眠。
- 验证时不要执行真实系统电源动作。
- Windows notification and startup options do not change the need to confirm real execution mode before disabling Dry-run.
- 当前 exe **未做代码签名**，Windows 首次运行可能提示安全警告。
- 当前发布包是便携版，不是安装器。

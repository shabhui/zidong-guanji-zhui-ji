# AutoShutdownQt 2.4 Release Notes

AutoShutdownQt 2.4 是 2.3 command center UI polish release 之后的 reminder / snooze / local music release。它保留默认 Dry-run 安全策略，重点增强任务执行前的救场能力和本地音乐播放体验。

## 发布产物

- 便携版目录：`dist/AutoShutdownQt-2.4/`
- 便携版 zip：`dist/AutoShutdownQt-2.4.zip`
- 校验文件：`dist/SHA256SUMS.txt`
- 发布检查清单：`dist/release-checklist-v2.4.md`

## Reminder & snooze

- Queue reminders are evaluated per queued task, so one task does not suppress the next task's reminder threshold.
- Tray background scheduling remains local-only; reminders are shown in the app window rather than native Windows notifications.
- 设置页新增“执行前提醒”开关。
- 可配置提醒分钟列表，默认 `10,5,1`。
- 可配置默认延后分钟，默认 `15`。
- 倒计时队列任务进入提醒窗口时显示应用内提醒弹窗。
- 提醒弹窗显示当前动作、剩余时间和 Dry-run / 真实执行模式。
- 提醒弹窗支持：默认延后、取消当前任务、知道了。
- 每个队列任务的每个提醒点只提醒一次。
- 延后任务后会重置提醒跟踪，按新的目标时间重新计算提醒点。

## Music playback

- 启动时可自动播放本地 mp3。
- 独立音乐播放器窗口。
- 支持选择音乐文件夹并扫描 `.mp3`。
- 支持歌曲列表点击切歌。
- 支持播放 / 暂停 / 停止。
- 支持音量调节。
- 支持播放进度显示和拖动跳转。
- 支持上一首 / 下一首。
- 支持顺序播放 / 列表循环 / 单曲循环。
- 根目录 mp3 会被打进便携发布包。

## Packaging

- 发布版本更新为 2.4。
- PyInstaller spec 使用 `AutoShutdownQt-2.4.spec`。
- 发布 zip 使用 `AutoShutdownQt-2.4.zip`。
- release manifest 记录 2.4 版本和关键文件检查。
- SHA256SUMS.txt 随 release 资产发布。

## 安全说明

- 默认开启 **Dry-run** 安全模式。
- Dry-run 下不会真实关机、重启、注销、锁定、睡眠或休眠。
- 验证时不要执行真实系统电源动作。
- 执行前提醒不会替代用户对真实执行模式的确认责任。
- 当前 exe **未做代码签名**，Windows 首次运行可能提示安全警告。
- 当前发布包是便携版，不是安装器。

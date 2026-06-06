# 定时关机助手 3.2 Safety and Background Experience Design

## Goal
定时关机助手 3.2 是安全与后台体验增强版本。它不新增复杂触发器，重点让用户更清楚当前执行模式、关闭窗口后的后台状态，以及真实执行前如何取消或延后任务。

## Scope
- Add a first-run safety guide.
- Add a one-time close-to-tray hint.
- Strengthen live-mode warning copy and visual emphasis.
- Make task source labels clearer in queue, reminders, and history.
- Update tests, release notes, README, and release checklist for 3.2.

## Non-goals
- No new trigger types.
- No broad UI redesign.
- No large controller refactor.
- No code-signing automation.
- No change to the default Dry-run safety policy.

## Settings
Add two persisted booleans in `settings_service.py`:

- `firstRunSafetyGuideShown`: default `false`.
- `trayCloseHintShown`: default `false`.

The controller exposes matching QML-readable properties and slots to mark each hint as acknowledged. Existing settings merge behavior keeps older user configs compatible.

## First-run safety guide
On startup, QML opens a modal guide when `firstRunSafetyGuideShown` is false.

The guide explains:

- Dry-run is enabled by default and does not execute real power actions.
- Disabling Dry-run allows real shutdown, restart, sleep, hibernate, logoff, lock, or scripts.
- Closing the window may keep the app running in the system tray.
- To exit completely, use the tray menu Quit action.

The primary action is `我知道了`. Clicking it calls a controller slot that saves `firstRunSafetyGuideShown = true` and closes the dialog. No secondary opt-in is required because the guide itself is shown only once.

## Close-to-tray hint
Current QML intercepts window close when tray is available and minimizes to tray. In 3.2, the first close request shows a one-time modal hint instead of immediately hiding.

Behavior:

1. User clicks the window close button.
2. If tray is unavailable, keep existing close behavior.
3. If tray is available and `trayCloseHintShown` is false, cancel the close event and show the hint.
4. User confirms the hint.
5. Controller saves `trayCloseHintShown = true`.
6. QML calls the existing close/minimize-to-tray path.
7. Future close requests minimize directly without repeating the hint.

The hint copy states that countdowns, queue tasks, and triggers continue while the app is in the tray, and that full exit requires the tray menu Quit action.

## Live-mode warning improvements
Dry-run remains the default. 3.2 only improves communication when Dry-run is disabled.

Changes:

- Make the existing `LIVE MODE` state more visually prominent in the safety strip.
- Add concise warning copy near immediate execution controls when live mode is active.
- Update the immediate execution confirmation dialog so it explicitly names the action and states that it may execute a real Windows power action.
- Keep the existing live-mode confirmation for disabling Dry-run.

This avoids adding new confirmation layers that would make normal use noisy while still making live mode harder to miss.

## Task source labels
Task source display should be centralized in the controller rather than duplicated as raw strings in QML.

Source labels:

- `countdown`: 手动倒计时
- `clock`: 指定时间
- `template`: 模板任务
- `process`: 进程退出触发
- `network`: 网络闲置触发
- `idle`: 空闲触发
- `queue`: 队列任务
- `reminder`: 执行前提醒

Queue rows, reminder dialog text, and history messages use these labels where relevant. Existing stored history rows are not migrated; new entries use the clearer labels.

## Error handling
If saving acknowledgement settings fails, the app should keep running and log the failure through the existing logging path. The dialog can still close for the current session, but the guide may appear again next launch because persistence failed.

No new behavior should bypass Dry-run or execute power actions.

## Testing
Add or update tests for:

- Default settings include `firstRunSafetyGuideShown = false` and `trayCloseHintShown = false`.
- Controller properties and acknowledgement slots persist both settings.
- QML contains the first-run safety guide dialog and calls the controller acknowledgement slot.
- QML contains the close-to-tray hint dialog and routes confirmed close through the existing tray path.
- Live-mode warning copy exists near execution controls.
- Task source labels are generated consistently by controller code.
- Release packaging tests expect version 3.2 artifacts once the release version is bumped.

## Documentation and release
Update:

- `README.md`: current release, safety mode, tray/background explanation, generated artifact names.
- `RELEASE_NOTES_v3.2.md`: highlight safety guide, tray-close hint, stronger live-mode warnings, clearer task source labels.
- `package_release.py`: version 3.2 when preparing the release.
- PyInstaller/Inno files: add `AutoShutdownQt-3.2.spec` and `AutoShutdownQt-3.2.iss` based on 3.1 when packaging 3.2.
- Release checklist: verify first-run guide, close-to-tray hint, live-mode warnings, and no real power actions during validation.

## Acceptance criteria
- A fresh config shows the first-run safety guide exactly once.
- The first close-to-tray action shows the tray hint exactly once when tray is available.
- Dry-run remains enabled by default.
- Live mode is visually and textually harder to miss before immediate execution.
- New task/reminder/history text identifies trigger source clearly.
- Existing 3.1 behavior for tray minimize, reminders, history, startup, idle trigger, packaging, and tests remains intact.

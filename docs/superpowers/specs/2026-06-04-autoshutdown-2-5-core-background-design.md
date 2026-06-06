# AutoShutdownQt 2.5 Core Background Experience Design

## Goal
AutoShutdownQt 2.5 keeps the portable zip release model and improves background task reliability with Windows notifications, task history, and opt-in startup behavior.

## Scope
- No installer in 2.5.
- Keep existing in-app reminder dialog.
- Add Windows notification as an enhancement layer, not a replacement.
- Add persistent task history with configurable retention, default 500 entries.
- Add opt-in startup settings: launch at Windows login and start minimized to tray.

## Windows notifications
A new notification service exposes a small interface: show reminder, report availability, and open the main window when the notification is clicked. On Windows with Qt tray support, the first implementation uses QSystemTrayIcon.showMessage because it is already available in the app and works in portable mode. If actionable toast buttons are unavailable, the app falls back to click/open-window behavior and the in-app reminder remains the place for snooze/cancel actions.

## Task history
A new history service stores task events in settings.json under `taskHistory`. Each event records time, event type, action, trigger/source, mode, task id, and a readable message. Retention is controlled by `taskHistoryLimit`, default 500. The controller records create, dry-run execution, live execution success/failure, cancellation, snooze, trigger activation, and pause/resume events. UI shows recent history and provides clear/export controls.

## Startup behavior
Settings add `startWithWindows` and `startMinimizedToTray`, both default false. A startup service writes/removes a current-user Windows Run registry value for the packaged executable or current Python script. This is opt-in and does not require admin rights. If start-minimized is enabled, main.py hides the window after tray setup.

## UI
Settings page gains sections for Windows notifications, history retention/clear/export, and startup behavior. A history view is added to the task page or settings area using JSON rows from the controller.

## Tests
Unit tests cover default settings, history retention and export, controller event recording, notification fallback calls, startup registry command generation, QML wiring, release version bump, manifest checks, and final packaging.

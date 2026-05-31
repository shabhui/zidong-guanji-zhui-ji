# AutoShutdown 1.2 Power Actions Design

## Goal
Add selectable power actions for version 1.2: shutdown, sleep, hibernate, restart, log out, and lock. Existing countdown and fixed-time scheduling should execute the selected action.

## Scope
- Add a `PowerAction` enum and persist the selected action in settings.
- Add an action selector to the main window using the current neon UI style.
- Update status text, tray notifications, and reminder dialog copy to use the selected action label.
- Keep current countdown and fixed-time scheduling behavior.
- Keep the existing force-close-apps option, but make it apply only to shutdown, restart, and log out. Sleep, hibernate, and lock should not show or use forced close behavior.

## Power action behavior
- Shutdown: `shutdown /s /t 0`, with `/f` if force-close is enabled.
- Restart: `shutdown /r /t 0`, with `/f` if force-close is enabled.
- Log out: `shutdown /l`, with `/f` if force-close is enabled.
- Sleep: call Windows sleep API.
- Hibernate: call Windows hibernate API.
- Lock: call Windows lock workstation API.

## UI behavior
- Main window gets a new “执行动作” section above the time input panel.
- The selected action is visually highlighted.
- Status card shows “计划执行：自动睡眠/自动重启/锁定电脑”等 action-specific copy.
- Reminder dialog title and message change from “即将关机” to the selected action.
- The force-close setting row is visible/enabled only when the selected action supports force close.

## Non-goals for 1.2
- Multi-task queue.
- Repeat rules such as daily/workday/weekend.
- Calendar picking.
- Network idle detection.
- Process-exit triggers.
- Script execution.
- Soft-save automation for third-party apps.

## Validation
- Build must pass with 0 errors.
- Manually verify action selection updates labels and force-close availability.
- Do not execute real shutdown/restart/logout during validation; code paths should be reviewed and non-destructive actions can be smoke-tested only if safe.

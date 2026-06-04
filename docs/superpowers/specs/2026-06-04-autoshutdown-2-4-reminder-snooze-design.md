# AutoShutdownQt 2.4 Pre-Execution Reminder and Snooze Design

## Goal

Add a lightweight safety layer before scheduled power actions run. Users can configure reminder times and a default snooze duration, then respond from an in-app reminder dialog before shutdown, sleep, hibernate, restart, logoff, lock, or dry-run simulation proceeds.

## Scope

AutoShutdownQt 2.4 adds:

- A setting to enable or disable execution reminders.
- A configurable comma-separated reminder minute list, defaulting to `10,5,1`.
- A configurable default snooze duration, defaulting to `15` minutes.
- A QML reminder dialog shown inside the main window.
- Dialog actions for snoozing, cancelling the current task, or dismissing the reminder.
- Persistence for the reminder and snooze settings.

Out of scope:

- Windows native toast notifications.
- Tray menu enhancements.
- Multiple preset snooze buttons.
- Per-task custom reminder configuration.
- Changes to the default dry-run safety behavior.

## User Experience

Settings page gets a small reminder section:

- Enable execution reminders.
- Reminder minutes before execution, entered as comma-separated minutes such as `10,5,1`.
- Default snooze minutes, such as `15`.

When a scheduled action reaches a configured reminder point, the app opens an in-app dialog with:

- The action label, such as `关机` or `睡眠`.
- Remaining time.
- Safety mode text that clearly distinguishes dry-run from real execution.
- Buttons:
  - `延后 15 分钟`
  - `取消当前任务`
  - `知道了`

The snooze button label uses the configured snooze duration.

## Behavior Rules

- Reminders apply in both dry-run and real execution mode.
- Dialog copy must clearly state whether the upcoming action is dry-run only or real execution.
- Each task should show each configured reminder minute only once.
- If a user snoozes, the current task target time moves later by the configured snooze duration.
- Snoozing resets reminder tracking for the shifted task so future reminder points can appear again relative to the new target time.
- Cancelling the current task follows the existing cancellation behavior for the active task and returns the controller to the appropriate ready or queue-driven state.
- Dismissing the dialog only closes that reminder; it does not cancel or pause the task.
- Invalid reminder minute input falls back to `10,5,1`.
- Invalid snooze minute input falls back to `15`.
- Reminder minutes are positive integers, de-duplicated, and evaluated from largest to smallest.

## Architecture

### Settings service

Add these persisted keys to the default settings:

- `reminderEnabled`: boolean, default `true`.
- `reminderMinutesCsv`: string, default `10,5,1`.
- `snoozeMinutes`: integer, default `15`.

The controller remains responsible for coercing settings values because it already owns similar UI-facing validation for dry-run, triggers, music, and timing inputs.

### Controller

Add controller state for:

- Reminder enabled flag.
- Raw reminder CSV text.
- Parsed reminder minute list.
- Snooze minutes.
- A set of reminder points already shown for the current active target.
- Dialog-facing reminder title/body/action text.

The existing one-second timer tick is the natural place to check reminders because it already updates countdown state and handles execution transitions. On each tick:

1. Skip if reminders are disabled.
2. Skip if no active target exists.
3. Compute remaining seconds.
4. For each configured reminder minute, trigger when remaining seconds is less than or equal to `minute * 60` and greater than zero.
5. Ignore reminder points already shown for the current target.
6. Populate dialog-facing properties and emit a signal for QML to open the dialog.

Snooze should adjust the active target by `snoozeMinutes`, update remaining time, clear reminder tracking for the shifted target, save settings, and log the action.

### QML

Add a reminder dialog to `Main.qml` using the existing dialog/component style. The dialog binds to controller reminder properties and calls controller slots for:

- `snoozeCurrentTask()`
- Existing current-task cancellation slot; if no direct slot exists, add `cancelCurrentTask()` as a thin controller slot that reuses the existing cancellation path.
- Dismiss/close

The settings page adds controls consistent with the current QML style: a switch, a text field for reminder CSV, and a numeric field for snooze minutes.

## Error Handling

Reminder parsing is forgiving:

- Empty CSV uses defaults.
- Non-numeric tokens are ignored.
- Zero and negative values are ignored.
- If no valid reminder minutes remain, use defaults.
- Snooze values below one minute use default `15`.

No filesystem, network, or external process behavior is introduced.

## Testing

Add or update unit/static tests for:

- Default settings include reminder keys.
- Reminder CSV parsing handles valid, empty, duplicate, invalid, zero, and negative values.
- Snooze minute coercion falls back to `15` for invalid values.
- Reminder fires once per configured reminder point.
- Reminder text distinguishes dry-run from real execution mode.
- Snooze moves the active target later and updates remaining time.
- Snooze clears reminder tracking for the shifted target.
- Cancelling from the reminder uses existing cancellation behavior.
- QML includes the reminder settings controls and reminder dialog actions.

## Release Notes

The 2.4 release note should describe this as a safety and convenience improvement: configurable execution reminders plus one-click default snooze before a scheduled action runs.

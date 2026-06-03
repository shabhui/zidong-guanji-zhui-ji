# AutoShutdownQt 2.1 Practical Scheduler Design

## Goal

AutoShutdownQt 2.1 should turn the 2.0 single-task desktop utility into a more practical daily-use scheduler while preserving the 2.0 safety posture. The release will add system tray/background operation, recurring fixed-time tasks, a usable multi-task queue, and lightweight release checklist/checksum output.

## Scope

### In scope

- System tray icon and menu.
- Window close-to-tray behavior with explicit quit.
- A small task model and scheduler separated from the QML controller.
- Multiple saved tasks with enabled/disabled state.
- One-shot and recurring fixed-time tasks.
- Countdown tasks in the queue as one-shot tasks.
- Existing process-exit and network-idle triggers represented as queue task types.
- Dry-run-safe execution through the existing controller/power-service boundary.
- Release checksum and release checklist generation.
- README/release-note updates for 2.1 behavior.

### Out of scope

- Installer generation.
- Code signing.
- Automatic online update installation.
- Windows startup/registry integration.
- Cloud sync or cross-device scheduling.
- Sub-minute calendar recurrence rules.
- True parallel execution of multiple real power actions. If several live-mode power actions become due at the same time, the scheduler attempts the first actionable task in deterministic order; a real system action may end the session before later tasks can execute.

## Architecture

Use small focused modules and keep `controller.py` as the QML bridge instead of making it own all scheduling logic.

### `task_model.py`

Defines serializable task data:

- `TaskTriggerType`: `countdown`, `fixed_time`, `process_exit`, `network_idle`.
- `RepeatRule`: `once`, `daily`, `weekdays`, `weekends`.
- `TaskStatus`: `pending`, `active`, `paused`, `completed`, `failed`.
- `ScheduledTask`: id, name, action, force-close, trigger type/config, repeat rule, enabled flag, status, created order, next-run timestamp, last-run timestamp, and last error.

The model is plain Python data so tests can cover it without QML.

### `task_scheduler.py`

Owns queue behavior:

- Add/update/remove tasks.
- Enable/disable tasks.
- Compute next due time for one-shot and recurring fixed-time tasks.
- Tick on the existing Qt timer cadence.
- Return due execution requests to the controller instead of directly invoking system actions.
- Reschedule recurring tasks after execution.
- Mark one-shot tasks completed after execution.

The scheduler must not call Windows power APIs directly. It only decides what is due.

### `tray_service.py`

Owns QSystemTrayIcon integration:

- Create tray icon/menu after the QApplication exists.
- Show/hide the main window.
- Display current summary text.
- Pause/resume the scheduler.
- Cancel all tasks after confirmation through the controller/UI layer.
- Quit explicitly.

If a platform or runtime does not provide a usable tray, the app remains usable as a normal window and logs the tray limitation.

### Controller responsibilities

`AppController` remains the boundary exposed to QML:

- Publish queue rows as QML-friendly JSON/text properties.
- Accept QML slots for add/update/delete/enable task operations.
- Bridge scheduler due events into the existing dry-run/live power execution path.
- Preserve existing single-task slots where possible by converting them into queue operations.
- Keep dry-run default true and preserve live-mode confirmation behavior.
- Save and load queued tasks through the settings service.

### QML responsibilities

`Main.qml` gets a task queue section without replacing the current simple controls:

- Existing quick controls remain for fast one-task creation.
- New queue view shows task name, action, trigger summary, repeat rule, status, next run, and enabled state.
- Row actions: enable/disable, delete, and run dry-run check. Editing existing tasks is out of scope for 2.1; users delete and recreate tasks when fields need to change.
- Settings/status copy explains that close sends the app to tray and explicit quit exits.

## Behavior Details

### Tray and background behavior

- Closing the main window hides it to tray by default when tray is available.
- The tray menu has: Show/Hide, Pause/Resume scheduling, Cancel all tasks, Quit.
- Quit asks for confirmation when any enabled task is pending or active.
- While hidden, timers and trigger monitors continue to run.
- Dry-run remains the default and applies equally when hidden.

### Recurring tasks

- Recurrence applies to fixed-time tasks.
- Supported rules: once, daily, weekdays, weekends.
- A fixed time earlier than now schedules the next valid day.
- After a recurring task fires, the next valid occurrence is computed immediately.
- Countdown tasks are one-shot only in 2.1 to avoid ambiguous repeated countdown semantics.

### Multi-task queue

- Tasks are ordered by next due time, then created order.
- Disabled tasks do not fire and keep their configuration.
- Deleting an active process/network trigger stops its monitor.
- Queue rows support fixed-time and countdown tasks fully. For process-exit and network-idle triggers, 2.1 stores them as queue tasks and allows one active process trigger plus one active network trigger at a time; enabling a second task of the same trigger type disables the previous active one with a log entry.
- If multiple tasks are due in dry-run mode, each due task logs what would happen.
- If multiple tasks are due in live mode, execute the first actionable task and log that later due tasks may not run because the system action can end the session.

### Persistence

- Store the task queue in settings as a versioned list.
- On load, ignore invalid task entries with a diagnostic log instead of crashing.
- Recompute next-run values on startup so stale saved timestamps do not fire unexpectedly.
- Preserve existing 2.0 settings keys for dry-run, selected action, force-close, script configuration, process trigger configuration, and network trigger configuration.

### Safety and error handling

- No new code path may bypass dry-run.
- Live mode still requires the existing confirmation before dry-run can be disabled.
- Missing script paths in live mode continue to block execution when scripts are enabled.
- Scheduler errors mark the task failed and log the error; they must not crash the app.
- Process and network trigger read failures continue to fail closed.

## Release Experience

Enhance `package_release.py` to produce release support files next to the zip:

- `dist/SHA256SUMS.txt` containing the zip checksum.
- `dist/release-checklist-v2.1.md` with local verification items and safety reminders.
- `release-manifest.json` inside the bundle keeps version, executable, archive, required file checks, and safety notes.

README and release notes should document:

- Tray/background behavior.
- Recurring task rules.
- Task queue limitations.
- Dry-run/live-mode safety.
- Download and checksum verification steps.

## Testing Strategy

- Unit tests for recurrence calculations, queue ordering, add/update/remove/enable behavior, invalid persisted tasks, and due-task handling.
- Controller tests for converting current quick actions into queue tasks and preserving dry-run execution.
- Release packaging tests for checksum/checklist generation.
- QML static regression tests for new queue/tray/repeat strings and critical bindings.
- Runtime verification launches the app and observes dry-run behavior only. Do not execute real shutdown, restart, sleep, hibernate, log out, or lock actions during validation.

## Implementation Order

1. Add task model and scheduler tests.
2. Implement task model and scheduler.
3. Add persistence through settings service.
4. Bridge controller slots/properties to the scheduler.
5. Add QML task queue and recurrence controls.
6. Add tray service and close-to-tray behavior.
7. Add release checksum/checklist output and docs.
8. Run dry-run runtime verification and packaging checks.

# AutoShutdownQt Core MVP Completion Design

Date: 2026-06-02
Branch: v2-e5e8-reference-ui

## Goal

Complete the v2.0 e5e8 core MVP: fix the overview bottom action text clipping, turn the placeholder secondary pages into usable MVP features, and keep dry-run safety as the default.

## Root Cause: Overview Bottom Text Clipping

The overview column currently allocates fixed height to the hero card and quick countdown row, then lets the power action card consume the remaining height. At the default 1120x720 window this leaves too little space for two rows of `ActionTile` content, so bottom tile text is clipped.

## Chosen Scope

User approved **Core MVP**:

- Fix overview layout so all six power action tiles remain readable at the default window size.
- Add common task templates.
- Add pre-execution script configuration with dry-run-safe behavior.
- Add a process-exit smart trigger MVP.
- Add controller logs/status messages so actions are visible to users.
- Do not add network idle monitoring in this pass; leave it as a clearly labeled future item.

## Architecture

Keep the application small and focused. `AppController` remains the QML-facing state owner, but gains MVP state for script config, process trigger config, and recent logs. QML remains declarative and calls controller slots for actions. `power_service.py` continues to own real OS power actions and is only called when dry-run is disabled.

A new `script_service.py` will isolate subprocess script execution so controller code stays readable and tests can exercise script behavior without touching OS power APIs.

## Feature Behavior

### Overview Layout

The hero and quick countdown cards become more compact, and action tiles use a compact tile height in the overview. The six action tiles must show both Chinese labels and English subtitles without clipping at 1120x720.

### Task Templates

The task page provides one-click templates:

- 15 分钟后关机
- 30 分钟后关机
- 1 小时后睡眠
- 今晚 23:00 关机

Each template sets the selected action and starts the relevant countdown/fixed-time task.

### Script MVP

The script page provides:

- enable/disable switch
- script path input
- timeout seconds input
- run-script dry-run/test button

When script is enabled and a live power action is about to execute, the controller runs the configured script first. If the script is missing, exits non-zero, or times out, the power action is blocked and a log entry is added. In dry-run, no external script is executed; the controller logs what would happen.

### Process Exit Trigger MVP

The smart trigger page provides:

- process name input, e.g. `notepad.exe`
- poll interval seconds input
- start/stop monitoring buttons

The controller periodically checks running process names via a safe service. When a previously seen process disappears, it calls the same execution path as timer completion, preserving script and dry-run behavior. If the process is not currently running when monitoring starts, the trigger is armed in a waiting state and logs that it is waiting to see the process before triggering on exit.

### Logs

The controller exposes a recent log string to QML. Pages show the latest status messages for started tasks, canceled tasks, script dry-run/success/failure, trigger state, and execution decisions.

## Safety

- Dry-run remains true by default.
- No tests or verification should perform real shutdown/restart/logoff/sleep/hibernate/lock.
- Real OS action still requires dry-run disabled and the existing confirm path or trigger/timer completion.
- Script execution is skipped in dry-run.

## Testing

Use Python `unittest` because the repo already has no pytest setup. Tests cover:

- overview QML contains compact readable action tile layout
- task template slots update action/status/countdown
- script dry-run does not run external scripts and logs intent
- script live failure blocks power action path
- process trigger state changes and logs without requiring a real process
- existing UI regression checks still pass

## Acceptance Criteria

- Default overview shows all six power action tile labels/subtitles without bottom clipping.
- Task templates start expected actions.
- Script page fields are editable and controller state updates.
- Process trigger can be started/stopped and logs state.
- Logs appear in QML.
- `python -m py_compile AutoShutdownQt/main.py AutoShutdownQt/controller.py AutoShutdownQt/power_service.py AutoShutdownQt/script_service.py` passes.
- `python -m unittest discover AutoShutdownQt/tests -v` passes.
- QML app loads and dry-run smoke interactions work.

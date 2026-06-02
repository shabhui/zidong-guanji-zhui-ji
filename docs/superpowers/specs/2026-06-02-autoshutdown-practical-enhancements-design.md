# AutoShutdownQt Practical Enhancements Design

Date: 2026-06-02
Branch: v2-e5e8-reference-ui

## Goal

Make the v2.0 e5e8 MVP feel like a usable desktop tool by adding practical persistence, network idle triggering, log utilities, and script path utilities while preserving dry-run safety.

## Chosen Scope

User approved the **实用增强** package:

- Persist key user settings.
- Turn network idle trigger from a future card into a usable MVP feature.
- Add log clear/export actions.
- Add script path validation and opening the containing folder.
- Keep real power execution gated behind the existing dry-run and script execution path.

## Architecture

`AppController` remains the QML-facing state owner. Two small services are added:

- `settings_service.py` handles JSON load/save and chooses a safe config path.
- `network_service.py` reads network byte counters and computes KB/s deltas. It must fail closed: if the platform command/API is unavailable, return an unavailable status instead of crashing.

Controller stores editable network trigger state and owns a network polling `QTimer`. Process exit and network idle triggers both route to `_execute_with_script()` so dry-run/script behavior stays consistent.

## Feature Behavior

### Settings Persistence

Persist these keys:

- `dryRun`
- `forceClose`
- `selectedAction`
- `scriptEnabled`
- `scriptPath`
- `scriptTimeoutSeconds`
- `processName`
- `processPollSeconds`
- `networkDownloadThresholdKbps`
- `networkUploadThresholdKbps`
- `networkIdleSeconds`
- `networkPollSeconds`

Loading invalid/missing values falls back to safe defaults. Saving happens when these properties change. Tests may inject a temp config path/service to avoid writing user files.

### Network Idle Trigger MVP

Smart Trigger page adds editable fields:

- download threshold KB/s
- upload threshold KB/s
- required idle duration seconds
- poll interval seconds

Buttons:

- start network idle monitoring
- stop network idle monitoring

Status display:

- active/inactive state
- latest down/up speed
- accumulated idle seconds
- unavailable message if counters cannot be read

Trigger rule:

1. On start, reset baseline counters and idle accumulation.
2. On each poll, compute KB/s since previous sample.
3. If both down/up are below thresholds, add elapsed time to idle accumulation.
4. If either exceeds threshold, reset idle accumulation to 0.
5. Once idle accumulation reaches required idle duration, stop monitoring and call `_execute_with_script("网络闲置触发")`.

### Log Utilities

Expose:

- `clearLogs()` resets logs to a single ready/safety entry.
- `exportLogs()` writes current logs to a default log file and records the path in logs.

Default export path is a simple deterministic file in the user config directory when available, with project directory fallback. No file picker is required for this pass.

### Script Path Utilities

Expose:

- `validateScriptPath()` logs whether the configured path exists.
- `openScriptFolder()` opens the containing folder when the path exists, or logs an error when it does not.

Dry-run does not affect validation/open-folder because they do not execute the script or power action.

## Safety

- Dry-run remains true by default.
- Network trigger only reads counters.
- Network and process triggers call `_execute_with_script()`, not `power_service.py` directly.
- Script execution still skips in dry-run.
- Real OS power action is not exercised in tests or smoke verification.

## Testing

Use Python `unittest`:

- settings round-trip save/load
- controller auto-save on property changes
- invalid settings fall back safely
- network service parser/counter failure behavior
- network idle trigger fires only after sustained below-threshold samples
- network busy sample resets idle accumulation
- network unavailable logs and does not trigger
- clear/export logs behavior
- script validate/open-folder logging
- QML wiring static checks for new fields/buttons

## Acceptance Criteria

- App loads with persisted settings and safe defaults.
- Network idle trigger can start/stop and shows current status.
- Network idle trigger dry-run path logs simulated execution without real OS action.
- Log clear/export buttons work.
- Script path validation/open-folder buttons work safely.
- `python -m py_compile AutoShutdownQt/main.py AutoShutdownQt/controller.py AutoShutdownQt/power_service.py AutoShutdownQt/script_service.py AutoShutdownQt/settings_service.py AutoShutdownQt/network_service.py` passes.
- `python -m unittest discover AutoShutdownQt/tests -v` passes.
- QML dry-run smoke verifies navigation, network trigger start/stop, log clear/export, and script path validation.

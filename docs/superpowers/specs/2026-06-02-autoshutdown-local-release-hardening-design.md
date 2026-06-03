# AutoShutdownQt 2.0 Local Release Hardening Design

Date: 2026-06-02
Branch: v20-local-release-hardening

## Goal

Prepare AutoShutdownQt 2.0 for a safer local release package without creating a GitHub tag or uploading a Release. The work combines local release checks with small runtime reliability hardening so the final package is harder to publish incorrectly and failures are visible to the user.

## Chosen Scope

User approved **方案 B：发布校验 + 小可靠性补强**.

In scope:

- Keep release work local: no tag creation and no GitHub Release upload.
- Correct release-facing documentation that still points at the old feature branch.
- Add package artifact validation to the existing release script.
- Add targeted runtime safeguards around task replacement, script path validation, power-action errors, and process trigger failures.
- Cover the changes with unit tests and existing release packaging tests.

Out of scope:

- GitHub Release creation.
- Deleting local screenshot files.
- Installer creation, icons, code signing, or CI automation.
- Broad QML visual redesign.

## Architecture

The current structure stays intact:

- `AppController` remains the QML-facing state and orchestration layer.
- `script_service.py`, `power_service.py`, `settings_service.py`, and `network_service.py` remain focused services.
- `package_release.py` remains the single local packaging entry point.

This pass does not introduce new frameworks. It adds small helper methods where they reduce duplication:

- A controller helper for replacing an active timed task before starting another timed task.
- A controller helper for validating the configured script before real execution.
- A package helper for validating expected files inside the zip archive.

## Feature Behavior

### Local Release Validation

`package_release.py` will validate the generated archive after `create_zip()`.

Expected checks:

1. `dist/AutoShutdownQt-2.0.zip` exists.
2. The archive contains `AutoShutdownQt-2.0/AutoShutdownQt.exe`.
3. The archive contains packaged QML assets under the app bundle.
4. The archive is not empty.

If any required artifact is missing, the script raises a clear error instead of printing a successful build message. This keeps the current workflow simple while reducing the chance of uploading a broken zip later.

`README.md` will describe the current local release status using `main` as the source branch. It should state that GitHub Release creation is still a separate manual step.

### Timed Task Replacement

Starting a countdown or fixed-time task while another timed task is running will replace the active timed task cleanly:

- Stop the existing timer.
- Reset the previous remaining time before applying the new task.
- Add a log entry such as `已替换上一任务`.
- Start the new countdown/fixed-time task normally.

Manual triggers such as `executeNow`, process trigger, and network trigger are not treated as timed-task replacement.

### Script Safety Before Real Execution

Dry-run behavior remains unchanged: scripts are not executed, and the log records what would happen.

When dry-run is off and `scriptEnabled` is true, the controller validates the script path before invoking `script_service.run_script()`:

- Empty script path blocks the power action and logs a clear error.
- Missing script path blocks the power action and logs a clear error.
- Existing file or directory paths can proceed to the existing script runner.

This prevents a misconfigured script from falling through into a real power action.

### Power Action Error Visibility

Real power execution will be wrapped so exceptions do not crash the UI flow silently:

- `_execute_power_action()` still delegates to an injected test executor or `power_service.execute_power_action()`.
- `_execute_with_script()` catches execution exceptions and logs `电源动作执行失败：...`.
- Dry-run execution remains unaffected and never calls the real power service.

The goal is visibility, not retry logic.

### Process Trigger Failure Visibility

Process detection currently fails closed. This pass keeps that safety but makes failures visible when possible:

- `_is_process_running()` records the last process-check error when `tasklist` or parsing fails.
- `startProcessTrigger()` and `_poll_process_trigger()` use that error to update trigger status and log a clear message.
- A failed process check does not execute the power action.

This avoids confusing `等待进程出现` status when process detection itself is unavailable.

## Error Handling

- Release validation errors are explicit `RuntimeError`/`SystemExit` messages from `package_release.py`.
- Settings save failures continue to log instead of crashing.
- Script misconfiguration blocks real execution and logs why.
- Power-action exceptions are logged once per failed execution attempt.
- Process-trigger detection failures stop or avoid starting the trigger; they do not trigger power actions.

## Testing

Use Python `unittest` and existing static packaging tests.

Controller tests:

- Starting a new countdown while one is running logs replacement and uses the new duration.
- Starting a fixed-time task while a countdown is running logs replacement.
- Real mode with script enabled and an empty script path blocks the power action.
- Real mode with script enabled and a missing script path blocks the power action.
- Power executor exceptions are logged and do not propagate.
- Process detection failure updates status/log and does not execute a power action.

Release tests:

- `package_release.py` exposes archive validation behavior.
- Validation passes for a zip containing exe and QML entries.
- Validation fails clearly when the exe is missing.
- README no longer points at the old `v2-e5e8-reference-ui` branch as the current release branch.

Existing tests remain part of acceptance.

## Acceptance Criteria

- `README.md` current branch/release status is accurate for `main` and local release preparation.
- `package_release.py` validates generated zip contents before reporting success.
- Timed task replacement is explicit and logged.
- Misconfigured real-mode scripts block power actions.
- Real power execution errors are visible in logs.
- Process trigger detection failures are visible and fail closed.
- `python -m py_compile AutoShutdownQt/main.py AutoShutdownQt/controller.py AutoShutdownQt/power_service.py AutoShutdownQt/script_service.py AutoShutdownQt/settings_service.py AutoShutdownQt/network_service.py AutoShutdownQt/package_release.py` passes.
- `python -m unittest discover AutoShutdownQt/tests -v` passes.
- Existing local screenshots remain untracked and untouched.

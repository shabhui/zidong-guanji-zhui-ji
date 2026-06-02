# AutoShutdownQt Core MVP Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the v2.0 e5e8 core MVP by fixing overview clipping and adding task templates, script configuration, process-exit trigger, and logs.

**Architecture:** `AppController` remains the QML state owner. New `script_service.py` isolates subprocess script execution. QML pages become editable/interactive while preserving dry-run safety and existing `power_service.py` behavior.

**Tech Stack:** Python 3, PySide6/QML, Qt Quick Controls, Python `unittest`.

---

## Files

- Modify: `AutoShutdownQt/controller.py` — add MVP state, slots, logs, templates, script and process trigger logic.
- Create: `AutoShutdownQt/script_service.py` — run configured scripts with timeout and structured result.
- Modify: `AutoShutdownQt/qml/Main.qml` — compact overview layout and wire secondary pages to controller.
- Modify: `AutoShutdownQt/tests/test_e5e8_ui_regressions.py` — add layout/string regression checks.
- Create: `AutoShutdownQt/tests/test_core_mvp_controller.py` — controller behavior tests.

## Task 1: Tests First

- [ ] Add `AutoShutdownQt/tests/test_core_mvp_controller.py` with unittest coverage for task templates, script dry-run/failure, process trigger state, and logs.
- [ ] Extend `AutoShutdownQt/tests/test_e5e8_ui_regressions.py` to assert compact overview action tile heights and secondary page wiring text.
- [ ] Run `python -m unittest discover AutoShutdownQt/tests -v` and confirm new tests fail because controller slots/properties do not exist yet.

## Task 2: Services and Controller

- [ ] Create `AutoShutdownQt/script_service.py` with `ScriptResult` and `run_script(path, timeout_seconds)`.
- [ ] Update `AutoShutdownQt/controller.py` with properties: `scriptEnabled`, `scriptPath`, `scriptTimeoutSeconds`, `processName`, `processPollSeconds`, `processTriggerActive`, `processTriggerStatus`, `logText`.
- [ ] Add slots: `applyTaskTemplate(key)`, `testScript()`, `startProcessTrigger()`, `stopProcessTrigger()`.
- [ ] Route timer completion and immediate execution through `_execute_with_script()`.
- [ ] Ensure dry-run skips external script execution and real power actions.
- [ ] Run controller tests until green.

## Task 3: QML Wiring and Layout

- [ ] Compact overview hero/quick/action-card heights so action tile text is visible at 1120x720.
- [ ] Replace placeholder task page content with template NeonButtons and log/status card.
- [ ] Replace script placeholder with switch, text fields, timeout input, test button, and logs.
- [ ] Replace process trigger placeholder with process input, poll input, start/stop buttons, and status; leave network idle labeled as future.
- [ ] Run UI regression tests until green.

## Task 4: Verification and Commit

- [ ] Run `python -m py_compile AutoShutdownQt/main.py AutoShutdownQt/controller.py AutoShutdownQt/power_service.py AutoShutdownQt/script_service.py`.
- [ ] Run `python -m unittest discover AutoShutdownQt/tests -v`.
- [ ] Launch QML offscreen, navigate pages, click a task template, set script dry-run values, start/stop process trigger, and grab a screenshot.
- [ ] Confirm only source/test/docs changes are staged; do not stage screenshots.
- [ ] Commit with message `Complete AutoShutdownQt core MVP functionality`.

## Self-Review

Spec coverage: layout, task templates, script MVP, process trigger MVP, logs, dry-run safety, tests, and commit are covered. Placeholder scan: no TBD/TODO/fill-ins. Type consistency: property and slot names are listed once and should be used exactly in tests, controller, and QML.

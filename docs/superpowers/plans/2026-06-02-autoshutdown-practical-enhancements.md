# AutoShutdownQt Practical Enhancements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add settings persistence, network idle trigger, log utilities, and script path utilities to the v2.0 e5e8 MVP.

**Architecture:** Keep `AppController` as the QML-facing coordinator. Add `settings_service.py` for JSON persistence and `network_service.py` for network counter/speed sampling. All trigger execution remains routed through `_execute_with_script()` for dry-run safety.

**Tech Stack:** Python 3, PySide6/QML, Qt Quick Controls, Python `unittest`, JSON files, Windows shell helpers.

---

## Files

- Create: `AutoShutdownQt/settings_service.py` — settings path selection, safe JSON load/save, defaults merge.
- Create: `AutoShutdownQt/network_service.py` — network sample dataclass and byte counter/speed sampling with unavailable fallback.
- Modify: `AutoShutdownQt/controller.py` — settings injection/load/save, network trigger properties/slots/timer, log clear/export, script path utilities.
- Modify: `AutoShutdownQt/qml/Main.qml` — network idle controls, log utility buttons, script validation/open-folder buttons.
- Create: `AutoShutdownQt/tests/test_practical_enhancements.py` — behavior tests for services and controller.
- Modify: `AutoShutdownQt/tests/test_e5e8_ui_regressions.py` — static QML wiring tests.

## Task 1: Failing Tests

- [ ] Create `AutoShutdownQt/tests/test_practical_enhancements.py` with tests for settings round-trip, controller auto-save, network idle trigger, log utilities, script path utilities, and network unavailable behavior.
- [ ] Extend `AutoShutdownQt/tests/test_e5e8_ui_regressions.py` to assert QML includes network idle fields/buttons, log buttons, and script utility buttons.
- [ ] Run `python -m unittest discover AutoShutdownQt/tests -v` and verify the new tests fail because new services/properties/slots do not exist.

## Task 2: Settings and Network Services

- [ ] Create `settings_service.py` with `DEFAULT_SETTINGS`, `default_settings()`, `settings_path()`, `load_settings(path=None)`, and `save_settings(settings, path=None)`.
- [ ] Create `network_service.py` with `NetworkSample`, `NetworkSpeed`, `NetworkReader.sample()`, and `compute_speed(previous, current)`.
- [ ] Run tests for services until green.

## Task 3: Controller Enhancements

- [ ] Update `AppController.__init__` to accept optional `settings_path`, `settings_service`, `network_reader`, and `open_folder` injection points for tests.
- [ ] Load persisted settings during initialization with safe defaults.
- [ ] Save settings when persisted properties change.
- [ ] Add network properties: `networkDownloadThresholdKbps`, `networkUploadThresholdKbps`, `networkIdleSeconds`, `networkPollSeconds`, `networkTriggerActive`, `networkTriggerStatus`, `networkSpeedText`.
- [ ] Add slots: `startNetworkTrigger()`, `stopNetworkTrigger()`, `clearLogs()`, `exportLogs()`, `validateScriptPath()`, `openScriptFolder()`.
- [ ] Implement network idle polling and route trigger execution through `_execute_with_script("网络闲置触发")`.
- [ ] Run controller tests until green.

## Task 4: QML Wiring

- [ ] Replace network idle future card with editable controls for thresholds, idle seconds, poll seconds, start/stop, speed/status.
- [ ] Add `清空日志` and `导出日志` buttons to log cards.
- [ ] Add `验证路径` and `打开目录` buttons to script page.
- [ ] Run QML regression tests until green.

## Task 5: Verification and Commit

- [ ] Run `python -m py_compile AutoShutdownQt/main.py AutoShutdownQt/controller.py AutoShutdownQt/power_service.py AutoShutdownQt/script_service.py AutoShutdownQt/settings_service.py AutoShutdownQt/network_service.py`.
- [ ] Run `python -m unittest discover AutoShutdownQt/tests -v`.
- [ ] Launch QML offscreen and drive: network start/stop, script path validation, clear/export logs, dry-run safety.
- [ ] Run `git diff --check`.
- [ ] Stage only source/test files and commit with `Enhance AutoShutdownQt practical functionality`.

## Self-Review

Spec coverage: persistence, network idle trigger, log utilities, script path utilities, safety, testing, and QML verification are covered. Placeholder scan: no TBD/TODO/fill-ins. Type consistency: property/slot names are listed once and should be used exactly in controller, tests, and QML.

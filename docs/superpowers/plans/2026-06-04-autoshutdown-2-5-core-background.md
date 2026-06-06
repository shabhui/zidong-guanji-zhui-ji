# AutoShutdownQt 2.5 Core Background Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build AutoShutdownQt 2.5 portable background-experience enhancements: Windows notifications, task history, and opt-in startup behavior.

**Architecture:** Add focused services for task history, startup registration, and notification delivery. Wire them through AppController properties/slots so QML can present and control the features without moving existing scheduling logic.

**Tech Stack:** Python 3.12, PySide6/QML, unittest, PyInstaller portable zip packaging.

---

## File Structure

- Create `AutoShutdownQt/history_service.py`: task-history event model, retention, export JSON.
- Create `AutoShutdownQt/startup_service.py`: current-user Windows Run registry helpers with injectable registry for tests.
- Create `AutoShutdownQt/notification_service.py`: portable notification wrapper around tray showMessage with fallback logging.
- Modify `AutoShutdownQt/settings_service.py`: add 2.5 settings defaults.
- Modify `AutoShutdownQt/controller.py`: expose properties/slots, record history, call notifications.
- Modify `AutoShutdownQt/main.py`: set version 2.5, inject notification service, apply startup-to-tray behavior.
- Modify `AutoShutdownQt/qml/Main.qml`: add settings/history controls and bindings.
- Modify `AutoShutdownQt/package_release.py`, specs, README, release notes: update 2.5 packaging.
- Add tests under `AutoShutdownQt/tests/` for each service and integration behavior.

## Tasks

### Task 1: Add settings and history service
- [ ] Add failing tests for default history/startup settings and history retention.
- [ ] Implement `history_service.py`.
- [ ] Update `settings_service.py` defaults.
- [ ] Run targeted tests.

### Task 2: Add startup service
- [ ] Add tests for command generation and Run registry set/remove with fake registry.
- [ ] Implement `startup_service.py`.
- [ ] Run targeted tests.

### Task 3: Add notification service
- [ ] Add tests for unavailable fallback and tray showMessage path.
- [ ] Implement `notification_service.py`.
- [ ] Run targeted tests.

### Task 4: Wire controller behavior
- [ ] Add controller tests for history rows, clear/export, snooze/cancel/execution history, notification reminder calls, startup settings.
- [ ] Modify controller properties and slots.
- [ ] Run controller tests.

### Task 5: Wire UI and startup-to-tray
- [ ] Add static QML tests for settings/history controls.
- [ ] Update `Main.qml`.
- [ ] Update `main.py` to version 2.5 and startup-to-tray.
- [ ] Run UI regression tests.

### Task 6: Update release packaging and docs
- [ ] Update package constants/spec to 2.5.
- [ ] Update README and add release notes.
- [ ] Update release tests.
- [ ] Run full tests.
- [ ] Build release zip and checksum.

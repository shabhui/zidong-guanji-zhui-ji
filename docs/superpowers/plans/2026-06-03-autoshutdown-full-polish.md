# AutoShutdownQt 2.0 Full Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete local release, diagnostics, safety UI, and low-risk usability polish for AutoShutdownQt 2.0 without external side effects.

**Architecture:** Keep the existing PySide6/QML architecture. Add small controller slots/properties for diagnostics, safety-mode requests, and snooze; extend the existing packaging script with a release manifest; add static QML regression tests for UI wiring. All behavior is tested through `unittest` and verified by packaging/running the exe in dry-run mode.

**Tech Stack:** Python 3.12, PySide6/QML, PyInstaller, Python `unittest`, JSON, standard-library filesystem tools.

---

## File Structure

- Create `RELEASE_NOTES_v2.0.md`: user-facing release notes and local verification notes.
- Modify `README.md`: point to release notes and mention manifest/diagnostics.
- Modify `AutoShutdownQt/package_release.py`: write and validate `release-manifest.json`.
- Modify `AutoShutdownQt/controller.py`: diagnostics export, dry-run request slot, live-mode warning logging, new templates, snooze.
- Modify `AutoShutdownQt/qml/Main.qml`: stronger LIVE MODE warning, diagnostic export button, maximize/restore controls, new templates/snooze controls.
- Modify tests under `AutoShutdownQt/tests/`: TDD coverage for release docs, manifest, diagnostics, safety slots, templates, snooze, and QML static wiring.

---

### Task 1: Release Notes and Manifest

- [ ] Add tests in `AutoShutdownQt/tests/test_release_packaging.py` asserting `RELEASE_NOTES_v2.0.md` exists and contains: `Dry-run`, `便携版`, `未做代码签名`, `dist/AutoShutdownQt-2.0.zip`.
- [ ] Add tests that `package_release.create_release_manifest()` writes `release-manifest.json` with version `2.0`, exe name, QML entrypoint, and safety notes.
- [ ] Add failing test that zip validation requires `release-manifest.json`.
- [ ] Implement `create_release_manifest()` and include it in `main()` before zipping.
- [ ] Update zip validation to require manifest.
- [ ] Create `RELEASE_NOTES_v2.0.md` and update README.
- [ ] Run `python -m unittest AutoShutdownQt.tests.test_release_packaging -v`.

### Task 2: Diagnostics Export

- [ ] Add tests in `AutoShutdownQt/tests/test_practical_enhancements.py` for `diagnosticText`, `exportLogs()` including diagnostics, and `exportDiagnostics()` writing a diagnostics file.
- [ ] Implement controller diagnostic snapshot/text property and `exportDiagnostics()` slot.
- [ ] Update log export format to include diagnostics before logs.
- [ ] Run targeted diagnostics tests.

### Task 3: Safety Requests and Advanced Templates

- [ ] Add tests for `requestDryRunChange(False)` logging strong live-mode warning and `requestDryRunChange(True)` returning to dry-run.
- [ ] Add tests for new templates: `lock_5`, `sleep_10`, `shutdown_midnight`.
- [ ] Add tests for `snoozeMinutes(minutes)` adjusting active timed task and rejecting invalid/no-active cases.
- [ ] Implement controller slot `requestDryRunChange(bool)`, new templates, and `snoozeMinutes(int)`.
- [ ] Run targeted controller tests.

### Task 4: QML Safety/UI Wiring

- [ ] Add/extend QML static regression tests checking: LIVE MODE warning copy, `requestDryRunChange`, `exportDiagnostics`, maximize/restore control, double-click title bar toggle, new template keys, snooze button.
- [ ] Update `AutoShutdownQt/qml/Main.qml` with static-wired UI polish.
- [ ] Run `python -m unittest AutoShutdownQt.tests.test_e5e8_ui_regressions -v`.

### Task 5: Full Verification

- [ ] Run Python compile check.
- [ ] Run all unit tests.
- [ ] Run `python AutoShutdownQt/package_release.py`.
- [ ] Launch packaged exe in isolated dry-run environment for 8 seconds and confirm it remains running.
- [ ] Run `git status --short` and confirm screenshots remain untracked and untouched.

## Self-Review

- Spec coverage: release notes/manifest in Task 1; diagnostics in Task 2; safety request/templates/snooze in Task 3; UI polish in Task 4; verification in Task 5.
- Placeholder scan: no placeholders; all tasks name exact files and commands.
- Type consistency: controller slots use PySide `@Slot`; manifest helpers live in `package_release.py`; tests use existing `unittest` style.

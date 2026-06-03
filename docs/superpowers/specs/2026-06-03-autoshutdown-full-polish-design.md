# AutoShutdownQt 2.0 Full Polish Design

Date: 2026-06-03
Branch: v20-local-release-hardening

## Goal

Finish the remaining local polish for AutoShutdownQt 2.0 so it is safer to use, easier to diagnose, and more release-ready while staying fully local: no GitHub Release upload, no tag creation, no push, no screenshot deletion, no registry/startup writes, and no real power actions during verification.

## Scope

User asked to do all remaining improvement categories and continue autonomously. This design includes:

1. Release readiness polish.
2. Diagnostics and support polish.
3. UI safety and interaction polish.
4. Low-risk advanced usability features.

High-side-effect work is represented by safe local alternatives:

- No code signing.
- No installer generation.
- No registry writes for startup.
- No real tray daemon behavior that keeps hidden processes running unattended.
- No external publication.

## Release Readiness

### Release Notes

Add `RELEASE_NOTES_v2.0.md` at the repo root. It documents:

- Portable zip release.
- Default dry-run safety mode.
- How live mode works.
- Included features.
- Packaging output path.
- No code signing.
- Known PyInstaller/PySide warning that does not block a successful build.
- Local verification checklist.

### Release Manifest

Enhance `package_release.py` to write a `release-manifest.json` into the app bundle before zipping. The manifest records:

- app name and version.
- bundle directory name.
- expected executable.
- whether required QML entrypoint exists.
- archive name.
- a small list of safety notes.

The manifest must be included in the zip and validated by release tests.

## Diagnostics and Support

### Diagnostic Snapshot

Add a controller diagnostic snapshot that can be exported with logs. The snapshot includes:

- app/version label.
- dry-run/live mode.
- selected action and action label.
- force-close setting.
- script enabled/path/timeout.
- process trigger configuration and current status.
- network trigger configuration and current status.
- current timer status and target info.

`exportLogs()` should write diagnostics first, then recent logs. This improves support reports without exposing secrets beyond the script path the user already configured.

### Explicit Diagnostic Export

Expose `exportDiagnostics()` as a QML slot that writes the same diagnostic block to a deterministic file next to the log export target. QML can wire this as a separate “导出诊断” button where space allows.

## UI Safety and Interaction Polish

### Live Mode Visibility

Make LIVE MODE harder to miss:

- Stronger title-bar text when dry-run is off.
- Settings page warning copy near the dry-run switch.
- Overview cards should describe dry-run vs live behavior clearly.

### Live Mode Toggle Confirmation

Replace direct dry-run switch assignment with a controller slot `requestDryRunChange(enabled)` and QML confirmation dialog for turning dry-run off. Since tests cannot click the dialog reliably, the controller slot still enforces clear logging; QML shows the confirmation before calling it.

### Window Controls

Improve the frameless title bar with a maximize/restore button and double-click-to-toggle maximize. This is UI-only and does not affect core power behavior.

## Low-Risk Advanced Usability

### Safer Presets

Add more task templates that are useful but safe:

- 5 分钟后锁定.
- 10 分钟后睡眠.
- 明天 00:00 关机.

These route through existing countdown/fixed-time behavior and remain covered by dry-run.

### Snooze Current Timed Task

Add a small controller slot `snoozeMinutes(minutes)` that only works when a countdown/fixed-time timer is active. It adds minutes to the remaining countdown and clears fixed target text because the resulting target is now relative. Invalid values log and do nothing.

This gives users a practical “延后” action without building a full task queue.

### Startup Helper Without Registry Writes

Add documentation and diagnostics text for startup support rather than modifying registry automatically. The release notes explain how users can create a Windows shortcut manually if desired. This keeps unattended automation safe.

## Error Handling

- Release manifest write failures should fail packaging clearly.
- Diagnostic export errors should log and not crash.
- Invalid snooze values should log and do nothing.
- Live-mode requests should log a warning when switching off dry-run.

## Testing

Use Python `unittest` and QML static regression tests:

- release notes file exists and documents dry-run, portable zip, unsigned exe, and verification.
- release manifest is created and included in zip validation.
- log export includes diagnostic snapshot.
- `exportDiagnostics()` writes diagnostics file.
- dry-run change request logs strong live-mode warning.
- new task templates start expected actions.
- snooze adjusts active timed task and rejects invalid values.
- QML includes live-mode confirmation copy, maximize/restore control, diagnostic export button, and new template/snooze buttons.

## Acceptance Criteria

- `python -m py_compile ...` passes.
- `python -m unittest discover AutoShutdownQt/tests -v` passes.
- `python AutoShutdownQt/package_release.py` succeeds.
- Packaged exe starts and remains running for at least 8 seconds in dry-run/default mode.
- No GitHub tag, Release upload, push, screenshot deletion, registry startup write, or real power action occurs.

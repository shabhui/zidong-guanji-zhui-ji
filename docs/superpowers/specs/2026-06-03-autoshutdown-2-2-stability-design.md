# AutoShutdownQt 2.2 Stability Design

## Goal

AutoShutdownQt 2.2 is a focused stability patch after the 2.1 practical scheduler release. It should make task queue behavior, tray/background behavior, and release verification more predictable without adding large new features.

## Scope

### In scope

- Keep process-exit and network-idle trigger queue rows synchronized with their active monitors.
- Prevent duplicate active process/network trigger queue entries of the same trigger type.
- Recompute recurring fixed-time task next-run values on startup so stale saved timestamps do not fire unexpectedly.
- Make tray Quit behavior explicit and predictable with close-to-tray interception.
- Improve tray-unavailable diagnostics and user-facing copy.
- Update release packaging identity and checklist for 2.2.
- Update README/release notes with download, checksum, tray, and queue persistence validation notes.

### Out of scope

- Installer generation.
- Code signing.
- Windows startup/registry integration.
- Automatic online updates.
- Task editing UI.
- Large UI redesign.
- Multi-instance coordination.
- Package-size optimization beyond documenting the current size and validation path.

## Behavior Details

### Queue and trigger consistency

Process-exit and network-idle triggers are represented as queue rows, but the monitor is still the authoritative runtime mechanism. v2.2 should keep those two views consistent:

- Starting a process trigger removes or disables any previous active process-exit queue task before adding the new one.
- Starting a network trigger removes or disables any previous active network-idle queue task before adding the new one.
- Stopping a process trigger updates/removes the corresponding process queue row.
- Stopping a network trigger updates/removes the corresponding network queue row.
- Deleting a process/network queue row stops the corresponding monitor when it matches the active runtime trigger.
- Deleting countdown or fixed-time tasks only affects the scheduler queue.

### Recurring task startup

Settings load must not blindly trust saved `nextRunAt` for enabled fixed-time recurring tasks. On startup:

- Disabled tasks remain paused with no next run.
- Completed and failed one-shot tasks remain non-due.
- Enabled recurring fixed-time tasks recompute `nextRunAt` from the current time.
- Enabled one-shot countdown tasks may preserve their saved next-run value only if it is still in the future; stale values are completed or rescheduled according to the existing safe behavior chosen in implementation tests.

### Tray and close behavior

Close-to-tray should not make explicit Quit ambiguous:

- Normal window close hides to tray when the app is running and tray support is available.
- Tray Quit must request explicit application quit and bypass close-to-tray interception.
- If enabled tasks exist, Quit logs a clear warning before quitting.
- If tray setup fails, the app remains usable as a normal window and logs that background tray behavior is unavailable.
- Settings copy should tell users that close-to-tray depends on tray availability.

### Release experience

The 2.2 package should preserve the 2.1 release support files and update identity:

- `AutoShutdownQt-2.2.zip`.
- `SHA256SUMS.txt` with the 2.2 archive checksum.
- `release-checklist-v2.2.md` with explicit tray Quit, close-to-tray, queue persistence, recurring task, and dry-run checks.
- `release-manifest.json` with version `2.2`, archive name, and safety notes.
- README/release notes should document v2.2 as a stability patch and explain checksum verification.

## Architecture

Keep the 2.1 module boundaries:

- `task_scheduler.py` owns task queue state, ordering, due detection, enable/disable, and serialization.
- `controller.py` remains the QML boundary and coordinates runtime trigger monitors with scheduler queue rows.
- `tray_service.py` owns tray callbacks and delegates decisions to the controller.
- `package_release.py` owns build artifacts and release support file generation.

Avoid adding a new abstraction unless tests show that controller trigger/queue synchronization becomes too tangled. Prefer small helper methods in `AppController` for locating and removing trigger queue rows.

## Testing Strategy

- Add scheduler tests for recurring fixed-time startup recomputation.
- Add controller tests for process/network trigger row replacement, stop/delete synchronization, and queue persistence after these operations.
- Add tray tests or QML static tests for Quit bypass copy and tray-unavailable copy.
- Add release packaging tests for 2.2 constants, checksum/checklist names, manifest identity, and release notes.
- Run `python -m unittest discover AutoShutdownQt/tests -v` before committing.

## Implementation Order

1. Add failing scheduler/controller tests for trigger queue synchronization and recurring startup recomputation.
2. Implement minimal scheduler/controller fixes.
3. Add tray/QML tests for Quit and tray-unavailable copy.
4. Implement tray/QML stability fixes.
5. Add 2.2 packaging/release-note tests.
6. Update package release constants, spec, checklist, README/release notes.
7. Run full tests and package validation.

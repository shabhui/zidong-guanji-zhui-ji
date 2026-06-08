# Smooth Process And Network Monitoring Implementation Notes

**Goal:** Make process-exit and network-idle monitoring feel smooth by removing slow system polling from the UI path.

**Implemented approach:** `AppController` now schedules process and network monitor checks through an injectable monitor executor. Production uses a daemon background thread and marshals results back through the controller's existing worker callback signal; tests can use immediate or delayed executors. Process and network monitors keep generation tokens and pending flags so slow checks cannot overlap and stale results after stop/restart are ignored.

**Network sampling:** `NetworkReader` now prefers `psutil.net_io_counters()` when available, avoiding a `netstat -e` subprocess on normal runs. If psutil is unavailable or cannot provide counters, the previous `netstat` fallback and localized error behavior remain intact.

**Behavior preserved:** Existing queue rows, trigger semantics, logs, dry-run execution, and stop/delete behavior remain covered by regression tests. Starting either monitor now immediately shows a "检测中" status and returns without waiting for `tasklist` or `netstat`.

**Verification:**
- `D:\python\python.exe -m unittest discover AutoShutdownQt/tests -v`
- `D:\python\python.exe -m compileall AutoShutdownQt`
- `git diff --check`


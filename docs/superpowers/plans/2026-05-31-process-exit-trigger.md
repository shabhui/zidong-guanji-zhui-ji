# Process Exit Trigger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a trigger that executes the selected power action after a chosen process name has been seen and all matching processes exit.

**Architecture:** Add a focused `ProcessExitService` that polls running processes once per second. `MainWindow` owns process list refresh and start/stop UI. On trigger, reuse the existing reminder/power-action flow by scheduling a countdown equal to the reminder seconds.

**Tech Stack:** WPF, C#/.NET 9, `System.Diagnostics.Process`, existing `ShutdownService`, `MainWindow`, `ReminderWindow`.

---

### Task 1: Create process monitor service

**Files:**
- Create: `AutoShutdown/Services/ProcessExitService.cs`

- [ ] Implement a service with:
  - `Start(string processName)`
  - `Stop()`
  - `Tick` event with process name, count, hasSeenProcess
  - `ProcessExited` event

- [ ] Poll every second with `Process.GetProcessesByName(processName)`.
- [ ] Do not trigger until the process has been seen at least once.
- [ ] Trigger when `hasSeenProcess == true` and count becomes zero.

### Task 2: Add process trigger UI

**Files:**
- Modify: `AutoShutdown/MainWindow.xaml`

- [ ] Add a “进程退出触发” card below network idle trigger.
- [ ] Add `ComboBox x:Name="ProcessListCombo"`.
- [ ] Add buttons:
  - `RefreshProcessListButton`
  - `StartProcessTriggerButton`
  - `StopProcessTriggerButton`
- [ ] Add `TextBlock x:Name="ProcessTriggerStatusLabel"`.

### Task 3: Wire UI to service

**Files:**
- Modify: `AutoShutdown/MainWindow.xaml.cs`

- [ ] Add field:

```csharp
private readonly ProcessExitService _processExit = new();
```

- [ ] Subscribe to service events in constructor.
- [ ] Implement `RefreshProcessList_Click` to populate process names grouped with counts like `chrome (12)`.
- [ ] Implement `StartProcessTrigger_Click` to parse selected process name and start service.
- [ ] Implement `StopProcessTrigger_Click`.
- [ ] On trigger, stop service and schedule reminder countdown using current action.

### Task 4: Verify

**Files:**
- No extra source changes.

- [ ] Build:

```bash
dotnet build "AutoShutdown/AutoShutdown.csproj"
```

Expected: 0 warnings, 0 errors.

- [ ] Smoke test start only:

```bash
"AutoShutdown/bin/Debug/net9.0-windows/AutoShutdown.exe" --minimized
```

Expected: app starts. For manual testing, choose a safe action like Lock and monitor a harmless app such as Notepad.

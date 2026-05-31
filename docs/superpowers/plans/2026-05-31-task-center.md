# Single Active Task Center Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a lightweight task center that saves multiple task presets and automatically runs the nearest enabled task.

**Architecture:** Keep one real timer in `ShutdownService`. Store saved tasks in `AppSettings`; `MainWindow` selects the nearest enabled task, applies its settings to the existing scheduler, and refreshes the UI list. This avoids a multi-timer architecture while making the app feel like a task center.

**Tech Stack:** WPF, C#/.NET 9, existing `SettingsService`, `ShutdownService`, `MainWindow` code-behind.

---

### Task 1: Add saved task model

**Files:**
- Modify: `AutoShutdown/Models/AppSettings.cs`

- [ ] Add to `AppSettings`:

```csharp
public List<SavedTask> SavedTasks { get; set; } = new();
```

- [ ] Add model:

```csharp
public class SavedTask
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N");
    public string Name { get; set; } = "新任务";
    public bool Enabled { get; set; } = true;
    public TimerMode Mode { get; set; } = TimerMode.FixedTime;
    public PowerAction Action { get; set; } = PowerAction.Shutdown;
    public RepeatRule RepeatRule { get; set; } = RepeatRule.Once;
    public int Hours { get; set; }
    public int Minutes { get; set; }
    public int Seconds { get; set; }
    public bool ForceCloseApps { get; set; }
}
```

### Task 2: Add task scheduling helpers to MainWindow

**Files:**
- Modify: `AutoShutdown/MainWindow.xaml.cs`

- [ ] Add field:

```csharp
private SavedTask? _activeTask;
```

- [ ] Add helper `CreateTaskFromCurrentSettings()` to read current UI values.
- [ ] Add helper `GetNextTaskTime(SavedTask task)` to compute countdown/fixed-time next occurrence using repeat rules.
- [ ] Add helper `ScheduleNearestEnabledTask()` to find enabled task with nearest next time, apply action/repeat/force-close, and call existing schedule methods.
- [ ] Add helper `ApplyTaskToInputs(SavedTask task)` so selecting a task fills the current controls.

### Task 3: Add task center UI

**Files:**
- Modify: `AutoShutdown/MainWindow.xaml`
- Modify: `AutoShutdown/MainWindow.xaml.cs`

- [ ] Add a card below action selector titled “任务中心”.
- [ ] Add buttons:
  - Save current as task
  - Run nearest enabled task
- [ ] Add `StackPanel x:Name="TaskListPanel"` to render saved tasks.
- [ ] In code-behind, render each task as a small neon card with name, summary, enabled toggle, apply button, delete button.

### Task 4: Add task operations

**Files:**
- Modify: `AutoShutdown/MainWindow.xaml.cs`

- [ ] Add `SaveCurrentTask_Click` that creates a `SavedTask`, appends it to `_settings.SavedTasks`, saves settings, and refreshes list.
- [ ] Add `RunNearestTask_Click` that calls `ScheduleNearestEnabledTask()`.
- [ ] Add per-task handlers using `Button.Tag` for:
  - apply
  - enable/disable
  - delete
- [ ] Refresh task list after every operation.

### Task 5: Verify

**Files:**
- No additional source changes.

- [ ] Build:

```bash
dotnet build "AutoShutdown/AutoShutdown.csproj"
```

Expected: 0 warnings, 0 errors.

- [ ] Smoke test start only:

```bash
"AutoShutdown/bin/Debug/net9.0-windows/AutoShutdown.exe" --minimized
```

Expected: app starts; do not trigger any real power action.

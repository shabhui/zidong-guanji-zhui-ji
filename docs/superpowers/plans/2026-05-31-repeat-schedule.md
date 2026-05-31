# Repeat Schedule Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add repeat rules for fixed-time schedules: once, daily, workdays, and weekends.

**Architecture:** Keep the app's single active schedule model. Countdown remains one-time. Fixed-time schedules store a repeat rule; when the timer reaches zero, the service either executes once and stops or rolls the target time forward to the next matching day after triggering the selected power action.

**Tech Stack:** WPF, C#/.NET 9, existing `ShutdownService`, `AppSettings`, and `MainWindow` code-behind.

---

### Task 1: Add repeat rule model

**Files:**
- Modify: `AutoShutdown/Models/AppSettings.cs`

- [ ] Add a persisted setting to `AppSettings`:

```csharp
public RepeatRule DefaultRepeatRule { get; set; } = RepeatRule.Once;
```

- [ ] Add enum:

```csharp
public enum RepeatRule
{
    Once,
    Daily,
    Workdays,
    Weekends
}
```

### Task 2: Add recurrence to scheduler service

**Files:**
- Modify: `AutoShutdown/Services/ShutdownService.cs`

- [ ] Add field and property:

```csharp
private RepeatRule _repeatRule = RepeatRule.Once;
public RepeatRule RepeatRule => _repeatRule;
```

- [ ] Add setter:

```csharp
public void SetRepeatRule(RepeatRule repeatRule) => _repeatRule = repeatRule;
```

- [ ] Add helper:

```csharp
private static DateTime GetNextTarget(DateTime currentTarget, RepeatRule repeatRule)
{
    var next = currentTarget.AddDays(1);
    return repeatRule switch
    {
        RepeatRule.Daily => next,
        RepeatRule.Workdays => MoveToMatchingDay(next, day => day is >= DayOfWeek.Monday and <= DayOfWeek.Friday),
        RepeatRule.Weekends => MoveToMatchingDay(next, day => day is DayOfWeek.Saturday or DayOfWeek.Sunday),
        _ => next
    };
}

private static DateTime MoveToMatchingDay(DateTime date, Func<DayOfWeek, bool> matches)
{
    while (!matches(date.DayOfWeek))
        date = date.AddDays(1);
    return date;
}
```

- [ ] In `ExecuteShutdown()`, after `ShutdownTriggered?.Invoke();`, if `_repeatRule != RepeatRule.Once`, compute `_targetTime = GetNextTarget(_targetTime, _repeatRule)`, set `_isScheduled = true`, restart timer, then execute the power action. For once, keep existing stop behavior.

### Task 3: Add repeat selector UI

**Files:**
- Modify: `AutoShutdown/MainWindow.xaml`
- Modify: `AutoShutdown/MainWindow.xaml.cs`

- [ ] In `FixedTimePanel`, add a repeat selector under the hour/minute inputs with four options:
  - `RepeatOnce` tag `Once`
  - `RepeatDaily` tag `Daily`
  - `RepeatWorkdays` tag `Workdays`
  - `RepeatWeekends` tag `Weekends`

- [ ] Add click handler `RepeatRule_Click` that saves `_settings.DefaultRepeatRule`, calls `_shutdown.SetRepeatRule`, updates highlight, and refreshes status if scheduled.

- [ ] In `LoadSettings()`, call:

```csharp
_shutdown.SetRepeatRule(_settings.DefaultRepeatRule);
UpdateRepeatRuleUI();
```

- [ ] In `FixedTimeStart_Click()`, call `_shutdown.SetRepeatRule(_settings.DefaultRepeatRule)` before scheduling.

- [ ] In `CountdownStart_Click()`, call `_shutdown.SetRepeatRule(RepeatRule.Once)` so countdown stays one-time.

### Task 4: Update status labels

**Files:**
- Modify: `AutoShutdown/MainWindow.xaml.cs`

- [ ] Add label helper:

```csharp
private static string GetRepeatLabel(RepeatRule repeatRule) => repeatRule switch
{
    RepeatRule.Once => "单次",
    RepeatRule.Daily => "每日",
    RepeatRule.Workdays => "工作日",
    RepeatRule.Weekends => "周末",
    _ => "单次"
};
```

- [ ] Update `UpdateStatusUI()` to append repeat label for fixed-time schedules and keep countdown as single-use.

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

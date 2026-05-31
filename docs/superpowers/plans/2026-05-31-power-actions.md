# Power Actions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add selectable shutdown alternatives: shutdown, sleep, hibernate, restart, log out, and lock.

**Architecture:** Keep the existing single scheduled timer model. Add a persisted `PowerAction`, pass it through `ShutdownService`, and update UI text based on the selected action. Windows system calls stay isolated inside `ShutdownService`.

**Tech Stack:** WPF, C#/.NET 9, Windows `shutdown.exe`, `powrprof.dll`, `user32.dll`.

---

### Task 1: Add power action model

**Files:**
- Modify: `AutoShutdown/Models/AppSettings.cs`

- [ ] Add this enum after `TimerMode` and add `SelectedPowerAction` to `AppSettings`:

```csharp
public bool ForceCloseApps { get; set; } = false;
public PowerAction SelectedPowerAction { get; set; } = PowerAction.Shutdown;
```

```csharp
public enum PowerAction
{
    Shutdown,
    Sleep,
    Hibernate,
    Restart,
    LogOut,
    Lock
}
```

- [ ] Run build:

```bash
dotnet build "AutoShutdown/AutoShutdown.csproj"
```

Expected: compile errors until service/UI are updated, specifically missing new behavior is acceptable at this checkpoint.

### Task 2: Update shutdown service execution

**Files:**
- Modify: `AutoShutdown/Services/ShutdownService.cs`

- [ ] Add `using System.Runtime.InteropServices;` and `using AutoShutdown.Models;`.

- [ ] Add fields/properties:

```csharp
private PowerAction _powerAction = PowerAction.Shutdown;

public PowerAction PowerAction => _powerAction;
```

- [ ] Add setter:

```csharp
public void SetPowerAction(PowerAction action) => _powerAction = action;
```

- [ ] Replace `ExecuteShutdown()` body to call action-specific execution:

```csharp
public void ExecuteShutdown()
{
    lock (_lock)
    {
        _isScheduled = false;
    }
    _countdownTimer?.Stop();
    _countdownTimer?.Dispose();
    _countdownTimer = null;
    ShutdownTriggered?.Invoke();
    ExecutePowerAction();
}
```

- [ ] Add helpers:

```csharp
public bool SupportsForceCloseApps => _powerAction is PowerAction.Shutdown or PowerAction.Restart or PowerAction.LogOut;

private void ExecutePowerAction()
{
    switch (_powerAction)
    {
        case PowerAction.Shutdown:
            Process.Start("shutdown", _forceCloseApps ? "/s /f /t 0" : "/s /t 0");
            break;
        case PowerAction.Restart:
            Process.Start("shutdown", _forceCloseApps ? "/r /f /t 0" : "/r /t 0");
            break;
        case PowerAction.LogOut:
            Process.Start("shutdown", _forceCloseApps ? "/l /f" : "/l");
            break;
        case PowerAction.Sleep:
            SetSuspendState(false, true, false);
            break;
        case PowerAction.Hibernate:
            SetSuspendState(true, true, false);
            break;
        case PowerAction.Lock:
            LockWorkStation();
            break;
    }
}

[DllImport("powrprof.dll", SetLastError = true)]
private static extern bool SetSuspendState(bool hibernate, bool forceCritical, bool disableWakeEvent);

[DllImport("user32.dll", SetLastError = true)]
private static extern bool LockWorkStation();
```

- [ ] Build:

```bash
dotnet build "AutoShutdown/AutoShutdown.csproj"
```

Expected: may still fail until UI references are added.

### Task 3: Add action selector to main UI

**Files:**
- Modify: `AutoShutdown/MainWindow.xaml`
- Modify: `AutoShutdown/MainWindow.xaml.cs`

- [ ] In XAML, add an “执行动作” card above `CountdownPanel` with six `Border` options named:
  - `ActionShutdown`
  - `ActionSleep`
  - `ActionHibernate`
  - `ActionRestart`
  - `ActionLogOut`
  - `ActionLock`

Each border calls `PowerAction_Click` and has `Tag="Shutdown"`, `Tag="Sleep"`, etc.

- [ ] In code-behind, load and save selected action:

```csharp
_shutdown.SetPowerAction(_settings.SelectedPowerAction);
UpdatePowerActionUI();
```

- [ ] Add action labels:

```csharp
private static string GetActionLabel(PowerAction action) => action switch
{
    PowerAction.Shutdown => "关机",
    PowerAction.Sleep => "睡眠",
    PowerAction.Hibernate => "休眠",
    PowerAction.Restart => "重启",
    PowerAction.LogOut => "注销",
    PowerAction.Lock => "锁定",
    _ => "关机"
};

private static string GetActionVerb(PowerAction action) => action switch
{
    PowerAction.Shutdown => "自动关机",
    PowerAction.Sleep => "自动睡眠",
    PowerAction.Hibernate => "自动休眠",
    PowerAction.Restart => "自动重启",
    PowerAction.LogOut => "自动注销",
    PowerAction.Lock => "自动锁定",
    _ => "自动关机"
};
```

- [ ] Add click handler that parses `Tag`, saves setting, updates service, UI, and status if scheduled.

- [ ] Update `UpdateStatusUI()` to use action-specific text:

```csharp
TargetTimeLabel.Text = $"计划执行：{GetActionVerb(_settings.SelectedPowerAction)} · {_shutdown.TargetTime:yyyy-MM-dd HH:mm:ss}";
ShutdownModeLabel.Text = _shutdown.SupportsForceCloseApps && _settings.ForceCloseApps
    ? "执行方式：强制关闭应用（未保存内容可能丢失）"
    : "执行方式：正常执行";
```

- [ ] Update `OnShutdownTriggered()` balloon text:

```csharp
_tray.ShowBalloon("智能定时关机", $"电脑即将{GetActionLabel(_settings.SelectedPowerAction)}...");
```

- [ ] Hide or disable force-close row when action does not support it.

### Task 4: Update reminder dialog copy

**Files:**
- Modify: `AutoShutdown/ReminderWindow.xaml.cs`
- Modify: `AutoShutdown/ReminderWindow.xaml`

- [ ] Change constructor signature:

```csharp
public ReminderWindow(int seconds, ShutdownService shutdown, MainWindow mainWindow, PowerAction action)
```

- [ ] Store `_action` and update title/message copy:

```csharp
TitleLabel.Text = $"即将{GetActionLabel(_action)}";
MessageLabel.Text = $"电脑将在 {_remainingSeconds} 秒后{GetActionLabel(_action)}";
```

- [ ] Add `x:Name="TitleLabel"` to the title `TextBlock` in XAML.

- [ ] Update `MainWindow.OnReminderReached()` to pass `_settings.SelectedPowerAction`.

### Task 5: Verify and publish

**Files:**
- No source changes expected beyond tasks above.

- [ ] Build:

```bash
dotnet build "AutoShutdown/AutoShutdown.csproj"
```

Expected: 0 warnings, 0 errors.

- [ ] Do not run destructive power actions. Manually review command mapping in `ShutdownService.cs`.

- [ ] Publish:

```bash
dotnet publish "AutoShutdown/AutoShutdown.csproj" -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:EnableCompressionInSingleFile=true -o "AutoShutdown/publish"
```

Expected: publish succeeds. `publish/` remains ignored by git.

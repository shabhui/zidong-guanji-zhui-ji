# Timed Process Close Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enhance the existing process-exit trigger so it can automatically close the monitored process after a configured countdown, then let the existing process-exit flow execute the selected power action.

**Architecture:** Add persisted process-trigger auto-close settings, a focused `TimedProcessCloseService` that only counts down and closes processes, and UI wiring inside the existing “进程退出触发” card. The new service does not execute power actions; `ProcessExitService` remains the single source for detecting “process was seen and then all instances exited,” which keeps the existing reminder flow intact.

**Tech Stack:** WPF, C#/.NET 9, `System.Diagnostics.Process`, `System.Timers.Timer`, existing `AppSettings`, `MainWindow`, `ProcessExitService`, `ShutdownService`, and tray notifications.

---

## File Structure

- Modify `AutoShutdown/Models/AppSettings.cs`
  - Add persisted defaults for the process-trigger auto-close feature.
- Create `AutoShutdown/Services/TimedProcessCloseService.cs`
  - Owns countdown timing and process closing only.
  - Emits UI-friendly events for tick/closing/completed.
  - Reuses `ProcessExitService.NormalizeProcessName` for consistent `.exe` handling.
- Modify `AutoShutdown/MainWindow.xaml`
  - Extend the existing “进程退出触发” card.
  - Make process selection editable.
  - Add auto-close toggle, countdown inputs, timeout input, and status label.
- Modify `AutoShutdown/MainWindow.xaml.cs`
  - Load/save new settings.
  - Start/stop `TimedProcessCloseService` alongside `ProcessExitService`.
  - Display combined process and auto-close status.
  - Preserve the existing `OnProcessExited` reminder scheduling behavior.

---

### Task 1: Add process-trigger auto-close settings

**Files:**
- Modify: `AutoShutdown/Models/AppSettings.cs:12-18`

- [ ] **Step 1: Add persisted settings**

Update `AppSettings` so the top-level settings class contains these properties after `NetworkIdleMinutes` and before `PreActionScriptEnabled`:

```csharp
public bool ProcessTriggerAutoCloseEnabled { get; set; } = false;
public string ProcessTriggerProcessName { get; set; } = string.Empty;
public int ProcessTriggerCloseHours { get; set; } = 1;
public int ProcessTriggerCloseMinutes { get; set; } = 0;
public int ProcessTriggerCloseSeconds { get; set; } = 0;
public int ProcessTriggerCloseTimeoutSeconds { get; set; } = 10;
```

The resulting `AppSettings` class should begin like this:

```csharp
public class AppSettings
{
    public int ReminderSeconds { get; set; } = 60;
    public int DefaultCountdownHours { get; set; } = 0;
    public int DefaultCountdownMinutes { get; set; } = 30;
    public int DefaultCountdownSeconds { get; set; } = 0;
    public bool AutoStartEnabled { get; set; } = false;
    public bool ForceCloseApps { get; set; } = false;
    public PowerAction SelectedPowerAction { get; set; } = PowerAction.Shutdown;
    public RepeatRule DefaultRepeatRule { get; set; } = RepeatRule.Once;
    public int NetworkDownloadThresholdKb { get; set; } = 100;
    public int NetworkUploadThresholdKb { get; set; } = 50;
    public int NetworkIdleMinutes { get; set; } = 5;
    public bool ProcessTriggerAutoCloseEnabled { get; set; } = false;
    public string ProcessTriggerProcessName { get; set; } = string.Empty;
    public int ProcessTriggerCloseHours { get; set; } = 1;
    public int ProcessTriggerCloseMinutes { get; set; } = 0;
    public int ProcessTriggerCloseSeconds { get; set; } = 0;
    public int ProcessTriggerCloseTimeoutSeconds { get; set; } = 10;
    public bool PreActionScriptEnabled { get; set; } = false;
    public string PreActionScriptPath { get; set; } = string.Empty;
    public int PreActionScriptTimeoutSeconds { get; set; } = 60;
    public List<SavedTask> SavedTasks { get; set; } = new();
}
```

- [ ] **Step 2: Build to verify settings compile**

Run:

```bash
dotnet build "AutoShutdown/AutoShutdown.csproj"
```

Expected: build succeeds with `0 Warning(s)` and `0 Error(s)`.

- [ ] **Step 3: Commit settings change**

Run:

```bash
git add AutoShutdown/Models/AppSettings.cs
git commit -m "Add process auto-close settings"
```

---

### Task 2: Create TimedProcessCloseService

**Files:**
- Create: `AutoShutdown/Services/TimedProcessCloseService.cs`

- [ ] **Step 1: Create the service file**

Create `AutoShutdown/Services/TimedProcessCloseService.cs` with this complete content:

```csharp
using System.Diagnostics;
using System.Timers;

namespace AutoShutdown.Services;

public sealed record ProcessCloseResult(
    string ProcessName,
    int InitialCount,
    int NormalCloseRequestedCount,
    int ForceKilledCount,
    int FailedCount,
    string Message);

public sealed class TimedProcessCloseService : IDisposable
{
    private readonly System.Timers.Timer _timer = new(1000);
    private readonly object _lock = new();
    private string _processName = string.Empty;
    private DateTime _targetTime;
    private int _timeoutSeconds;
    private bool _running;
    private bool _closing;

    public event Action<string, TimeSpan>? Tick;
    public event Action<string>? Closing;
    public event Action<ProcessCloseResult>? Completed;

    public TimedProcessCloseService()
    {
        _timer.AutoReset = true;
        _timer.Elapsed += OnTimerElapsed;
    }

    public void Start(string processName, TimeSpan delay, int timeoutSeconds)
    {
        var normalizedName = ProcessExitService.NormalizeProcessName(processName);
        if (string.IsNullOrWhiteSpace(normalizedName) || delay <= TimeSpan.Zero)
            return;

        lock (_lock)
        {
            _processName = normalizedName;
            _targetTime = DateTime.Now + delay;
            _timeoutSeconds = Math.Clamp(timeoutSeconds, 1, 300);
            _running = true;
            _closing = false;
        }

        _timer.Stop();
        _timer.Start();
        RaiseTick();
    }

    public void Stop()
    {
        lock (_lock)
        {
            _running = false;
            _closing = false;
            _processName = string.Empty;
        }

        _timer.Stop();
    }

    private void OnTimerElapsed(object? sender, ElapsedEventArgs e)
    {
        string processName;
        bool shouldClose;

        lock (_lock)
        {
            if (!_running || _closing)
                return;

            processName = _processName;
            shouldClose = DateTime.Now >= _targetTime;
            if (shouldClose)
            {
                _closing = true;
                _running = false;
            }
        }

        if (!shouldClose)
        {
            RaiseTick();
            return;
        }

        _timer.Stop();
        Closing?.Invoke(processName);
        _ = CloseProcessAsync(processName);
    }

    private void RaiseTick()
    {
        string processName;
        TimeSpan remaining;

        lock (_lock)
        {
            if (!_running || _closing)
                return;

            processName = _processName;
            remaining = _targetTime - DateTime.Now;
        }

        Tick?.Invoke(processName, remaining > TimeSpan.Zero ? remaining : TimeSpan.Zero);
    }

    private async Task CloseProcessAsync(string processName)
    {
        int timeoutSeconds;
        lock (_lock)
        {
            timeoutSeconds = _timeoutSeconds;
        }

        var processes = GetProcesses(processName);
        var initialCount = processes.Length;
        var normalCloseRequested = 0;
        var forceKilled = 0;
        var failed = 0;

        if (initialCount == 0)
        {
            Completed?.Invoke(new ProcessCloseResult(processName, 0, 0, 0, 0, $"未找到 {processName} 进程"));
            return;
        }

        foreach (var process in processes)
        {
            try
            {
                if (!process.HasExited && process.MainWindowHandle != IntPtr.Zero && process.CloseMainWindow())
                    normalCloseRequested++;
            }
            catch
            {
                failed++;
            }
        }

        await WaitForExitAsync(processName, timeoutSeconds);

        foreach (var process in GetProcesses(processName))
        {
            try
            {
                if (!process.HasExited)
                {
                    process.Kill();
                    forceKilled++;
                }
            }
            catch
            {
                failed++;
            }
        }

        await WaitForExitAsync(processName, 2);

        var remaining = GetProcesses(processName).Length;
        if (remaining > 0)
            failed += remaining;

        var message = remaining == 0
            ? $"已处理 {processName}：正常关闭 {normalCloseRequested} 个，强制结束 {forceKilled} 个"
            : $"已处理 {processName}，但仍有 {remaining} 个实例未退出";

        Completed?.Invoke(new ProcessCloseResult(processName, initialCount, normalCloseRequested, forceKilled, failed, message));
    }

    private static Process[] GetProcesses(string processName)
    {
        try
        {
            return Process.GetProcessesByName(processName);
        }
        catch
        {
            return Array.Empty<Process>();
        }
    }

    private static async Task WaitForExitAsync(string processName, int timeoutSeconds)
    {
        var deadline = DateTime.Now + TimeSpan.FromSeconds(Math.Clamp(timeoutSeconds, 1, 300));
        while (DateTime.Now < deadline)
        {
            if (GetProcesses(processName).Length == 0)
                return;

            await Task.Delay(250);
        }
    }

    public void Dispose()
    {
        _timer.Dispose();
    }
}
```

- [ ] **Step 2: Build to verify service compiles**

Run:

```bash
dotnet build "AutoShutdown/AutoShutdown.csproj"
```

Expected: build succeeds with `0 Warning(s)` and `0 Error(s)`.

- [ ] **Step 3: Commit service**

Run:

```bash
git add AutoShutdown/Services/TimedProcessCloseService.cs
git commit -m "Add timed process close service"
```

---

### Task 3: Extend the process trigger UI

**Files:**
- Modify: `AutoShutdown/MainWindow.xaml:220-244`

- [ ] **Step 1: Make the process ComboBox editable**

Find the existing process ComboBox:

```xml
<ComboBox x:Name="ProcessListCombo" Height="42" FontSize="14"/>
```

Replace it with:

```xml
<ComboBox x:Name="ProcessListCombo" Height="42" FontSize="14" IsEditable="True" IsTextSearchEnabled="True"/>
```

- [ ] **Step 2: Add auto-close controls inside the process trigger card**

In `AutoShutdown/MainWindow.xaml`, inside the “进程退出触发” card, insert this block after the process picker grid and before the start/stop button grid:

```xml
<Border Height="1" Background="#334D5BFF" Margin="0,16,0,16"/>

<Grid Margin="0,0,0,14">
    <Grid.ColumnDefinitions>
        <ColumnDefinition Width="*"/>
        <ColumnDefinition Width="Auto"/>
    </Grid.ColumnDefinitions>
    <StackPanel Margin="0,0,20,0">
        <TextBlock Text="自动关闭被监控程序" FontSize="14" FontWeight="SemiBold" Foreground="{StaticResource TextPrimaryBrush}"/>
        <TextBlock Text="开启后，到设定时间会先关闭该程序；程序退出后再触发当前电源动作。" FontSize="12" Foreground="{StaticResource TextSecondaryBrush}" TextWrapping="Wrap"/>
    </StackPanel>
    <Border x:Name="ProcessAutoCloseToggle" Grid.Column="1" Width="56" Height="30" CornerRadius="15" Cursor="Hand"
            MouseLeftButtonDown="ProcessAutoCloseToggle_Click" BorderBrush="#5536E8FF" BorderThickness="1">
        <Border x:Name="ProcessAutoCloseKnob" Width="24" Height="24" CornerRadius="12" HorizontalAlignment="Left" Margin="3,0,0,0"/>
    </Border>
</Grid>

<Grid x:Name="ProcessAutoCloseSettingsPanel">
    <Grid.ColumnDefinitions>
        <ColumnDefinition/>
        <ColumnDefinition Width="14"/>
        <ColumnDefinition/>
        <ColumnDefinition Width="14"/>
        <ColumnDefinition/>
        <ColumnDefinition Width="14"/>
        <ColumnDefinition/>
    </Grid.ColumnDefinitions>

    <StackPanel>
        <TextBlock Text="小时" Style="{StaticResource SubtitleText}" Margin="0,0,0,8"/>
        <TextBox x:Name="ProcessCloseHoursInput" Text="1" TextAlignment="Center" MaxLength="2"
                 PreviewTextInput="NumberPreviewTextInput" GotKeyboardFocus="NumberInput_GotKeyboardFocus"/>
    </StackPanel>

    <StackPanel Grid.Column="2">
        <TextBlock Text="分钟" Style="{StaticResource SubtitleText}" Margin="0,0,0,8"/>
        <TextBox x:Name="ProcessCloseMinutesInput" Text="0" TextAlignment="Center" MaxLength="2"
                 PreviewTextInput="NumberPreviewTextInput" GotKeyboardFocus="NumberInput_GotKeyboardFocus"/>
    </StackPanel>

    <StackPanel Grid.Column="4">
        <TextBlock Text="秒" Style="{StaticResource SubtitleText}" Margin="0,0,0,8"/>
        <TextBox x:Name="ProcessCloseSecondsInput" Text="0" TextAlignment="Center" MaxLength="2"
                 PreviewTextInput="NumberPreviewTextInput" GotKeyboardFocus="NumberInput_GotKeyboardFocus"/>
    </StackPanel>

    <StackPanel Grid.Column="6">
        <TextBlock Text="关闭超时秒" Style="{StaticResource SubtitleText}" Margin="0,0,0,8"/>
        <TextBox x:Name="ProcessCloseTimeoutInput" Text="10" TextAlignment="Center" MaxLength="3"
                 PreviewTextInput="NumberPreviewTextInput" GotKeyboardFocus="NumberInput_GotKeyboardFocus"/>
    </StackPanel>
</Grid>

<TextBlock x:Name="ProcessAutoCloseStatusLabel" Text="自动关闭：未启用" FontSize="13" Foreground="{StaticResource TextSecondaryBrush}" Margin="0,10,0,0" TextWrapping="Wrap"/>
```

The process trigger card should still end with the existing buttons and `ProcessTriggerStatusLabel`.

- [ ] **Step 3: Build to verify XAML names compile**

Run:

```bash
dotnet build "AutoShutdown/AutoShutdown.csproj"
```

Expected: this may fail until Task 4 adds `ProcessAutoCloseToggle_Click`. The expected failure, if present, is a missing event handler named `ProcessAutoCloseToggle_Click`. There should be no XML syntax errors.

Do not commit yet if the build fails because the event handler is intentionally added in Task 4.

---

### Task 4: Wire auto-close service into MainWindow

**Files:**
- Modify: `AutoShutdown/MainWindow.xaml.cs:17-23`
- Modify: `AutoShutdown/MainWindow.xaml.cs:37-43`
- Modify: `AutoShutdown/MainWindow.xaml.cs:47-69`
- Modify: `AutoShutdown/MainWindow.xaml.cs:558-628`
- Modify: `AutoShutdown/MainWindow.xaml.cs:737-870`

- [ ] **Step 1: Add the service field and status storage**

Near the existing service fields in `MainWindow`, add `TimedProcessCloseService` plus two status fields:

```csharp
private readonly NetworkIdleService _networkIdle = new();
private readonly ProcessExitService _processExit = new();
private readonly TimedProcessCloseService _timedProcessClose = new();
private readonly PreActionScriptService _preActionScript = new();
private readonly AppSettings _settings;
private SavedTask? _activeTask;
private ReminderWindow? _reminderWindow;
private string _processMonitorStatus = "进程状态：等待选择";
private string _processAutoCloseStatus = "自动关闭：未启用";
```

- [ ] **Step 2: Subscribe to timed close events**

In the constructor, after existing `_processExit` subscriptions and before `_shutdown.BeforePowerActionAsync = RunPreActionScriptAsync;`, add:

```csharp
_timedProcessClose.Tick += OnTimedProcessCloseTick;
_timedProcessClose.Closing += OnTimedProcessCloseClosing;
_timedProcessClose.Completed += OnTimedProcessCloseCompleted;
```

The event subscription block should include:

```csharp
_networkIdle.Tick += OnNetworkIdleTick;
_networkIdle.IdleReached += OnNetworkIdleReached;
_processExit.Tick += OnProcessExitTick;
_processExit.ProcessExited += OnProcessExited;
_timedProcessClose.Tick += OnTimedProcessCloseTick;
_timedProcessClose.Closing += OnTimedProcessCloseClosing;
_timedProcessClose.Completed += OnTimedProcessCloseCompleted;
_shutdown.BeforePowerActionAsync = RunPreActionScriptAsync;
```

- [ ] **Step 3: Load auto-close settings into UI**

In `LoadSettings()`, after network idle inputs are loaded, add:

```csharp
ProcessCloseHoursInput.Text = _settings.ProcessTriggerCloseHours.ToString();
ProcessCloseMinutesInput.Text = _settings.ProcessTriggerCloseMinutes.ToString();
ProcessCloseSecondsInput.Text = _settings.ProcessTriggerCloseSeconds.ToString();
ProcessCloseTimeoutInput.Text = _settings.ProcessTriggerCloseTimeoutSeconds.ToString();
_processAutoCloseStatus = _settings.ProcessTriggerAutoCloseEnabled ? "自动关闭：等待开始监控" : "自动关闭：未启用";
```

After `RefreshProcessList();`, add:

```csharp
if (!string.IsNullOrWhiteSpace(_settings.ProcessTriggerProcessName))
{
    ProcessListCombo.Text = _settings.ProcessTriggerProcessName;
    ProcessListCombo.SelectedValue = _settings.ProcessTriggerProcessName;
}
UpdateProcessAutoCloseUI();
UpdateProcessTriggerLabels();
```

The end of `LoadSettings()` should keep existing calls to `UpdateAutoStartUI()` and `UpdateForceCloseUI()`.

- [ ] **Step 4: Replace RefreshProcessList to preserve typed text**

Replace the current `RefreshProcessList()` method with:

```csharp
private void RefreshProcessList()
{
    var selected = GetSelectedProcessName();
    var processes = System.Diagnostics.Process.GetProcesses()
        .Where(process => !string.IsNullOrWhiteSpace(process.ProcessName))
        .GroupBy(process => process.ProcessName)
        .Select(group => new ProcessListItem(group.Key, group.Count()))
        .OrderBy(item => item.Name)
        .ToList();

    ProcessListCombo.ItemsSource = processes;
    ProcessListCombo.DisplayMemberPath = nameof(ProcessListItem.Display);
    ProcessListCombo.SelectedValuePath = nameof(ProcessListItem.Name);

    if (!string.IsNullOrWhiteSpace(selected))
        ProcessListCombo.Text = selected;
    else if (processes.Count > 0)
        ProcessListCombo.SelectedIndex = 0;
}
```

- [ ] **Step 5: Replace StartProcessTrigger_Click**

Replace the current `StartProcessTrigger_Click` method with:

```csharp
private void StartProcessTrigger_Click(object sender, RoutedEventArgs e)
{
    var processName = ProcessExitService.NormalizeProcessName(GetSelectedProcessName());
    if (string.IsNullOrWhiteSpace(processName))
    {
        _processMonitorStatus = "进程状态：请先刷新并选择进程，或手动输入进程名";
        UpdateProcessTriggerLabels();
        return;
    }

    SaveProcessAutoCloseSettings();
    _settings.ProcessTriggerProcessName = processName;

    var closeDelay = GetProcessCloseDelay();
    if (_settings.ProcessTriggerAutoCloseEnabled && closeDelay <= TimeSpan.Zero)
    {
        _processMonitorStatus = "进程状态：自动关闭倒计时必须大于 0 秒";
        UpdateProcessTriggerLabels();
        return;
    }

    _settingsService.Save(_settings);
    ProcessListCombo.Text = processName;
    _processExit.Start(processName);

    StartProcessTriggerButton.IsEnabled = false;
    StopProcessTriggerButton.IsEnabled = true;
    RefreshProcessListButton.IsEnabled = false;
    ProcessListCombo.IsEnabled = false;
    _processMonitorStatus = $"进程状态：正在监控 {processName}";

    if (_settings.ProcessTriggerAutoCloseEnabled)
    {
        _processAutoCloseStatus = $"自动关闭：将在 {FormatDuration(closeDelay)} 后关闭 {processName}";
        _timedProcessClose.Start(processName, closeDelay, _settings.ProcessTriggerCloseTimeoutSeconds);
    }
    else
    {
        _processAutoCloseStatus = "自动关闭：未启用";
    }

    UpdateProcessAutoCloseUI();
    UpdateProcessTriggerLabels();
}
```

- [ ] **Step 6: Replace StopProcessMonitoring**

Replace the current `StopProcessMonitoring(string statusText)` method with:

```csharp
private void StopProcessMonitoring(string statusText)
{
    _processExit.Stop();
    _timedProcessClose.Stop();
    StartProcessTriggerButton.IsEnabled = true;
    StopProcessTriggerButton.IsEnabled = false;
    RefreshProcessListButton.IsEnabled = true;
    ProcessListCombo.IsEnabled = true;
    _processMonitorStatus = statusText;
    _processAutoCloseStatus = _settings.ProcessTriggerAutoCloseEnabled ? "自动关闭：已停止" : "自动关闭：未启用";
    UpdateProcessAutoCloseUI();
    UpdateProcessTriggerLabels();
}
```

- [ ] **Step 7: Update process status event handlers**

Replace `OnProcessExitTick` with:

```csharp
private void OnProcessExitTick(string processName, int count, bool hasSeenProcess)
{
    Dispatcher.Invoke(() =>
    {
        _processMonitorStatus = hasSeenProcess
            ? $"进程状态：{processName} 正在运行 {count} 个实例"
            : $"进程状态：等待 {processName} 启动/出现";
        UpdateProcessTriggerLabels();
    });
}
```

Replace `OnProcessExited` with:

```csharp
private void OnProcessExited(string processName)
{
    Dispatcher.Invoke(() =>
    {
        StopProcessMonitoring($"进程状态：{processName} 已退出，已触发任务");
        _processAutoCloseStatus = "自动关闭：被监控程序已退出";
        UpdateProcessTriggerLabels();
        _shutdown.SetRepeatRule(RepeatRule.Once);
        _shutdown.ResetReminderFlag();
        _shutdown.ScheduleCountdown(TimeSpan.FromSeconds(_settings.ReminderSeconds));
        UpdateStatusUI();
    });
}
```

- [ ] **Step 8: Add timed close event handlers and helpers**

Add these methods in the `// === Process Exit Trigger ===` section before `ProcessListItem`:

```csharp
private void OnTimedProcessCloseTick(string processName, TimeSpan remaining)
{
    Dispatcher.Invoke(() =>
    {
        _processAutoCloseStatus = $"自动关闭：将在 {FormatDuration(remaining)} 后关闭 {processName}";
        UpdateProcessTriggerLabels();
    });
}

private void OnTimedProcessCloseClosing(string processName)
{
    Dispatcher.Invoke(() =>
    {
        _processAutoCloseStatus = $"自动关闭：正在关闭 {processName}...";
        UpdateProcessTriggerLabels();
    });
}

private void OnTimedProcessCloseCompleted(ProcessCloseResult result)
{
    Dispatcher.Invoke(() =>
    {
        _processAutoCloseStatus = $"自动关闭：{result.Message}";
        UpdateProcessTriggerLabels();
        _tray.ShowBalloon("智能定时关机", result.Message);
    });
}

private string GetSelectedProcessName()
{
    if (ProcessListCombo.SelectedItem is ProcessListItem selectedItem)
    {
        var typedText = ProcessListCombo.Text?.Trim() ?? string.Empty;
        if (string.IsNullOrWhiteSpace(typedText) || typedText == selectedItem.Display || typedText == selectedItem.Name)
            return selectedItem.Name;
    }

    if (!string.IsNullOrWhiteSpace(ProcessListCombo.Text))
        return ProcessListCombo.Text.Trim();

    return ProcessListCombo.SelectedValue?.ToString()?.Trim() ?? string.Empty;
}

private void SaveProcessAutoCloseSettings()
{
    _settings.ProcessTriggerCloseHours = Math.Clamp(ParseInt(ProcessCloseHoursInput.Text), 0, 99);
    _settings.ProcessTriggerCloseMinutes = Math.Clamp(ParseInt(ProcessCloseMinutesInput.Text), 0, 59);
    _settings.ProcessTriggerCloseSeconds = Math.Clamp(ParseInt(ProcessCloseSecondsInput.Text), 0, 59);
    _settings.ProcessTriggerCloseTimeoutSeconds = Math.Clamp(ParseInt(ProcessCloseTimeoutInput.Text), 1, 300);

    ProcessCloseHoursInput.Text = _settings.ProcessTriggerCloseHours.ToString();
    ProcessCloseMinutesInput.Text = _settings.ProcessTriggerCloseMinutes.ToString();
    ProcessCloseSecondsInput.Text = _settings.ProcessTriggerCloseSeconds.ToString();
    ProcessCloseTimeoutInput.Text = _settings.ProcessTriggerCloseTimeoutSeconds.ToString();
}

private TimeSpan GetProcessCloseDelay()
{
    return new TimeSpan(
        _settings.ProcessTriggerCloseHours,
        _settings.ProcessTriggerCloseMinutes,
        _settings.ProcessTriggerCloseSeconds);
}

private void UpdateProcessTriggerLabels()
{
    ProcessTriggerStatusLabel.Text = _processMonitorStatus;
    ProcessAutoCloseStatusLabel.Text = _processAutoCloseStatus;
}

private static string FormatDuration(TimeSpan duration)
{
    if (duration < TimeSpan.Zero)
        duration = TimeSpan.Zero;

    return duration.TotalHours >= 1
        ? duration.ToString(@"hh\:mm\:ss")
        : duration.ToString(@"mm\:ss");
}
```

- [ ] **Step 9: Add auto-close toggle UI handler**

Add this method in the `// === Settings ===` section before `ForceCloseToggle_Click`:

```csharp
private void ProcessAutoCloseToggle_Click(object sender, MouseButtonEventArgs e)
{
    _settings.ProcessTriggerAutoCloseEnabled = !_settings.ProcessTriggerAutoCloseEnabled;
    SaveProcessAutoCloseSettings();
    _settings.ProcessTriggerProcessName = GetSelectedProcessName();
    _settingsService.Save(_settings);
    _processAutoCloseStatus = _settings.ProcessTriggerAutoCloseEnabled ? "自动关闭：等待开始监控" : "自动关闭：未启用";
    UpdateProcessAutoCloseUI();
    UpdateProcessTriggerLabels();
}

private void UpdateProcessAutoCloseUI()
{
    if (_settings.ProcessTriggerAutoCloseEnabled)
    {
        ProcessAutoCloseToggle.Background = FindResource("HeroBrush") as Brush;
        ProcessAutoCloseToggle.Effect = FindResource("CyanShadow") as System.Windows.Media.Effects.Effect;
        ProcessAutoCloseKnob.HorizontalAlignment = System.Windows.HorizontalAlignment.Right;
        ProcessAutoCloseKnob.Background = Brushes.White;
        ProcessAutoCloseSettingsPanel.Opacity = 1;
    }
    else
    {
        ProcessAutoCloseToggle.Background = new SolidColorBrush(Color.FromRgb(28, 31, 54));
        ProcessAutoCloseToggle.Effect = null;
        ProcessAutoCloseKnob.HorizontalAlignment = System.Windows.HorizontalAlignment.Left;
        ProcessAutoCloseKnob.Background = FindResource("TextSecondaryBrush") as Brush;
        ProcessAutoCloseSettingsPanel.Opacity = 0.45;
    }

    PulseElement(ProcessAutoCloseToggle, 1.06);
}
```

- [ ] **Step 10: Build to verify MainWindow wiring**

Run:

```bash
dotnet build "AutoShutdown/AutoShutdown.csproj"
```

Expected: build succeeds with `0 Warning(s)` and `0 Error(s)`.

- [ ] **Step 11: Commit UI and wiring**

Run:

```bash
git add AutoShutdown/MainWindow.xaml AutoShutdown/MainWindow.xaml.cs
git commit -m "Wire timed process close trigger"
```

---

### Task 5: Verify behavior and polish edge cases

**Files:**
- Modify only if verification reveals a compile/runtime issue:
  - `AutoShutdown/Services/TimedProcessCloseService.cs`
  - `AutoShutdown/MainWindow.xaml`
  - `AutoShutdown/MainWindow.xaml.cs`

- [ ] **Step 1: Build from a clean command**

Run:

```bash
dotnet build "AutoShutdown/AutoShutdown.csproj"
```

Expected:

```text
Build succeeded.
    0 Warning(s)
    0 Error(s)
```

If build fails because `AutoShutdown.exe` is in use, run:

```bash
powershell.exe -NoProfile -Command "Get-Process AutoShutdown -ErrorAction SilentlyContinue | Stop-Process -Force"
dotnet build "AutoShutdown/AutoShutdown.csproj"
```

- [ ] **Step 2: Manual safe smoke test with Notepad**

Run the app without triggering destructive actions:

```bash
dotnet run --project "AutoShutdown/AutoShutdown.csproj"
```

Manual steps:

1. Select the safe power action “锁定”.
2. Open Notepad.
3. In “进程退出触发”, choose or type `notepad`.
4. Enable “自动关闭被监控程序”.
5. Set close countdown to `0` hours, `0` minutes, `5` seconds.
6. Set close timeout to `2` seconds.
7. Click “开始监控进程退出”.
8. Confirm the auto-close status counts down.
9. Confirm Notepad closes when the countdown ends.
10. Confirm the existing reminder flow starts after Notepad exits.
11. Cancel the task before it locks the session if you do not want to test the lock action.

Expected:

- The process status reports Notepad running, then exited.
- The auto-close status reports closing/completed.
- The status card appears with a reminder countdown.

- [ ] **Step 3: Manual never-seen process test**

Manual steps:

1. Type a fake process name such as `definitely-not-running-monitor-app`.
2. Enable automatic close.
3. Set close countdown to `0:0:3`.
4. Click “开始监控进程退出”.
5. Wait for the countdown to finish.

Expected:

- Auto-close status says the process was not found.
- Process status continues waiting for the process to appear.
- No power-action reminder is scheduled because `ProcessExitService` never saw the process.
- Click “停止监控” to stop waiting.

- [ ] **Step 4: Manual validation test for zero countdown**

Manual steps:

1. Type or select any process name.
2. Enable automatic close.
3. Set hours, minutes, and seconds to `0`.
4. Click “开始监控进程退出”.

Expected:

- Monitoring does not start.
- Status says `进程状态：自动关闭倒计时必须大于 0 秒`.
- Start button remains enabled.

- [ ] **Step 5: Commit any verification fixes**

If no files changed, skip this step.

If files changed, run:

```bash
git status --short
git add AutoShutdown/Services/TimedProcessCloseService.cs AutoShutdown/MainWindow.xaml AutoShutdown/MainWindow.xaml.cs AutoShutdown/Models/AppSettings.cs
git commit -m "Polish timed process close trigger"
```

---

## Self-Review Notes

- Spec coverage: settings persistence is covered by Task 1; focused close service by Task 2; editable process picker and auto-close UI by Task 3; start/stop behavior and event wiring by Task 4; build plus manual safe scenarios by Task 5.
- Placeholder scan: no `TBD`, `TODO`, “similar to”, or unspecified implementation steps remain.
- Type consistency: property names, event names, method names, and record names are consistent across tasks.

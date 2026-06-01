using System.ComponentModel;
using System.Text.RegularExpressions;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Animation;
using AutoShutdown.Models;
using AutoShutdown.Services;

namespace AutoShutdown;

public enum UiSection
{
    Overview,
    Timer,
    Tasks,
    Triggers,
    Script,
    Settings
}

public partial class MainWindow : Window
{
    private readonly ShutdownService _shutdown;
    private readonly SettingsService _settingsService;
    private readonly TrayIconService _tray;
    private readonly NetworkIdleService _networkIdle = new();
    private readonly ProcessExitService _processExit = new();
    private readonly TimedProcessCloseService _timedProcessClose = new();
    private readonly PreActionScriptService _preActionScript = new();
    private readonly AppSettings _settings;
    private SavedTask? _activeTask;
    private ReminderWindow? _reminderWindow;
    private UiSection _currentSection = UiSection.Overview;
    private string _processMonitorStatus = "进程状态：等待选择";
    private string _processAutoCloseStatus = "自动关闭：未启用";

    public MainWindow(ShutdownService shutdown, SettingsService settingsService, TrayIconService tray)
    {
        InitializeComponent();
        _shutdown = shutdown;
        _settingsService = settingsService;
        _tray = tray;
        _settings = settingsService.Load();

        _shutdown.Tick += OnTick;
        _shutdown.ReminderTimeReached += OnReminderReached;
        _shutdown.ShutdownTriggered += OnShutdownTriggered;
        _shutdown.Cancelled += OnCancelled;
        _shutdown.PauseStateChanged += OnPauseStateChanged;
        _networkIdle.Tick += OnNetworkIdleTick;
        _networkIdle.IdleReached += OnNetworkIdleReached;
        _processExit.Tick += OnProcessExitTick;
        _processExit.ProcessExited += OnProcessExited;
        _timedProcessClose.Tick += OnTimedProcessCloseTick;
        _timedProcessClose.Closing += OnTimedProcessCloseClosing;
        _timedProcessClose.Completed += OnTimedProcessCloseCompleted;
        _shutdown.BeforePowerActionAsync = RunPreActionScriptAsync;

        LoadSettings();
        Loaded += (_, _) => StartEntranceAnimations();
    }

    private void LoadSettings()
    {
        ReminderSecondsInput.Text = _settings.ReminderSeconds.ToString();
        HoursInput.Text = _settings.DefaultCountdownHours.ToString();
        MinutesInput.Text = _settings.DefaultCountdownMinutes.ToString();
        SecondsInput.Text = _settings.DefaultCountdownSeconds.ToString();
        NetworkDownloadThresholdInput.Text = _settings.NetworkDownloadThresholdKb.ToString();
        NetworkUploadThresholdInput.Text = _settings.NetworkUploadThresholdKb.ToString();
        NetworkIdleMinutesInput.Text = _settings.NetworkIdleMinutes.ToString();
        ProcessCloseHoursInput.Text = _settings.ProcessTriggerCloseHours.ToString();
        ProcessCloseMinutesInput.Text = _settings.ProcessTriggerCloseMinutes.ToString();
        ProcessCloseSecondsInput.Text = _settings.ProcessTriggerCloseSeconds.ToString();
        ProcessCloseTimeoutInput.Text = _settings.ProcessTriggerCloseTimeoutSeconds.ToString();
        _processAutoCloseStatus = _settings.ProcessTriggerAutoCloseEnabled ? "自动关闭：等待开始监控" : "自动关闭：未启用";
        PreActionScriptPathInput.Text = _settings.PreActionScriptPath;
        PreActionScriptTimeoutInput.Text = _settings.PreActionScriptTimeoutSeconds.ToString();
        UpdatePreActionScriptUI();
        _shutdown.SetReminderSeconds(_settings.ReminderSeconds);
        _shutdown.SetForceCloseApps(_settings.ForceCloseApps);
        _shutdown.SetPowerAction(_settings.SelectedPowerAction);
        _shutdown.SetRepeatRule(_settings.DefaultRepeatRule);
        UpdatePowerActionUI();
        UpdateRepeatRuleUI();
        RefreshTaskList();
        RefreshProcessList();
        if (!string.IsNullOrWhiteSpace(_settings.ProcessTriggerProcessName))
        {
            ProcessListCombo.Text = _settings.ProcessTriggerProcessName;
            ProcessListCombo.SelectedValue = _settings.ProcessTriggerProcessName;
        }
        UpdateProcessAutoCloseUI();
        UpdateProcessTriggerLabels();
        UpdateAutoStartUI();
        UpdateForceCloseUI();
        ShowSection(UiSection.Overview);
        UpdateReadyOverview();
    }

    // === Mode Switching ===

    private void CountdownMode_Click(object sender, MouseButtonEventArgs e)
    {
        BtnCountdown.Background = FindResource("HeroBrush") as Brush;
        BtnCountdown.Effect = FindResource("NeonShadow") as System.Windows.Media.Effects.Effect;
        ((TextBlock)((Border)BtnCountdown).Child).Foreground = Brushes.White;
        BtnFixed.Background = Brushes.Transparent;
        BtnFixed.Effect = null;
        ((TextBlock)((Border)BtnFixed).Child).Foreground = FindResource("TextSecondaryBrush") as Brush;
        SwitchPanel(CountdownPanel, FixedTimePanel);
    }

    private void FixedMode_Click(object sender, MouseButtonEventArgs e)
    {
        BtnFixed.Background = FindResource("HeroBrush") as Brush;
        BtnFixed.Effect = FindResource("NeonShadow") as System.Windows.Media.Effects.Effect;
        ((TextBlock)((Border)BtnFixed).Child).Foreground = Brushes.White;
        BtnCountdown.Background = Brushes.Transparent;
        BtnCountdown.Effect = null;
        ((TextBlock)((Border)BtnCountdown).Child).Foreground = FindResource("TextSecondaryBrush") as Brush;
        SwitchPanel(FixedTimePanel, CountdownPanel);
    }

    // === Countdown ===

    private void CountdownStart_Click(object sender, RoutedEventArgs e)
    {
        int h = ParseInt(HoursInput.Text);
        int m = ParseInt(MinutesInput.Text);
        int s = ParseInt(SecondsInput.Text);

        if (h == 0 && m == 0 && s == 0) return;

        var duration = new TimeSpan(h, m, s);
        _shutdown.SetRepeatRule(RepeatRule.Once);
        _shutdown.ResetReminderFlag();
        _shutdown.ScheduleCountdown(duration);

        UpdateStatusUI();
    }

    private void QuickCountdown_Click(object sender, RoutedEventArgs e)
    {
        if (sender is not System.Windows.Controls.Button button || button.Tag is not string tag || !int.TryParse(tag, out var minutes))
            return;

        var duration = TimeSpan.FromMinutes(minutes);
        HoursInput.Text = ((int)duration.TotalHours).ToString();
        MinutesInput.Text = duration.Minutes.ToString();
        SecondsInput.Text = "0";
        UpdateReadyOverview();
        PulseElement(StatusCard, 1.01);
    }

    // === Fixed Time ===

    private void FixedTimeStart_Click(object sender, RoutedEventArgs e)
    {
        int h = ParseInt(FixedHourInput.Text);
        int m = ParseInt(FixedMinuteInput.Text);

        if (h < 0 || h > 23) h = 23;
        if (m < 0 || m > 59) m = 0;

        var now = DateTime.Now;
        var target = new DateTime(now.Year, now.Month, now.Day, h, m, 0);
        if (target <= now) target = target.AddDays(1);

        _shutdown.SetRepeatRule(_settings.DefaultRepeatRule);
        _shutdown.ResetReminderFlag();
        _shutdown.ScheduleFixedTime(target);

        UpdateStatusUI();
    }

    private void ExecuteCurrentAction_Click(object sender, RoutedEventArgs e)
    {
        _shutdown.SetPowerAction(_settings.SelectedPowerAction);
        _shutdown.SetForceCloseApps(_settings.ForceCloseApps);
        _shutdown.SetRepeatRule(RepeatRule.Once);
        _shutdown.ResetReminderFlag();
        _shutdown.ExecuteShutdown();
    }

    // === Cancel ===

    private void CancelShutdown_Click(object sender, RoutedEventArgs e)
    {
        _activeTask = null;
        _shutdown.Cancel();
        _reminderWindow?.Close();
    }

    // === Task Center ===

    private SavedTask CreateTaskFromCurrentSettings()
    {
        var mode = CountdownPanel.Visibility == Visibility.Visible ? TimerMode.Countdown : TimerMode.FixedTime;
        return new SavedTask
        {
            Name = $"{GetActionLabel(_settings.SelectedPowerAction)} · {DateTime.Now:HH:mm:ss}",
            Enabled = true,
            Mode = mode,
            Action = _settings.SelectedPowerAction,
            RepeatRule = mode == TimerMode.Countdown ? RepeatRule.Once : _settings.DefaultRepeatRule,
            Hours = mode == TimerMode.Countdown ? ParseInt(HoursInput.Text) : ParseInt(FixedHourInput.Text),
            Minutes = mode == TimerMode.Countdown ? ParseInt(MinutesInput.Text) : ParseInt(FixedMinuteInput.Text),
            Seconds = mode == TimerMode.Countdown ? ParseInt(SecondsInput.Text) : 0,
            ForceCloseApps = _settings.ForceCloseApps
        };
    }

    private DateTime GetNextTaskTime(SavedTask task)
    {
        if (task.Mode == TimerMode.Countdown)
            return DateTime.Now + new TimeSpan(task.Hours, task.Minutes, task.Seconds);

        var now = DateTime.Now;
        var target = new DateTime(now.Year, now.Month, now.Day, Math.Clamp(task.Hours, 0, 23), Math.Clamp(task.Minutes, 0, 59), 0);
        if (target <= now)
            target = target.AddDays(1);

        return task.RepeatRule switch
        {
            RepeatRule.Workdays => MoveToMatchingDay(target, day => day is >= DayOfWeek.Monday and <= DayOfWeek.Friday),
            RepeatRule.Weekends => MoveToMatchingDay(target, day => day is DayOfWeek.Saturday or DayOfWeek.Sunday),
            _ => target
        };
    }

    private static DateTime MoveToMatchingDay(DateTime date, Func<DayOfWeek, bool> matches)
    {
        while (!matches(date.DayOfWeek))
            date = date.AddDays(1);
        return date;
    }

    private bool ScheduleNearestEnabledTask()
    {
        var next = _settings.SavedTasks
            .Where(task => task.Enabled)
            .Select(task => new { Task = task, Time = GetNextTaskTime(task) })
            .OrderBy(item => item.Time)
            .FirstOrDefault();

        if (next == null)
            return false;

        ApplyTaskToInputs(next.Task);
        _activeTask = next.Task;
        _settings.SelectedPowerAction = next.Task.Action;
        _settings.ForceCloseApps = next.Task.ForceCloseApps;
        _settings.DefaultRepeatRule = next.Task.RepeatRule;
        _shutdown.SetPowerAction(next.Task.Action);
        _shutdown.SetForceCloseApps(next.Task.ForceCloseApps);
        _shutdown.SetRepeatRule(next.Task.Mode == TimerMode.Countdown ? RepeatRule.Once : next.Task.RepeatRule);
        _shutdown.ResetReminderFlag();

        if (next.Task.Mode == TimerMode.Countdown)
            _shutdown.ScheduleCountdown(new TimeSpan(next.Task.Hours, next.Task.Minutes, next.Task.Seconds));
        else
            _shutdown.ScheduleFixedTime(next.Time);

        UpdatePowerActionUI();
        UpdateRepeatRuleUI();
        UpdateForceCloseUI();
        UpdateStatusUI();
        return true;
    }

    private void ApplyTaskToInputs(SavedTask task)
    {
        _settings.SelectedPowerAction = task.Action;
        _settings.ForceCloseApps = task.ForceCloseApps;
        _settings.DefaultRepeatRule = task.RepeatRule;
        _shutdown.SetPowerAction(task.Action);
        _shutdown.SetForceCloseApps(task.ForceCloseApps);
        _shutdown.SetRepeatRule(task.RepeatRule);

        if (task.Mode == TimerMode.Countdown)
        {
            CountdownMode_Click(BtnCountdown, new MouseButtonEventArgs(Mouse.PrimaryDevice, 0, MouseButton.Left));
            HoursInput.Text = task.Hours.ToString();
            MinutesInput.Text = task.Minutes.ToString();
            SecondsInput.Text = task.Seconds.ToString();
        }
        else
        {
            FixedMode_Click(BtnFixed, new MouseButtonEventArgs(Mouse.PrimaryDevice, 0, MouseButton.Left));
            FixedHourInput.Text = Math.Clamp(task.Hours, 0, 23).ToString();
            FixedMinuteInput.Text = Math.Clamp(task.Minutes, 0, 59).ToString("00");
        }

        UpdatePowerActionUI();
        UpdateRepeatRuleUI();
        UpdateForceCloseUI();
    }

    private string GetTaskSummary(SavedTask task)
    {
        var time = task.Mode == TimerMode.Countdown
            ? $"{task.Hours:D2}:{task.Minutes:D2}:{task.Seconds:D2} 后"
            : $"{task.Hours:D2}:{task.Minutes:D2} · {GetRepeatLabel(task.RepeatRule)}";
        return $"{GetActionVerb(task.Action)} · {time}";
    }

    private void SaveCurrentTask_Click(object sender, RoutedEventArgs e)
    {
        var task = CreateTaskFromCurrentSettings();
        if (task.Mode == TimerMode.Countdown && task.Hours == 0 && task.Minutes == 0 && task.Seconds == 0)
            return;

        _settings.SavedTasks.Add(task);
        _settingsService.Save(_settings);
        RefreshTaskList();
    }

    private void RunNearestTask_Click(object sender, RoutedEventArgs e)
    {
        if (!ScheduleNearestEnabledTask())
            _tray.ShowBalloon("智能定时关机", "没有启用的任务");
    }

    private void TaskApply_Click(object sender, RoutedEventArgs e)
    {
        var task = GetTaskFromButton(sender);
        if (task == null) return;
        ApplyTaskToInputs(task);
        _settingsService.Save(_settings);
    }

    private void TaskToggle_Click(object sender, RoutedEventArgs e)
    {
        var task = GetTaskFromButton(sender);
        if (task == null) return;
        task.Enabled = !task.Enabled;
        _settingsService.Save(_settings);
        RefreshTaskList();
    }

    private void TaskDelete_Click(object sender, RoutedEventArgs e)
    {
        var task = GetTaskFromButton(sender);
        if (task == null) return;
        _settings.SavedTasks.Remove(task);
        if (_activeTask?.Id == task.Id)
            _activeTask = null;
        _settingsService.Save(_settings);
        RefreshTaskList();
    }

    private SavedTask? GetTaskFromButton(object sender)
    {
        if (sender is not System.Windows.Controls.Button button || button.Tag is not string id)
            return null;
        return _settings.SavedTasks.FirstOrDefault(task => task.Id == id);
    }

    private void RefreshTaskList()
    {
        TaskListPanel.Children.Clear();
        if (_settings.SavedTasks.Count == 0)
        {
            TaskListPanel.Children.Add(new TextBlock
            {
                Text = "还没有保存的任务。先设置动作和时间，再点击“保存当前为任务”。",
                Foreground = FindResource("TextSecondaryBrush") as Brush,
                TextWrapping = TextWrapping.Wrap,
                Margin = new Thickness(0, 4, 0, 0)
            });
            return;
        }

        foreach (var task in _settings.SavedTasks.OrderBy(GetNextTaskTime))
        {
            var card = new Border
            {
                CornerRadius = new CornerRadius(20),
                Padding = new Thickness(16),
                Margin = new Thickness(0, 0, 0, 12),
                Background = FindResource("CommandCardBrush") as Brush,
                BorderBrush = task.Enabled ? FindResource("CommandCardBorderBrush") as Brush : FindResource("GlassBorderBrush") as Brush,
                BorderThickness = new Thickness(1),
                Effect = task.Enabled ? FindResource("CyanShadow") as System.Windows.Media.Effects.Effect : null,
                Opacity = task.Enabled ? 1 : 0.52
            };

            var root = new Grid();
            root.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            root.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            var text = new StackPanel();
            text.Children.Add(new TextBlock
            {
                Text = task.Name,
                FontWeight = FontWeights.Bold,
                Foreground = FindResource("TextPrimaryBrush") as Brush,
                FontSize = 14
            });
            text.Children.Add(new TextBlock
            {
                Text = GetTaskSummary(task),
                Foreground = FindResource("TextSecondaryBrush") as Brush,
                FontSize = 12,
                Margin = new Thickness(0, 4, 0, 0)
            });
            text.Children.Add(new TextBlock
            {
                Text = $"NEXT · {GetNextTaskTime(task):yyyy-MM-dd HH:mm:ss}",
                Foreground = FindResource("AccentBrush") as Brush,
                FontSize = 12,
                Margin = new Thickness(0, 4, 0, 0)
            });
            root.Children.Add(text);

            var actions = new StackPanel { Orientation = System.Windows.Controls.Orientation.Horizontal, VerticalAlignment = VerticalAlignment.Center };
            actions.Children.Add(CreateTaskButton(task, task.Enabled ? "禁用" : "启用", TaskToggle_Click));
            actions.Children.Add(CreateTaskButton(task, "应用", TaskApply_Click));
            actions.Children.Add(CreateTaskButton(task, "删除", TaskDelete_Click));
            Grid.SetColumn(actions, 1);
            root.Children.Add(actions);

            card.Child = root;
            TaskListPanel.Children.Add(card);
        }
    }

    private System.Windows.Controls.Button CreateTaskButton(SavedTask task, string text, RoutedEventHandler click)
    {
        var button = new System.Windows.Controls.Button
        {
            Content = text,
            Tag = task.Id,
            Style = FindResource("SecondaryButton") as Style,
            Padding = new Thickness(10, 7, 10, 7),
            Margin = new Thickness(8, 0, 0, 0),
            FontSize = 12
        };
        button.Click += click;
        return button;
    }

    // === Status Updates ===

    private void UpdateReadyOverview()
    {
        var duration = new TimeSpan(ParseInt(HoursInput.Text), ParseInt(MinutesInput.Text), ParseInt(SecondsInput.Text));
        StatusTitle.Text = "准备启动任务";
        RemainingLabel.Text = "默认倒计时";
        RemainingTime.Text = duration.ToString(@"hh\:mm\:ss");
        TargetTimeLabel.Text = $"当前动作：{GetActionLabel(_settings.SelectedPowerAction)}";
        ShutdownModeLabel.Text = _shutdown.SupportsForceCloseApps && _settings.ForceCloseApps
            ? "执行方式：强制关闭应用（未保存内容可能丢失）"
            : "执行方式：正常执行";
        SetStatusBadge("READY", "StatusReadyBrush");
        OverviewStartButton.IsEnabled = true;
        PauseResumeButton.Visibility = Visibility.Collapsed;
        CancelPlanButton.Visibility = Visibility.Collapsed;
        UpdateOverviewSummaries();
    }

    private void SetStatusBadge(string text, string brushKey)
    {
        HeaderStatusText.Text = text;
        OverviewStatusText.Text = text;
        var brush = FindResource(brushKey) as Brush;
        HeaderStatusText.Foreground = brush;
        OverviewStatusText.Foreground = brush;
    }

    private void UpdateOverviewSummaries()
    {
        OverviewActionSummary.Text = $"动作：{GetActionLabel(_settings.SelectedPowerAction)}";
        OverviewReminderSummary.Text = $"提醒：提前 {_settings.ReminderSeconds} 秒";
        OverviewForceSummary.Text = _settings.ForceCloseApps && _shutdown.SupportsForceCloseApps ? "强制关闭：开启" : "强制关闭：关闭";
        OverviewScriptSummary.Text = _settings.PreActionScriptEnabled ? $"脚本：已启用 · 超时 {_settings.PreActionScriptTimeoutSeconds} 秒" : "脚本：未启用";
    }

    private void UpdateStatusUI()
    {
        StatusCard.Visibility = Visibility.Visible;
        PulseElement(StatusCard);
        CountdownStartBtn.IsEnabled = false;
        FixedTimeStartBtn.IsEnabled = false;
        OverviewStartButton.IsEnabled = false;
        PauseResumeButton.Visibility = Visibility.Visible;
        CancelPlanButton.Visibility = Visibility.Visible;
        _tray.SetShutdownActive(true);
        UpdatePauseUI();
        var repeatText = _shutdown.RepeatRule == RepeatRule.Once ? "单次" : GetRepeatLabel(_shutdown.RepeatRule);
        TargetTimeLabel.Text = _shutdown.IsPaused
            ? $"已暂停：{GetActionVerb(_settings.SelectedPowerAction)} · {repeatText} · 将于 {_shutdown.PauseUntil:HH:mm} 自动恢复"
            : $"计划执行：{GetActionVerb(_settings.SelectedPowerAction)} · {repeatText} · {_shutdown.TargetTime:yyyy-MM-dd HH:mm:ss}";
        ShutdownModeLabel.Text = _shutdown.SupportsForceCloseApps && _settings.ForceCloseApps
            ? "执行方式：强制关闭应用（未保存内容可能丢失）"
            : "执行方式：正常执行";
        UpdateOverviewSummaries();
    }

    private void OnTick(string remaining)
    {
        Dispatcher.Invoke(() =>
        {
            RemainingTime.Text = remaining;
            PulseElement(RemainingTime, 1.025);
        });
    }

    private void OnReminderReached()
    {
        Dispatcher.Invoke(() =>
        {
            _reminderWindow = new ReminderWindow(_settings.ReminderSeconds, _shutdown, this, _settings.SelectedPowerAction);
            _reminderWindow.ShowDialog();
        });
    }

    private void OnShutdownTriggered()
    {
        Dispatcher.Invoke(() =>
        {
            _tray.ShowBalloon("智能定时关机", $"电脑即将{GetActionLabel(_settings.SelectedPowerAction)}...");
        });
    }

    private void OnCancelled()
    {
        Dispatcher.Invoke(() =>
        {
            CountdownStartBtn.IsEnabled = true;
            FixedTimeStartBtn.IsEnabled = true;
            OverviewStartButton.IsEnabled = true;
            PauseResumeButton.Visibility = Visibility.Collapsed;
            CancelPlanButton.Visibility = Visibility.Collapsed;
            _tray.SetShutdownActive(false);
            _tray.SetPaused(false);
            UpdateReadyOverview();
            _tray.ShowBalloon("智能定时关机", "已取消任务计划");
        });
    }

    private void OnPauseStateChanged()
    {
        Dispatcher.Invoke(() =>
        {
            _reminderWindow?.Close();
            UpdatePauseUI();
            UpdateStatusUI();
            _tray.SetPaused(_shutdown.IsPaused);
            _tray.ShowBalloon("智能定时关机", _shutdown.IsPaused ? "任务已暂停 1 小时" : "任务已恢复");
        });
    }

    private void PauseResume_Click(object sender, RoutedEventArgs e)
    {
        if (_shutdown.IsPaused)
            _shutdown.Resume();
        else
            _shutdown.PauseFor(TimeSpan.FromHours(1));
    }

    private void UpdatePauseUI()
    {
        var paused = _shutdown.IsPaused;
        PauseResumeButton.Content = paused ? "恢复任务" : "暂停 1 小时";
        StatusTitle.Text = paused ? "任务已暂停" : "任务计划运行中";
        RemainingLabel.Text = paused ? "恢复后剩余时间" : "距离执行还有";
        SetStatusBadge(paused ? "PAUSED" : "RUNNING", paused ? "StatusPausedBrush" : "StatusRunningBrush");
    }

    // === Network Idle ===

    private void StartNetworkIdle_Click(object sender, RoutedEventArgs e)
    {
        _settings.NetworkDownloadThresholdKb = Math.Clamp(ParseInt(NetworkDownloadThresholdInput.Text), 0, 102400);
        _settings.NetworkUploadThresholdKb = Math.Clamp(ParseInt(NetworkUploadThresholdInput.Text), 0, 102400);
        _settings.NetworkIdleMinutes = Math.Clamp(ParseInt(NetworkIdleMinutesInput.Text), 1, 1440);
        NetworkDownloadThresholdInput.Text = _settings.NetworkDownloadThresholdKb.ToString();
        NetworkUploadThresholdInput.Text = _settings.NetworkUploadThresholdKb.ToString();
        NetworkIdleMinutesInput.Text = _settings.NetworkIdleMinutes.ToString();
        _settingsService.Save(_settings);

        _networkIdle.Start(_settings.NetworkDownloadThresholdKb, _settings.NetworkUploadThresholdKb, _settings.NetworkIdleMinutes);
        StartNetworkIdleButton.IsEnabled = false;
        StopNetworkIdleButton.IsEnabled = true;
        NetworkIdleProgressLabel.Text = "闲置进度：监控中...";
    }

    private void StopNetworkIdle_Click(object sender, RoutedEventArgs e)
    {
        StopNetworkIdleMonitoring("当前速度：已停止监控", "闲置进度：0/0 秒");
    }

    private void OnNetworkIdleTick(double downloadKb, double uploadKb, int idleSeconds, int requiredSeconds)
    {
        Dispatcher.Invoke(() =>
        {
            NetworkSpeedLabel.Text = $"当前速度：下载 {downloadKb:F1} KB/s · 上传 {uploadKb:F1} KB/s";
            NetworkIdleProgressLabel.Text = $"闲置进度：{idleSeconds}/{requiredSeconds} 秒";
        });
    }

    private void OnNetworkIdleReached()
    {
        Dispatcher.Invoke(() =>
        {
            StopNetworkIdleMonitoring("当前速度：已达到闲置条件", "闲置进度：已触发");
            _shutdown.SetRepeatRule(RepeatRule.Once);
            _shutdown.ResetReminderFlag();
            _shutdown.ScheduleCountdown(TimeSpan.FromSeconds(_settings.ReminderSeconds));
            UpdateStatusUI();
        });
    }

    private void StopNetworkIdleMonitoring(string speedText, string progressText)
    {
        _networkIdle.Stop();
        StartNetworkIdleButton.IsEnabled = true;
        StopNetworkIdleButton.IsEnabled = false;
        NetworkSpeedLabel.Text = speedText;
        NetworkIdleProgressLabel.Text = progressText;
    }

    // === Process Exit Trigger ===

    private void RefreshProcessList_Click(object sender, RoutedEventArgs e)
    {
        RefreshProcessList();
    }

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
        ProcessAutoCloseToggle.IsEnabled = false;
        ProcessAutoCloseSettingsPanel.IsEnabled = false;
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

    private void StopProcessTrigger_Click(object sender, RoutedEventArgs e)
    {
        StopProcessMonitoring("进程状态：已停止监控");
    }

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

    private void StopProcessMonitoring(string statusText)
    {
        _processExit.Stop();
        _timedProcessClose.Stop();
        StartProcessTriggerButton.IsEnabled = true;
        StopProcessTriggerButton.IsEnabled = false;
        RefreshProcessListButton.IsEnabled = true;
        ProcessListCombo.IsEnabled = true;
        ProcessAutoCloseToggle.IsEnabled = true;
        ProcessAutoCloseSettingsPanel.IsEnabled = true;
        _processMonitorStatus = statusText;
        _processAutoCloseStatus = _settings.ProcessTriggerAutoCloseEnabled ? "自动关闭：已停止" : "自动关闭：未启用";
        UpdateProcessAutoCloseUI();
        UpdateProcessTriggerLabels();
    }

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
            ? $"{(int)duration.TotalHours:D2}:{duration.Minutes:D2}:{duration.Seconds:D2}"
            : duration.ToString(@"mm\:ss");
    }

    private sealed record ProcessListItem(string Name, int Count)
    {
        public string Display => $"{Name} ({Count})";
    }

    // === Pre-Action Script ===

    private void BrowsePreActionScript_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new Microsoft.Win32.OpenFileDialog
        {
            Filter = "脚本文件 (*.bat;*.cmd;*.ps1)|*.bat;*.cmd;*.ps1|所有文件 (*.*)|*.*"
        };

        if (dialog.ShowDialog(this) != true)
            return;

        _settings.PreActionScriptPath = dialog.FileName;
        PreActionScriptPathInput.Text = dialog.FileName;
        _settingsService.Save(_settings);
        UpdatePreActionScriptUI();
    }

    private void TogglePreActionScript_Click(object sender, RoutedEventArgs e)
    {
        _settings.PreActionScriptPath = PreActionScriptPathInput.Text.Trim();
        _settings.PreActionScriptEnabled = !_settings.PreActionScriptEnabled;
        SavePreActionScriptTimeout();
        _settingsService.Save(_settings);
        UpdatePreActionScriptUI();
    }

    private void PreActionScriptTimeoutInput_LostFocus(object sender, RoutedEventArgs e)
    {
        SavePreActionScriptTimeout();
        _settings.PreActionScriptPath = PreActionScriptPathInput.Text.Trim();
        _settingsService.Save(_settings);
        UpdatePreActionScriptUI();
    }

    private void SavePreActionScriptTimeout()
    {
        _settings.PreActionScriptTimeoutSeconds = Math.Clamp(ParseInt(PreActionScriptTimeoutInput.Text), 1, 3600);
        PreActionScriptTimeoutInput.Text = _settings.PreActionScriptTimeoutSeconds.ToString();
    }

    private void UpdatePreActionScriptUI()
    {
        PreActionScriptToggleButton.Content = _settings.PreActionScriptEnabled ? "关闭脚本" : "启用脚本";
        PreActionScriptToggleButton.Background = _settings.PreActionScriptEnabled ? FindResource("HeroBrush") as Brush : FindResource("BgInputBrush") as Brush;
        PreActionScriptStatusLabel.Text = _settings.PreActionScriptEnabled
            ? $"脚本状态：已启用 · 超时 {_settings.PreActionScriptTimeoutSeconds} 秒"
            : "脚本状态：未启用";
        UpdateOverviewSummaries();
    }

    private async Task<bool> RunPreActionScriptAsync()
    {
        var enabled = _settings.PreActionScriptEnabled;
        var path = _settings.PreActionScriptPath;
        var timeoutSeconds = _settings.PreActionScriptTimeoutSeconds;

        if (!enabled)
            return true;

        Dispatcher.Invoke(() => PreActionScriptStatusLabel.Text = "脚本状态：执行中...");
        var result = await _preActionScript.RunAsync(path, timeoutSeconds);
        Dispatcher.Invoke(() =>
        {
            PreActionScriptStatusLabel.Text = $"脚本状态：{result.Message}";
            if (!result.Success)
                _tray.ShowBalloon("智能定时关机", $"执行前脚本失败，已取消动作：{result.Message}");
        });
        return result.Success;
    }

    // === Settings ===

    private void ReminderMinus_Click(object sender, RoutedEventArgs e)
    {
        int val = ParseInt(ReminderSecondsInput.Text);
        val = Math.Max(10, val - 10);
        ReminderSecondsInput.Text = val.ToString();
        SaveReminderSetting();
    }

    private void ReminderPlus_Click(object sender, RoutedEventArgs e)
    {
        int val = ParseInt(ReminderSecondsInput.Text);
        val = Math.Min(300, val + 10);
        ReminderSecondsInput.Text = val.ToString();
        SaveReminderSetting();
    }

    private void SaveReminderSetting()
    {
        int val = ParseInt(ReminderSecondsInput.Text);
        _settings.ReminderSeconds = Math.Clamp(val, 10, 300);
        ReminderSecondsInput.Text = _settings.ReminderSeconds.ToString();
        _shutdown.SetReminderSeconds(_settings.ReminderSeconds);
        _settingsService.Save(_settings);
        UpdateOverviewSummaries();
    }

    private void ReminderSecondsInput_LostFocus(object sender, RoutedEventArgs e)
    {
        SaveReminderSetting();
    }

    private void ApplyToggleVisual(Border toggle, Border knob, bool isOn, bool useDanger = false)
    {
        toggle.Background = isOn
            ? (useDanger ? FindResource("DangerBrush") as Brush : FindResource("HeroBrush") as Brush)
            : FindResource("ToggleOffBrush") as Brush;
        toggle.Effect = isOn
            ? (useDanger ? FindResource("DangerShadow") as System.Windows.Media.Effects.Effect : FindResource("CyanShadow") as System.Windows.Media.Effects.Effect)
            : null;
        knob.HorizontalAlignment = isOn ? System.Windows.HorizontalAlignment.Right : System.Windows.HorizontalAlignment.Left;
        knob.Background = isOn ? Brushes.White : FindResource("ToggleKnobOffBrush") as Brush;
    }

    private void ProcessAutoCloseToggle_Click(object sender, MouseButtonEventArgs e)
    {
        if (!ProcessAutoCloseToggle.IsEnabled)
            return;

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
        ApplyToggleVisual(ProcessAutoCloseToggle, ProcessAutoCloseKnob, _settings.ProcessTriggerAutoCloseEnabled);
        ProcessAutoCloseSettingsPanel.Opacity = _settings.ProcessTriggerAutoCloseEnabled ? 1 : 0.45;
        PulseElement(ProcessAutoCloseToggle, 1.03);
    }

    private void ForceCloseToggle_Click(object sender, MouseButtonEventArgs e)
    {
        if (!_shutdown.SupportsForceCloseApps)
            return;

        _settings.ForceCloseApps = !_settings.ForceCloseApps;
        _shutdown.SetForceCloseApps(_settings.ForceCloseApps);
        _settingsService.Save(_settings);
        UpdateForceCloseUI();
        if (_shutdown.IsScheduled)
            UpdateStatusUI();
    }

    private void PowerAction_Click(object sender, MouseButtonEventArgs e)
    {
        if (sender is not Border border || border.Tag is not string tag || !Enum.TryParse(tag, out PowerAction action))
            return;

        _settings.SelectedPowerAction = action;
        _shutdown.SetPowerAction(action);
        _settingsService.Save(_settings);
        UpdatePowerActionUI();
        UpdateForceCloseUI();
        if (_shutdown.IsScheduled)
            UpdateStatusUI();
    }

    private void RepeatRule_Click(object sender, MouseButtonEventArgs e)
    {
        if (sender is not Border border || border.Tag is not string tag || !Enum.TryParse(tag, out RepeatRule repeatRule))
            return;

        _settings.DefaultRepeatRule = repeatRule;
        _shutdown.SetRepeatRule(repeatRule);
        _settingsService.Save(_settings);
        UpdateRepeatRuleUI();
        if (_shutdown.IsScheduled)
            UpdateStatusUI();
    }

    private void UpdateRepeatRuleUI()
    {
        foreach (var button in new[] { RepeatOnce, RepeatDaily, RepeatWorkdays, RepeatWeekends })
        {
            var isSelected = button.Tag?.ToString() == _settings.DefaultRepeatRule.ToString();
            button.Background = isSelected ? FindResource("ActionTileActiveBrush") as Brush : Brushes.Transparent;
            button.BorderBrush = isSelected ? FindResource("GlassBorderStrongBrush") as Brush : FindResource("GlassBorderBrush") as Brush;
            button.Effect = isSelected ? FindResource("CyanShadow") as System.Windows.Media.Effects.Effect : null;
        }
    }

    private void UpdatePowerActionUI()
    {
        var actionButtons = new[]
        {
            ActionShutdown,
            ActionSleep,
            ActionHibernate,
            ActionRestart,
            ActionLogOut,
            ActionLock
        };

        foreach (var button in actionButtons)
        {
            var isSelected = button.Tag?.ToString() == _settings.SelectedPowerAction.ToString();
            button.Background = isSelected ? FindResource("ActionTileActiveBrush") as Brush : FindResource("ActionTileBrush") as Brush;
            button.BorderBrush = isSelected ? FindResource("GlassBorderStrongBrush") as Brush : FindResource("GlassBorderBrush") as Brush;
            button.Effect = isSelected ? FindResource("HeroGlowShadow") as System.Windows.Media.Effects.Effect : null;
        }

        var label = GetActionLabel(_settings.SelectedPowerAction);
        var verb = GetActionVerb(_settings.SelectedPowerAction);
        CountdownPanelTitle.Text = $"倒计时{label}";
        CountdownPanelSubtitle.Text = $"输入时长后开始计时，到点后{verb}，执行前会按设置弹窗提醒。";
        FixedTimePanelTitle.Text = $"指定时间{label}";
        FixedTimePanelSubtitle.Text = $"选择今天或明天的具体时间，到点后{verb}。";
        ReminderSettingSubtitle.Text = $"{label}前弹窗提醒，可在 10-300 秒之间设置。";
        UpdateReadyOverview();
    }

    private void UpdateForceCloseUI()
    {
        ForceCloseRow.Opacity = _shutdown.SupportsForceCloseApps ? 1 : 0.38;
        ForceCloseToggle.IsEnabled = _shutdown.SupportsForceCloseApps;
        ForceCloseHint.Text = _shutdown.SupportsForceCloseApps
            ? $"开启后{GetActionLabel(_settings.SelectedPowerAction)}会关闭所有应用，未保存内容可能丢失。"
            : $"{GetActionLabel(_settings.SelectedPowerAction)}不使用强制关闭应用。";

        ApplyToggleVisual(ForceCloseToggle, ForceCloseKnob, _settings.ForceCloseApps && _shutdown.SupportsForceCloseApps, useDanger: true);
        PulseElement(ForceCloseToggle, 1.03);
        UpdateOverviewSummaries();
    }

    private void AutoStartToggle_Click(object sender, MouseButtonEventArgs e)
    {
        _settings.AutoStartEnabled = !_settings.AutoStartEnabled;
        var autoStart = new AutoStartService();
        if (_settings.AutoStartEnabled)
            autoStart.Enable();
        else
            autoStart.Disable();
        _settingsService.Save(_settings);
        UpdateAutoStartUI();
    }

    private void UpdateAutoStartUI()
    {
        ApplyToggleVisual(AutoStartToggle, AutoStartKnob, _settings.AutoStartEnabled);
        PulseElement(AutoStartToggle, 1.03);
        UpdateOverviewSummaries();
    }

    private void NavItem_Click(object sender, MouseButtonEventArgs e)
    {
        if (sender is not Border border || border.Tag is not string tag || !Enum.TryParse(tag, out UiSection section))
            return;

        ShowSection(section);
    }

    private void ShowSection(UiSection section)
    {
        _currentSection = section;

        OverviewSection.Visibility = section == UiSection.Overview ? Visibility.Visible : Visibility.Collapsed;
        TimerSection.Visibility = section == UiSection.Timer ? Visibility.Visible : Visibility.Collapsed;
        TasksSection.Visibility = section == UiSection.Tasks ? Visibility.Visible : Visibility.Collapsed;
        TriggersSection.Visibility = section == UiSection.Triggers ? Visibility.Visible : Visibility.Collapsed;
        ScriptSection.Visibility = section == UiSection.Script ? Visibility.Visible : Visibility.Collapsed;
        SettingsSection.Visibility = section == UiSection.Settings ? Visibility.Visible : Visibility.Collapsed;

        UpdateNavigationUI();
        AnimateActiveSection(section);
    }

    private void UpdateNavigationUI()
    {
        var navItems = new (Border Item, Border Indicator)[]
        {
            (NavOverview, NavOverviewIndicator),
            (NavTimer, NavTimerIndicator),
            (NavTasks, NavTasksIndicator),
            (NavTriggers, NavTriggersIndicator),
            (NavScript, NavScriptIndicator),
            (NavSettings, NavSettingsIndicator)
        };

        foreach (var (item, indicator) in navItems)
        {
            var isActive = item.Tag?.ToString() == _currentSection.ToString();
            item.Background = isActive ? FindResource("NavPillActiveBrush") as Brush : FindResource("NavPillBrush") as Brush;
            item.BorderBrush = isActive ? FindResource("GlassBorderStrongBrush") as Brush : FindResource("GlassBorderBrush") as Brush;
            item.Effect = isActive ? FindResource("CyanShadow") as System.Windows.Media.Effects.Effect : null;
            indicator.Background = isActive ? FindResource("NavPillIndicatorBrush") as Brush : FindResource("NavIndicatorBrush") as Brush;
            indicator.Opacity = isActive ? 1 : 0;
        }
    }

    private void AnimateActiveSection(UiSection section)
    {
        var active = section switch
        {
            UiSection.Overview => OverviewSection,
            UiSection.Timer => TimerSection,
            UiSection.Tasks => TasksSection,
            UiSection.Triggers => TriggersSection,
            UiSection.Script => ScriptSection,
            UiSection.Settings => SettingsSection,
            _ => OverviewSection
        };

        active.Opacity = 0;
        active.RenderTransform = new TranslateTransform(0, 12);
        active.BeginAnimation(OpacityProperty, new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(220))
        {
            EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut }
        });
        ((TranslateTransform)active.RenderTransform).BeginAnimation(TranslateTransform.YProperty, new DoubleAnimation(12, 0, TimeSpan.FromMilliseconds(240))
        {
            EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut }
        });
    }

    // === Window Controls ===

    private void StartEntranceAnimations()
    {
        HeroHeader.RenderTransform = new TranslateTransform(0, -18);
        ContentPanel.RenderTransform = new TranslateTransform(0, 24);

        HeroHeader.BeginAnimation(OpacityProperty, new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(420))
        {
            EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut }
        });
        ((TranslateTransform)HeroHeader.RenderTransform).BeginAnimation(TranslateTransform.YProperty, new DoubleAnimation(-18, 0, TimeSpan.FromMilliseconds(420))
        {
            EasingFunction = new BackEase { EasingMode = EasingMode.EaseOut, Amplitude = 0.25 }
        });

        ContentPanel.BeginAnimation(OpacityProperty, new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(520))
        {
            BeginTime = TimeSpan.FromMilliseconds(90),
            EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut }
        });
        ((TranslateTransform)ContentPanel.RenderTransform).BeginAnimation(TranslateTransform.YProperty, new DoubleAnimation(24, 0, TimeSpan.FromMilliseconds(520))
        {
            BeginTime = TimeSpan.FromMilliseconds(90),
            EasingFunction = new BackEase { EasingMode = EasingMode.EaseOut, Amplitude = 0.18 }
        });

        FloatGlow(GlowPurple, -96, -112, -70, -92, 4.8);
        FloatGlow(GlowCyan, -118, 92, -88, 122, 5.8);
        FloatGlow(GlowPink, -118, -88, -88, -116, 6.4);
    }

    private static void FloatGlow(FrameworkElement element, double fromX, double fromY, double toX, double toY, double seconds)
    {
        var transform = new TranslateTransform();
        element.RenderTransform = transform;

        var xAnimation = new DoubleAnimation(fromX, toX, TimeSpan.FromSeconds(seconds))
        {
            AutoReverse = true,
            RepeatBehavior = RepeatBehavior.Forever,
            EasingFunction = new SineEase { EasingMode = EasingMode.EaseInOut }
        };
        var yAnimation = new DoubleAnimation(fromY, toY, TimeSpan.FromSeconds(seconds + 0.6))
        {
            AutoReverse = true,
            RepeatBehavior = RepeatBehavior.Forever,
            EasingFunction = new SineEase { EasingMode = EasingMode.EaseInOut }
        };

        transform.BeginAnimation(TranslateTransform.XProperty, xAnimation);
        transform.BeginAnimation(TranslateTransform.YProperty, yAnimation);
    }

    private static void SwitchPanel(UIElement panelToShow, UIElement panelToHide)
    {
        panelToHide.Visibility = Visibility.Collapsed;
        panelToShow.Visibility = Visibility.Visible;
        panelToShow.Opacity = 0;
        panelToShow.RenderTransform = new TranslateTransform(0, 16);
        panelToShow.BeginAnimation(OpacityProperty, new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(240))
        {
            EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut }
        });
        ((TranslateTransform)panelToShow.RenderTransform).BeginAnimation(TranslateTransform.YProperty, new DoubleAnimation(16, 0, TimeSpan.FromMilliseconds(260))
        {
            EasingFunction = new BackEase { EasingMode = EasingMode.EaseOut, Amplitude = 0.16 }
        });
    }

    private static void PulseElement(UIElement element, double scale = 1.02)
    {
        element.RenderTransformOrigin = new Point(0.5, 0.5);
        var transform = element.RenderTransform as ScaleTransform;
        if (transform == null)
        {
            transform = new ScaleTransform(1, 1);
            element.RenderTransform = transform;
        }

        var animation = new DoubleAnimation(1, scale, TimeSpan.FromMilliseconds(130))
        {
            AutoReverse = true,
            EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut }
        };
        transform.BeginAnimation(ScaleTransform.ScaleXProperty, animation);
        transform.BeginAnimation(ScaleTransform.ScaleYProperty, animation.Clone());
    }

    private void Window_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
    {
        if (e.ButtonState == MouseButtonState.Pressed)
            DragMove();
    }

    private void Minimize_Click(object sender, RoutedEventArgs e)
    {
        Hide();
    }

    private void Close_Click(object sender, RoutedEventArgs e)
    {
        Hide();
    }

    // === Input Validation ===

    private void NumberPreviewTextInput(object sender, TextCompositionEventArgs e)
    {
        e.Handled = !Regex.IsMatch(e.Text, @"^\d+$");
    }

    private void NumberInput_GotKeyboardFocus(object sender, KeyboardFocusChangedEventArgs e)
    {
        if (sender is System.Windows.Controls.TextBox textBox)
            textBox.SelectAll();
    }

    private static int ParseInt(string? s)
    {
        return int.TryParse(s, out int v) ? v : 0;
    }

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

    private static string GetRepeatLabel(RepeatRule repeatRule) => repeatRule switch
    {
        RepeatRule.Once => "单次",
        RepeatRule.Daily => "每日",
        RepeatRule.Workdays => "工作日",
        RepeatRule.Weekends => "周末",
        _ => "单次"
    };

    public void UpdateStatusAfterDelay()
    {
        UpdateStatusUI();
    }

    protected override void OnClosing(CancelEventArgs e)
    {
        e.Cancel = true;
        Hide();
    }
}

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

public partial class MainWindow : Window
{
    private readonly ShutdownService _shutdown;
    private readonly SettingsService _settingsService;
    private readonly TrayIconService _tray;
    private readonly AppSettings _settings;
    private SavedTask? _activeTask;
    private ReminderWindow? _reminderWindow;

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

        LoadSettings();
        Loaded += (_, _) => StartEntranceAnimations();
    }

    private void LoadSettings()
    {
        ReminderSecondsInput.Text = _settings.ReminderSeconds.ToString();
        HoursInput.Text = _settings.DefaultCountdownHours.ToString();
        MinutesInput.Text = _settings.DefaultCountdownMinutes.ToString();
        SecondsInput.Text = _settings.DefaultCountdownSeconds.ToString();
        _shutdown.SetReminderSeconds(_settings.ReminderSeconds);
        _shutdown.SetForceCloseApps(_settings.ForceCloseApps);
        _shutdown.SetPowerAction(_settings.SelectedPowerAction);
        _shutdown.SetRepeatRule(_settings.DefaultRepeatRule);
        UpdatePowerActionUI();
        UpdateRepeatRuleUI();
        RefreshTaskList();
        UpdateAutoStartUI();
        UpdateForceCloseUI();
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
        PulseElement(CountdownPanel, 1.01);
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
                CornerRadius = new CornerRadius(16),
                Padding = new Thickness(14),
                Margin = new Thickness(0, 0, 0, 10),
                Background = new SolidColorBrush(Color.FromArgb(112, 17, 24, 43)),
                BorderBrush = task.Enabled ? FindResource("AccentBrush") as Brush : new SolidColorBrush(Color.FromRgb(51, 77, 191)),
                BorderThickness = new Thickness(1),
                Opacity = task.Enabled ? 1 : 0.55
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
                Text = $"下次：{GetNextTaskTime(task):yyyy-MM-dd HH:mm:ss}",
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

    private void UpdateStatusUI()
    {
        StatusCard.Visibility = Visibility.Visible;
        PulseElement(StatusCard);
        CountdownStartBtn.IsEnabled = false;
        FixedTimeStartBtn.IsEnabled = false;
        _tray.SetShutdownActive(true);
        UpdatePauseUI();
        var repeatText = _shutdown.RepeatRule == RepeatRule.Once ? "单次" : GetRepeatLabel(_shutdown.RepeatRule);
        TargetTimeLabel.Text = _shutdown.IsPaused
            ? $"已暂停：{GetActionVerb(_settings.SelectedPowerAction)} · {repeatText} · 将于 {_shutdown.PauseUntil:HH:mm} 自动恢复"
            : $"计划执行：{GetActionVerb(_settings.SelectedPowerAction)} · {repeatText} · {_shutdown.TargetTime:yyyy-MM-dd HH:mm:ss}";
        ShutdownModeLabel.Text = _shutdown.SupportsForceCloseApps && _settings.ForceCloseApps
            ? "执行方式：强制关闭应用（未保存内容可能丢失）"
            : "执行方式：正常执行";
    }

    private void OnTick(string remaining)
    {
        Dispatcher.Invoke(() =>
        {
            RemainingTime.Text = remaining;
            PulseElement(RemainingTime, 1.035);
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
            StatusCard.Visibility = Visibility.Collapsed;
            CountdownStartBtn.IsEnabled = true;
            FixedTimeStartBtn.IsEnabled = true;
            _tray.SetShutdownActive(false);
            _tray.SetPaused(false);
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
        PauseResumeButton.Content = _shutdown.IsPaused ? "恢复任务" : "暂停 1 小时";
        StatusTitle.Text = _shutdown.IsPaused ? "任务已暂停" : "任务计划运行中";
        RemainingLabel.Text = _shutdown.IsPaused ? "恢复后剩余时间" : "距离执行还有";
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
    }

    private void ReminderSecondsInput_LostFocus(object sender, RoutedEventArgs e)
    {
        SaveReminderSetting();
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
            button.Background = isSelected ? FindResource("HeroBrush") as Brush : Brushes.Transparent;
            button.BorderBrush = isSelected ? FindResource("AccentBrush") as Brush : new SolidColorBrush(Color.FromRgb(51, 77, 191));
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
            button.Background = isSelected ? FindResource("HeroBrush") as Brush : Brushes.Transparent;
            button.BorderBrush = isSelected ? FindResource("AccentBrush") as Brush : new SolidColorBrush(Color.FromRgb(51, 77, 191));
            button.Effect = isSelected ? FindResource("CyanShadow") as System.Windows.Media.Effects.Effect : null;
        }

        var label = GetActionLabel(_settings.SelectedPowerAction);
        var verb = GetActionVerb(_settings.SelectedPowerAction);
        CountdownPanelTitle.Text = $"倒计时{label}";
        CountdownPanelSubtitle.Text = $"输入时长后开始计时，到点后{verb}，执行前会按设置弹窗提醒。";
        FixedTimePanelTitle.Text = $"指定时间{label}";
        FixedTimePanelSubtitle.Text = $"选择今天或明天的具体时间，到点后{verb}。";
        ReminderSettingSubtitle.Text = $"{label}前弹窗提醒，可在 10-300 秒之间设置。";
    }

    private void UpdateForceCloseUI()
    {
        ForceCloseRow.Opacity = _shutdown.SupportsForceCloseApps ? 1 : 0.38;
        ForceCloseToggle.IsEnabled = _shutdown.SupportsForceCloseApps;
        ForceCloseHint.Text = _shutdown.SupportsForceCloseApps
            ? $"开启后{GetActionLabel(_settings.SelectedPowerAction)}会关闭所有应用，未保存内容可能丢失。"
            : $"{GetActionLabel(_settings.SelectedPowerAction)}不使用强制关闭应用。";

        if (_settings.ForceCloseApps && _shutdown.SupportsForceCloseApps)
        {
            ForceCloseToggle.Background = FindResource("DangerBrush") as Brush;
            ForceCloseToggle.Effect = FindResource("DangerShadow") as System.Windows.Media.Effects.Effect;
            ForceCloseKnob.HorizontalAlignment = System.Windows.HorizontalAlignment.Right;
            ForceCloseKnob.Background = Brushes.White;
        }
        else
        {
            ForceCloseToggle.Background = new SolidColorBrush(Color.FromRgb(28, 31, 54));
            ForceCloseToggle.Effect = null;
            ForceCloseKnob.HorizontalAlignment = System.Windows.HorizontalAlignment.Left;
            ForceCloseKnob.Background = FindResource("TextSecondaryBrush") as Brush;
        }
        PulseElement(ForceCloseToggle, 1.06);
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
        if (_settings.AutoStartEnabled)
        {
            AutoStartToggle.Background = FindResource("HeroBrush") as Brush;
            AutoStartToggle.Effect = FindResource("CyanShadow") as System.Windows.Media.Effects.Effect;
            AutoStartKnob.HorizontalAlignment = System.Windows.HorizontalAlignment.Right;
            AutoStartKnob.Background = Brushes.White;
        }
        else
        {
            AutoStartToggle.Background = new SolidColorBrush(Color.FromRgb(28, 31, 54));
            AutoStartToggle.Effect = null;
            AutoStartKnob.HorizontalAlignment = System.Windows.HorizontalAlignment.Left;
            AutoStartKnob.Background = FindResource("TextSecondaryBrush") as Brush;
        }
        PulseElement(AutoStartToggle, 1.06);
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

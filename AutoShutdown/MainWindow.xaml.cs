using System.ComponentModel;
using System.Text.RegularExpressions;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using AutoShutdown.Models;
using AutoShutdown.Services;

namespace AutoShutdown;

public partial class MainWindow : Window
{
    private readonly ShutdownService _shutdown;
    private readonly SettingsService _settingsService;
    private readonly TrayIconService _tray;
    private readonly AppSettings _settings;
    private TimerMode _currentMode = TimerMode.Countdown;
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

        LoadSettings();
    }

    private void LoadSettings()
    {
        ReminderSecondsInput.Text = _settings.ReminderSeconds.ToString();
        HoursInput.Text = _settings.DefaultCountdownHours.ToString();
        MinutesInput.Text = _settings.DefaultCountdownMinutes.ToString();
        SecondsInput.Text = _settings.DefaultCountdownSeconds.ToString();
        _shutdown.SetReminderSeconds(_settings.ReminderSeconds);
        UpdateAutoStartUI();
    }

    // === Mode Switching ===

    private void CountdownMode_Click(object sender, MouseButtonEventArgs e)
    {
        _currentMode = TimerMode.Countdown;
        BtnCountdown.Background = FindResource("PrimaryBrush") as Brush;
        ((TextBlock)((Border)BtnCountdown).Child).Foreground = Brushes.White;
        BtnFixed.Background = Brushes.Transparent;
        ((TextBlock)((Border)BtnFixed).Child).Foreground = FindResource("TextSecondaryBrush") as Brush;
        CountdownPanel.Visibility = Visibility.Visible;
        FixedTimePanel.Visibility = Visibility.Collapsed;
    }

    private void FixedMode_Click(object sender, MouseButtonEventArgs e)
    {
        _currentMode = TimerMode.FixedTime;
        BtnFixed.Background = FindResource("PrimaryBrush") as Brush;
        ((TextBlock)((Border)BtnFixed).Child).Foreground = Brushes.White;
        BtnCountdown.Background = Brushes.Transparent;
        ((TextBlock)((Border)BtnCountdown).Child).Foreground = FindResource("TextSecondaryBrush") as Brush;
        CountdownPanel.Visibility = Visibility.Collapsed;
        FixedTimePanel.Visibility = Visibility.Visible;
    }

    // === Countdown ===

    private void CountdownStart_Click(object sender, RoutedEventArgs e)
    {
        int h = ParseInt(HoursInput.Text);
        int m = ParseInt(MinutesInput.Text);
        int s = ParseInt(SecondsInput.Text);

        if (h == 0 && m == 0 && s == 0) return;

        var duration = new TimeSpan(h, m, s);
        _shutdown.ResetReminderFlag();
        _shutdown.ScheduleCountdown(duration);

        UpdateStatusUI();
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

        _shutdown.ResetReminderFlag();
        _shutdown.ScheduleFixedTime(target);

        UpdateStatusUI();
    }

    // === Cancel ===

    private void CancelShutdown_Click(object sender, RoutedEventArgs e)
    {
        _shutdown.Cancel();
        _reminderWindow?.Close();
    }

    // === Status Updates ===

    private void UpdateStatusUI()
    {
        StatusCard.Visibility = Visibility.Visible;
        CountdownStartBtn.IsEnabled = false;
        FixedTimeStartBtn.IsEnabled = false;
        _tray.SetShutdownActive(true);
        TargetTimeLabel.Text = $"计划关机时间: {_shutdown.TargetTime:yyyy-MM-dd HH:mm:ss}";
    }

    private void OnTick(string remaining)
    {
        Dispatcher.Invoke(() => RemainingTime.Text = remaining);
    }

    private void OnReminderReached()
    {
        Dispatcher.Invoke(() =>
        {
            _reminderWindow = new ReminderWindow(_settings.ReminderSeconds, _shutdown, this);
            _reminderWindow.ShowDialog();
        });
    }

    private void OnShutdownTriggered()
    {
        Dispatcher.Invoke(() =>
        {
            _tray.ShowBalloon("智能定时关机", "电脑即将关机...");
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
            _tray.ShowBalloon("智能定时关机", "已取消定时关机");
        });
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
        _shutdown.SetReminderSeconds(_settings.ReminderSeconds);
        _settingsService.Save(_settings);
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
            AutoStartToggle.Background = FindResource("PrimaryBrush") as Brush;
            AutoStartKnob.HorizontalAlignment = System.Windows.HorizontalAlignment.Right;
            AutoStartKnob.Background = Brushes.White;
        }
        else
        {
            AutoStartToggle.Background = new SolidColorBrush(Color.FromRgb(80, 80, 100));
            AutoStartKnob.HorizontalAlignment = System.Windows.HorizontalAlignment.Left;
            AutoStartKnob.Background = new SolidColorBrush(Color.FromRgb(180, 180, 200));
        }
    }

    // === Window Controls ===

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

    private static int ParseInt(string? s)
    {
        return int.TryParse(s, out int v) ? v : 0;
    }

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

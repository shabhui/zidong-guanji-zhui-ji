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
        PulseElement(StatusCard);
        CountdownStartBtn.IsEnabled = false;
        FixedTimeStartBtn.IsEnabled = false;
        _tray.SetShutdownActive(true);
        TargetTimeLabel.Text = $"计划关机时间：{_shutdown.TargetTime:yyyy-MM-dd HH:mm:ss}";
        ShutdownModeLabel.Text = _settings.ForceCloseApps
            ? "关机方式：强制关闭所有应用（未保存内容可能丢失）"
            : "关机方式：正常关机（应用可提示保存或阻止关机）";
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
        _settings.ForceCloseApps = !_settings.ForceCloseApps;
        _shutdown.SetForceCloseApps(_settings.ForceCloseApps);
        _settingsService.Save(_settings);
        UpdateForceCloseUI();
        if (_shutdown.IsScheduled)
            UpdateStatusUI();
    }

    private void UpdateForceCloseUI()
    {
        if (_settings.ForceCloseApps)
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

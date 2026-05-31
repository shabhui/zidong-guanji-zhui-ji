using System.Windows;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Windows.Threading;
using AutoShutdown.Services;

namespace AutoShutdown;

public partial class ReminderWindow : Window
{
    private readonly ShutdownService _shutdown;
    private readonly MainWindow _mainWindow;
    private readonly DispatcherTimer _timer;
    private int _remainingSeconds;

    public ReminderWindow(int seconds, ShutdownService shutdown, MainWindow mainWindow)
    {
        InitializeComponent();
        _shutdown = shutdown;
        _mainWindow = mainWindow;
        _remainingSeconds = seconds;

        UpdateDisplay();
        Loaded += (_, _) => StartEntranceAnimation();

        _timer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(1) };
        _timer.Tick += (_, _) =>
        {
            _remainingSeconds--;
            if (_remainingSeconds <= 0)
            {
                _timer.Stop();
                _shutdown.ExecuteShutdown();
                Close();
                return;
            }
            UpdateDisplay();
        };
        _timer.Start();
    }

    private void UpdateDisplay()
    {
        CountdownLabel.Text = $"{_remainingSeconds}s";
        MessageLabel.Text = $"电脑将在 {_remainingSeconds} 秒后自动关机";
        PulseElement(CountdownLabel, 1.08);
    }

    private void StartEntranceAnimation()
    {
        ReminderCard.Opacity = 0;
        ReminderCard.RenderTransformOrigin = new Point(0.5, 0.5);
        ReminderCard.RenderTransform = new ScaleTransform(0.88, 0.88);

        ReminderCard.BeginAnimation(OpacityProperty, new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(260))
        {
            EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut }
        });
        ((ScaleTransform)ReminderCard.RenderTransform).BeginAnimation(ScaleTransform.ScaleXProperty, new DoubleAnimation(0.88, 1, TimeSpan.FromMilliseconds(320))
        {
            EasingFunction = new BackEase { EasingMode = EasingMode.EaseOut, Amplitude = 0.32 }
        });
        ((ScaleTransform)ReminderCard.RenderTransform).BeginAnimation(ScaleTransform.ScaleYProperty, new DoubleAnimation(0.88, 1, TimeSpan.FromMilliseconds(320))
        {
            EasingFunction = new BackEase { EasingMode = EasingMode.EaseOut, Amplitude = 0.32 }
        });

        var glowTransform = new ScaleTransform(1, 1);
        AlertGlow.RenderTransformOrigin = new Point(0.5, 0.5);
        AlertGlow.RenderTransform = glowTransform;
        var pulse = new DoubleAnimation(0.92, 1.12, TimeSpan.FromSeconds(1.2))
        {
            AutoReverse = true,
            RepeatBehavior = RepeatBehavior.Forever,
            EasingFunction = new SineEase { EasingMode = EasingMode.EaseInOut }
        };
        glowTransform.BeginAnimation(ScaleTransform.ScaleXProperty, pulse);
        glowTransform.BeginAnimation(ScaleTransform.ScaleYProperty, pulse.Clone());
    }

    private static void PulseElement(UIElement element, double scale)
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

    private void Cancel_Click(object sender, RoutedEventArgs e)
    {
        _timer.Stop();
        _shutdown.Cancel();
        Close();
    }

    private void Delay_Click(object sender, RoutedEventArgs e)
    {
        _timer.Stop();
        _shutdown.ResetReminderFlag();
        _shutdown.ScheduleCountdown(TimeSpan.FromMinutes(5));
        _mainWindow.UpdateStatusAfterDelay();
        Close();
    }

    private void ShutdownNow_Click(object sender, RoutedEventArgs e)
    {
        _timer.Stop();
        _shutdown.ExecuteShutdown();
        Close();
    }

    private void Window_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
    {
        if (e.ButtonState == MouseButtonState.Pressed)
            DragMove();
    }
}

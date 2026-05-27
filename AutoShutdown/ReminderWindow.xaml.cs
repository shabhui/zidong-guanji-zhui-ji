using System.Windows;
using System.Windows.Input;
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
        CountdownLabel.Text = _remainingSeconds.ToString();
        MessageLabel.Text = $"电脑将在 {_remainingSeconds} 秒后自动关机";
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
        // Add 5 more minutes to the shutdown schedule
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

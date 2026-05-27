using AutoShutdown.Services;

namespace AutoShutdown;

public partial class App : System.Windows.Application
{
    private TrayIconService? _tray;
    private MainWindow? _mainWindow;
    private readonly ShutdownService _shutdown = new();
    private readonly SettingsService _settingsService = new();

    private void Application_Startup(object sender, System.Windows.StartupEventArgs e)
    {
        var args = e.Args;
        bool startMinimized = args.Contains("--minimized") || args.Contains("-m");

        _tray = new TrayIconService();
        _tray.ShowWindow += ShowMainWindow;
        _tray.CancelShutdown += CancelShutdown;
        _tray.ExitApp += ExitApplication;

        _settingsService.Load();

        _mainWindow = new MainWindow(_shutdown, _settingsService, _tray);
        _mainWindow.Closed += (_, _) => ExitApplication();

        if (!startMinimized)
            _mainWindow.Show();
    }

    private void ShowMainWindow()
    {
        _mainWindow?.Dispatcher.Invoke(() =>
        {
            if (_mainWindow == null) return;
            _mainWindow.Show();
            _mainWindow.WindowState = System.Windows.WindowState.Normal;
            _mainWindow.Activate();
        });
    }

    private void CancelShutdown()
    {
        _shutdown.Cancel();
    }

    private void ExitApplication()
    {
        _shutdown.Cancel();
        _tray?.Dispose();
        Current.Shutdown();
    }

    protected override void OnExit(System.Windows.ExitEventArgs e)
    {
        _tray?.Dispose();
        base.OnExit(e);
    }
}

using System.Diagnostics;
using System.Timers;

namespace AutoShutdown.Services;

public sealed class ProcessExitService : IDisposable
{
    private readonly System.Timers.Timer _timer = new(1000);
    private string _processName = string.Empty;
    private bool _running;
    private bool _hasSeenProcess;

    public event Action<string, int, bool>? Tick;
    public event Action<string>? ProcessExited;

    public ProcessExitService()
    {
        _timer.AutoReset = true;
        _timer.Elapsed += OnTimerElapsed;
    }

    public void Start(string processName)
    {
        _processName = NormalizeProcessName(processName);
        if (string.IsNullOrWhiteSpace(_processName))
            return;

        _hasSeenProcess = false;
        _running = true;
        _timer.Start();
        OnTimerElapsed(this, null!);
    }

    public void Stop()
    {
        _running = false;
        _timer.Stop();
        _hasSeenProcess = false;
    }

    private void OnTimerElapsed(object? sender, ElapsedEventArgs e)
    {
        if (!_running || string.IsNullOrWhiteSpace(_processName))
            return;

        var count = Process.GetProcessesByName(_processName).Length;
        if (count > 0)
            _hasSeenProcess = true;

        Tick?.Invoke(_processName, count, _hasSeenProcess);

        if (_hasSeenProcess && count == 0)
        {
            var name = _processName;
            Stop();
            ProcessExited?.Invoke(name);
        }
    }

    public static string NormalizeProcessName(string processName)
    {
        var name = processName.Trim();
        if (name.EndsWith(".exe", StringComparison.OrdinalIgnoreCase))
            name = name[..^4];
        return name;
    }

    public void Dispose()
    {
        _timer.Dispose();
    }
}

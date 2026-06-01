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

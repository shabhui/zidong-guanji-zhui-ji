using System.Diagnostics;
using System.Timers;

namespace AutoShutdown.Services;

public class ShutdownService
{
    private System.Timers.Timer? _countdownTimer;
    private DateTime _targetTime;
    private bool _isScheduled;
    private bool _forceCloseApps;
    private readonly object _lock = new();

    public event Action<string>? Tick;
    public event Action? ReminderTimeReached;
    public event Action? ShutdownTriggered;
    public event Action? Cancelled;

    public bool IsScheduled => _isScheduled;
    public DateTime TargetTime => _targetTime;

    public void ScheduleCountdown(TimeSpan duration)
    {
        Cancel();
        lock (_lock)
        {
            _targetTime = DateTime.Now + duration;
            _isScheduled = true;
        }
        StartTimer();
    }

    public void ScheduleFixedTime(DateTime time)
    {
        Cancel();
        lock (_lock)
        {
            _targetTime = time;
            if (_targetTime <= DateTime.Now)
                _targetTime = _targetTime.AddDays(1);
            _isScheduled = true;
        }
        StartTimer();
    }

    public TimeSpan GetRemaining()
    {
        lock (_lock)
        {
            var remaining = _targetTime - DateTime.Now;
            return remaining > TimeSpan.Zero ? remaining : TimeSpan.Zero;
        }
    }

    public void Cancel()
    {
        lock (_lock)
        {
            _isScheduled = false;
        }
        _countdownTimer?.Stop();
        _countdownTimer?.Dispose();
        _countdownTimer = null;
        Cancelled?.Invoke();
    }

    public void SetForceCloseApps(bool enabled) => _forceCloseApps = enabled;

    public void ExecuteShutdown()
    {
        lock (_lock)
        {
            _isScheduled = false;
        }
        _countdownTimer?.Stop();
        _countdownTimer?.Dispose();
        _countdownTimer = null;
        ShutdownTriggered?.Invoke();
        var arguments = _forceCloseApps ? "/s /f /t 0" : "/s /t 0";
        Process.Start("shutdown", arguments);
    }

    private void StartTimer()
    {
        _countdownTimer?.Dispose();
        _countdownTimer = new System.Timers.Timer(1000);
        _countdownTimer.Elapsed += OnTimerElapsed;
        _countdownTimer.AutoReset = true;
        _countdownTimer.Start();
    }

    private bool _reminderFired;
    private int _reminderSeconds = 60;

    public void SetReminderSeconds(int seconds) => _reminderSeconds = seconds;

    private void OnTimerElapsed(object? sender, ElapsedEventArgs e)
    {
        var remaining = GetRemaining();

        if (remaining <= TimeSpan.Zero)
        {
            ExecuteShutdown();
            return;
        }

        Tick?.Invoke(remaining.ToString(@"hh\:mm\:ss"));

        if (!_reminderFired && remaining.TotalSeconds <= _reminderSeconds)
        {
            _reminderFired = true;
            ReminderTimeReached?.Invoke();
        }
    }

    public void ResetReminderFlag()
    {
        _reminderFired = false;
    }
}

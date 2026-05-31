using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Timers;
using AutoShutdown.Models;

namespace AutoShutdown.Services;

public class ShutdownService
{
    private System.Timers.Timer? _countdownTimer;
    private System.Timers.Timer? _pauseTimer;
    private DateTime _targetTime;
    private DateTime _pauseUntil;
    private TimeSpan _pausedRemaining;
    private bool _isScheduled;
    private bool _isPaused;
    private bool _forceCloseApps;
    private bool _reminderFired;
    private int _reminderSeconds = 60;
    private PowerAction _powerAction = PowerAction.Shutdown;
    private readonly object _lock = new();

    public event Action<string>? Tick;
    public event Action? ReminderTimeReached;
    public event Action? ShutdownTriggered;
    public event Action? Cancelled;
    public event Action? PauseStateChanged;

    public bool IsScheduled => _isScheduled;
    public bool IsPaused => _isPaused;
    public DateTime TargetTime => _targetTime;
    public DateTime PauseUntil => _pauseUntil;
    public TimeSpan PausedRemaining => _pausedRemaining;
    public PowerAction PowerAction => _powerAction;
    public bool SupportsForceCloseApps => _powerAction is PowerAction.Shutdown or PowerAction.Restart or PowerAction.LogOut;

    public void ScheduleCountdown(TimeSpan duration)
    {
        Cancel();
        lock (_lock)
        {
            _targetTime = DateTime.Now + duration;
            _isScheduled = true;
            _isPaused = false;
            _pausedRemaining = TimeSpan.Zero;
            _pauseUntil = DateTime.MinValue;
            _reminderFired = false;
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
            _isPaused = false;
            _pausedRemaining = TimeSpan.Zero;
            _pauseUntil = DateTime.MinValue;
            _reminderFired = false;
        }
        StartTimer();
    }

    public TimeSpan GetRemaining()
    {
        lock (_lock)
        {
            if (_isPaused)
                return _pausedRemaining;

            var remaining = _targetTime - DateTime.Now;
            return remaining > TimeSpan.Zero ? remaining : TimeSpan.Zero;
        }
    }

    public void PauseFor(TimeSpan duration)
    {
        TimeSpan remaining;
        lock (_lock)
        {
            if (!_isScheduled || _isPaused)
                return;

            remaining = _targetTime - DateTime.Now;
            if (remaining <= TimeSpan.Zero)
                return;

            _pausedRemaining = remaining;
            _pauseUntil = DateTime.Now + duration;
            _isPaused = true;
        }

        StopCountdownTimer();
        StartPauseTimer(duration);
        PauseStateChanged?.Invoke();
    }

    public void Resume()
    {
        lock (_lock)
        {
            if (!_isScheduled || !_isPaused)
                return;

            _targetTime = DateTime.Now + _pausedRemaining;
            _isPaused = false;
            _pauseUntil = DateTime.MinValue;
            _pausedRemaining = TimeSpan.Zero;
            _reminderFired = false;
        }

        StopPauseTimer();
        StartTimer();
        PauseStateChanged?.Invoke();
    }

    public void Cancel()
    {
        lock (_lock)
        {
            _isScheduled = false;
            _isPaused = false;
            _pausedRemaining = TimeSpan.Zero;
            _pauseUntil = DateTime.MinValue;
        }
        StopCountdownTimer();
        StopPauseTimer();
        Cancelled?.Invoke();
    }

    public void SetForceCloseApps(bool enabled) => _forceCloseApps = enabled;

    public void SetPowerAction(PowerAction action) => _powerAction = action;

    public void ExecuteShutdown()
    {
        lock (_lock)
        {
            _isScheduled = false;
            _isPaused = false;
            _pausedRemaining = TimeSpan.Zero;
            _pauseUntil = DateTime.MinValue;
        }
        StopCountdownTimer();
        StopPauseTimer();
        ShutdownTriggered?.Invoke();
        ExecutePowerAction();
    }

    private void ExecutePowerAction()
    {
        switch (_powerAction)
        {
            case PowerAction.Shutdown:
                Process.Start("shutdown", _forceCloseApps ? "/s /f /t 0" : "/s /t 0");
                break;
            case PowerAction.Restart:
                Process.Start("shutdown", _forceCloseApps ? "/r /f /t 0" : "/r /t 0");
                break;
            case PowerAction.LogOut:
                Process.Start("shutdown", _forceCloseApps ? "/l /f" : "/l");
                break;
            case PowerAction.Sleep:
                SetSuspendState(false, false, false);
                break;
            case PowerAction.Hibernate:
                SetSuspendState(true, false, false);
                break;
            case PowerAction.Lock:
                LockWorkStation();
                break;
        }
    }

    [DllImport("powrprof.dll", SetLastError = true)]
    private static extern bool SetSuspendState(bool hibernate, bool forceCritical, bool disableWakeEvent);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool LockWorkStation();

    private void StartTimer()
    {
        StopCountdownTimer();
        _countdownTimer = new System.Timers.Timer(1000);
        _countdownTimer.Elapsed += OnTimerElapsed;
        _countdownTimer.AutoReset = true;
        _countdownTimer.Start();
    }

    private void StartPauseTimer(TimeSpan duration)
    {
        StopPauseTimer();
        _pauseTimer = new System.Timers.Timer(duration.TotalMilliseconds);
        _pauseTimer.Elapsed += (_, _) => Resume();
        _pauseTimer.AutoReset = false;
        _pauseTimer.Start();
    }

    private void StopCountdownTimer()
    {
        _countdownTimer?.Stop();
        _countdownTimer?.Dispose();
        _countdownTimer = null;
    }

    private void StopPauseTimer()
    {
        _pauseTimer?.Stop();
        _pauseTimer?.Dispose();
        _pauseTimer = null;
    }

    public void SetReminderSeconds(int seconds) => _reminderSeconds = seconds;

    private void OnTimerElapsed(object? sender, ElapsedEventArgs e)
    {
        bool isPaused;
        lock (_lock)
        {
            isPaused = _isPaused;
        }

        if (isPaused)
            return;

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

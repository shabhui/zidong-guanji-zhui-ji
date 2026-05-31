namespace AutoShutdown.Models;

public class AppSettings
{
    public int ReminderSeconds { get; set; } = 60;
    public int DefaultCountdownHours { get; set; } = 0;
    public int DefaultCountdownMinutes { get; set; } = 30;
    public int DefaultCountdownSeconds { get; set; } = 0;
    public bool AutoStartEnabled { get; set; } = false;
    public bool ForceCloseApps { get; set; } = false;
    public PowerAction SelectedPowerAction { get; set; } = PowerAction.Shutdown;
}

public enum TimerMode
{
    Countdown,
    FixedTime
}

public enum PowerAction
{
    Shutdown,
    Sleep,
    Hibernate,
    Restart,
    LogOut,
    Lock
}

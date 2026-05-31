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
    public RepeatRule DefaultRepeatRule { get; set; } = RepeatRule.Once;
    public int NetworkDownloadThresholdKb { get; set; } = 100;
    public int NetworkUploadThresholdKb { get; set; } = 50;
    public int NetworkIdleMinutes { get; set; } = 5;
    public bool PreActionScriptEnabled { get; set; } = false;
    public string PreActionScriptPath { get; set; } = string.Empty;
    public int PreActionScriptTimeoutSeconds { get; set; } = 60;
    public List<SavedTask> SavedTasks { get; set; } = new();
}

public class SavedTask
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N");
    public string Name { get; set; } = "新任务";
    public bool Enabled { get; set; } = true;
    public TimerMode Mode { get; set; } = TimerMode.FixedTime;
    public PowerAction Action { get; set; } = PowerAction.Shutdown;
    public RepeatRule RepeatRule { get; set; } = RepeatRule.Once;
    public int Hours { get; set; }
    public int Minutes { get; set; }
    public int Seconds { get; set; }
    public bool ForceCloseApps { get; set; }
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

public enum RepeatRule
{
    Once,
    Daily,
    Workdays,
    Weekends
}

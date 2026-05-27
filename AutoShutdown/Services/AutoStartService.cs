using Microsoft.Win32;

namespace AutoShutdown.Services;

public class AutoStartService
{
    private const string RunKey = @"SOFTWARE\Microsoft\Windows\CurrentVersion\Run";
    private const string AppName = "AutoShutdown";

    public bool IsEnabled()
    {
        using var key = Registry.CurrentUser.OpenSubKey(RunKey);
        return key?.GetValue(AppName) != null;
    }

    public void Enable()
    {
        using var key = Registry.CurrentUser.OpenSubKey(RunKey, true);
        var exePath = Environment.ProcessPath!;
        key?.SetValue(AppName, $"\"{exePath}\"");
    }

    public void Disable()
    {
        using var key = Registry.CurrentUser.OpenSubKey(RunKey, true);
        key?.DeleteValue(AppName, false);
    }
}

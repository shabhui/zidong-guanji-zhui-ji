using System.Text.Json;
using AutoShutdown.Models;
using System.IO;

namespace AutoShutdown.Services;

public class SettingsService
{
    private static readonly string SettingsPath = System.IO.Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "AutoShutdown",
        "settings.json");

    public AppSettings Load()
    {
        try
        {
            if (System.IO.File.Exists(SettingsPath))
            {
                var json = System.IO.File.ReadAllText(SettingsPath);
                return JsonSerializer.Deserialize<AppSettings>(json) ?? new AppSettings();
            }
        }
        catch { }
        return new AppSettings();
    }

    public void Save(AppSettings settings)
    {
        var dir = System.IO.Path.GetDirectoryName(SettingsPath)!;
        System.IO.Directory.CreateDirectory(dir);
        var json = JsonSerializer.Serialize(settings, new JsonSerializerOptions { WriteIndented = true });
        System.IO.File.WriteAllText(SettingsPath, json);
    }
}

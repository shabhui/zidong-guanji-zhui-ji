using System.Diagnostics;
using System.IO;

namespace AutoShutdown.Services;

public sealed record ScriptRunResult(bool Success, bool TimedOut, int? ExitCode, string Message);

public sealed class PreActionScriptService
{
    public async Task<ScriptRunResult> RunAsync(string path, int timeoutSeconds)
    {
        if (string.IsNullOrWhiteSpace(path))
            return new ScriptRunResult(false, false, null, "脚本路径为空");

        if (!File.Exists(path))
            return new ScriptRunResult(false, false, null, "脚本文件不存在");

        timeoutSeconds = Math.Clamp(timeoutSeconds, 1, 3600);
        var extension = Path.GetExtension(path).ToLowerInvariant();
        ProcessStartInfo? startInfo = null;
        if (extension == ".bat" || extension == ".cmd")
        {
            startInfo = new ProcessStartInfo
            {
                FileName = "cmd.exe",
                Arguments = $"/c \"{path}\"",
                UseShellExecute = false,
                CreateNoWindow = true
            };
        }
        else if (extension == ".ps1")
        {
            startInfo = new ProcessStartInfo
            {
                FileName = "powershell.exe",
                Arguments = $"-NoProfile -ExecutionPolicy Bypass -File \"{path}\"",
                UseShellExecute = false,
                CreateNoWindow = true
            };
        }

        if (startInfo == null)
            return new ScriptRunResult(false, false, null, "仅支持 .bat、.cmd、.ps1 脚本");

        using var process = new Process { StartInfo = startInfo };
        try
        {
            if (!process.Start())
                return new ScriptRunResult(false, false, null, "脚本启动失败");

            var exited = await Task.Run(() => process.WaitForExit(timeoutSeconds * 1000));
            if (!exited)
            {
                try
                {
                    process.Kill(entireProcessTree: true);
                }
                catch
                {
                    // Ignore cleanup failures; timeout is the important result.
                }
                return new ScriptRunResult(false, true, null, "脚本执行超时");
            }

            return process.ExitCode == 0
                ? new ScriptRunResult(true, false, process.ExitCode, "脚本执行完成")
                : new ScriptRunResult(false, false, process.ExitCode, $"脚本退出码：{process.ExitCode}");
        }
        catch (Exception ex)
        {
            return new ScriptRunResult(false, false, null, ex.Message);
        }
    }
}

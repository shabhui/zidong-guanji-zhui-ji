# Pre-Action Script Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run an optional user-selected `.bat`, `.cmd`, or `.ps1` script before executing the selected power action.

**Architecture:** Add script settings to `AppSettings`, a focused `PreActionScriptService` for executing scripts with timeout, and UI in `MainWindow` to configure path/enabled/timeout. Integrate at `ShutdownService.ExecuteShutdown()` by adding a cancellable pre-action callback that runs before the system power command.

**Tech Stack:** WPF, C#/.NET 9, `System.Diagnostics.Process`, existing `ShutdownService`, `MainWindow`.

---

### Task 1: Add script settings

**Files:**
- Modify: `AutoShutdown/Models/AppSettings.cs`

- [ ] Add:

```csharp
public bool PreActionScriptEnabled { get; set; } = false;
public string PreActionScriptPath { get; set; } = string.Empty;
public int PreActionScriptTimeoutSeconds { get; set; } = 60;
```

### Task 2: Add script runner service

**Files:**
- Create: `AutoShutdown/Services/PreActionScriptService.cs`

- [ ] Implement:

```csharp
public sealed record ScriptRunResult(bool Success, bool TimedOut, int? ExitCode, string Message);
```

- [ ] Implement `Task<ScriptRunResult> RunAsync(string path, int timeoutSeconds)`.
- [ ] Support `.bat`/`.cmd` using `cmd.exe /c`.
- [ ] Support `.ps1` using `powershell.exe -ExecutionPolicy Bypass -File`.
- [ ] Reject missing files and unsupported extensions.
- [ ] Kill process on timeout.

### Task 3: Add UI

**Files:**
- Modify: `AutoShutdown/MainWindow.xaml`
- Modify: `AutoShutdown/MainWindow.xaml.cs`

- [ ] Add “执行前脚本” card with:
  - enabled toggle
  - script path textbox
  - browse button
  - timeout textbox
  - status label
- [ ] Browse uses `Microsoft.Win32.OpenFileDialog` filtered to `.bat;.cmd;.ps1`.
- [ ] Save settings when changed.

### Task 4: Integrate before power action

**Files:**
- Modify: `AutoShutdown/Services/ShutdownService.cs`
- Modify: `AutoShutdown/MainWindow.xaml.cs`

- [ ] Add async pre-action hook to `ShutdownService`:

```csharp
public Func<Task<bool>>? BeforePowerActionAsync { get; set; }
```

- [ ] Make `ExecuteShutdown()` run hook before `ExecutePowerAction()`. If hook returns false, cancel executing power action and fire `Cancelled`.
- [ ] In `MainWindow`, set hook to run configured script through `PreActionScriptService`.
- [ ] If script disabled, return true.
- [ ] If script fails/times out, show balloon and return false for safety.

### Task 5: Verify

**Files:**
- No extra source changes.

- [ ] Build:

```bash
dotnet build "AutoShutdown/AutoShutdown.csproj"
```

Expected: 0 warnings, 0 errors.

- [ ] Smoke test start only:

```bash
"AutoShutdown/bin/Debug/net9.0-windows/AutoShutdown.exe" --minimized
```

Expected: app starts. Do not run destructive power action during automated verification.

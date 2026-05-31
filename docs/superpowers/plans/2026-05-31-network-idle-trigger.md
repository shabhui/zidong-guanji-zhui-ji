# Network Idle Trigger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a global network idle trigger that executes the selected power action after upload and download stay below thresholds for a configured duration.

**Architecture:** Add a focused `NetworkIdleService` that samples all active IPv4 network interfaces once per second and reports current upload/download KB/s plus idle progress. `MainWindow` owns the UI and starts/stops the trigger. When idle duration is reached, it reuses existing reminder and power-action flow through `ShutdownService`.

**Tech Stack:** WPF, C#/.NET 9, `System.Net.NetworkInformation`, existing `ShutdownService`, `MainWindow`, `ReminderWindow`.

---

### Task 1: Add network idle settings

**Files:**
- Modify: `AutoShutdown/Models/AppSettings.cs`

- [ ] Add persisted defaults:

```csharp
public int NetworkDownloadThresholdKb { get; set; } = 100;
public int NetworkUploadThresholdKb { get; set; } = 50;
public int NetworkIdleMinutes { get; set; } = 5;
```

### Task 2: Create NetworkIdleService

**Files:**
- Create: `AutoShutdown/Services/NetworkIdleService.cs`

- [ ] Implement a service with:
  - `Start(int downloadThresholdKb, int uploadThresholdKb, int idleMinutes)`
  - `Stop()`
  - `Tick` event carrying download KB/s, upload KB/s, idle elapsed seconds, required idle seconds
  - `IdleReached` event

- [ ] Use `NetworkInterface.GetAllNetworkInterfaces()` and IPv4 stats bytes sent/received.
- [ ] Ignore interfaces not `OperationalStatus.Up`.

### Task 3: Add UI card

**Files:**
- Modify: `AutoShutdown/MainWindow.xaml`

- [ ] Add a “网络闲置触发” card below task center.
- [ ] Inputs:
  - `NetworkDownloadThresholdInput`
  - `NetworkUploadThresholdInput`
  - `NetworkIdleMinutesInput`
- [ ] Buttons:
  - `StartNetworkIdleButton`
  - `StopNetworkIdleButton`
- [ ] Status labels:
  - `NetworkSpeedLabel`
  - `NetworkIdleProgressLabel`

### Task 4: Wire UI to service

**Files:**
- Modify: `AutoShutdown/MainWindow.xaml.cs`

- [ ] Add field:

```csharp
private readonly NetworkIdleService _networkIdle = new();
```

- [ ] Subscribe to `Tick` and `IdleReached` in constructor.
- [ ] Load/save network idle settings.
- [ ] Implement `StartNetworkIdle_Click` and `StopNetworkIdle_Click`.
- [ ] On idle reached:
  - stop the network idle service
  - set repeat rule once
  - schedule a countdown equal to reminder seconds so existing reminder flow appears

### Task 5: Verify

**Files:**
- No additional source changes.

- [ ] Build:

```bash
dotnet build "AutoShutdown/AutoShutdown.csproj"
```

Expected: 0 warnings, 0 errors.

- [ ] Smoke test start only:

```bash
"AutoShutdown/bin/Debug/net9.0-windows/AutoShutdown.exe" --minimized
```

Expected: app starts; do not wait for real power action unless using safe Lock action.

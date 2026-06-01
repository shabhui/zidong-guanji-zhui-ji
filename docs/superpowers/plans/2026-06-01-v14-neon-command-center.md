# AutoShutdown v1.4 Neon Command Center Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild AutoShutdown's WPF UI into a clearly different v1.4 Neon Command Center and publish a v1.4 release without uploading the local `build/` reference folder.

**Architecture:** Keep the existing WPF/.NET app and business services. Add a stronger v1.4 theme layer in `DarkTheme.xaml`, rewrite the main window layout around a dashboard-style overview, and adapt `MainWindow.xaml.cs` only where UI names/status labels require synchronization. Preserve destructive action behavior and avoid adding new scheduling logic.

**Tech Stack:** WPF, .NET 9, XAML ResourceDictionary, `MainWindow.xaml`, `MainWindow.xaml.cs`, `dotnet publish`, GitHub CLI.

---

## File Structure

- Modify `AutoShutdown/Themes/DarkTheme.xaml`
  - Add v1.4 Neon semantic resources and reusable styles.
  - Keep existing resource keys so reminder window and old controls remain compatible.
- Modify `AutoShutdown/MainWindow.xaml`
  - Increase window to a command-center layout.
  - Replace v1.3 text with v1.4 text.
  - Rebuild overview as Hero status + quick chips + config summary + action grid.
  - Rebuild trigger cards as static EAccordion-style panels.
- Modify `AutoShutdown/MainWindow.xaml.cs`
  - Add helpers for overview default time, status badge, config summary, and recursive text lookup.
  - Update status, cancel, pause, quick countdown, action selection, pre-action script, navigation, and task-card visuals.
- Generated only, not committed:
  - `AutoShutdown/publish/`
  - `AutoShutdown/AutoShutdown-v1.4-win-x64.zip`

---

### Task 1: Add v1.4 Neon theme resources

**Files:**
- Modify: `AutoShutdown/Themes/DarkTheme.xaml`

- [ ] **Step 1: Add v1.4 brushes after `ToggleKnobOffBrush`**

Insert this block immediately after:

```xml
<SolidColorBrush x:Key="ToggleKnobOffBrush" Color="#CDBFEA"/>
```

Add:

```xml
<SolidColorBrush x:Key="CommandCardBorderBrush" Color="#88DDF7FF"/>
<SolidColorBrush x:Key="CommandCardInnerBorderBrush" Color="#3379D8FF"/>
<SolidColorBrush x:Key="NavPillBrush" Color="#1823405F"/>
<SolidColorBrush x:Key="NavPillActiveBrush" Color="#3A79D8FF"/>
<SolidColorBrush x:Key="NavPillIndicatorBrush" Color="#FF8ACF"/>
<SolidColorBrush x:Key="StatusReadyBrush" Color="#7DFFC4"/>
<SolidColorBrush x:Key="StatusRunningBrush" Color="#FFD166"/>
<SolidColorBrush x:Key="StatusPausedBrush" Color="#B779FF"/>
<SolidColorBrush x:Key="ActionTileBrush" Color="#1F243A60"/>
<SolidColorBrush x:Key="ActionTileHoverBrush" Color="#33406486"/>
<SolidColorBrush x:Key="BadgeBrush" Color="#2629D8FF"/>
<SolidColorBrush x:Key="ChipBrush" Color="#223D2F62"/>
<SolidColorBrush x:Key="ChipHoverBrush" Color="#355B3F86"/>
```

- [ ] **Step 2: Add v1.4 gradients after `InputGlowBrush`**

Insert this block immediately after the closing `</LinearGradientBrush>` for `InputGlowBrush`:

```xml
<LinearGradientBrush x:Key="CommandBackgroundBrush" StartPoint="0,0" EndPoint="1,1">
    <GradientStop Color="#0B1024" Offset="0"/>
    <GradientStop Color="#161039" Offset="0.42"/>
    <GradientStop Color="#2B164D" Offset="1"/>
</LinearGradientBrush>

<LinearGradientBrush x:Key="CommandHeroBrush" StartPoint="0,0" EndPoint="1,1">
    <GradientStop Color="#6636E8FF" Offset="0"/>
    <GradientStop Color="#55B779FF" Offset="0.42"/>
    <GradientStop Color="#44FF8ACF" Offset="1"/>
</LinearGradientBrush>

<LinearGradientBrush x:Key="CommandCardBrush" StartPoint="0,0" EndPoint="1,1">
    <GradientStop Color="#3AFFFFFF" Offset="0"/>
    <GradientStop Color="#23203655" Offset="0.55"/>
    <GradientStop Color="#1A10182F" Offset="1"/>
</LinearGradientBrush>

<LinearGradientBrush x:Key="ActionTileActiveBrush" StartPoint="0,0" EndPoint="1,1">
    <GradientStop Color="#BBFF8ACF" Offset="0"/>
    <GradientStop Color="#99B779FF" Offset="0.5"/>
    <GradientStop Color="#8879D8FF" Offset="1"/>
</LinearGradientBrush>
```

- [ ] **Step 3: Add a stronger hero glow effect after `SoftShadow`**

Insert after:

```xml
<DropShadowEffect x:Key="SoftShadow" Color="#000000" BlurRadius="26" ShadowDepth="6" Opacity="0.24"/>
```

Add:

```xml
<DropShadowEffect x:Key="HeroGlowShadow" Color="#79D8FF" BlurRadius="36" ShadowDepth="0" Opacity="0.42"/>
<DropShadowEffect x:Key="PinkGlowShadow" Color="#FF8ACF" BlurRadius="30" ShadowDepth="0" Opacity="0.36"/>
```

- [ ] **Step 4: Add reusable v1.4 styles before `TitleText`**

Insert before:

```xml
<Style x:Key="TitleText" TargetType="TextBlock">
```

Add:

```xml
<Style x:Key="CommandCard" TargetType="Border" BasedOn="{StaticResource CardBorder}">
    <Setter Property="Background" Value="{StaticResource CommandCardBrush}"/>
    <Setter Property="BorderBrush" Value="{StaticResource CommandCardBorderBrush}"/>
    <Setter Property="CornerRadius" Value="28"/>
    <Setter Property="Padding" Value="22"/>
    <Setter Property="Effect" Value="{StaticResource SoftShadow}"/>
</Style>

<Style x:Key="HeroCommandCard" TargetType="Border" BasedOn="{StaticResource CommandCard}">
    <Setter Property="Background" Value="{StaticResource CommandHeroBrush}"/>
    <Setter Property="BorderBrush" Value="{StaticResource GlassBorderStrongBrush}"/>
    <Setter Property="Effect" Value="{StaticResource HeroGlowShadow}"/>
</Style>

<Style x:Key="StatusBadge" TargetType="Border">
    <Setter Property="CornerRadius" Value="14"/>
    <Setter Property="Padding" Value="10,5"/>
    <Setter Property="Background" Value="{StaticResource BadgeBrush}"/>
    <Setter Property="BorderBrush" Value="{StaticResource CommandCardBorderBrush}"/>
    <Setter Property="BorderThickness" Value="1"/>
</Style>

<Style x:Key="ChipButton" TargetType="Button" BasedOn="{StaticResource SecondaryButton}">
    <Setter Property="Background" Value="{StaticResource ChipBrush}"/>
    <Setter Property="BorderBrush" Value="{StaticResource CommandCardInnerBorderBrush}"/>
    <Setter Property="Padding" Value="12,9"/>
    <Setter Property="MinHeight" Value="38"/>
</Style>

<Style x:Key="ActionTile" TargetType="Border">
    <Setter Property="CornerRadius" Value="20"/>
    <Setter Property="Padding" Value="16,14"/>
    <Setter Property="Background" Value="{StaticResource ActionTileBrush}"/>
    <Setter Property="BorderBrush" Value="{StaticResource GlassBorderBrush}"/>
    <Setter Property="BorderThickness" Value="1"/>
    <Setter Property="Cursor" Value="Hand"/>
</Style>

<Style x:Key="AccordionPanel" TargetType="Border" BasedOn="{StaticResource CommandCard}">
    <Setter Property="CornerRadius" Value="26"/>
    <Setter Property="Padding" Value="0"/>
    <Setter Property="Margin" Value="0,0,0,16"/>
</Style>
```

- [ ] **Step 5: Build and commit**

Run:

```bash
dotnet build "AutoShutdown/AutoShutdown.csproj"
git add AutoShutdown/Themes/DarkTheme.xaml
git commit -m "Add v1.4 neon theme resources"
```

Expected: build succeeds with 0 warnings and 0 errors.

---

### Task 2: Rebuild shell, header, sidebar, and overview command center

**Files:**
- Modify: `AutoShutdown/MainWindow.xaml`

- [ ] **Step 1: Update window size and background**

Change the `<Window>` size to:

```xml
Width="1040" Height="720"
```

Change `RootGrid` background resource from `AppBackgroundBrush` to:

```xml
<StaticResource ResourceKey="CommandBackgroundBrush"/>
```

- [ ] **Step 2: Replace the top header content**

In `HeroHeader`, keep the `x:Name` and `Grid.Row`, but change its `Padding` to `26,14`, `Background` to `{StaticResource CommandCardBrush}`, and replace title texts with:

```xml
<TextBlock Text="AutoShutdown v1.4" FontSize="28" FontWeight="Bold" Foreground="{StaticResource TextPrimaryBrush}"/>
<TextBlock Text="Neon Command Center" FontSize="13" FontWeight="SemiBold" Margin="0,4,0,0" Foreground="{StaticResource AccentBrush}" Opacity="0.98"/>
<TextBlock Text="状态、动作、触发器都集中在一个更醒目的控制台里。" FontSize="12" Margin="0,5,0,0" Foreground="{StaticResource TextSecondaryBrush}"/>
```

Add a header status badge before the window buttons:

```xml
<Border x:Name="HeaderStatusBadge" Style="{StaticResource StatusBadge}" Margin="0,0,12,0" VerticalAlignment="Center">
    <TextBlock x:Name="HeaderStatusText" Text="READY" FontSize="12" FontWeight="Bold" Foreground="{StaticResource StatusReadyBrush}"/>
</Border>
```

- [ ] **Step 3: Update main grid columns**

Change the main content grid columns to:

```xml
<ColumnDefinition Width="205"/>
<ColumnDefinition Width="20"/>
<ColumnDefinition Width="*"/>
```

- [ ] **Step 4: Update sidebar version text**

Replace `v1.3 · Glass Anime` with:

```xml
v1.4 · Neon Center
```

- [ ] **Step 5: Replace overview section with command center layout**

Replace the whole `OverviewSection` inner `<StackPanel>...</StackPanel>` with this structure while preserving existing control names and click handlers:

```xml
<StackPanel>
    <Border x:Name="StatusCard" Style="{StaticResource HeroCommandCard}" Margin="0,0,0,16">
        <Grid>
            <Grid.ColumnDefinitions>
                <ColumnDefinition Width="*"/>
                <ColumnDefinition Width="Auto"/>
            </Grid.ColumnDefinitions>
            <StackPanel>
                <StackPanel Orientation="Horizontal" Margin="0,0,0,10">
                    <Border x:Name="OverviewStatusBadge" Style="{StaticResource StatusBadge}" Margin="0,0,10,0">
                        <TextBlock x:Name="OverviewStatusText" Text="READY" FontSize="12" FontWeight="Bold" Foreground="{StaticResource StatusReadyBrush}"/>
                    </Border>
                    <TextBlock x:Name="StatusTitle" Text="准备启动任务" FontSize="18" FontWeight="Bold" Foreground="{StaticResource TextPrimaryBrush}" VerticalAlignment="Center"/>
                </StackPanel>
                <TextBlock x:Name="RemainingLabel" Text="默认倒计时" FontSize="13" Foreground="{StaticResource TextSecondaryBrush}"/>
                <TextBlock x:Name="RemainingTime" Text="00:30:00" FontSize="58" FontWeight="Bold" Foreground="{StaticResource WarningBrush}" Margin="0,2,0,6"/>
                <TextBlock x:Name="TargetTimeLabel" Text="选择动作和时间后启动任务" FontSize="13" Foreground="{StaticResource TextPrimaryBrush}" TextWrapping="Wrap"/>
                <TextBlock x:Name="ShutdownModeLabel" Text="执行方式：正常执行" Margin="0,6,0,0" FontSize="13" Foreground="{StaticResource TextSecondaryBrush}" TextWrapping="Wrap"/>
            </StackPanel>
            <StackPanel Grid.Column="1" Width="210" VerticalAlignment="Center">
                <Button x:Name="OverviewStartButton" Content="启动倒计时" Style="{StaticResource PrimaryButton}" Click="CountdownStart_Click" Margin="0,0,0,10"/>
                <Button x:Name="ExecuteCurrentActionButton" Content="立即执行当前动作" Style="{StaticResource DangerButton}" Click="ExecuteCurrentAction_Click" Margin="0,0,0,10"/>
                <Button x:Name="PauseResumeButton" Content="暂停 1 小时" Style="{StaticResource SecondaryButton}" Click="PauseResume_Click" Margin="0,0,0,10" Visibility="Collapsed"/>
                <Button x:Name="CancelPlanButton" Content="取消任务计划" Style="{StaticResource SecondaryButton}" Click="CancelShutdown_Click" Visibility="Collapsed"/>
            </StackPanel>
        </Grid>
    </Border>

    <Grid Margin="0,0,0,16">
        <Grid.ColumnDefinitions>
            <ColumnDefinition Width="1.05*"/>
            <ColumnDefinition Width="16"/>
            <ColumnDefinition Width="0.95*"/>
        </Grid.ColumnDefinitions>
        <Border Style="{StaticResource CommandCard}">
            <StackPanel>
                <TextBlock Text="快捷倒计时" Style="{StaticResource TitleText}" FontSize="18" Margin="0,0,0,8"/>
                <UniformGrid Columns="2">
                    <Button Content="15 分钟" Tag="15" Style="{StaticResource ChipButton}" Margin="0,0,8,8" Click="QuickCountdown_Click"/>
                    <Button Content="30 分钟" Tag="30" Style="{StaticResource ChipButton}" Margin="0,0,0,8" Click="QuickCountdown_Click"/>
                    <Button Content="1 小时" Tag="60" Style="{StaticResource ChipButton}" Margin="0,0,8,0" Click="QuickCountdown_Click"/>
                    <Button Content="2 小时" Tag="120" Style="{StaticResource ChipButton}" Click="QuickCountdown_Click"/>
                </UniformGrid>
            </StackPanel>
        </Border>
        <Border Grid.Column="2" Style="{StaticResource CommandCard}">
            <StackPanel>
                <TextBlock Text="当前配置" Style="{StaticResource TitleText}" FontSize="18" Margin="0,0,0,8"/>
                <TextBlock x:Name="OverviewActionSummary" Text="动作：关机" Style="{StaticResource SubtitleText}" Margin="0,0,0,6"/>
                <TextBlock x:Name="OverviewReminderSummary" Text="提醒：提前 60 秒" Style="{StaticResource SubtitleText}" Margin="0,0,0,6"/>
                <TextBlock x:Name="OverviewForceSummary" Text="强制关闭：关闭" Style="{StaticResource SubtitleText}" Margin="0,0,0,6"/>
                <TextBlock x:Name="OverviewScriptSummary" Text="脚本：未启用" Style="{StaticResource SubtitleText}"/>
            </StackPanel>
        </Border>
    </Grid>

    <Border Style="{StaticResource CommandCard}" Margin="0,0,0,16">
        <StackPanel>
            <TextBlock Text="电源动作" Style="{StaticResource TitleText}" Margin="0,0,0,8"/>
            <TextBlock Text="所有定时、触发器和立即执行都会使用这里的动作。" Style="{StaticResource SubtitleText}" Margin="0,0,0,16"/>
            <UniformGrid Columns="3" Rows="2">
                <Border x:Name="ActionShutdown" Tag="Shutdown" Style="{StaticResource ActionTile}" Margin="0,0,10,10" MouseLeftButtonDown="PowerAction_Click"><StackPanel><TextBlock Text="关机" FontSize="16" FontWeight="Bold" Foreground="{StaticResource TextPrimaryBrush}" HorizontalAlignment="Center"/><TextBlock Text="SHUTDOWN" FontSize="10" Foreground="{StaticResource TextSecondaryBrush}" HorizontalAlignment="Center" Margin="0,5,0,0"/></StackPanel></Border>
                <Border x:Name="ActionSleep" Tag="Sleep" Style="{StaticResource ActionTile}" Margin="0,0,10,10" MouseLeftButtonDown="PowerAction_Click"><StackPanel><TextBlock Text="睡眠" FontSize="16" FontWeight="Bold" Foreground="{StaticResource TextPrimaryBrush}" HorizontalAlignment="Center"/><TextBlock Text="SLEEP" FontSize="10" Foreground="{StaticResource TextSecondaryBrush}" HorizontalAlignment="Center" Margin="0,5,0,0"/></StackPanel></Border>
                <Border x:Name="ActionHibernate" Tag="Hibernate" Style="{StaticResource ActionTile}" Margin="0,0,0,10" MouseLeftButtonDown="PowerAction_Click"><StackPanel><TextBlock Text="休眠" FontSize="16" FontWeight="Bold" Foreground="{StaticResource TextPrimaryBrush}" HorizontalAlignment="Center"/><TextBlock Text="HIBERNATE" FontSize="10" Foreground="{StaticResource TextSecondaryBrush}" HorizontalAlignment="Center" Margin="0,5,0,0"/></StackPanel></Border>
                <Border x:Name="ActionRestart" Tag="Restart" Style="{StaticResource ActionTile}" Margin="0,0,10,0" MouseLeftButtonDown="PowerAction_Click"><StackPanel><TextBlock Text="重启" FontSize="16" FontWeight="Bold" Foreground="{StaticResource TextPrimaryBrush}" HorizontalAlignment="Center"/><TextBlock Text="RESTART" FontSize="10" Foreground="{StaticResource TextSecondaryBrush}" HorizontalAlignment="Center" Margin="0,5,0,0"/></StackPanel></Border>
                <Border x:Name="ActionLogOut" Tag="LogOut" Style="{StaticResource ActionTile}" Margin="0,0,10,0" MouseLeftButtonDown="PowerAction_Click"><StackPanel><TextBlock Text="注销" FontSize="16" FontWeight="Bold" Foreground="{StaticResource TextPrimaryBrush}" HorizontalAlignment="Center"/><TextBlock Text="LOG OUT" FontSize="10" Foreground="{StaticResource TextSecondaryBrush}" HorizontalAlignment="Center" Margin="0,5,0,0"/></StackPanel></Border>
                <Border x:Name="ActionLock" Tag="Lock" Style="{StaticResource ActionTile}" MouseLeftButtonDown="PowerAction_Click"><StackPanel><TextBlock Text="锁定" FontSize="16" FontWeight="Bold" Foreground="{StaticResource TextPrimaryBrush}" HorizontalAlignment="Center"/><TextBlock Text="LOCK" FontSize="10" Foreground="{StaticResource TextSecondaryBrush}" HorizontalAlignment="Center" Margin="0,5,0,0"/></StackPanel></Border>
            </UniformGrid>
        </StackPanel>
    </Border>
</StackPanel>
```

- [ ] **Step 6: Build and commit**

Run:

```bash
dotnet build "AutoShutdown/AutoShutdown.csproj"
git add AutoShutdown/MainWindow.xaml
git commit -m "Rebuild v1.4 command center overview"
```

Expected: build succeeds with 0 warnings and 0 errors.

---

### Task 3: Adapt code-behind to the new overview and neon states

**Files:**
- Modify: `AutoShutdown/MainWindow.xaml.cs`

- [ ] **Step 1: Update quick countdown to refresh overview hero**

Replace `QuickCountdown_Click` with:

```csharp
private void QuickCountdown_Click(object sender, RoutedEventArgs e)
{
    if (sender is not System.Windows.Controls.Button button || button.Tag is not string tag || !int.TryParse(tag, out var minutes))
        return;

    var duration = TimeSpan.FromMinutes(minutes);
    HoursInput.Text = ((int)duration.TotalHours).ToString();
    MinutesInput.Text = duration.Minutes.ToString();
    SecondsInput.Text = "0";
    UpdateReadyOverview();
    PulseElement(StatusCard, 1.01);
}
```

- [ ] **Step 2: Replace status update methods**

Replace `UpdateStatusUI`, `OnTick`, `OnCancelled`, and `UpdatePauseUI` with:

```csharp
private void UpdateStatusUI()
{
    StatusCard.Visibility = Visibility.Visible;
    PulseElement(StatusCard);
    CountdownStartBtn.IsEnabled = false;
    FixedTimeStartBtn.IsEnabled = false;
    OverviewStartButton.IsEnabled = false;
    PauseResumeButton.Visibility = Visibility.Visible;
    CancelPlanButton.Visibility = Visibility.Visible;
    _tray.SetShutdownActive(true);
    UpdatePauseUI();
    var repeatText = _shutdown.RepeatRule == RepeatRule.Once ? "单次" : GetRepeatLabel(_shutdown.RepeatRule);
    TargetTimeLabel.Text = _shutdown.IsPaused
        ? $"已暂停：{GetActionVerb(_settings.SelectedPowerAction)} · {repeatText} · 将于 {_shutdown.PauseUntil:HH:mm} 自动恢复"
        : $"计划执行：{GetActionVerb(_settings.SelectedPowerAction)} · {repeatText} · {_shutdown.TargetTime:yyyy-MM-dd HH:mm:ss}";
    ShutdownModeLabel.Text = _shutdown.SupportsForceCloseApps && _settings.ForceCloseApps
        ? "执行方式：强制关闭应用（未保存内容可能丢失）"
        : "执行方式：正常执行";
    UpdateOverviewSummaries();
}

private void OnTick(string remaining)
{
    Dispatcher.Invoke(() =>
    {
        RemainingTime.Text = remaining;
        PulseElement(RemainingTime, 1.025);
    });
}

private void OnCancelled()
{
    Dispatcher.Invoke(() =>
    {
        CountdownStartBtn.IsEnabled = true;
        FixedTimeStartBtn.IsEnabled = true;
        OverviewStartButton.IsEnabled = true;
        PauseResumeButton.Visibility = Visibility.Collapsed;
        CancelPlanButton.Visibility = Visibility.Collapsed;
        _tray.SetShutdownActive(false);
        _tray.SetPaused(false);
        UpdateReadyOverview();
        _tray.ShowBalloon("智能定时关机", "已取消任务计划");
    });
}

private void UpdatePauseUI()
{
    var paused = _shutdown.IsPaused;
    PauseResumeButton.Content = paused ? "恢复任务" : "暂停 1 小时";
    StatusTitle.Text = paused ? "任务已暂停" : "任务计划运行中";
    RemainingLabel.Text = paused ? "恢复后剩余时间" : "距离执行还有";
    SetStatusBadge(paused ? "PAUSED" : "RUNNING", paused ? "StatusPausedBrush" : "StatusRunningBrush");
}
```

- [ ] **Step 3: Add overview helper methods before `UpdateStatusUI`**

Insert before `private void UpdateStatusUI()`:

```csharp
private void UpdateReadyOverview()
{
    var duration = new TimeSpan(ParseInt(HoursInput.Text), ParseInt(MinutesInput.Text), ParseInt(SecondsInput.Text));
    StatusTitle.Text = "准备启动任务";
    RemainingLabel.Text = "默认倒计时";
    RemainingTime.Text = duration.ToString(@"hh\:mm\:ss");
    TargetTimeLabel.Text = $"当前动作：{GetActionLabel(_settings.SelectedPowerAction)}";
    ShutdownModeLabel.Text = _shutdown.SupportsForceCloseApps && _settings.ForceCloseApps
        ? "执行方式：强制关闭应用（未保存内容可能丢失）"
        : "执行方式：正常执行";
    SetStatusBadge("READY", "StatusReadyBrush");
    UpdateOverviewSummaries();
}

private void SetStatusBadge(string text, string brushKey)
{
    HeaderStatusText.Text = text;
    OverviewStatusText.Text = text;
    var brush = FindResource(brushKey) as Brush;
    HeaderStatusText.Foreground = brush;
    OverviewStatusText.Foreground = brush;
}

private void UpdateOverviewSummaries()
{
    OverviewActionSummary.Text = $"动作：{GetActionLabel(_settings.SelectedPowerAction)}";
    OverviewReminderSummary.Text = $"提醒：提前 {_settings.ReminderSeconds} 秒";
    OverviewForceSummary.Text = _settings.ForceCloseApps && _shutdown.SupportsForceCloseApps ? "强制关闭：开启" : "强制关闭：关闭";
    OverviewScriptSummary.Text = _settings.PreActionScriptEnabled ? $"脚本：已启用 · 超时 {_settings.PreActionScriptTimeoutSeconds} 秒" : "脚本：未启用";
}
```

- [ ] **Step 4: Refresh overview in settings and selections**

Add `UpdateReadyOverview();` at the end of `LoadSettings()` after `ShowSection(UiSection.Overview);`.

Add `UpdateOverviewSummaries();` at the end of these methods:

```csharp
SaveReminderSetting()
UpdatePreActionScriptUI()
UpdateForceCloseUI()
UpdateAutoStartUI()
```

In `UpdatePowerActionUI()`, after `ReminderSettingSubtitle.Text = ...`, add:

```csharp
UpdateReadyOverview();
```

- [ ] **Step 5: Update action tile and nav visuals**

In `UpdatePowerActionUI()`, change selected/unselected visuals to:

```csharp
button.Background = isSelected ? FindResource("ActionTileActiveBrush") as Brush : FindResource("ActionTileBrush") as Brush;
button.BorderBrush = isSelected ? FindResource("GlassBorderStrongBrush") as Brush : FindResource("GlassBorderBrush") as Brush;
button.Effect = isSelected ? FindResource("HeroGlowShadow") as System.Windows.Media.Effects.Effect : null;
```

In `UpdateNavigationUI()`, change selected/unselected visuals to:

```csharp
item.Background = isActive ? FindResource("NavPillActiveBrush") as Brush : FindResource("NavPillBrush") as Brush;
item.BorderBrush = isActive ? FindResource("GlassBorderStrongBrush") as Brush : FindResource("GlassBorderBrush") as Brush;
item.Effect = isActive ? FindResource("CyanShadow") as System.Windows.Media.Effects.Effect : null;
indicator.Background = isActive ? FindResource("NavPillIndicatorBrush") as Brush : FindResource("NavIndicatorBrush") as Brush;
indicator.Opacity = isActive ? 1 : 0;
```

- [ ] **Step 6: Build and commit**

Run:

```bash
dotnet build "AutoShutdown/AutoShutdown.csproj"
git add AutoShutdown/MainWindow.xaml.cs
git commit -m "Wire v1.4 command center status UI"
```

Expected: build succeeds with 0 warnings and 0 errors.

---

### Task 4: Polish sub-pages, task cards, and trigger accordion panels

**Files:**
- Modify: `AutoShutdown/MainWindow.xaml`
- Modify: `AutoShutdown/MainWindow.xaml.cs`

- [ ] **Step 1: Convert trigger cards to visible accordion panels**

For both trigger cards, change the outer border style from `CardBorder` to `AccordionPanel`. Replace the first title block area with a header grid like this for network idle:

```xml
<Border CornerRadius="26,26,0,0" Background="{StaticResource CommandHeroBrush}" BorderBrush="{StaticResource CommandCardBorderBrush}" BorderThickness="0,0,0,1" Padding="18,16">
    <Grid>
        <Grid.ColumnDefinitions>
            <ColumnDefinition Width="Auto"/>
            <ColumnDefinition Width="*"/>
            <ColumnDefinition Width="Auto"/>
        </Grid.ColumnDefinitions>
        <Border Width="38" Height="38" CornerRadius="15" Background="{StaticResource HeroBrush}" Effect="{StaticResource CyanShadow}">
            <TextBlock Text="&#xE968;" FontFamily="Segoe MDL2 Assets" FontSize="17" Foreground="White" HorizontalAlignment="Center" VerticalAlignment="Center"/>
        </Border>
        <StackPanel Grid.Column="1" Margin="14,0,0,0" VerticalAlignment="Center">
            <TextBlock Text="网络闲置触发" FontSize="20" FontWeight="Bold" Foreground="{StaticResource TextPrimaryBrush}"/>
            <TextBlock Text="上传和下载速度持续低于阈值后，自动执行当前选择的电源动作。" FontSize="12" Foreground="{StaticResource TextSecondaryBrush}" TextWrapping="Wrap"/>
        </StackPanel>
        <Border Grid.Column="2" Style="{StaticResource StatusBadge}" VerticalAlignment="Center">
            <TextBlock Text="AUTO" FontSize="11" FontWeight="Bold" Foreground="{StaticResource AccentBrush}"/>
        </Border>
    </Grid>
</Border>
```

Use the same structure for process exit with title `进程退出触发`, icon `&#xE756;`, and badge text `PROCESS`.

Wrap each card body content in:

```xml
<StackPanel Margin="18">
    ...existing body controls...
</StackPanel>
```

- [ ] **Step 2: Make Timer, Script, and Settings panels use `CommandCard`**

In `MainWindow.xaml`, replace page-level `Style="{StaticResource CardBorder}"` on Timer, Tasks, Script, and Settings cards with:

```xml
Style="{StaticResource CommandCard}"
```

Keep nested input panels as `GlassPanel`.

- [ ] **Step 3: Update task list card visuals**

In `RefreshTaskList()`, replace the `card` Border initialization with:

```csharp
var card = new Border
{
    CornerRadius = new CornerRadius(20),
    Padding = new Thickness(16),
    Margin = new Thickness(0, 0, 0, 12),
    Background = FindResource("CommandCardBrush") as Brush,
    BorderBrush = task.Enabled ? FindResource("CommandCardBorderBrush") as Brush : FindResource("GlassBorderBrush") as Brush,
    BorderThickness = new Thickness(1),
    Effect = task.Enabled ? FindResource("CyanShadow") as System.Windows.Media.Effects.Effect : null,
    Opacity = task.Enabled ? 1 : 0.52
};
```

Change the next-time text to:

```csharp
Text = $"NEXT · {GetNextTaskTime(task):yyyy-MM-dd HH:mm:ss}",
```

- [ ] **Step 4: Build and commit**

Run:

```bash
dotnet build "AutoShutdown/AutoShutdown.csproj"
git add AutoShutdown/MainWindow.xaml AutoShutdown/MainWindow.xaml.cs
git commit -m "Polish v1.4 neon subpages"
```

Expected: build succeeds with 0 warnings and 0 errors.

---

### Task 5: Publish v1.4 release

**Files:**
- Generated only, not committed:
  - `AutoShutdown/publish/`
  - `AutoShutdown/AutoShutdown-v1.4-win-x64.zip`

- [ ] **Step 1: Verify ignored local artifacts**

Run:

```bash
git check-ignore -v build/ AutoShutdown/publish/ AutoShutdown/AutoShutdown-v1.4-win-x64.zip
```

Expected: each path is ignored by `.gitignore`.

- [ ] **Step 2: Final build**

Run:

```bash
dotnet build "AutoShutdown/AutoShutdown.csproj"
```

Expected: build succeeds with 0 warnings and 0 errors.

If the executable is locked, run:

```bash
powershell.exe -NoProfile -Command "Get-Process AutoShutdown -ErrorAction SilentlyContinue | Stop-Process -Force"
dotnet build "AutoShutdown/AutoShutdown.csproj"
```

- [ ] **Step 3: Publish single-file win-x64 build**

Run:

```bash
dotnet publish "AutoShutdown/AutoShutdown.csproj" -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:EnableCompressionInSingleFile=true -o "AutoShutdown/publish"
```

Expected: publish succeeds.

If publish fails with `AutoShutdown.exe` locked, run:

```bash
powershell.exe -NoProfile -Command "Get-Process AutoShutdown -ErrorAction SilentlyContinue | Stop-Process -Force"
dotnet publish "AutoShutdown/AutoShutdown.csproj" -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:EnableCompressionInSingleFile=true -o "AutoShutdown/publish"
```

- [ ] **Step 4: Create v1.4 zip**

Run:

```bash
rm -f "AutoShutdown/AutoShutdown-v1.4-win-x64.zip"
powershell.exe -NoProfile -Command "Compress-Archive -Path 'AutoShutdown/publish/*' -DestinationPath 'AutoShutdown/AutoShutdown-v1.4-win-x64.zip' -Force; Get-Item 'AutoShutdown/AutoShutdown-v1.4-win-x64.zip' | Select-Object FullName,Length"
```

Expected: zip exists and is ignored by git.

- [ ] **Step 5: Create GitHub release v1.4**

Run:

```bash
gh release create v1.4 "AutoShutdown/AutoShutdown-v1.4-win-x64.zip" --repo shabhui/AIRUANJIAN --target main --title "AutoShutdown v1.4" --notes "AutoShutdown v1.4 更新：全新 Neon Command Center 首页，参考 EvolveUI Neon 风格重做主界面；强化倒计时状态 Hero、侧边导航、电源动作网格和智能触发分组视觉，同时保留 v1.3.1 的稳定功能。"
```

If release already exists, run:

```bash
gh release upload v1.4 "AutoShutdown/AutoShutdown-v1.4-win-x64.zip" --repo shabhui/AIRUANJIAN --clobber
```

- [ ] **Step 6: Push code**

Run:

```bash
git status --short
git push origin main
```

Expected: code is pushed; `build/`, `AutoShutdown/publish/`, and zip remain ignored.

---

## Self-Review Notes

- Spec coverage: Task 1 covers v1.4 resources; Task 2 covers first-screen command center, version text, sidebar, hero, quick chips, config summary, and action grid; Task 3 covers code-behind synchronization; Task 4 covers trigger accordion panels and subpage polish; Task 5 covers publish and GitHub release.
- Placeholder scan: no placeholders remain; each command and code snippet is concrete.
- Type consistency: new XAML names used by C# are `HeaderStatusText`, `OverviewStatusText`, `OverviewStartButton`, `OverviewActionSummary`, `OverviewReminderSummary`, `OverviewForceSummary`, and `OverviewScriptSummary`; all are created in Task 2 before code references them in Task 3.

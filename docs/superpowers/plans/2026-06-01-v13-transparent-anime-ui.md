# AutoShutdown v1.3 Transparent Anime UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign AutoShutdown into a transparent light-anime desktop UI with side navigation, then publish GitHub Release v1.3.

**Architecture:** Keep the existing WPF business logic and named controls, but reorganize `MainWindow.xaml` into a two-column shell: left navigation and right section panels. `MainWindow.xaml.cs` adds simple section switching while preserving all existing button/event handlers. Release packaging uses the existing .NET single-file publish and GitHub CLI workflow.

**Tech Stack:** WPF, .NET 9, XAML resource dictionaries, existing `MainWindow`, `DarkTheme.xaml`, `gh` CLI.

---

## File Structure

- Modify `AutoShutdown/Themes/DarkTheme.xaml`
  - Add the transparent light-anime palette and softer glass styles.
- Modify `AutoShutdown/MainWindow.xaml`
  - Replace the long single-scroll layout with a header, sidebar nav, and six content sections.
  - Preserve existing named controls and click handlers.
- Modify `AutoShutdown/MainWindow.xaml.cs`
  - Add `UiSection`, nav click handlers, `ShowSection`, `UpdateNavigationUI`, and section transition animation.
  - Keep all existing feature logic intact.
- Create/Update release artifact outside git tracking:
  - `AutoShutdown/AutoShutdown-v1.3-win-x64.zip`
- GitHub Release:
  - Create or update tag/release `v1.3`.

---

### Task 1: Refresh theme resources

**Files:**
- Modify: `AutoShutdown/Themes/DarkTheme.xaml`

- [ ] **Step 1: Update color tokens**

Replace the current color block at the top of `DarkTheme.xaml` with a transparent light-anime palette:

```xml
<Color x:Key="PrimaryColor">#B779FF</Color>
<Color x:Key="PrimaryHoverColor">#D7B7FF</Color>
<Color x:Key="AccentColor">#79D8FF</Color>
<Color x:Key="AccentPinkColor">#FF8ACF</Color>
<Color x:Key="BgDarkColor">#151226</Color>
<Color x:Key="BgCardColor">#332A4B</Color>
<Color x:Key="BgInputColor">#241D3A</Color>
<Color x:Key="TextPrimaryColor">#FFF7FF</Color>
<Color x:Key="TextSecondaryColor">#CDBFEA</Color>
<Color x:Key="DangerColor">#FF5C8A</Color>
<Color x:Key="DangerHoverColor">#FF7FA3</Color>
<Color x:Key="SuccessColor">#7DFFC4</Color>
<Color x:Key="WarningColor">#FFD166</Color>
<Color x:Key="StrokeColor">#AA8EEB</Color>
```

- [ ] **Step 2: Update gradient and glass resources**

Use these resource definitions:

```xml
<LinearGradientBrush x:Key="AppBackgroundBrush" StartPoint="0,0" EndPoint="1,1">
    <GradientStop Color="#151226" Offset="0"/>
    <GradientStop Color="#241B3F" Offset="0.48"/>
    <GradientStop Color="#3A245F" Offset="1"/>
</LinearGradientBrush>

<LinearGradientBrush x:Key="HeroBrush" StartPoint="0,0" EndPoint="1,1">
    <GradientStop Color="#FF8ACF" Offset="0"/>
    <GradientStop Color="#B779FF" Offset="0.52"/>
    <GradientStop Color="#79D8FF" Offset="1"/>
</LinearGradientBrush>

<LinearGradientBrush x:Key="NeonCardBrush" StartPoint="0,0" EndPoint="1,1">
    <GradientStop Color="#44FFFFFF" Offset="0"/>
    <GradientStop Color="#223D2F62" Offset="0.55"/>
    <GradientStop Color="#181B1530" Offset="1"/>
</LinearGradientBrush>

<LinearGradientBrush x:Key="InputGlowBrush" StartPoint="0,0" EndPoint="1,1">
    <GradientStop Color="#40FFFFFF" Offset="0"/>
    <GradientStop Color="#22261C3E" Offset="1"/>
</LinearGradientBrush>
```

- [ ] **Step 3: Soften shadows and cards**

Set:

```xml
<DropShadowEffect x:Key="NeonShadow" Color="#FF8ACF" BlurRadius="26" ShadowDepth="0" Opacity="0.34"/>
<DropShadowEffect x:Key="CyanShadow" Color="#79D8FF" BlurRadius="20" ShadowDepth="0" Opacity="0.32"/>
<DropShadowEffect x:Key="DangerShadow" Color="#FF5C8A" BlurRadius="20" ShadowDepth="0" Opacity="0.36"/>
<DropShadowEffect x:Key="SoftShadow" Color="#000000" BlurRadius="26" ShadowDepth="6" Opacity="0.24"/>
```

Update card styles:

```xml
<Style x:Key="CardBorder" TargetType="Border">
    <Setter Property="Background" Value="{StaticResource NeonCardBrush}"/>
    <Setter Property="BorderBrush" Value="#55FFFFFF"/>
    <Setter Property="BorderThickness" Value="1"/>
    <Setter Property="CornerRadius" Value="24"/>
    <Setter Property="Padding" Value="20"/>
    <Setter Property="Effect" Value="{StaticResource SoftShadow}"/>
</Style>

<Style x:Key="GlassPanel" TargetType="Border" BasedOn="{StaticResource CardBorder}">
    <Setter Property="Background" Value="#22FFFFFF"/>
    <Setter Property="BorderBrush" Value="#66FFFFFF"/>
</Style>
```

- [ ] **Step 4: Build and commit**

Run:

```bash
dotnet build "AutoShutdown/AutoShutdown.csproj"
git add AutoShutdown/Themes/DarkTheme.xaml
git commit -m "Refresh v1.3 glass anime theme"
```

Expected: build succeeds with 0 warnings and 0 errors.

---

### Task 2: Rebuild MainWindow with side navigation

**Files:**
- Modify: `AutoShutdown/MainWindow.xaml`

- [ ] **Step 1: Replace the single-scroll shell**

Rewrite the outer structure of `MainWindow.xaml` to:

```xml
<Window x:Class="AutoShutdown.MainWindow"
        xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Width="900" Height="660"
        WindowStartupLocation="CenterScreen"
        MouseLeftButtonDown="Window_MouseLeftButtonDown">
```

Keep the merged `DarkTheme.xaml` resources.

Inside `RootGrid`, use the app background brush, the three existing glow ellipses, and a main grid with two rows: compact header and content area.

- [ ] **Step 2: Add compact header**

Keep `HeroHeader`, `GlowPurple`, `GlowCyan`, `GlowPink`, minimize and close buttons. Header height should be about 92px and title text should include `v1.3`.

- [ ] **Step 3: Add sidebar navigation**

Create a left sidebar `Border` with six clickable `Border` nav items:

```xml
<Border x:Name="NavOverview" Tag="Overview" MouseLeftButtonDown="NavItem_Click">总览</Border>
<Border x:Name="NavTimer" Tag="Timer" MouseLeftButtonDown="NavItem_Click">定时</Border>
<Border x:Name="NavTasks" Tag="Tasks" MouseLeftButtonDown="NavItem_Click">任务</Border>
<Border x:Name="NavTriggers" Tag="Triggers" MouseLeftButtonDown="NavItem_Click">智能触发</Border>
<Border x:Name="NavScript" Tag="Script" MouseLeftButtonDown="NavItem_Click">脚本</Border>
<Border x:Name="NavSettings" Tag="Settings" MouseLeftButtonDown="NavItem_Click">设置</Border>
```

Use `TextBlock` children rather than emoji icons.

- [ ] **Step 4: Add right content host**

Create `Grid x:Name="ContentPanel"` in the right column. Inside it create six `ScrollViewer` sections:

- `OverviewSection`
- `TimerSection`
- `TasksSection`
- `TriggersSection`
- `ScriptSection`
- `SettingsSection`

Set only `OverviewSection` visible by default. All sections use `VerticalScrollBarVisibility="Auto"`.

- [ ] **Step 5: Move existing cards into sections**

Preserve all existing named controls exactly. Place controls as follows:

- Overview: action selection card, quick countdown buttons, `StatusCard`, `ExecuteCurrentActionButton`.
- Timer: `CountdownPanel`, `FixedTimePanel`, repeat rules, timer mode switch.
- Tasks: task center card and `TaskListPanel`.
- Triggers: network idle card and process exit trigger card.
- Script: pre-action script card.
- Settings: reminder seconds, force close, auto start.

- [ ] **Step 6: Build expectation**

Run:

```bash
dotnet build "AutoShutdown/AutoShutdown.csproj"
```

Expected: build may fail until Task 3 adds `NavItem_Click` and section fields are wired. There should be no XML syntax errors.

Do not commit until Task 3 passes build.

---

### Task 3: Wire section navigation

**Files:**
- Modify: `AutoShutdown/MainWindow.xaml.cs`

- [ ] **Step 1: Add section enum**

Add before `public partial class MainWindow`:

```csharp
public enum UiSection
{
    Overview,
    Timer,
    Tasks,
    Triggers,
    Script,
    Settings
}
```

- [ ] **Step 2: Add current section field**

Add near fields:

```csharp
private UiSection _currentSection = UiSection.Overview;
```

- [ ] **Step 3: Initialize navigation**

At the end of `LoadSettings()`, after `UpdateForceCloseUI();`, add:

```csharp
ShowSection(UiSection.Overview);
```

- [ ] **Step 4: Add nav handler and switching methods**

Add methods before `// === Window Controls ===`:

```csharp
private void NavItem_Click(object sender, MouseButtonEventArgs e)
{
    if (sender is not Border border || border.Tag is not string tag || !Enum.TryParse(tag, out UiSection section))
        return;

    ShowSection(section);
}

private void ShowSection(UiSection section)
{
    _currentSection = section;

    OverviewSection.Visibility = section == UiSection.Overview ? Visibility.Visible : Visibility.Collapsed;
    TimerSection.Visibility = section == UiSection.Timer ? Visibility.Visible : Visibility.Collapsed;
    TasksSection.Visibility = section == UiSection.Tasks ? Visibility.Visible : Visibility.Collapsed;
    TriggersSection.Visibility = section == UiSection.Triggers ? Visibility.Visible : Visibility.Collapsed;
    ScriptSection.Visibility = section == UiSection.Script ? Visibility.Visible : Visibility.Collapsed;
    SettingsSection.Visibility = section == UiSection.Settings ? Visibility.Visible : Visibility.Collapsed;

    UpdateNavigationUI();
    AnimateActiveSection(section);
}

private void UpdateNavigationUI()
{
    foreach (var nav in new[] { NavOverview, NavTimer, NavTasks, NavTriggers, NavScript, NavSettings })
    {
        var isActive = nav.Tag?.ToString() == _currentSection.ToString();
        nav.Background = isActive ? FindResource("HeroBrush") as Brush : new SolidColorBrush(Color.FromArgb(34, 255, 255, 255));
        nav.BorderBrush = isActive ? FindResource("AccentBrush") as Brush : new SolidColorBrush(Color.FromArgb(72, 255, 255, 255));
        nav.Effect = isActive ? FindResource("CyanShadow") as System.Windows.Media.Effects.Effect : null;
    }
}

private void AnimateActiveSection(UiSection section)
{
    var active = section switch
    {
        UiSection.Overview => OverviewSection,
        UiSection.Timer => TimerSection,
        UiSection.Tasks => TasksSection,
        UiSection.Triggers => TriggersSection,
        UiSection.Script => ScriptSection,
        UiSection.Settings => SettingsSection,
        _ => OverviewSection
    };

    active.Opacity = 0;
    active.RenderTransform = new TranslateTransform(0, 12);
    active.BeginAnimation(OpacityProperty, new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(220))
    {
        EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut }
    });
    ((TranslateTransform)active.RenderTransform).BeginAnimation(TranslateTransform.YProperty, new DoubleAnimation(12, 0, TimeSpan.FromMilliseconds(240))
    {
        EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut }
    });
}
```

- [ ] **Step 5: Update entrance animation**

If `ContentPanel` is now a `Grid`, keep the existing `StartEntranceAnimations()` logic valid by leaving `ContentPanel.Opacity` and `ContentPanel.RenderTransform` supported. No business logic changes needed.

- [ ] **Step 6: Build and commit UI shell**

Run:

```bash
dotnet build "AutoShutdown/AutoShutdown.csproj"
git add AutoShutdown/MainWindow.xaml AutoShutdown/MainWindow.xaml.cs
git commit -m "Add v1.3 side navigation layout"
```

Expected: build succeeds with 0 warnings and 0 errors.

---

### Task 4: Polish density and visual states

**Files:**
- Modify: `AutoShutdown/MainWindow.xaml`
- Modify: `AutoShutdown/MainWindow.xaml.cs` if needed

- [ ] **Step 1: Reduce card padding where needed**

For dense cards in Triggers and Settings, use `Padding="18"` or smaller inner margins so content fits comfortably in the new right pane.

- [ ] **Step 2: Ensure common actions are on Overview**

Verify Overview shows:

- selected power action
- quick countdown presets
- status card
- pause/cancel when scheduled
- immediate action button

- [ ] **Step 3: Ensure advanced features are hidden from Overview**

Verify network idle, process trigger, auto-close, scripts, and settings appear only in their own sections.

- [ ] **Step 4: Build and commit polish**

Run:

```bash
dotnet build "AutoShutdown/AutoShutdown.csproj"
git add AutoShutdown/MainWindow.xaml AutoShutdown/MainWindow.xaml.cs AutoShutdown/Themes/DarkTheme.xaml
git commit -m "Polish v1.3 transparent anime UI"
```

Expected: build succeeds with 0 warnings and 0 errors. If there are no source changes, skip the commit.

---

### Task 5: Publish and release v1.3

**Files:**
- Generated only, not committed:
  - `AutoShutdown/publish/`
  - `AutoShutdown/AutoShutdown-v1.3-win-x64.zip`

- [ ] **Step 1: Final build**

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

- [ ] **Step 2: Publish single-file win-x64 build**

Run:

```bash
dotnet publish "AutoShutdown/AutoShutdown.csproj" -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:EnableCompressionInSingleFile=true -o "AutoShutdown/publish"
```

Expected: publish succeeds.

- [ ] **Step 3: Create v1.3 zip**

Run:

```bash
rm -f "AutoShutdown/AutoShutdown-v1.3-win-x64.zip"
powershell.exe -NoProfile -Command "Compress-Archive -Path 'AutoShutdown/publish/*' -DestinationPath 'AutoShutdown/AutoShutdown-v1.3-win-x64.zip' -Force"
```

Expected: zip exists and is ignored by git.

- [ ] **Step 4: Create or update GitHub release**

Run:

```bash
gh release view v1.3 >/dev/null 2>&1
```

If it exists:

```bash
gh release upload v1.3 "AutoShutdown/AutoShutdown-v1.3-win-x64.zip" --clobber
```

If it does not exist:

```bash
gh release create v1.3 "AutoShutdown/AutoShutdown-v1.3-win-x64.zip" --title "AutoShutdown v1.3" --notes "AutoShutdown v1.3 更新：透明轻二次元界面、侧边导航模块化布局、降低主界面臃肿感，并保留 v1.2 的智能触发、任务中心和执行前脚本功能。"
```

- [ ] **Step 5: Push code**

Run:

```bash
git status --short
git push origin main
```

Expected: only ignored publish artifacts remain untracked, or working tree is clean. Code is pushed to GitHub.

---

## Self-Review Notes

- Spec coverage: transparent anime theme is covered by Task 1; side navigation and module split by Tasks 2-3; density polish by Task 4; v1.3 release by Task 5.
- Placeholder scan: no `TBD`, `TODO`, or unspecified implementation steps remain.
- Type consistency: `UiSection` names match nav `Tag` values and section control names.

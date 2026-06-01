# AutoShutdown v1.3.1 EvolveUI/Fluent Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Polish the v1.3 WPF UI using EvolveUI and FluentWinUI3-inspired component patterns, then publish AutoShutdown v1.3.1.

**Architecture:** Keep AutoShutdown as WPF/.NET and do not depend on the Qt/QML `build/` folder. Move visual constants into `DarkTheme.xaml`, update WPF control templates for Fluent-like states, adjust sidebar navigation to use a left active indicator, and keep all business logic/event handlers intact.

**Tech Stack:** WPF, .NET 9, XAML ResourceDictionary, existing `MainWindow.xaml`, `MainWindow.xaml.cs`, `gh` CLI.

---

## File Structure

- Modify `AutoShutdown/Themes/DarkTheme.xaml`
  - Add EvolveUI-like semantic theme brushes.
  - Update Button, TextBox, ComboBox, Card and Glass styles.
- Modify `AutoShutdown/MainWindow.xaml`
  - Replace hardcoded glass colors with semantic resources.
  - Add nav item indicator bars.
  - Add section/group header styling for Trigger cards.
- Modify `AutoShutdown/MainWindow.xaml.cs`
  - Update `UpdateNavigationUI()` to drive nav item indicator bars.
  - Add helper methods for switch/toggle styling to reduce duplicated hardcoded colors.
- Generated but not committed:
  - `AutoShutdown/publish/`
  - `AutoShutdown/AutoShutdown-v1.3.1-win-x64.zip`

---

### Task 1: Add semantic theme resources and Fluent input states

**Files:**
- Modify: `AutoShutdown/Themes/DarkTheme.xaml`

- [ ] **Step 1: Add semantic brushes after existing solid color brushes**

After the existing `StrokeBrush` resource, add:

```xml
<SolidColorBrush x:Key="GlassSurfaceBrush" Color="#22FFFFFF"/>
<SolidColorBrush x:Key="GlassSurfaceHoverBrush" Color="#34FFFFFF"/>
<SolidColorBrush x:Key="GlassSurfacePressedBrush" Color="#18FFFFFF"/>
<SolidColorBrush x:Key="GlassBorderBrush" Color="#55FFFFFF"/>
<SolidColorBrush x:Key="GlassBorderStrongBrush" Color="#88FFFFFF"/>
<SolidColorBrush x:Key="NavItemBrush" Color="#22FFFFFF"/>
<SolidColorBrush x:Key="NavItemHoverBrush" Color="#34FFFFFF"/>
<SolidColorBrush x:Key="NavIndicatorBrush" Color="#79D8FF"/>
<SolidColorBrush x:Key="InputFocusBrush" Color="#79D8FF"/>
<SolidColorBrush x:Key="ToggleOffBrush" Color="#1C1F36"/>
<SolidColorBrush x:Key="ToggleKnobOffBrush" Color="#CDBFEA"/>
```

- [ ] **Step 2: Replace the base Button style with Fluent-inspired state layers**

Replace the existing default `Style TargetType="Button"` block with this complete style:

```xml
<Style TargetType="Button">
    <Setter Property="FontFamily" Value="Microsoft YaHei UI"/>
    <Setter Property="FontSize" Value="14"/>
    <Setter Property="FontWeight" Value="SemiBold"/>
    <Setter Property="Cursor" Value="Hand"/>
    <Setter Property="Padding" Value="16,9"/>
    <Setter Property="MinHeight" Value="36"/>
    <Setter Property="RenderTransformOrigin" Value="0.5,0.5"/>
    <Setter Property="RenderTransform">
        <Setter.Value>
            <ScaleTransform ScaleX="1" ScaleY="1"/>
        </Setter.Value>
    </Setter>
    <Setter Property="Template">
        <Setter.Value>
            <ControlTemplate TargetType="Button">
                <Border x:Name="border"
                        Background="{TemplateBinding Background}"
                        CornerRadius="12"
                        Padding="{TemplateBinding Padding}"
                        BorderBrush="{TemplateBinding BorderBrush}"
                        BorderThickness="{TemplateBinding BorderThickness}">
                    <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                </Border>
                <ControlTemplate.Triggers>
                    <Trigger Property="IsMouseOver" Value="True">
                        <Setter TargetName="border" Property="BorderBrush" Value="{StaticResource GlassBorderStrongBrush}"/>
                        <Setter TargetName="border" Property="Effect" Value="{StaticResource CyanShadow}"/>
                    </Trigger>
                    <Trigger Property="IsPressed" Value="True">
                        <Setter TargetName="border" Property="Opacity" Value="0.86"/>
                        <Setter Property="RenderTransform">
                            <Setter.Value>
                                <ScaleTransform ScaleX="0.99" ScaleY="0.99"/>
                            </Setter.Value>
                        </Setter>
                    </Trigger>
                    <Trigger Property="IsEnabled" Value="False">
                        <Setter TargetName="border" Property="Opacity" Value="0.42"/>
                    </Trigger>
                </ControlTemplate.Triggers>
            </ControlTemplate>
        </Setter.Value>
    </Setter>
</Style>
```

- [ ] **Step 3: Update SecondaryButton colors to theme resources**

Replace `SecondaryButton` with:

```xml
<Style x:Key="SecondaryButton" TargetType="Button" BasedOn="{StaticResource {x:Type Button}}">
    <Setter Property="Background" Value="{StaticResource GlassSurfaceBrush}"/>
    <Setter Property="Foreground" Value="{StaticResource TextPrimaryBrush}"/>
    <Setter Property="BorderBrush" Value="{StaticResource GlassBorderBrush}"/>
    <Setter Property="BorderThickness" Value="1"/>
</Style>
```

- [ ] **Step 4: Replace TextBox template with bottom focus stroke**

Replace the existing default `Style TargetType="TextBox"` block with this complete style:

```xml
<Style TargetType="TextBox">
    <Setter Property="FontFamily" Value="Microsoft YaHei UI"/>
    <Setter Property="FontSize" Value="18"/>
    <Setter Property="FontWeight" Value="SemiBold"/>
    <Setter Property="Background" Value="{StaticResource InputGlowBrush}"/>
    <Setter Property="Foreground" Value="{StaticResource TextPrimaryBrush}"/>
    <Setter Property="BorderBrush" Value="{StaticResource GlassBorderBrush}"/>
    <Setter Property="BorderThickness" Value="1"/>
    <Setter Property="Padding" Value="12,10"/>
    <Setter Property="CaretBrush" Value="{StaticResource AccentBrush}"/>
    <Setter Property="Template">
        <Setter.Value>
            <ControlTemplate TargetType="TextBox">
                <Border x:Name="border"
                        Background="{TemplateBinding Background}"
                        BorderBrush="{TemplateBinding BorderBrush}"
                        BorderThickness="{TemplateBinding BorderThickness}"
                        CornerRadius="12">
                    <Grid>
                        <ScrollViewer x:Name="PART_ContentHost" Margin="{TemplateBinding Padding}"/>
                        <Border x:Name="focusStroke" Height="2" CornerRadius="1" HorizontalAlignment="Stretch" VerticalAlignment="Bottom"
                                Margin="10,0,10,2" Background="{StaticResource InputFocusBrush}" Opacity="0"/>
                    </Grid>
                </Border>
                <ControlTemplate.Triggers>
                    <Trigger Property="IsMouseOver" Value="True">
                        <Setter TargetName="border" Property="BorderBrush" Value="{StaticResource GlassBorderStrongBrush}"/>
                    </Trigger>
                    <Trigger Property="IsKeyboardFocusWithin" Value="True">
                        <Setter TargetName="border" Property="BorderBrush" Value="{StaticResource AccentBrush}"/>
                        <Setter TargetName="focusStroke" Property="Opacity" Value="1"/>
                    </Trigger>
                    <Trigger Property="IsEnabled" Value="False">
                        <Setter TargetName="border" Property="Opacity" Value="0.45"/>
                    </Trigger>
                </ControlTemplate.Triggers>
            </ControlTemplate>
        </Setter.Value>
    </Setter>
</Style>
```

- [ ] **Step 5: Add ComboBox style**

Before `ToggleButton` style, add:

```xml
<Style TargetType="ComboBox">
    <Setter Property="FontFamily" Value="Microsoft YaHei UI"/>
    <Setter Property="FontSize" Value="14"/>
    <Setter Property="Foreground" Value="{StaticResource TextPrimaryBrush}"/>
    <Setter Property="Background" Value="{StaticResource GlassSurfaceBrush}"/>
    <Setter Property="BorderBrush" Value="{StaticResource GlassBorderBrush}"/>
    <Setter Property="BorderThickness" Value="1"/>
    <Setter Property="Padding" Value="10,7"/>
</Style>
```

- [ ] **Step 6: Build and commit**

Run:

```bash
dotnet build "AutoShutdown/AutoShutdown.csproj"
git add AutoShutdown/Themes/DarkTheme.xaml
git commit -m "Add v1.3.1 Fluent theme states"
```

Expected: build succeeds with 0 warnings and 0 errors.

---

### Task 2: Add Fluent sidebar indicators and reduce hardcoded colors

**Files:**
- Modify: `AutoShutdown/MainWindow.xaml`
- Modify: `AutoShutdown/MainWindow.xaml.cs`

- [ ] **Step 1: Replace sidebar nav item content**

In `MainWindow.xaml`, each nav item (`NavOverview`, `NavTimer`, `NavTasks`, `NavTriggers`, `NavScript`, `NavSettings`) should contain a `Grid` with a 3px indicator and text. For example, replace the `NavOverview` child with:

```xml
<Grid>
    <Grid.ColumnDefinitions>
        <ColumnDefinition Width="3"/>
        <ColumnDefinition Width="10"/>
        <ColumnDefinition Width="*"/>
    </Grid.ColumnDefinitions>
    <Border x:Name="NavOverviewIndicator" Width="3" CornerRadius="2" Background="{StaticResource NavIndicatorBrush}" Opacity="0"/>
    <TextBlock Grid.Column="2" Text="总览" FontWeight="Bold" Foreground="{StaticResource TextPrimaryBrush}"/>
</Grid>
```

Repeat the same pattern with these names/text:

- `NavTimerIndicator` / `定时`
- `NavTasksIndicator` / `任务`
- `NavTriggersIndicator` / `智能触发`
- `NavScriptIndicator` / `脚本`
- `NavSettingsIndicator` / `设置`

Keep the existing outer `Border` names, tags, click handlers, padding and margins.

- [ ] **Step 2: Replace obvious glass hardcoded brushes in MainWindow.xaml**

Replace common hardcoded colors:

```xml
BorderBrush="#55FFFFFF"
```

with:

```xml
BorderBrush="{StaticResource GlassBorderBrush}"
```

Replace:

```xml
BorderBrush="#66FFFFFF"
```

with:

```xml
BorderBrush="{StaticResource GlassBorderStrongBrush}"
```

Replace background usages of `#22FFFFFF` that are generic glass surfaces with:

```xml
Background="{StaticResource GlassSurfaceBrush}"
```

Do not replace danger-specific or accent-specific colors such as `#33FF5C8A`, `#AA79D8FF`, or `#2279D8FF`.

- [ ] **Step 3: Update UpdateNavigationUI**

Replace the existing `UpdateNavigationUI()` method with:

```csharp
private void UpdateNavigationUI()
{
    var navItems = new (Border Item, Border Indicator)[]
    {
        (NavOverview, NavOverviewIndicator),
        (NavTimer, NavTimerIndicator),
        (NavTasks, NavTasksIndicator),
        (NavTriggers, NavTriggersIndicator),
        (NavScript, NavScriptIndicator),
        (NavSettings, NavSettingsIndicator)
    };

    foreach (var (item, indicator) in navItems)
    {
        var isActive = item.Tag?.ToString() == _currentSection.ToString();
        item.Background = isActive ? FindResource("GlassSurfaceHoverBrush") as Brush : FindResource("NavItemBrush") as Brush;
        item.BorderBrush = isActive ? FindResource("AccentBrush") as Brush : FindResource("GlassBorderBrush") as Brush;
        item.Effect = isActive ? FindResource("CyanShadow") as System.Windows.Media.Effects.Effect : null;
        indicator.Opacity = isActive ? 1 : 0;
    }
}
```

- [ ] **Step 4: Build and commit**

Run:

```bash
dotnet build "AutoShutdown/AutoShutdown.csproj"
git add AutoShutdown/MainWindow.xaml AutoShutdown/MainWindow.xaml.cs
git commit -m "Add Fluent sidebar indicators"
```

Expected: build succeeds with 0 warnings and 0 errors.

---

### Task 3: Add trigger group headers and toggle helpers

**Files:**
- Modify: `AutoShutdown/MainWindow.xaml`
- Modify: `AutoShutdown/MainWindow.xaml.cs`

- [ ] **Step 1: Add trigger group header accents**

In `TriggersSection`, for the network idle card and process exit card, insert a small header row at the top of each card before the title text:

```xml
<Border Width="38" Height="4" CornerRadius="2" Background="{StaticResource HeroBrush}" HorizontalAlignment="Left" Margin="0,0,0,12"/>
```

This references EAccordion-style group headers without adding risky dynamic collapse behavior.

- [ ] **Step 2: Add toggle helper methods**

In `MainWindow.xaml.cs`, add these methods before `ProcessAutoCloseToggle_Click`:

```csharp
private void ApplyToggleVisual(Border toggle, Border knob, bool isOn, bool useDanger = false)
{
    toggle.Background = isOn
        ? (useDanger ? FindResource("DangerBrush") as Brush : FindResource("HeroBrush") as Brush)
        : FindResource("ToggleOffBrush") as Brush;
    toggle.Effect = isOn
        ? (useDanger ? FindResource("DangerShadow") as System.Windows.Media.Effects.Effect : FindResource("CyanShadow") as System.Windows.Media.Effects.Effect)
        : null;
    knob.HorizontalAlignment = isOn ? System.Windows.HorizontalAlignment.Right : System.Windows.HorizontalAlignment.Left;
    knob.Background = isOn ? Brushes.White : FindResource("ToggleKnobOffBrush") as Brush;
}
```

- [ ] **Step 3: Use helper in UpdateProcessAutoCloseUI**

Replace `UpdateProcessAutoCloseUI()` with:

```csharp
private void UpdateProcessAutoCloseUI()
{
    ApplyToggleVisual(ProcessAutoCloseToggle, ProcessAutoCloseKnob, _settings.ProcessTriggerAutoCloseEnabled);
    ProcessAutoCloseSettingsPanel.Opacity = _settings.ProcessTriggerAutoCloseEnabled ? 1 : 0.45;
    PulseElement(ProcessAutoCloseToggle, 1.03);
}
```

- [ ] **Step 4: Use helper in UpdateForceCloseUI**

Inside `UpdateForceCloseUI()`, replace the long `if (_settings.ForceCloseApps && _shutdown.SupportsForceCloseApps) { ... } else { ... }` visual block with:

```csharp
ApplyToggleVisual(ForceCloseToggle, ForceCloseKnob, _settings.ForceCloseApps && _shutdown.SupportsForceCloseApps, useDanger: true);
PulseElement(ForceCloseToggle, 1.03);
```

Keep the existing `ForceCloseRow.Opacity`, `ForceCloseToggle.IsEnabled`, and `ForceCloseHint.Text` logic.

- [ ] **Step 5: Use helper in UpdateAutoStartUI**

Replace the visual block in `UpdateAutoStartUI()` with:

```csharp
ApplyToggleVisual(AutoStartToggle, AutoStartKnob, _settings.AutoStartEnabled);
PulseElement(AutoStartToggle, 1.03);
```

- [ ] **Step 6: Build and commit**

Run:

```bash
dotnet build "AutoShutdown/AutoShutdown.csproj"
git add AutoShutdown/MainWindow.xaml AutoShutdown/MainWindow.xaml.cs
git commit -m "Polish v1.3.1 grouped controls"
```

Expected: build succeeds with 0 warnings and 0 errors.

---

### Task 4: Publish v1.3.1

**Files:**
- Generated only, not committed:
  - `AutoShutdown/publish/`
  - `AutoShutdown/AutoShutdown-v1.3.1-win-x64.zip`

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

- [ ] **Step 3: Create v1.3.1 zip**

Run:

```bash
rm -f "AutoShutdown/AutoShutdown-v1.3.1-win-x64.zip"
powershell.exe -NoProfile -Command "Compress-Archive -Path 'AutoShutdown/publish/*' -DestinationPath 'AutoShutdown/AutoShutdown-v1.3.1-win-x64.zip' -Force"
```

Expected: zip exists and is ignored by git.

- [ ] **Step 4: Create GitHub release v1.3.1**

Run:

```bash
gh release create v1.3.1 "AutoShutdown/AutoShutdown-v1.3.1-win-x64.zip" --title "AutoShutdown v1.3.1" --notes "AutoShutdown v1.3.1 更新：参考 EvolveUI 与 FluentWinUI3 的组件状态，对透明轻二次元界面进行细节打磨；优化按钮、输入框、侧边导航指示和智能触发分组视觉。"
```

If release already exists, run:

```bash
gh release upload v1.3.1 "AutoShutdown/AutoShutdown-v1.3.1-win-x64.zip" --clobber
```

- [ ] **Step 5: Push code**

Run:

```bash
git status --short
git push origin main
```

Expected: code is pushed; build artifacts remain ignored.

---

## Self-Review Notes

- Spec coverage: ETheme-style semantic resources are covered by Task 1; Fluent Button/TextField/ComboBox by Task 1; ItemDelegate-style sidebar by Task 2; EAccordion-inspired trigger grouping by Task 3; v1.3.1 release by Task 4.
- Placeholder scan: no placeholders or unspecified implementation steps remain.
- Type consistency: nav indicator names match the `UpdateNavigationUI()` tuple list; toggle helper accepts existing WPF `Border` controls.

using System.Drawing;
using System.Windows.Forms;

namespace AutoShutdown.Services;

public class TrayIconService : IDisposable
{
    private readonly NotifyIcon _icon;
    private ToolStripItem? _cancelItem;
    private ToolStripItem? _pauseItem;
    private ToolStripItem? _resumeItem;

    private bool _hasActiveTask;

    public event Action? ShowWindow;
    public event Action? CancelShutdown;
    public event Action? PauseTasks;
    public event Action? ResumeTasks;
    public event Action? ExitApp;

    public TrayIconService()
    {
        _icon = new NotifyIcon
        {
            Text = "智能定时关机",
            Visible = true,
            Icon = CreateTrayIcon()
        };

        var menu = new ContextMenuStrip();
        var showItem = menu.Items.Add("显示主窗口");
        showItem.Click += (_, _) => ShowWindow?.Invoke();
        _cancelItem = menu.Items.Add("取消任务");
        _cancelItem.Click += (_, _) => CancelShutdown?.Invoke();
        _cancelItem.Enabled = false;
        _pauseItem = menu.Items.Add("暂停1小时");
        _pauseItem.Click += (_, _) => PauseTasks?.Invoke();
        _pauseItem.Enabled = false;
        _resumeItem = menu.Items.Add("恢复任务");
        _resumeItem.Click += (_, _) => ResumeTasks?.Invoke();
        _resumeItem.Enabled = false;
        menu.Items.Add(new ToolStripSeparator());
        var exitItem = menu.Items.Add("退出");
        exitItem.Click += (_, _) =>
        {
            _icon.Visible = false;
            ExitApp?.Invoke();
        };

        _icon.ContextMenuStrip = menu;
        _icon.DoubleClick += (_, _) => ShowWindow?.Invoke();
    }

    public void SetShutdownActive(bool active)
    {
        _hasActiveTask = active;
        if (_cancelItem != null)
            _cancelItem.Enabled = active;
        if (_pauseItem != null)
            _pauseItem.Enabled = active;
        if (_resumeItem != null)
            _resumeItem.Enabled = false;
    }

    public void SetPaused(bool paused)
    {
        if (_pauseItem != null)
            _pauseItem.Enabled = _hasActiveTask && !paused;
        if (_resumeItem != null)
            _resumeItem.Enabled = _hasActiveTask && paused;
    }

    public void ShowBalloon(string title, string text)
    {
        _icon.ShowBalloonTip(3000, title, text, ToolTipIcon.Info);
    }

    public void Dispose()
    {
        _icon.Visible = false;
        _icon.Dispose();
    }

    private static Icon CreateTrayIcon()
    {
        var bmp = new Bitmap(32, 32);
        using var g = Graphics.FromImage(bmp);
        g.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;

        // Background circle
        using var bgBrush = new SolidBrush(Color.FromArgb(124, 58, 237));
        g.FillEllipse(bgBrush, 0, 0, 32, 32);

        // Clock face
        using var pen = new Pen(Color.White, 2.5f);
        g.DrawEllipse(pen, 3, 3, 26, 26);

        // Hour hand
        g.DrawLine(pen, 16, 16, 16, 8);

        // Minute hand
        pen.Width = 2f;
        g.DrawLine(pen, 16, 16, 22, 16);

        return Icon.FromHandle(bmp.GetHicon());
    }
}

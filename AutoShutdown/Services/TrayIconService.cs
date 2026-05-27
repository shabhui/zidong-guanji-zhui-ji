using System.Drawing;
using System.Windows.Forms;

namespace AutoShutdown.Services;

public class TrayIconService : IDisposable
{
    private readonly NotifyIcon _icon;
    private ToolStripItem? _cancelItem;

    public event Action? ShowWindow;
    public event Action? CancelShutdown;
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
        _cancelItem = menu.Items.Add("取消关机");
        _cancelItem.Click += (_, _) => CancelShutdown?.Invoke();
        _cancelItem.Enabled = false;
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
        if (_cancelItem != null)
            _cancelItem.Enabled = active;
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

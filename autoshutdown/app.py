"""极简定时关机 —— 单窗口界面。

设计立意「凌晨的台灯」：深靛底色，暖琥珀代表「已定时」。
巨大的等宽数字既是输入框也是倒计时读数，一个元素两种状态。
"""

import tkinter as tk
from datetime import datetime
from pathlib import Path

from power import cancel_shutdown, schedule_shutdown
from shutdown_timer import (
    absolute_target,
    countdown_target,
    describe_target,
    format_remaining,
    split_minutes,
    step_value,
)

# --- 设计令牌 ---------------------------------------------------------------
INK = "#171A2B"        # 底色：夜蓝
SURFACE = "#1F2338"    # 抬起面：时间卡片
LINE = "#2E3350"       # 分隔与描边
PAPER = "#EDEFF7"      # 主文字
MUTED = "#767C9B"      # 次级文字与单位
AMBER = "#FFC24B"      # 已定时的活色
CORAL = "#FF6B5A"      # 取消
PRESETS = ((30, "30 分"), (60, "1 小时"), (120, "2 小时"))

WINDOW_W, WINDOW_H = 420, 580


def _pick_font(root, candidates, size, weight="normal"):
    """挑第一个系统里装了的字体，避免 Windows 上回退成难看的默认值。"""
    from tkinter import font as tkfont

    available = {name.lower() for name in tkfont.families(root)}
    for name in candidates:
        if name.lower() in available:
            return (name, size, weight)
    return ("TkDefaultFont", size, weight)


class RoundButton(tk.Canvas):
    """圆角按钮。tkinter 原生按钮没法做圆角，用 Canvas 画。"""

    def __init__(self, parent, text, command, fill, fg, font, width, height=48):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=INK,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self._command = command
        self._fill = fill
        self._enabled = True
        self._shape = self._rounded(2, 2, width - 2, height - 2, 12, fill)
        self._label = self.create_text(
            width / 2, height / 2, text=text, fill=fg, font=font
        )
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", lambda _e: self._enabled and self._tint(1.12))
        self.bind("<Leave>", lambda _e: self._enabled and self._tint(1.0))

    def _rounded(self, x1, y1, x2, y2, r, fill):
        points = [
            x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
        ]
        return self.create_polygon(points, smooth=True, fill=fill, outline="")

    def _tint(self, factor):
        rgb = [int(self._fill[i : i + 2], 16) for i in (1, 3, 5)]
        shifted = [min(255, int(channel * factor)) for channel in rgb]
        self.itemconfigure(self._shape, fill="#%02x%02x%02x" % tuple(shifted))

    def _on_click(self, _event):
        if self._enabled:
            self._command()

    def configure_style(self, text=None, fill=None, fg=None):
        if text is not None:
            self.itemconfigure(self._label, text=text)
        if fg is not None:
            self.itemconfigure(self._label, fill=fg)
        if fill is not None:
            self._fill = fill
            self.itemconfigure(self._shape, fill=fill)

    def set_enabled(self, enabled):
        self._enabled = enabled
        self.configure(cursor="hand2" if enabled else "arrow")


class ModeSwitch(tk.Canvas):
    """两段式模式切换，滑块在两个标签之间移动。"""

    def __init__(self, parent, labels, command, font, width, height=38):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=INK,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self._command = command
        self._index = 0
        self._seg_w = width / 2
        self._font = font
        self._track = self._rounded(0, 0, width, height, height / 2, SURFACE)
        self._thumb = self._rounded(
            3, 3, self._seg_w - 3, height - 3, (height - 6) / 2, LINE
        )
        self._labels = [
            self.create_text(
                self._seg_w * (i + 0.5), height / 2, text=text, font=font, fill=PAPER
            )
            for i, text in enumerate(labels)
        ]
        self._paint()
        self.bind("<Button-1>", self._on_click)

    def _rounded(self, x1, y1, x2, y2, r, fill):
        points = [
            x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
        ]
        return self.create_polygon(points, smooth=True, fill=fill, outline="")

    def _paint(self):
        offset = self._index * self._seg_w
        height = int(self["height"])
        self.coords(
            self._thumb,
            *self._rounded_points(
                offset + 3, 3, offset + self._seg_w - 3, height - 3, (height - 6) / 2
            ),
        )
        for i, item in enumerate(self._labels):
            self.itemconfigure(item, fill=PAPER if i == self._index else MUTED)

    def _rounded_points(self, x1, y1, x2, y2, r):
        return [
            x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
        ]

    def _on_click(self, event):
        index = 0 if event.x < self._seg_w else 1
        if index != self._index:
            self.select(index)
            self._command(index)

    def select(self, index):
        self._index = index
        self._paint()


class ShutdownApp:
    """定时关机主窗口。"""

    def __init__(self, root):
        self.root = root
        self.mode = 0            # 0 = 倒计时, 1 = 指定时刻
        self.target = None       # 已定时的关机时刻
        self.blink = True
        self._tick_job = None

        self.f_display = _pick_font(
            root, ("Cascadia Mono", "Consolas", "DengXian"), 56
        )
        self.f_colon = _pick_font(root, ("Cascadia Mono", "Consolas"), 34)
        self.f_unit = _pick_font(root, ("Microsoft YaHei UI", "Segoe UI"), 10)
        self.f_body = _pick_font(root, ("Microsoft YaHei UI", "Segoe UI"), 11)
        self.f_action = _pick_font(root, ("Microsoft YaHei UI", "Segoe UI"), 13, "bold")

        root.title("定时关机")
        root.configure(bg=INK)
        root.resizable(False, False)
        self._center(WINDOW_W, WINDOW_H)

        self._build()
        self._refresh_idle_display()

    def _center(self, width, height):
        x = (self.root.winfo_screenwidth() - width) // 2
        y = (self.root.winfo_screenheight() - height) // 3
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    # --- 构建 ---------------------------------------------------------------
    def _build(self):
        pad = 32
        body = tk.Frame(self.root, bg=INK)
        body.pack(fill="both", expand=True, padx=pad, pady=(28, 24))
        inner_w = WINDOW_W - pad * 2

        self.switch = ModeSwitch(
            body,
            ("倒计时", "指定时刻"),
            self._on_mode_change,
            self.f_body,
            inner_w,
        )
        self.switch.pack()

        self.card = tk.Frame(body, bg=SURFACE)
        self.card.pack(fill="x", pady=(22, 0))
        self._build_card(inner_w)

        self.presets = tk.Frame(body, bg=INK)
        self.presets.pack(fill="x", pady=(20, 0))
        self._build_presets(inner_w)

        self.action = RoundButton(
            body,
            "开始",
            self._on_action,
            AMBER,
            INK,
            self.f_action,
            inner_w,
            height=50,
        )
        self.action.pack(pady=(22, 0))

        self.status = tk.Label(
            body,
            text="",
            bg=INK,
            fg=MUTED,
            font=self.f_body,
            wraplength=inner_w,
            justify="center",
        )
        self.status.pack(pady=(16, 0))

    def _build_card(self, inner_w):
        row = tk.Frame(self.card, bg=SURFACE)
        row.pack(pady=(30, 26))

        self.left = self._digit_entry(row, 1, 23)
        self.left.grid(row=0, column=0)
        self.colon = tk.Label(
            row, text=":", bg=SURFACE, fg=MUTED, font=self.f_colon
        )
        self.colon.grid(row=0, column=1, padx=6)
        self.right = self._digit_entry(row, 30, 59)
        self.right.grid(row=0, column=2)

        # 单位标签放进同一个 grid 的第二行，列宽自动继承数字，对齐不用算。
        self.unit_left = tk.Label(
            row, text="小时", bg=SURFACE, fg=MUTED, font=self.f_unit
        )
        self.unit_left.grid(row=1, column=0, sticky="ew", pady=(0, 2))
        self.unit_right = tk.Label(
            row, text="分钟", bg=SURFACE, fg=MUTED, font=self.f_unit
        )
        self.unit_right.grid(row=1, column=2, sticky="ew", pady=(0, 2))

    def _digit_entry(self, parent, initial, maximum):
        """大号数字既是显示也是输入框，滚轮和方向键都能调。"""
        var = tk.StringVar(value=f"{initial:02d}")
        entry = tk.Entry(
            parent,
            textvariable=var,
            font=self.f_display,
            width=2,
            bg=SURFACE,
            fg=PAPER,
            insertbackground=AMBER,
            relief="flat",
            justify="center",
            highlightthickness=0,
            bd=0,
        )
        entry.var = var
        entry.maximum = maximum
        entry.bind("<MouseWheel>", lambda e: self._on_wheel(entry, e))
        entry.bind("<Up>", lambda _e: self._step(entry, 1))
        entry.bind("<Down>", lambda _e: self._step(entry, -1))
        entry.bind("<FocusOut>", lambda _e: self._normalize(entry))
        entry.bind("<Return>", lambda _e: self._on_action())
        return entry

    def _current(self, entry):
        try:
            return int(entry.var.get())
        except ValueError:
            return 0

    def _on_wheel(self, entry, event):
        if self.target is None:
            self._step(entry, 1 if event.delta > 0 else -1)

    def _step(self, entry, delta):
        entry.var.set(f"{step_value(self._current(entry), delta, entry.maximum):02d}")
        self._refresh_idle_display()

    def _normalize(self, entry):
        value = min(max(self._current(entry), 0), entry.maximum)
        entry.var.set(f"{value:02d}")
        self._refresh_idle_display()

    def _build_presets(self, inner_w):
        gap = 8
        chip_w = (inner_w - gap * (len(PRESETS) - 1)) / len(PRESETS)
        self.chips = []
        for index, (minutes, label) in enumerate(PRESETS):
            chip = RoundButton(
                self.presets,
                label,
                lambda m=minutes: self._apply_preset(m),
                LINE,
                PAPER,
                self.f_body,
                int(chip_w),
                height=38,
            )
            chip.grid(row=0, column=index, padx=(0 if index == 0 else gap, 0))
            self.chips.append(chip)

    def _apply_preset(self, minutes):
        if self.target is not None:
            return
        if self.mode == 1:
            self.switch.select(0)
            self._on_mode_change(0)
        hours, mins = split_minutes(minutes)
        self.left.var.set(f"{hours:02d}")
        self.right.var.set(f"{mins:02d}")
        self._refresh_idle_display()

    def _on_mode_change(self, index):
        self.mode = index
        if index == 0:
            self.left.maximum, self.right.maximum = 23, 59
            self.unit_left.configure(text="小时")
            self.unit_right.configure(text="分钟")
            self.left.var.set("01")
            self.right.var.set("30")
        else:
            self.left.maximum, self.right.maximum = 23, 59
            self.unit_left.configure(text="时")
            self.unit_right.configure(text="分")
            now = datetime.now()
            self.left.var.set(f"{now.hour:02d}")
            self.right.var.set("30")
        self._refresh_idle_display()

    def _refresh_idle_display(self):
        """未定时状态下，状态行预告这次会关在什么时候。"""
        if self.target is not None:
            return
        now = datetime.now()
        try:
            target = self._compute_target(now)
        except ValueError as exc:
            self.status.configure(text=str(exc), fg=CORAL)
            return
        # 大数字已经说明「多久」，状态行只说「何时」，避免重复。
        self.status.configure(text=f"将在{describe_target(target, now)}", fg=MUTED)

    def _compute_target(self, now):
        left, right = self._current(self.left), self._current(self.right)
        if self.mode == 0:
            return countdown_target(now, left, right)
        return absolute_target(now, left, right)

    # --- 定时与取消 ----------------------------------------------------------
    def _on_action(self):
        if self.target is None:
            self._arm()
        else:
            self._disarm()

    def _arm(self):
        now = datetime.now()
        try:
            target = self._compute_target(now)
        except ValueError as exc:
            self.status.configure(text=str(exc), fg=CORAL)
            return
        ok, message = schedule_shutdown((target - now).total_seconds())
        if not ok:
            self.status.configure(text=f"定时失败：{message}", fg=CORAL)
            return
        self.target = target
        self._enter_armed_look()
        self._tick()

    def _disarm(self):
        ok, message = cancel_shutdown()
        if not ok:
            self.status.configure(text=f"取消失败：{message}", fg=CORAL)
            return
        self.target = None
        if self._tick_job is not None:
            self.root.after_cancel(self._tick_job)
            self._tick_job = None
        self._exit_armed_look()
        self._refresh_idle_display()

    def _enter_armed_look(self):
        self.action.configure_style(text="取消", fill=CORAL, fg=PAPER)
        self.switch.configure(cursor="arrow")
        for entry in (self.left, self.right):
            entry.configure(state="readonly", readonlybackground=SURFACE, fg=AMBER)
        self.colon.configure(fg=AMBER)
        for chip in self.chips:
            chip.set_enabled(False)
            chip.configure_style(fg=MUTED)

    def _exit_armed_look(self):
        self.action.configure_style(text="开始", fill=AMBER, fg=INK)
        self.switch.configure(cursor="hand2")
        for entry in (self.left, self.right):
            entry.configure(state="normal", fg=PAPER)
        self.colon.configure(fg=MUTED)
        for chip in self.chips:
            chip.set_enabled(True)
            chip.configure_style(fg=PAPER)
        self._on_mode_change(self.mode)

    def _tick(self):
        """每秒刷新：大数字变倒数，冒号脉冲。"""
        if self.target is None:
            return
        remaining = (self.target - datetime.now()).total_seconds()
        if remaining <= 0:
            self.status.configure(text="正在关机…", fg=AMBER)
            return

        if remaining >= 3600:
            hours, mins = divmod(int(remaining) // 60, 60)
            self.unit_left.configure(text="小时")
            self.unit_right.configure(text="分钟")
        elif remaining >= 60:
            hours, mins = divmod(int(remaining), 60)
            self.unit_left.configure(text="分")
            self.unit_right.configure(text="秒")
        else:
            hours, mins = 0, int(remaining)
            self.unit_left.configure(text="分")
            self.unit_right.configure(text="秒")

        self.left.var.set(f"{hours:02d}")
        self.right.var.set(f"{mins:02d}")
        self.blink = not self.blink
        self.colon.configure(fg=AMBER if self.blink else LINE)
        self.status.configure(
            text=f"已定 · {describe_target(self.target, datetime.now())}", fg=AMBER
        )
        self._tick_job = self.root.after(1000, self._tick)


def main():
    # Windows 高 DPI：不声明会被系统拉伸成模糊的。
    try:
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    root = tk.Tk()
    icon = Path(__file__).with_name("app_icon.ico")
    if icon.exists():
        try:
            root.iconbitmap(str(icon))
        except tk.TclError:
            pass
    app = ShutdownApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: _on_close(root, app))
    root.mainloop()


def _on_close(root, app):
    """关窗不取消已排定的关机，交给系统继续计时。"""
    if app._tick_job is not None:
        root.after_cancel(app._tick_job)
    root.destroy()


if __name__ == "__main__":
    main()


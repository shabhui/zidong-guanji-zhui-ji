"""定时关机的纯逻辑：目标时刻计算与文案格式化。

这一层不碰界面、不碰系统调用，便于直接用 unittest 覆盖。
"""

from datetime import datetime, timedelta


def countdown_target(now: datetime, hours: int, minutes: int) -> datetime:
    """按「从现在起 N 小时 M 分」算出关机时刻。"""
    total = hours * 60 + minutes
    if total <= 0:
        raise ValueError("倒计时至少要 1 分钟")
    return now + timedelta(minutes=total)


def absolute_target(now: datetime, hour: int, minute: int) -> datetime:
    """按「指定时刻」算出关机时刻，已过则顺延到明天。"""
    if not 0 <= hour <= 23:
        raise ValueError("小时需在 0 到 23 之间")
    if not 0 <= minute <= 59:
        raise ValueError("分钟需在 0 到 59 之间")
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return target


def format_remaining(seconds: float) -> str:
    """把剩余秒数写成人能一眼看懂的文案。"""
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours} 小时 {minutes} 分"
    if minutes:
        return f"{minutes} 分 {secs} 秒"
    return f"{secs} 秒"


def step_value(value: int, delta: int, maximum: int) -> int:
    """滚轮/方向键步进，越界时回绕到另一端。"""
    if not 0 <= value <= maximum:
        value = 0
    return (value + delta) % (maximum + 1)


def split_minutes(total_minutes: int) -> tuple:
    """把预设的总分钟拆成 (小时, 分钟)。"""
    return divmod(total_minutes, 60)


def describe_target(target: datetime, now: datetime) -> str:
    """描述关机时刻，跨天时标注「明天」。"""
    day_gap = (target.date() - now.date()).days
    prefix = {0: "今天", 1: "明天"}.get(day_gap, target.strftime("%m-%d"))
    return f"{prefix} {target:%H:%M} 关机"

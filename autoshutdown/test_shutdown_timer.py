"""极简定时关机工具的核心逻辑测试。"""

import unittest
from datetime import datetime

from shutdown_timer import (
    absolute_target,
    countdown_target,
    describe_target,
    format_remaining,
    split_minutes,
    step_value,
)


class CountdownTargetTests(unittest.TestCase):
    def test_adds_hours_and_minutes_to_now(self):
        now = datetime(2026, 8, 27, 15, 0)
        self.assertEqual(countdown_target(now, 1, 30), datetime(2026, 8, 27, 16, 30))

    def test_crosses_midnight(self):
        now = datetime(2026, 8, 27, 23, 40)
        self.assertEqual(countdown_target(now, 0, 30), datetime(2026, 8, 28, 0, 10))

    def test_rejects_zero_duration(self):
        with self.assertRaises(ValueError):
            countdown_target(datetime(2026, 8, 27, 15, 0), 0, 0)

    def test_rejects_negative_duration(self):
        with self.assertRaises(ValueError):
            countdown_target(datetime(2026, 8, 27, 15, 0), -1, 0)


class AbsoluteTargetTests(unittest.TestCase):
    def test_uses_today_when_time_still_ahead(self):
        now = datetime(2026, 8, 27, 15, 0)
        self.assertEqual(absolute_target(now, 23, 30), datetime(2026, 8, 27, 23, 30))

    def test_rolls_to_tomorrow_when_time_already_passed(self):
        now = datetime(2026, 8, 27, 23, 45)
        self.assertEqual(absolute_target(now, 6, 0), datetime(2026, 8, 28, 6, 0))

    def test_rolls_to_tomorrow_when_time_is_exactly_now(self):
        now = datetime(2026, 8, 27, 15, 0)
        self.assertEqual(absolute_target(now, 15, 0), datetime(2026, 8, 28, 15, 0))

    def test_rejects_hour_out_of_range(self):
        with self.assertRaises(ValueError):
            absolute_target(datetime(2026, 8, 27, 15, 0), 24, 0)

    def test_rejects_minute_out_of_range(self):
        with self.assertRaises(ValueError):
            absolute_target(datetime(2026, 8, 27, 15, 0), 10, 60)


class FormatRemainingTests(unittest.TestCase):
    def test_shows_hours_and_minutes(self):
        self.assertEqual(format_remaining(8 * 3600 + 12 * 60), "8 小时 12 分")

    def test_shows_minutes_and_seconds_under_one_hour(self):
        self.assertEqual(format_remaining(12 * 60 + 30), "12 分 30 秒")

    def test_shows_seconds_only_under_one_minute(self):
        self.assertEqual(format_remaining(9), "9 秒")

    def test_floors_at_zero(self):
        self.assertEqual(format_remaining(-5), "0 秒")


class DescribeTargetTests(unittest.TestCase):
    def test_labels_same_day_target_as_today(self):
        now = datetime(2026, 8, 27, 15, 0)
        target = datetime(2026, 8, 27, 23, 30)
        self.assertEqual(describe_target(target, now), "今天 23:30 关机")

    def test_labels_next_day_target_as_tomorrow(self):
        now = datetime(2026, 8, 27, 23, 45)
        target = datetime(2026, 8, 28, 6, 0)
        self.assertEqual(describe_target(target, now), "明天 06:00 关机")


class StepValueTests(unittest.TestCase):
    def test_increments_within_range(self):
        self.assertEqual(step_value(30, 1, 59), 31)

    def test_wraps_past_maximum_back_to_zero(self):
        self.assertEqual(step_value(59, 1, 59), 0)

    def test_wraps_below_zero_to_maximum(self):
        self.assertEqual(step_value(0, -1, 59), 59)

    def test_resets_out_of_range_input_then_steps(self):
        self.assertEqual(step_value(99, 1, 23), 1)


class SplitMinutesTests(unittest.TestCase):
    def test_splits_into_hours_and_minutes(self):
        self.assertEqual(split_minutes(150), (2, 30))

    def test_keeps_sub_hour_values_in_minutes(self):
        self.assertEqual(split_minutes(30), (0, 30))


if __name__ == "__main__":
    unittest.main()

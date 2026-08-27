"""关机命令构造的测试，用假执行器避免真的关机。"""

import unittest

from power import cancel_shutdown, schedule_shutdown


class FakeRunner:
    """记录收到的命令，模拟 subprocess 的返回码。"""

    def __init__(self, returncode=0, stderr=""):
        self.calls = []
        self.returncode = returncode
        self.stderr = stderr

    def __call__(self, args):
        self.calls.append(args)
        return self.returncode, self.stderr


class ScheduleShutdownTests(unittest.TestCase):
    def test_passes_delay_in_seconds_to_windows(self):
        runner = FakeRunner()
        schedule_shutdown(90, runner=runner)
        self.assertEqual(runner.calls, [["shutdown.exe", "/s", "/t", "90"]])

    def test_rounds_fractional_seconds_up(self):
        runner = FakeRunner()
        schedule_shutdown(59.4, runner=runner)
        self.assertEqual(runner.calls[0][-1], "60")

    def test_clamps_negative_delay_to_zero(self):
        runner = FakeRunner()
        schedule_shutdown(-10, runner=runner)
        self.assertEqual(runner.calls[0][-1], "0")

    def test_returns_true_on_success(self):
        self.assertIs(schedule_shutdown(60, runner=FakeRunner())[0], True)

    def test_returns_false_and_message_on_failure(self):
        runner = FakeRunner(returncode=1, stderr="拒绝访问")
        ok, message = schedule_shutdown(60, runner=runner)
        self.assertIs(ok, False)
        self.assertIn("拒绝访问", message)


class CancelShutdownTests(unittest.TestCase):
    def test_sends_abort_flag(self):
        runner = FakeRunner()
        cancel_shutdown(runner=runner)
        self.assertEqual(runner.calls, [["shutdown.exe", "/a"]])

    def test_treats_no_pending_shutdown_as_success(self):
        # 没有待执行的关机时 shutdown /a 返回 1116，不该当成错误。
        runner = FakeRunner(returncode=1116, stderr="无法中止系统关机")
        self.assertIs(cancel_shutdown(runner=runner)[0], True)


if __name__ == "__main__":
    unittest.main()

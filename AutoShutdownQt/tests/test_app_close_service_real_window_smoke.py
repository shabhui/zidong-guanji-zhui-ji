import os
import subprocess
import sys
import time
import unittest
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "AutoShutdownQt"
sys.path.insert(0, str(APP_DIR))

from app_close_service import WindowsAppCloser


@unittest.skipUnless(sys.platform == "win32", "Windows-only smoke test")
@unittest.skipUnless(
    os.environ.get("AUTOSHUTDOWNQT_REAL_WINDOW_SMOKE") == "1",
    "set AUTOSHUTDOWNQT_REAL_WINDOW_SMOKE=1 to open a real temporary window",
)
class RealWindowCloseSmokeTest(unittest.TestCase):
    def test_windows_app_closer_closes_throwaway_tk_window(self):
        title = f"AutoShutdownQt smoke {uuid4()}"
        script = (
            "import tkinter as tk\n"
            "root = tk.Tk()\n"
            f"root.title({title!r})\n"
            "root.geometry('260x80+80+80')\n"
            "root.mainloop()\n"
        )
        process = subprocess.Popen([sys.executable, "-c", script])
        closer = WindowsAppCloser(own_pid=os.getpid())
        try:
            window = self._wait_for_window(closer, title)

            self.assertTrue(closer.request_close(window))
            process.wait(timeout=5)

            self.assertNotEqual(process.poll(), None)
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)

    def _wait_for_window(self, closer, title):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            for window in closer.list_app_windows():
                if window.title == title:
                    return window
            time.sleep(0.1)
        self.fail(f"temporary window not found: {title}")


if __name__ == "__main__":
    unittest.main()

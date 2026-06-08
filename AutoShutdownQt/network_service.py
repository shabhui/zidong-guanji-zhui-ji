from dataclasses import dataclass
import re
import subprocess
import time


@dataclass
class NetworkSample:
    available: bool
    received_bytes: int = 0
    sent_bytes: int = 0
    monotonic_seconds: float = 0.0
    message: str = ""


@dataclass
class NetworkSpeed:
    available: bool
    download_kbps: float = 0.0
    upload_kbps: float = 0.0
    elapsed_seconds: float = 0.0
    message: str = ""


def compute_speed(previous, current):
    if not previous.available or not current.available:
        return NetworkSpeed(
            False,
            message=current.message or previous.message or "网络不可用",
        )
    received_delta = current.received_bytes - previous.received_bytes
    sent_delta = current.sent_bytes - previous.sent_bytes
    if received_delta < 0 or sent_delta < 0:
        return NetworkSpeed(False, message="网络计数已重置")
    elapsed = max(0.001, current.monotonic_seconds - previous.monotonic_seconds)
    return NetworkSpeed(
        True,
        download_kbps=received_delta / 1024 / elapsed,
        upload_kbps=sent_delta / 1024 / elapsed,
        elapsed_seconds=elapsed,
    )


class NetworkReader:
    def sample(self):
        try:
            completed = subprocess.run(
                ["netstat", "-e"],
                capture_output=True,
                text=True,
                timeout=4,
                check=False,
            )
        except Exception as exc:
            return NetworkSample(False, monotonic_seconds=time.monotonic(), message=str(exc))
        if completed.returncode != 0:
            message = (completed.stderr or completed.stdout).strip()
            return NetworkSample(
                False,
                monotonic_seconds=time.monotonic(),
                message=message or f"网络计数命令退出码 {completed.returncode}",
            )
        parsed = self._parse_netstat_bytes(completed.stdout)
        if parsed is None:
            return NetworkSample(
                False,
                monotonic_seconds=time.monotonic(),
                message="无法读取网络计数",
            )
        received, sent = parsed
        return NetworkSample(
            True,
            received_bytes=received,
            sent_bytes=sent,
            monotonic_seconds=time.monotonic(),
        )

    def _parse_netstat_bytes(self, output):
        for line in output.splitlines():
            lower = line.lower()
            if "bytes" not in lower and "字节" not in line and "位元组" not in line:
                continue
            numbers = [int(match.replace(",", "")) for match in re.findall(r"\d[\d,]*", line)]
            if len(numbers) >= 2:
                return numbers[0], numbers[1]
        return None

from dataclasses import dataclass
import subprocess


@dataclass
class ScriptResult:
    ok: bool
    message: str
    stdout: str = ""
    stderr: str = ""
    returncode: int | None = None


def run_script(path: str, timeout_seconds: int) -> ScriptResult:
    clean_path = (path or "").strip()
    if not clean_path:
        return ScriptResult(False, "脚本路径为空")

    try:
        completed = subprocess.run(
            clean_path,
            shell=True,
            capture_output=True,
            text=True,
            timeout=max(1, int(timeout_seconds or 1)),
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return ScriptResult(
            False,
            f"脚本超时（{timeout_seconds} 秒）",
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
            returncode=None,
        )
    except Exception as exc:
        return ScriptResult(False, f"脚本启动失败：{exc}")

    if completed.returncode == 0:
        return ScriptResult(True, "脚本执行成功", completed.stdout, completed.stderr, completed.returncode)
    return ScriptResult(
        False,
        f"脚本失败：exit {completed.returncode}",
        completed.stdout,
        completed.stderr,
        completed.returncode,
    )

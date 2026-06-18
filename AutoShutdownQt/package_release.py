from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile

VERSION = "3.2"
APP_DISPLAY_NAME = "定时关机助手"
APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
SPEC_FILE = APP_DIR / f"AutoShutdownQt-{VERSION}.spec"
INNO_SCRIPT = APP_DIR / f"AutoShutdownQt-{VERSION}.iss"
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build" / "pyinstaller"
APP_BUNDLE_NAME = f"{APP_DISPLAY_NAME}-{VERSION}"
APP_BUNDLE_DIR = DIST_DIR / APP_BUNDLE_NAME
ZIP_PATH = DIST_DIR / f"{APP_BUNDLE_NAME}.zip"
SETUP_PATH = DIST_DIR / f"{APP_BUNDLE_NAME}-Setup.exe"
SHA256SUMS_PATH = DIST_DIR / "SHA256SUMS.txt"
RELEASE_CHECKLIST_PATH = DIST_DIR / f"release-checklist-v{VERSION}.md"
REQUIRED_EXE = f"{APP_BUNDLE_NAME}/定时关机助手.exe"
REQUIRED_MANIFEST = f"{APP_BUNDLE_NAME}/release-manifest.json"
UNUSED_QT_PAYLOAD_MARKERS = (
    "/PySide6/Qt6Quick3D",
    "/PySide6/Qt6VirtualKeyboard",
    "/PySide6/Qt6WebEngine",
    "/PySide6/Qt6Pdf",
    "/PySide6/Qt63D",
    "/PySide6/Qt6Charts",
    "/PySide6/Qt6Graphs",
    "/PySide6/Qt6DataVisualization",
    "/PySide6/Qt6Location",
    "/PySide6/Qt6TextToSpeech",
    "/PySide6/Qt6WebChannel",
    "/PySide6/Qt6WebSockets",
    "/PySide6/Qt6WebView",
    "/PySide6/qml/QtQuick/VirtualKeyboard/",
    "/PySide6/qml/QtQuick3D/",
    "/PySide6/qml/Qt3D/",
    "/PySide6/qml/QtCharts/",
    "/PySide6/qml/QtDataVisualization/",
    "/PySide6/qml/QtGraphs/",
    "/PySide6/qml/QtLocation/",
    "/PySide6/qml/QtMultimedia/SpatialAudio/",
    "/PySide6/qml/QtPositioning/",
    "/PySide6/qml/QtQuick/Pdf/",
    "/PySide6/qml/QtQuick3DPhysics/",
    "/PySide6/qml/QtWebEngine/",
    "/PySide6/qml/QtTextToSpeech/",
    "/PySide6/qml/QtWebChannel/",
    "/PySide6/qml/QtWebSockets/",
    "/PySide6/qml/QtWebView/",
)
QML_PREFIXES = (
    f"{APP_BUNDLE_NAME}/_internal/qml/",
    f"{APP_BUNDLE_NAME}/qml/",
)
REQUIRED_MAIN_QMLS = tuple(f"{prefix}Main.qml" for prefix in QML_PREFIXES)


def root_mp3_files(root=ROOT):
    return sorted(path for path in Path(root).iterdir() if path.is_file() and path.suffix.lower() == ".mp3")


def copy_bundled_music(root=ROOT, bundle_dir=APP_BUNDLE_DIR):
    bundle = Path(bundle_dir)
    copied = []
    for source in root_mp3_files(root):
        target = bundle / source.name
        shutil.copy2(source, target)
        copied.append(target)
    return copied


def run_pyinstaller():
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(BUILD_DIR),
        str(SPEC_FILE),
    ]
    subprocess.run(command, cwd=ROOT, check=True)


def _is_unused_qt_payload(path_text):
    normalized = path_text.replace("\\", "/")
    return any(marker in normalized for marker in UNUSED_QT_PAYLOAD_MARKERS)


def prune_unused_qt_payload(bundle_dir=APP_BUNDLE_DIR):
    bundle = Path(bundle_dir)
    removed = 0
    for path in sorted(bundle.rglob("*"), reverse=True):
        if path.is_file() and _is_unused_qt_payload(str(path.relative_to(bundle))):
            path.unlink()
            removed += 1
    for path in sorted((p for p in bundle.rglob("*") if p.is_dir()), reverse=True):
        try:
            path.rmdir()
        except OSError:
            pass
    return removed


def create_release_manifest(bundle_dir=APP_BUNDLE_DIR):
    bundle = Path(bundle_dir)
    main_qml_candidates = [bundle / "_internal" / "qml" / "Main.qml", bundle / "qml" / "Main.qml"]
    manifest = {
        "app": "定时关机助手",
        "version": VERSION,
        "bundle": APP_BUNDLE_NAME,
        "executable": "定时关机助手.exe",
        "archive": ZIP_PATH.name,
        "checks": {
            "executablePresent": (bundle / "定时关机助手.exe").exists(),
            "mainQmlPresent": any(path.exists() for path in main_qml_candidates),
            "taskSchedulerIncluded": True,
            "bundledMusicPresent": bool(root_mp3_files(bundle)),
            "appCloseServiceHiddenImport": spec_includes_hidden_import("app_close_service"),
            "diagnosticsCenterWired": qml_contains_all(
                "controller.copyDiagnostics()",
                "controller.diagnosticText",
                "controller.safetySummaryText",
                "controller.triggerHealthSummaryText",
                "controller.logCategorySummaryText",
            ),
            "supportWorkflowWired": qml_contains_all(
                "controller.copyStatusText",
                "controller.runHealthCheck()",
                "controller.healthCheckText",
                'controller.setLogFilter("all")',
                'controller.setLogFilter("warning")',
                'controller.setLogFilter("error")',
                "controller.filteredLogText",
            ),
            "failedQueueRecoveryWired": qml_contains_all(
                "controller.retryQueueTask(modelData.id)",
                "controller.copyQueueTaskDiagnostic(modelData.id)",
                'modelData.status === "failed"',
                "modelData.lastError",
            ),
        },
        "safetyNotes": [
            "默认开启安全验证模式。",
            "真实执行模式会调用 Windows 电源动作。",
            "任务队列与托盘后台调度仅保存在本机。",
            "便携版 exe 暂未进行代码签名。",
        ],
    }
    target = bundle / "release-manifest.json"
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def qml_contains_all(*snippets, qml_path=APP_DIR / "qml"):
    try:
        qml_target = Path(qml_path)
        if qml_target.is_dir():
            qml = "\n".join(
                path.read_text(encoding="utf-8")
                for path in sorted(qml_target.rglob("*.qml"))
            )
        else:
            qml = qml_target.read_text(encoding="utf-8")
    except OSError:
        return False
    return all(snippet in qml for snippet in snippets)


def spec_includes_hidden_import(module_name, spec_file=SPEC_FILE):
    try:
        spec = Path(spec_file).read_text(encoding="utf-8")
    except OSError:
        return False
    return f'"{module_name}"' in spec or f"'{module_name}'" in spec


def inno_compiler_candidates():
    candidates = [Path("ISCC.exe"), Path("iscc")]
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidates.append(Path(local_app_data) / "Programs" / "Inno Setup 6" / "ISCC.exe")
    candidates.extend(
        [
            Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Inno Setup 6" / "ISCC.exe",
            Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Inno Setup 6" / "ISCC.exe",
        ]
    )
    return candidates


def build_inno_installer():
    last_error = None
    for executable in inno_compiler_candidates():
        try:
            subprocess.run([str(executable), str(INNO_SCRIPT)], cwd=ROOT, check=True)
            return SETUP_PATH
        except FileNotFoundError as exc:
            last_error = exc
        except subprocess.CalledProcessError:
            raise
    raise RuntimeError("Inno Setup compiler not found. Install Inno Setup and ensure ISCC.exe is on PATH.") from last_error


def create_sha256sums(artifact_paths=ZIP_PATH, target_path=SHA256SUMS_PATH):
    if isinstance(artifact_paths, (str, Path)):
        paths = [Path(artifact_paths)]
    else:
        paths = [Path(path) for path in artifact_paths]
    target = Path(target_path)
    lines = []
    for artifact in paths:
        with artifact.open("rb") as file:
            digest = hashlib.file_digest(file, "sha256").hexdigest()
        lines.append(f"{digest}  {artifact.name}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def create_release_checklist(target_path=RELEASE_CHECKLIST_PATH):
    target = Path(target_path)
    target.write_text(
        f"# 定时关机助手 {VERSION} 发布检查清单\n\n"
        "- [ ] 启动应用后确认默认开启安全验证模式。\n"
        "- [ ] 验证指挥中心安全状态条展示安全验证/真实执行状态、当前动作、托盘状态和队列数量。\n"
        "- [ ] 验证队列健康在空队列和有任务时都保持清晰可读。\n"
        "- [ ] 验证设置页可见并可配置执行前提醒。\n"
        "- [ ] 验证 1 分钟倒计时会显示执行前提醒弹窗。\n"
        "- [ ] 验证提醒弹窗能区分安全验证模式和真实执行模式。\n"
        "- [ ] 验证默认延后会延长当前队列任务且不会重复提醒。\n"
        "- [ ] 验证每个队列任务都有独立提醒阈值。\n"
        "- [ ] 验证任务队列面板的空状态和有任务状态。\n"
        "- [ ] 验证最近活动展示日志以及导出、清空控件。\n"
        "- [ ] 验证 Windows 原生通知兜底不会遮蔽应用内提醒。\n"
        "- [ ] 验证全新配置下首次启动安全说明只出现一次。\n"
        "- [ ] 验证首次关闭到托盘会显示后台运行提示且只出现一次。\n"
        "- [ ] 验证真实执行模式下立即执行前的风险提示清晰可见。\n"
        "- [ ] 验证任务历史记录创建、延后、取消和安全验证执行事件。\n"
        "- [ ] 验证任务历史支持清空和 JSON 导出。\n"
        "- [ ] 验证开机启动选项会写入或移除当前用户 Run 项。\n"
        "- [ ] 验证右下角托盘图标可见时关闭按钮只隐藏窗口。\n"
        "- [ ] 验证双击托盘图标可恢复窗口，托盘菜单“退出程序”可彻底退出。\n"
        "- [ ] 验证空闲自动关机可配置空闲分钟、轮询秒数和动作。\n"
        "- [ ] 验证空闲队列任务出现后可在执行前取消。\n"
        "- [ ] 验证关机前优雅关闭应用可开启，并支持 1-300 秒等待超时。\n"
        "- [ ] 验证关闭应用预检会列出候选窗口且不会关闭它们。\n"
        "- [ ] 验证安全验证下的关闭应用预览只列出应用，不真正关闭。\n"
        "- [ ] 验证真实执行关闭应用验证只使用可丢弃应用，且不会留下重复电源动作。\n"
        "- [ ] 验证导出的诊断信息包含关闭应用状态、预览和最近结果。\n"
        "- [ ] 验证安全摘要在设置页可见，并会随安全验证、脚本、关闭应用和强制关闭设置变化。\n"
        "- [ ] 验证触发器状态展示进程、网络和空闲触发器状态。\n"
        "- [ ] 验证日志分类统计最近活动中的信息、警告和错误记录。\n"
        "- [ ] 验证复制诊断写入剪贴板并显示复制字符数。\n"
        "- [ ] 验证日志筛选可在全部、警告和错误之间切换且不会清空日志。\n"
        "- [ ] 验证一键健康检查报告脚本、关闭应用服务、队列、触发器和安全状态。\n"
        "- [ ] 验证失败队列任务重试可以重新运行失败任务且不创建重复行。\n"
        "- [ ] 验证复制队列任务诊断会记录失败任务 id、状态和最近错误。\n"
        "- [ ] 发布前使用 AUTOSHUTDOWNQT_REAL_WINDOW_SMOKE=1 运行真实窗口冒烟测试。\n"
        "- [ ] 验证期间不要执行真实的关机、重启、睡眠、休眠、注销或锁定。\n"
        "- [ ] 将 SHA256SUMS.txt 与 zip 和安装器一起发布。\n",
        encoding="utf-8",
    )
    return target


def create_zip():
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(APP_BUNDLE_DIR.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(DIST_DIR))
    return ZIP_PATH


def _load_manifest(archive, target):
    try:
        return json.loads(archive.read(REQUIRED_MANIFEST).decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Archive manifest is not valid JSON: {target}") from exc


def _require_manifest_value(manifest, key, expected):
    actual = manifest.get(key)
    if actual != expected:
        raise RuntimeError(f"Archive manifest {key} mismatch: expected {expected!r}, got {actual!r}")


def _require_manifest_check(manifest, check_name, expected):
    checks = manifest.get("checks")
    actual = checks.get(check_name) if isinstance(checks, dict) else None
    if actual != expected:
        raise RuntimeError(f"Archive manifest check {check_name} mismatch: expected {expected!r}, got {actual!r}")


def validate_zip_contents(zip_path=ZIP_PATH):
    target = Path(zip_path)
    if not target.exists():
        raise RuntimeError(f"Missing archive: {target}")

    with zipfile.ZipFile(target, "r") as archive:
        names = set(archive.namelist())
        manifest = _load_manifest(archive, target) if REQUIRED_MANIFEST in names else None

    if not names:
        raise RuntimeError(f"Archive is empty: {target}")

    if REQUIRED_EXE not in names:
        raise RuntimeError(f"Archive is missing required executable: {REQUIRED_EXE}")

    if REQUIRED_MANIFEST not in names:
        raise RuntimeError(f"Archive is missing required manifest: {REQUIRED_MANIFEST}")

    if not any(name.startswith(QML_PREFIXES) for name in names):
        expected = " or ".join(QML_PREFIXES)
        raise RuntimeError(f"Archive is missing required QML resources under: {expected}")

    main_qml_present = any(main_qml in names for main_qml in REQUIRED_MAIN_QMLS)
    if not main_qml_present:
        expected = " or ".join(REQUIRED_MAIN_QMLS)
        raise RuntimeError(f"Archive is missing required QML entrypoint: {expected}")

    bundled_music_present = any(name.startswith(f"{APP_BUNDLE_NAME}/") and name.lower().endswith(".mp3") for name in names)
    if not bundled_music_present:
        raise RuntimeError("Archive is missing bundled music mp3")

    unused_qt_payload = [name for name in names if _is_unused_qt_payload(name)]
    if unused_qt_payload:
        raise RuntimeError(f"Archive contains unused Qt payload: {unused_qt_payload[0]}")

    if not isinstance(manifest, dict):
        raise RuntimeError(f"Archive manifest must be a JSON object: {target}")
    _require_manifest_value(manifest, "version", VERSION)
    _require_manifest_value(manifest, "bundle", APP_BUNDLE_NAME)
    _require_manifest_value(manifest, "executable", "定时关机助手.exe")
    _require_manifest_value(manifest, "archive", target.name)
    _require_manifest_check(manifest, "executablePresent", REQUIRED_EXE in names)
    _require_manifest_check(manifest, "mainQmlPresent", main_qml_present)
    _require_manifest_check(manifest, "taskSchedulerIncluded", True)
    _require_manifest_check(manifest, "bundledMusicPresent", bundled_music_present)
    _require_manifest_check(manifest, "appCloseServiceHiddenImport", True)
    _require_manifest_check(manifest, "diagnosticsCenterWired", True)
    _require_manifest_check(manifest, "supportWorkflowWired", True)
    _require_manifest_check(manifest, "failedQueueRecoveryWired", True)

    return True


def main():
    run_pyinstaller()
    if not APP_BUNDLE_DIR.exists():
        raise SystemExit(f"Missing build output: {APP_BUNDLE_DIR}")
    removed_qt_payload = prune_unused_qt_payload(APP_BUNDLE_DIR)
    copy_bundled_music(ROOT, APP_BUNDLE_DIR)
    create_release_manifest(APP_BUNDLE_DIR)
    zip_path = create_zip()
    validate_zip_contents(zip_path)
    setup_path = build_inno_installer()
    sums_path = create_sha256sums([zip_path, setup_path])
    checklist_path = create_release_checklist()
    print(f"Built AutoShutdownQt {VERSION}: {APP_BUNDLE_DIR}")
    print(f"Pruned unused Qt payload files: {removed_qt_payload}")
    print(f"Created archive: {zip_path}")
    print(f"Created installer: {setup_path}")
    print(f"Created checksum file: {sums_path}")
    print(f"Created release checklist: {checklist_path}")


if __name__ == "__main__":
    main()

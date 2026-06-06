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
        },
        "safetyNotes": [
            "Dry-run is enabled by default.",
            "Live mode can execute real Windows power actions.",
            "Task queues and tray background scheduling are local-only features.",
            "The portable exe is not code signed.",
        ],
    }
    target = bundle / "release-manifest.json"
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


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
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        lines.append(f"{digest}  {artifact.name}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def create_release_checklist(target_path=RELEASE_CHECKLIST_PATH):
    target = Path(target_path)
    target.write_text(
        f"# 定时关机助手 {VERSION} Release Checklist\n\n"
        "- [ ] Launch app with Dry-run enabled by default.\n"
        "- [ ] Verify Command Center safety strip shows dry-run/live state, action, tray, and queue count.\n"
        "- [ ] Verify Queue health remains readable with empty and populated queues.\n"
        "- [ ] Verify configurable execution reminders are visible in Settings.\n"
        "- [ ] Verify a one-minute countdown shows the execution reminder dialog.\n"
        "- [ ] Verify the reminder dialog distinguishes Dry-run from real execution mode.\n"
        "- [ ] Verify default snooze extends the queued task and does not duplicate reminders.\n"
        "- [ ] Verify each queued task gets its own reminder threshold.\n"
        "- [ ] Verify Task Queue Dashboard empty and populated states.\n"
        "- [ ] Verify Recent activity shows logs and export/clear controls.\n"
        "- [ ] Verify Windows native notification fallback does not hide the in-app reminder.\n"
        "- [ ] Verify first-run safety guide appears once on a fresh config.\n"
        "- [ ] Verify first close-to-tray action shows the tray background hint once.\n"
        "- [ ] Verify LIVE MODE warning copy is visible before immediate execution.\n"
        "- [ ] Verify task history records create, snooze, cancel, and Dry-run execution events.\n"
        "- [ ] Verify task history clear and JSON export controls.\n"
        "- [ ] Verify startup option writes/removes the current-user Run entry.\n"
        "- [ ] Verify close button hides the window only when the right-bottom tray icon is visible.\n"
        "- [ ] Verify double-clicking the tray icon restores the window and tray menu Quit exits.\n"
        "- [ ] Verify idle auto-shutdown can be configured with idle minutes, poll seconds, and action.\n"
        "- [ ] Verify idle queue task appears and can be cancelled before execution.\n"
        "- [ ] Do not execute real shutdown, restart, sleep, hibernate, logoff, or lock during validation.\n"
        "- [ ] Publish SHA256SUMS.txt next to the zip and installer.\n",
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

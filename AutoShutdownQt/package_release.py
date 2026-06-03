from pathlib import Path
import json
import subprocess
import sys
import zipfile

VERSION = "2.0"
APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
SPEC_FILE = APP_DIR / "AutoShutdownQt-2.0.spec"
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build" / "pyinstaller"
APP_BUNDLE_DIR = DIST_DIR / "AutoShutdownQt-2.0"
ZIP_PATH = DIST_DIR / "AutoShutdownQt-2.0.zip"
APP_BUNDLE_NAME = f"AutoShutdownQt-{VERSION}"
REQUIRED_EXE = f"{APP_BUNDLE_NAME}/AutoShutdownQt.exe"
REQUIRED_MANIFEST = f"{APP_BUNDLE_NAME}/release-manifest.json"
QML_PREFIXES = (
    f"{APP_BUNDLE_NAME}/_internal/qml/",
    f"{APP_BUNDLE_NAME}/qml/",
)
REQUIRED_MAIN_QMLS = tuple(f"{prefix}Main.qml" for prefix in QML_PREFIXES)


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


def create_release_manifest(bundle_dir=APP_BUNDLE_DIR):
    bundle = Path(bundle_dir)
    main_qml_candidates = [bundle / "_internal" / "qml" / "Main.qml", bundle / "qml" / "Main.qml"]
    manifest = {
        "app": "AutoShutdownQt",
        "version": VERSION,
        "bundle": APP_BUNDLE_NAME,
        "executable": "AutoShutdownQt.exe",
        "archive": ZIP_PATH.name,
        "checks": {
            "executablePresent": (bundle / "AutoShutdownQt.exe").exists(),
            "mainQmlPresent": any(path.exists() for path in main_qml_candidates),
        },
        "safetyNotes": [
            "Dry-run is enabled by default.",
            "Live mode can execute real Windows power actions.",
            "The portable exe is not code signed.",
        ],
    }
    target = bundle / "release-manifest.json"
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
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

    if not isinstance(manifest, dict):
        raise RuntimeError(f"Archive manifest must be a JSON object: {target}")
    _require_manifest_value(manifest, "version", VERSION)
    _require_manifest_value(manifest, "bundle", APP_BUNDLE_NAME)
    _require_manifest_value(manifest, "executable", "AutoShutdownQt.exe")
    _require_manifest_value(manifest, "archive", target.name)
    _require_manifest_check(manifest, "executablePresent", REQUIRED_EXE in names)
    _require_manifest_check(manifest, "mainQmlPresent", main_qml_present)

    return True


def main():
    run_pyinstaller()
    if not APP_BUNDLE_DIR.exists():
        raise SystemExit(f"Missing build output: {APP_BUNDLE_DIR}")
    create_release_manifest(APP_BUNDLE_DIR)
    zip_path = create_zip()
    validate_zip_contents(zip_path)
    print(f"Built AutoShutdownQt {VERSION}: {APP_BUNDLE_DIR}")
    print(f"Created archive: {zip_path}")


if __name__ == "__main__":
    main()

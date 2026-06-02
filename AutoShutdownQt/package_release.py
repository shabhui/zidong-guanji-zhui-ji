from pathlib import Path
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


def create_zip():
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(APP_BUNDLE_DIR.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(DIST_DIR))
    return ZIP_PATH


def main():
    run_pyinstaller()
    if not APP_BUNDLE_DIR.exists():
        raise SystemExit(f"Missing build output: {APP_BUNDLE_DIR}")
    zip_path = create_zip()
    print(f"Built AutoShutdownQt {VERSION}: {APP_BUNDLE_DIR}")
    print(f"Created archive: {zip_path}")


if __name__ == "__main__":
    main()

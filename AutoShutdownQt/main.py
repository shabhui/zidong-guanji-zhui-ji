import sys
from pathlib import Path
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from controller import AppController
from music_service import MusicService, NullMusicService
from notification_service import NotificationService
from startup_service import StartupService
from tray_service import TrayService

APP_ICON_PATH = Path(__file__).parent / "app_icon.png"


def _parse_screenshot_path(argv):
    if "--ui-screenshot" not in argv:
        return None
    option_index = argv.index("--ui-screenshot")
    try:
        return Path(argv[option_index + 1]).expanduser().resolve()
    except IndexError:
        raise SystemExit("--ui-screenshot requires an output path")


def _parse_screenshot_page(argv):
    if "--ui-page" not in argv:
        return 0
    option_index = argv.index("--ui-page")
    try:
        return int(argv[option_index + 1])
    except (IndexError, ValueError):
        raise SystemExit("--ui-page requires a page number")


class ScreenshotStartupService:
    def is_enabled(self):
        return False

    def set_enabled(self, enabled):
        return not bool(enabled)


if __name__ == "__main__":
    screenshot_path = _parse_screenshot_path(sys.argv)
    screenshot_page = _parse_screenshot_page(sys.argv)
    app = QApplication(sys.argv)
    app.setApplicationName("定时关机助手")
    app.setApplicationVersion("3.2")
    app.setWindowIcon(QIcon(str(APP_ICON_PATH)))

    # PySide6 versions differ in QQuickStyle introspection support.
    # Use Fusion as a safe baseline; QML supplies the custom Fluent Neon visuals.
    try:
        QQuickStyle.setStyle("Fusion")
    except Exception:
        pass

    controller = AppController(
        music_service=NullMusicService() if screenshot_path is not None else MusicService(Path(__file__).resolve().parents[1]),
        startup_service=ScreenshotStartupService() if screenshot_path is not None else StartupService(),
    )
    if screenshot_path is not None:
        controller._dry_run = True
        controller._logs = ["READY · Dry-run 已开启"]
        controller._first_run_safety_guide_shown = True
        controller._tray_close_hint_shown = True

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("controller", controller)

    qml_dir = Path(__file__).parent / "qml"
    engine.addImportPath(str(qml_dir))

    main_qml = qml_dir / "Main.qml"
    engine.load(str(main_qml))

    if not engine.rootObjects():
        sys.exit(-1)

    window = engine.rootObjects()[0]
    window.setIcon(QIcon(str(APP_ICON_PATH)))

    if screenshot_path is None:
        controller.startMusicAutoplay()
    else:
        window.setProperty("currentPage", screenshot_page)

        def capture_ui_screenshot():
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            image = window.grabWindow()
            if image.isNull() or not image.save(str(screenshot_path)):
                app.exit(2)
                return
            app.exit(0)

        window.show()
        window.raise_()
        QTimer.singleShot(900, capture_ui_screenshot)
        sys.exit(app.exec())

    tray_service = TrayService(controller, window, icon_path=APP_ICON_PATH, logger=controller._add_log)
    controller.trayService = tray_service
    tray_service.setup()
    controller.notificationService = NotificationService(tray_service=tray_service, logger=controller._add_log)

    sys.exit(app.exec())

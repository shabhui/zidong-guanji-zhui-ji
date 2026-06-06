import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from controller import AppController
from music_service import MusicService
from notification_service import NotificationService
from startup_service import StartupService
from tray_service import TrayService

APP_ICON_PATH = Path(__file__).parent / "app_icon.png"

if __name__ == "__main__":
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
        music_service=MusicService(Path(__file__).resolve().parents[1]),
        startup_service=StartupService(),
    )

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("controller", controller)

    qml_dir = Path(__file__).parent / "qml"
    engine.addImportPath(str(qml_dir))

    main_qml = qml_dir / "Main.qml"
    engine.load(str(main_qml))

    if not engine.rootObjects():
        sys.exit(-1)

    controller.startMusicAutoplay()

    window = engine.rootObjects()[0]
    window.setIcon(QIcon(str(APP_ICON_PATH)))
    tray_service = TrayService(controller, window, icon_path=APP_ICON_PATH, logger=controller._add_log)
    controller.trayService = tray_service
    tray_service.setup()
    controller.notificationService = NotificationService(tray_service=tray_service, logger=controller._add_log)

    sys.exit(app.exec())

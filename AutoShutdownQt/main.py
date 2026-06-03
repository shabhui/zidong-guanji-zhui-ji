import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from controller import AppController
from tray_service import TrayService

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("AutoShutdownQt")
    app.setApplicationVersion("2.2")

    # PySide6 versions differ in QQuickStyle introspection support.
    # Use Fusion as a safe baseline; QML supplies the custom Fluent Neon visuals.
    try:
        QQuickStyle.setStyle("Fusion")
    except Exception:
        pass

    controller = AppController()

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("controller", controller)

    qml_dir = Path(__file__).parent / "qml"
    engine.addImportPath(str(qml_dir))

    main_qml = qml_dir / "Main.qml"
    engine.load(str(main_qml))

    if not engine.rootObjects():
        sys.exit(-1)

    window = engine.rootObjects()[0]
    tray_service = TrayService(controller, window, logger=controller._add_log)
    controller.trayService = tray_service
    tray_service.setup()

    sys.exit(app.exec())

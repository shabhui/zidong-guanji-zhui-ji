import sys
from pathlib import Path
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from controller import AppController

if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    app.setApplicationName("AutoShutdownQt")
    app.setApplicationVersion("2.0")

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

    sys.exit(app.exec())

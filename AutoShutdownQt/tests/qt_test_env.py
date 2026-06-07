"""Test-only Qt fallback for environments without PySide6 installed."""

from __future__ import annotations

import sys
import types


def ensure_qt_modules():
    """Use real PySide6 when available, otherwise install small test stubs."""
    try:
        import PySide6.QtCore  # noqa: F401
        import PySide6.QtWidgets  # noqa: F401
        import PySide6.QtMultimedia  # noqa: F401
        return False
    except ImportError:
        install_qt_stubs()
        return True


class _Signal:
    def __init__(self, *args, **kwargs):
        self._callbacks = []

    def connect(self, callback):
        self._callbacks.append(callback)

    def emit(self, *args, **kwargs):
        for callback in list(self._callbacks):
            callback(*args, **kwargs)


def _Property(_type=None, fget=None, fset=None, notify=None):
    return property(fget, fset)


def _Slot(*args, **kwargs):
    def decorator(func):
        return func

    return decorator


class _QObject:
    def __init__(self, parent=None):
        self._thread = "main"

    def thread(self):
        return self._thread


class _QCoreApplication:
    _instance = None

    def __init__(self, args=None):
        _QCoreApplication._instance = self

    @staticmethod
    def instance():
        return _QCoreApplication._instance

    @staticmethod
    def processEvents():
        return None

    @staticmethod
    def applicationName():
        return ""


class _QThread:
    @staticmethod
    def currentThread():
        return "main"


class _QTimer:
    def __init__(self, parent=None):
        self.timeout = _Signal()
        self.interval = 0
        self._active = False

    def setInterval(self, value):
        self.interval = int(value)

    def start(self):
        self._active = True

    def stop(self):
        self._active = False

    def isActive(self):
        return self._active


class _QUrl:
    def __init__(self, path=""):
        self._path = str(path)

    @staticmethod
    def fromLocalFile(path):
        return _QUrl(path)

    def toLocalFile(self):
        return self._path


class _QMediaPlayer(_QObject):
    PlayingState = 1
    StoppedState = 0
    EndOfMedia = 7

    def __init__(self, parent=None):
        super().__init__(parent)
        self.playbackStateChanged = _Signal()
        self.positionChanged = _Signal()
        self.durationChanged = _Signal()
        self.mediaStatusChanged = _Signal()
        self.errorOccurred = _Signal()
        self._source = None
        self._position = 0
        self._state = self.StoppedState

    def setAudioOutput(self, output):
        self._audio_output = output

    def setSource(self, source):
        self._source = source

    def play(self):
        self._state = self.PlayingState
        self.playbackStateChanged.emit(self._state)

    def pause(self):
        self._state = self.StoppedState
        self.playbackStateChanged.emit(self._state)

    def stop(self):
        self._state = self.StoppedState
        self.playbackStateChanged.emit(self._state)

    def setPosition(self, position):
        self._position = int(position)
        self.positionChanged.emit(self._position)

    def playbackState(self):
        return self._state


class _QAudioOutput(_QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.volume = 1.0

    def setVolume(self, volume):
        self.volume = float(volume)


def install_qt_stubs():
    qtcore = types.ModuleType("PySide6.QtCore")
    qtcore.QObject = _QObject
    qtcore.Signal = _Signal
    qtcore.Property = _Property
    qtcore.Slot = _Slot
    qtcore.QTimer = _QTimer
    qtcore.QCoreApplication = _QCoreApplication
    qtcore.QThread = _QThread
    qtcore.QUrl = _QUrl

    qtwidgets = types.ModuleType("PySide6.QtWidgets")
    qtwidgets.QFileDialog = types.SimpleNamespace(getExistingDirectory=lambda *args, **kwargs: "")

    qtmultimedia = types.ModuleType("PySide6.QtMultimedia")
    qtmultimedia.QMediaPlayer = _QMediaPlayer
    qtmultimedia.QAudioOutput = _QAudioOutput

    pyside = types.ModuleType("PySide6")
    pyside.QtCore = qtcore
    pyside.QtWidgets = qtwidgets
    pyside.QtMultimedia = qtmultimedia

    sys.modules.setdefault("PySide6", pyside)
    sys.modules.setdefault("PySide6.QtCore", qtcore)
    sys.modules.setdefault("PySide6.QtWidgets", qtwidgets)
    sys.modules.setdefault("PySide6.QtMultimedia", qtmultimedia)

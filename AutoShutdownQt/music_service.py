from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer


class NullMusicService:
    available = False
    title = "未找到音乐文件"
    playing = False
    error = ""
    tracks = []
    current_index = -1
    position_ms = 0
    duration_ms = 0
    position_text = "00:00"
    duration_text = "00:00"

    def play(self):
        return False

    def pause(self):
        pass

    def stop(self):
        pass

    def set_volume(self, percent):
        pass

    def select_track(self, index, autoplay=False):
        return False

    def seek(self, position_ms):
        pass

    def set_folder(self, folder, current_index=0):
        pass


class MusicService(QObject):
    playbackChanged = Signal()
    errorChanged = Signal(str)

    def __init__(self, music_root, parent=None, player=None, audio_output=None, current_index=0):
        super().__init__(parent)
        self._music_root = Path(music_root)
        self._tracks = find_mp3_tracks(self._music_root)
        self._current_index = self._valid_index(current_index)
        self._path = self._tracks[self._current_index] if self._current_index >= 0 else None
        self._player = player or QMediaPlayer(self)
        self._audio_output = audio_output or QAudioOutput(self)
        self._playing = False
        self._error = ""
        self._position_ms = 0
        self._duration_ms = 0
        self._playback_mode = "sequence"
        self._player.setAudioOutput(self._audio_output)
        if self._path is not None:
            self._player.setSource(QUrl.fromLocalFile(str(self._path)))
        if hasattr(self._player, "playbackStateChanged"):
            self._player.playbackStateChanged.connect(self._sync_playback_state)
        if hasattr(self._player, "positionChanged"):
            self._player.positionChanged.connect(self._sync_position)
        if hasattr(self._player, "durationChanged"):
            self._player.durationChanged.connect(self._sync_duration)
        if hasattr(self._player, "mediaStatusChanged"):
            self._player.mediaStatusChanged.connect(self._sync_media_status)
        if hasattr(self._player, "errorOccurred"):
            self._player.errorOccurred.connect(self._handle_error)

    @property
    def playback_mode(self):
        return self._playback_mode

    @playback_mode.setter
    def playback_mode(self, mode):
        if mode not in {"sequence", "list_loop", "single_loop"}:
            mode = "sequence"
        self._playback_mode = mode
        self.playbackChanged.emit()

    @property
    def path(self):
        return self._path

    @property
    def folder(self):
        return self._music_root

    @property
    def tracks(self):
        return list(self._tracks)

    @property
    def current_index(self):
        return self._current_index

    @property
    def available(self):
        return self._path is not None

    @property
    def title(self):
        if self._path is None:
            return "未找到音乐文件"
        return self._path.name

    @property
    def playing(self):
        return self._playing

    @property
    def error(self):
        return self._error

    @property
    def position_ms(self):
        return self._position_ms

    @property
    def duration_ms(self):
        return self._duration_ms

    @property
    def position_text(self):
        return format_ms(self._position_ms)

    @property
    def duration_text(self):
        return format_ms(self._duration_ms)

    def set_folder(self, folder, current_index=0):
        self._music_root = Path(folder)
        self._tracks = find_mp3_tracks(self._music_root)
        self._current_index = self._valid_index(current_index)
        self._path = self._tracks[self._current_index] if self._current_index >= 0 else None
        self._position_ms = 0
        self._duration_ms = 0
        if self._path is not None:
            self._player.setSource(QUrl.fromLocalFile(str(self._path)))
        else:
            self._player.stop()
        self.playbackChanged.emit()

    def select_track(self, index, autoplay=False):
        index = int(index)
        if index < 0 or index >= len(self._tracks):
            return False
        self._current_index = index
        self._path = self._tracks[index]
        self._position_ms = 0
        self._duration_ms = 0
        self._player.setSource(QUrl.fromLocalFile(str(self._path)))
        if autoplay:
            self.play()
        else:
            self.playbackChanged.emit()
        return True

    def next_track(self, autoplay=True):
        if not self._tracks:
            return False
        next_index = self._current_index + 1
        if next_index >= len(self._tracks):
            next_index = 0
        return self.select_track(next_index, autoplay=autoplay)

    def previous_track(self, autoplay=True):
        if not self._tracks:
            return False
        previous_index = self._current_index - 1
        if previous_index < 0:
            previous_index = len(self._tracks) - 1
        return self.select_track(previous_index, autoplay=autoplay)

    def handle_track_finished(self):
        if self._playback_mode == "single_loop":
            self.seek(0)
            self.play()
            return True
        if self._playback_mode == "list_loop":
            return self.next_track(autoplay=True)
        if self._current_index < len(self._tracks) - 1:
            return self.next_track(autoplay=True)
        self.stop()
        return False

    def play(self):
        if self._path is None:
            return False
        self._player.play()
        self._playing = True
        self.playbackChanged.emit()
        return True

    def pause(self):
        self._player.pause()
        self._playing = False
        self.playbackChanged.emit()

    def stop(self):
        self._player.stop()
        self._playing = False
        self.playbackChanged.emit()

    def seek(self, position_ms):
        position_ms = max(0, int(position_ms))
        self._player.setPosition(position_ms)
        self._position_ms = position_ms
        self.playbackChanged.emit()

    def set_volume(self, percent):
        percent = max(0, min(100, int(percent)))
        self._audio_output.setVolume(percent / 100)

    def _valid_index(self, index):
        if not self._tracks:
            return -1
        index = max(0, min(len(self._tracks) - 1, int(index)))
        return index

    def _sync_playback_state(self, state):
        self._playing = state == QMediaPlayer.PlayingState
        self.playbackChanged.emit()

    def _sync_position(self, position_ms):
        self._position_ms = max(0, int(position_ms))
        self.playbackChanged.emit()

    def _sync_duration(self, duration_ms):
        self._duration_ms = max(0, int(duration_ms))
        self.playbackChanged.emit()

    def _sync_media_status(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self.handle_track_finished()

    def _handle_error(self, error, message=""):
        self._error = message or str(error)
        self._playing = False
        self.errorChanged.emit(self._error)
        self.playbackChanged.emit()


def find_mp3_tracks(root):
    root = Path(root)
    try:
        return sorted(path for path in root.iterdir() if path.is_file() and path.suffix.lower() == ".mp3")
    except OSError:
        return []


def find_first_mp3(root):
    tracks = find_mp3_tracks(root)
    return tracks[0] if tracks else None


def format_ms(value):
    total_seconds = max(0, int(value) // 1000)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"

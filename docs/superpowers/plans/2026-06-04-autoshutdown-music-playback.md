# AutoShutdownQt Music Playback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add local MP3 playback that autoplays on app launch by default, with a Settings switch to disable autoplay and a dedicated music player window.

**Architecture:** Add a focused `music_service.py` that finds the first project-root MP3 and wraps `QMediaPlayer`/`QAudioOutput`. Extend `AppController` with music properties, persistence, and slots. Update `Main.qml` with a Music entry, a separate music window, and a Settings autoplay switch.

**Tech Stack:** Python 3.12, PySide6 QtCore/QtMultimedia, QML, `unittest`.

---

## File Structure

- Create: `AutoShutdownQt/music_service.py` — MP3 discovery plus thin media-player wrapper.
- Create: `AutoShutdownQt/tests/test_music_service.py` — service-level tests for discovery and player delegation.
- Modify: `AutoShutdownQt/settings_service.py` — add persisted `musicAutoplayEnabled` and `musicVolume` defaults.
- Modify: `AutoShutdownQt/controller.py` — expose music properties/slots, instantiate service, persist settings, autoplay at startup.
- Modify: `AutoShutdownQt/main.py` — trigger controller startup autoplay after QML has loaded.
- Modify: `AutoShutdownQt/qml/Main.qml` — add Music button/window and autoplay setting switch.
- Modify: `AutoShutdownQt/tests/test_practical_enhancements.py` — controller tests for settings and music slot delegation.
- Modify: `AutoShutdownQt/tests/test_e5e8_ui_regressions.py` — QML static regression tests for music UI wiring.

---

### Task 1: Add music service with TDD

**Files:**
- Create: `AutoShutdownQt/tests/test_music_service.py`
- Create: `AutoShutdownQt/music_service.py`

- [ ] **Step 1: Write failing service tests**

Create `AutoShutdownQt/tests/test_music_service.py`:

```python
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "AutoShutdownQt"
sys.path.insert(0, str(APP_DIR))

from music_service import MusicService, find_first_mp3


class FakePlayer:
    def __init__(self):
        self.source = None
        self.play_calls = 0
        self.pause_calls = 0
        self.stop_calls = 0

    def setSource(self, source):
        self.source = source

    def play(self):
        self.play_calls += 1

    def pause(self):
        self.pause_calls += 1

    def stop(self):
        self.stop_calls += 1


class FakeAudioOutput:
    def __init__(self):
        self.volume = None

    def setVolume(self, volume):
        self.volume = volume


class MusicServiceTest(unittest.TestCase):
    def test_find_first_mp3_returns_sorted_first_project_root_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "b-song.mp3").write_bytes(b"demo")
            (root / "a-song.mp3").write_bytes(b"demo")
            (root / "nested").mkdir()
            (root / "nested" / "0-nested.mp3").write_bytes(b"demo")

            result = find_first_mp3(root)

            self.assertEqual(result, root / "a-song.mp3")

    def test_find_first_mp3_returns_none_when_root_has_no_mp3(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "song.wav").write_bytes(b"demo")

            result = find_first_mp3(root)

            self.assertIsNone(result)

    def test_service_reports_unavailable_without_mp3(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = MusicService(Path(tmp), player=FakePlayer(), audio_output=FakeAudioOutput())

            self.assertFalse(service.available)
            self.assertEqual(service.title, "未找到音乐文件")

    def test_service_sets_source_and_delegates_playback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            song = root / "see-you-again.mp3"
            song.write_bytes(b"demo")
            player = FakePlayer()
            audio_output = FakeAudioOutput()
            service = MusicService(root, player=player, audio_output=audio_output)

            service.set_volume(35)
            self.assertTrue(service.play())
            service.pause()
            service.stop()

            self.assertEqual(service.path, song)
            self.assertEqual(service.title, "see-you-again.mp3")
            self.assertEqual(player.source.toLocalFile(), str(song))
            self.assertEqual(player.play_calls, 1)
            self.assertEqual(player.pause_calls, 1)
            self.assertEqual(player.stop_calls, 1)
            self.assertAlmostEqual(audio_output.volume, 0.35)

    def test_service_does_not_play_when_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            player = FakePlayer()
            service = MusicService(Path(tmp), player=player, audio_output=FakeAudioOutput())

            self.assertFalse(service.play())
            self.assertEqual(player.play_calls, 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m unittest AutoShutdownQt/tests/test_music_service.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'music_service'`.

- [ ] **Step 3: Implement music service**

Create `AutoShutdownQt/music_service.py`:

```python
from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer


class MusicService(QObject):
    playbackChanged = Signal()
    errorChanged = Signal(str)

    def __init__(self, music_root, parent=None, player=None, audio_output=None):
        super().__init__(parent)
        self._music_root = Path(music_root)
        self._path = find_first_mp3(self._music_root)
        self._player = player or QMediaPlayer(self)
        self._audio_output = audio_output or QAudioOutput(self)
        self._playing = False
        self._error = ""
        self._player.setAudioOutput(self._audio_output)
        if self._path is not None:
            self._player.setSource(QUrl.fromLocalFile(str(self._path)))
        if hasattr(self._player, "playbackStateChanged"):
            self._player.playbackStateChanged.connect(self._sync_playback_state)
        if hasattr(self._player, "errorOccurred"):
            self._player.errorOccurred.connect(self._handle_error)

    @property
    def path(self):
        return self._path

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

    def set_volume(self, percent):
        percent = max(0, min(100, int(percent)))
        self._audio_output.setVolume(percent / 100)

    def _sync_playback_state(self, state):
        self._playing = state == QMediaPlayer.PlayingState
        self.playbackChanged.emit()

    def _handle_error(self, error, message=""):
        self._error = message or str(error)
        self._playing = False
        self.errorChanged.emit(self._error)
        self.playbackChanged.emit()


def find_first_mp3(root):
    root = Path(root)
    try:
        matches = sorted(path for path in root.iterdir() if path.is_file() and path.suffix.lower() == ".mp3")
    except OSError:
        return None
    return matches[0] if matches else None
```

- [ ] **Step 4: Run service tests to verify they pass**

Run:

```bash
python -m unittest AutoShutdownQt/tests/test_music_service.py -v
```

Expected: PASS all tests in `MusicServiceTest`.

---

### Task 2: Add persisted music settings

**Files:**
- Modify: `AutoShutdownQt/settings_service.py`
- Modify: `AutoShutdownQt/tests/test_practical_enhancements.py`

- [ ] **Step 1: Write failing settings test**

Add this method inside `PracticalEnhancementsTest` in `AutoShutdownQt/tests/test_practical_enhancements.py`:

```python
    def test_default_settings_include_music_preferences(self):
        settings = default_settings()

        self.assertTrue(settings["musicAutoplayEnabled"])
        self.assertEqual(settings["musicVolume"], 70)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m unittest AutoShutdownQt/tests/test_practical_enhancements.py::PracticalEnhancementsTest.test_default_settings_include_music_preferences -v
```

If `unittest` does not accept `::` on this platform, run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_default_settings_include_music_preferences -v
```

Expected: FAIL with `KeyError: 'musicAutoplayEnabled'`.

- [ ] **Step 3: Add settings defaults**

In `AutoShutdownQt/settings_service.py`, update `DEFAULT_SETTINGS` to include:

```python
DEFAULT_SETTINGS = {
    "dryRun": True,
    "forceClose": False,
    "selectedAction": "shutdown",
    "scriptEnabled": False,
    "scriptPath": "",
    "scriptTimeoutSeconds": 10,
    "processName": "",
    "processPollSeconds": 5,
    "networkDownloadThresholdKbps": 10.0,
    "networkUploadThresholdKbps": 10.0,
    "networkIdleSeconds": 60,
    "networkPollSeconds": 3,
    "musicAutoplayEnabled": True,
    "musicVolume": 70,
    "taskQueue": {"version": 1, "tasks": []},
}
```

- [ ] **Step 4: Run settings test**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_default_settings_include_music_preferences -v
```

Expected: PASS.

---

### Task 3: Add controller music API with TDD

**Files:**
- Modify: `AutoShutdownQt/controller.py`
- Modify: `AutoShutdownQt/tests/test_practical_enhancements.py`

- [ ] **Step 1: Add controller tests**

Add this fake class near `FakeNetworkReader` in `AutoShutdownQt/tests/test_practical_enhancements.py`:

```python
class FakeMusicService:
    def __init__(self, available=True, title="demo.mp3"):
        self.available = available
        self.title = title
        self.playing = False
        self.play_calls = 0
        self.pause_calls = 0
        self.stop_calls = 0
        self.volume_values = []

    def play(self):
        self.play_calls += 1
        if not self.available:
            return False
        self.playing = True
        return True

    def pause(self):
        self.pause_calls += 1
        self.playing = False

    def stop(self):
        self.stop_calls += 1
        self.playing = False

    def set_volume(self, value):
        self.volume_values.append(value)
```

Add these methods inside `PracticalEnhancementsTest`:

```python
    def test_controller_exposes_music_state_and_delegates_slots(self):
        music = FakeMusicService(available=True, title="demo.mp3")
        controller = AppController(music_service=music)

        self.assertTrue(controller.musicAvailable)
        self.assertEqual(controller.musicTitle, "demo.mp3")
        self.assertTrue(controller.musicAutoplayEnabled)
        self.assertEqual(controller.musicVolume, 70)

        controller.setMusicVolume(35)
        controller.playMusic()
        self.assertTrue(controller.musicPlaying)
        controller.pauseMusic()
        self.assertFalse(controller.musicPlaying)
        controller.stopMusic()

        self.assertEqual(music.volume_values, [70, 35])
        self.assertEqual(music.play_calls, 1)
        self.assertEqual(music.pause_calls, 1)
        self.assertEqual(music.stop_calls, 1)

    def test_controller_startup_autoplay_obeys_setting(self):
        music = FakeMusicService()
        controller = AppController(music_service=music)

        controller.startMusicAutoplay()
        self.assertEqual(music.play_calls, 1)

        controller.musicAutoplayEnabled = False
        controller.startMusicAutoplay()
        self.assertEqual(music.play_calls, 1)

    def test_controller_does_not_mark_music_playing_when_file_missing(self):
        music = FakeMusicService(available=False, title="未找到音乐文件")
        controller = AppController(music_service=music)

        controller.playMusic()

        self.assertFalse(controller.musicAvailable)
        self.assertFalse(controller.musicPlaying)
        self.assertIn("未找到音乐文件", controller.logText)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_controller_exposes_music_state_and_delegates_slots AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_controller_startup_autoplay_obeys_setting AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_controller_does_not_mark_music_playing_when_file_missing -v
```

Expected: FAIL with `TypeError: AppController.__init__() got an unexpected keyword argument 'music_service'`.

- [ ] **Step 3: Implement controller music fields and properties**

In `AutoShutdownQt/controller.py`, add the import near other imports:

```python
from music_service import MusicService
```

Change the constructor signature to:

```python
    def __init__(self, parent=None, settings_path=None, network_reader=None, log_export_path=None, open_folder=None, music_service=None):
```

After network settings initialization, add:

```python
        self._music_autoplay_enabled = self._coerce_bool(settings.get("musicAutoplayEnabled"), True)
        self._music_volume = self._coerce_int(settings.get("musicVolume"), 70, minimum=0)
        self._music_volume = min(100, self._music_volume)
```

After `_network_reader` setup, add:

```python
        self._music_service = music_service or MusicService(Path(__file__).resolve().parents[1])
        self._music_service.set_volume(self._music_volume)
```

Add this signal near existing signals:

```python
    musicChanged = Signal()
```

Add these QML properties near the other property definitions:

```python
    def getMusicAutoplayEnabled(self): return self._music_autoplay_enabled
    def setMusicAutoplayEnabled(self, v):
        v = bool(v)
        if self._music_autoplay_enabled != v:
            self._music_autoplay_enabled = v
            self._add_log("启动自动播放音乐已开启" if v else "启动自动播放音乐已关闭")
            self._save_settings()
            self.musicChanged.emit()
    musicAutoplayEnabled = Property(bool, getMusicAutoplayEnabled, setMusicAutoplayEnabled, notify=musicChanged)

    def getMusicAvailable(self): return bool(self._music_service.available)
    musicAvailable = Property(bool, getMusicAvailable, notify=musicChanged)

    def getMusicTitle(self): return self._music_service.title
    musicTitle = Property(str, getMusicTitle, notify=musicChanged)

    def getMusicPlaying(self): return bool(self._music_service.playing)
    musicPlaying = Property(bool, getMusicPlaying, notify=musicChanged)

    def getMusicVolume(self): return self._music_volume
    musicVolume = Property(int, getMusicVolume, notify=musicChanged)
```

Add these slots near existing slots:

```python
    @Slot()
    def startMusicAutoplay(self):
        if self._music_autoplay_enabled:
            self.playMusic()

    @Slot()
    def playMusic(self):
        if self._music_service.play():
            self._add_log(f"开始播放音乐：{self._music_service.title}")
        else:
            self._add_log("未找到音乐文件，无法播放")
        self.musicChanged.emit()

    @Slot()
    def pauseMusic(self):
        self._music_service.pause()
        self._add_log("音乐已暂停")
        self.musicChanged.emit()

    @Slot()
    def stopMusic(self):
        self._music_service.stop()
        self._add_log("音乐已停止")
        self.musicChanged.emit()

    @Slot(int)
    def setMusicVolume(self, value):
        value = self._coerce_int(value, 70, minimum=0)
        value = min(100, value)
        if self._music_volume != value:
            self._music_volume = value
            self._music_service.set_volume(value)
            self._save_settings()
            self.musicChanged.emit()
```

Update `_settings_snapshot()` to include:

```python
            "musicAutoplayEnabled": self._music_autoplay_enabled,
            "musicVolume": self._music_volume,
```

- [ ] **Step 4: Run controller tests**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_controller_exposes_music_state_and_delegates_slots AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_controller_startup_autoplay_obeys_setting AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_controller_does_not_mark_music_playing_when_file_missing -v
```

Expected: PASS.

---

### Task 4: Start autoplay after QML loads

**Files:**
- Modify: `AutoShutdownQt/main.py`
- Modify: `AutoShutdownQt/tests/test_e5e8_ui_regressions.py`

- [ ] **Step 1: Add static regression test for startup autoplay call**

Add this test method inside `E5E8ButtonRegressionTest` in `AutoShutdownQt/tests/test_e5e8_ui_regressions.py`:

```python
    def test_main_starts_music_autoplay_after_qml_loads(self):
        main_py = (ROOT / "AutoShutdownQt" / "main.py").read_text(encoding="utf-8")

        self.assertIn("controller.startMusicAutoplay()", main_py)
        self.assertGreater(main_py.index("engine.load(str(main_qml))"), main_py.index("engine.rootContext().setContextProperty"))
        self.assertGreater(main_py.index("controller.startMusicAutoplay()"), main_py.index("if not engine.rootObjects():"))
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_e5e8_ui_regressions.E5E8ButtonRegressionTest.test_main_starts_music_autoplay_after_qml_loads -v
```

Expected: FAIL because `controller.startMusicAutoplay()` is not present.

- [ ] **Step 3: Add startup autoplay call**

In `AutoShutdownQt/main.py`, after the `if not engine.rootObjects(): sys.exit(-1)` block and before `window = engine.rootObjects()[0]`, use:

```python
    controller.startMusicAutoplay()

    window = engine.rootObjects()[0]
```

- [ ] **Step 4: Run startup autoplay static test**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_e5e8_ui_regressions.E5E8ButtonRegressionTest.test_main_starts_music_autoplay_after_qml_loads -v
```

Expected: PASS.

---

### Task 5: Add music window and settings switch in QML

**Files:**
- Modify: `AutoShutdownQt/qml/Main.qml`
- Modify: `AutoShutdownQt/tests/test_e5e8_ui_regressions.py`

- [ ] **Step 1: Add failing QML regression test**

Add this test method inside `E5E8ButtonRegressionTest`:

```python
    def test_music_player_ui_is_wired_to_controller(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        for snippet in (
            "id: musicPlayerWindow",
            "controller.musicTitle",
            "controller.musicAvailable",
            "controller.musicPlaying",
            "controller.playMusic()",
            "controller.pauseMusic()",
            "controller.stopMusic()",
            "controller.setMusicVolume(",
            "controller.musicAutoplayEnabled",
            "启动时自动播放音乐",
            "音乐播放器",
        ):
            self.assertIn(snippet, main)
```

- [ ] **Step 2: Run QML test to verify it fails**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_e5e8_ui_regressions.E5E8ButtonRegressionTest.test_music_player_ui_is_wired_to_controller -v
```

Expected: FAIL because music UI snippets are not present.

- [ ] **Step 3: Add title-bar Music button**

In `AutoShutdownQt/qml/Main.qml`, in the title bar `RowLayout` before the minimize button, insert:

```qml
            NeonButton {
                Layout.preferredWidth: 88
                Layout.preferredHeight: 32
                compact: true
                variant: "ghost"
                text: "音乐"
                onClicked: musicPlayerWindow.show()
            }
```

- [ ] **Step 4: Add Settings autoplay switch**

In the Settings page `ColumnLayout`, after the force-close row, insert:

```qml
                    RowLayout {
                        Layout.fillWidth: true
                        Text { Layout.fillWidth: true; text: "启动时自动播放音乐"; color: Theme.textPrimary; font.pixelSize: 16; font.weight: Font.Bold }
                        FluentSwitch { checked: controller.musicAutoplayEnabled; onCheckedChanged: controller.musicAutoplayEnabled = checked }
                    }
```

- [ ] **Step 5: Add music player window**

In `AutoShutdownQt/qml/Main.qml`, before the existing `ConfirmDialog`, insert:

```qml
    Window {
        id: musicPlayerWindow
        width: 420
        height: 280
        minimumWidth: 380
        minimumHeight: 240
        visible: false
        title: "音乐播放器"
        color: Theme.bgDeep

        Rectangle {
            anchors.fill: parent
            gradient: Gradient {
                GradientStop { position: 0.0; color: Theme.e5BgA }
                GradientStop { position: 1.0; color: Theme.e5BgC }
            }
        }

        NeonCard {
            anchors.fill: parent
            anchors.margins: 18
            cardColor: Theme.cardGlassActive
            cardBorderColor: Theme.e5BorderPink
            radius: Theme.radiusXl

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 22
                spacing: 14

                Text {
                    Layout.fillWidth: true
                    text: "音乐播放器"
                    color: Theme.textPrimary
                    font.pixelSize: 24
                    font.weight: Font.Bold
                }

                Text {
                    Layout.fillWidth: true
                    text: controller.musicAvailable ? controller.musicTitle : "未找到音乐文件"
                    color: controller.musicAvailable ? Theme.textPrimary : Theme.danger
                    font.pixelSize: 15
                    wrapMode: Text.WordWrap
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    NeonButton {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 42
                        variant: "primary"
                        text: controller.musicPlaying ? "暂停" : "播放"
                        onClicked: controller.musicPlaying ? controller.pauseMusic() : controller.playMusic()
                    }
                    NeonButton {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 42
                        variant: "ghost"
                        text: "停止"
                        onClicked: controller.stopMusic()
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: "音量：" + controller.musicVolume + "%"
                    color: Theme.textSecondary
                    font.pixelSize: 13
                }

                Slider {
                    Layout.fillWidth: true
                    from: 0
                    to: 100
                    stepSize: 1
                    value: controller.musicVolume
                    onMoved: controller.setMusicVolume(value)
                }

                Item { Layout.fillHeight: true }
            }
        }
    }
```

- [ ] **Step 6: Run QML test**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_e5e8_ui_regressions.E5E8ButtonRegressionTest.test_music_player_ui_is_wired_to_controller -v
```

Expected: PASS.

---

### Task 6: Run focused and full test suite

**Files:**
- Verify only; no new edits unless tests fail.

- [ ] **Step 1: Run focused music-related tests**

Run:

```bash
python -m unittest AutoShutdownQt/tests/test_music_service.py AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_default_settings_include_music_preferences AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_controller_exposes_music_state_and_delegates_slots AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_controller_startup_autoplay_obeys_setting AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_controller_does_not_mark_music_playing_when_file_missing AutoShutdownQt.tests.test_e5e8_ui_regressions.E5E8ButtonRegressionTest.test_main_starts_music_autoplay_after_qml_loads AutoShutdownQt.tests.test_e5e8_ui_regressions.E5E8ButtonRegressionTest.test_music_player_ui_is_wired_to_controller -v
```

Expected: PASS.

- [ ] **Step 2: Run full test suite**

Run:

```bash
python -m unittest discover AutoShutdownQt/tests -v
```

Expected: PASS. If a test fails, use systematic debugging before changing code.

---

## Self-Review

- Spec coverage: MP3 discovery, startup autoplay, Settings toggle, dedicated music window, local-only scope, missing-file behavior, and tests are covered by Tasks 1-6.
- Placeholder scan: no TBD/TODO/fill-in instructions remain.
- Type consistency: controller names are consistent across Python tests, Python implementation, and QML: `musicAutoplayEnabled`, `musicAvailable`, `musicTitle`, `musicPlaying`, `musicVolume`, `startMusicAutoplay()`, `playMusic()`, `pauseMusic()`, `stopMusic()`, `setMusicVolume()`.

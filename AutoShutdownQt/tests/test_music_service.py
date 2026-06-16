from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "AutoShutdownQt"
sys.path.insert(0, str(APP_DIR))

from tests.qt_test_env import ensure_qt_modules
ensure_qt_modules()

from PySide6.QtMultimedia import QMediaPlayer

from music_service import MusicService, find_mp3_tracks, format_ms


class FakePlayer:
    def __init__(self):
        self.source = None
        self.play_calls = 0
        self.pause_calls = 0
        self.stop_calls = 0
        self.seek_position = None

    def setSource(self, source):
        self.source = source

    def setAudioOutput(self, audio_output):
        self.audio_output = audio_output

    def play(self):
        self.play_calls += 1

    def pause(self):
        self.pause_calls += 1

    def stop(self):
        self.stop_calls += 1

    def setPosition(self, position):
        self.seek_position = position


class FakeAudioOutput:
    def __init__(self):
        self.volume = None

    def setVolume(self, volume):
        self.volume = volume


class MusicServiceTest(unittest.TestCase):
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
            self.assertEqual(Path(player.source.toLocalFile()), song)
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
    def test_find_mp3_tracks_returns_sorted_root_level_tracks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "b-song.mp3").write_bytes(b"demo")
            (root / "a-song.MP3").write_bytes(b"demo")
            (root / "nested").mkdir()
            (root / "nested" / "0-nested.mp3").write_bytes(b"demo")

            result = find_mp3_tracks(root)

            self.assertEqual(result, [root / "a-song.MP3", root / "b-song.mp3"])

    def test_service_selects_track_and_seeks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "a-song.mp3"
            second = root / "b-song.mp3"
            first.write_bytes(b"demo")
            second.write_bytes(b"demo")
            player = FakePlayer()
            service = MusicService(root, player=player, audio_output=FakeAudioOutput())

            self.assertEqual(service.tracks, [first, second])
            self.assertEqual(service.current_index, 0)
            self.assertTrue(service.select_track(1, autoplay=True))
            service.seek(65000)

            self.assertEqual(service.path, second)
            self.assertEqual(service.title, "b-song.mp3")
            self.assertEqual(service.current_index, 1)
            self.assertEqual(Path(player.source.toLocalFile()), second)
            self.assertEqual(player.play_calls, 1)
            self.assertEqual(player.seek_position, 65000)

    def test_service_rejects_invalid_track_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a-song.mp3").write_bytes(b"demo")
            service = MusicService(root, player=FakePlayer(), audio_output=FakeAudioOutput())

            self.assertFalse(service.select_track(99, autoplay=True))
            self.assertEqual(service.current_index, 0)

    def test_format_ms_uses_minutes_or_hours(self):
        self.assertEqual(format_ms(0), "00:00")
        self.assertEqual(format_ms(65000), "01:05")
        self.assertEqual(format_ms(3661000), "01:01:01")

    def test_service_tracks_position_and_duration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a-song.mp3").write_bytes(b"demo")
            service = MusicService(root, player=FakePlayer(), audio_output=FakeAudioOutput())

            service._sync_position(65000)
            service._sync_duration(185000)

            self.assertEqual(service.position_ms, 65000)
            self.assertEqual(service.duration_ms, 185000)
            self.assertEqual(service.position_text, "01:05")
            self.assertEqual(service.duration_text, "03:05")
    def test_service_previous_and_next_track_wrap_playlist(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "a-song.mp3"
            second = root / "b-song.mp3"
            first.write_bytes(b"demo")
            second.write_bytes(b"demo")
            player = FakePlayer()
            service = MusicService(root, player=player, audio_output=FakeAudioOutput())

            self.assertTrue(service.next_track())
            self.assertEqual(service.current_index, 1)
            self.assertEqual(service.path, second)
            self.assertTrue(service.next_track())
            self.assertEqual(service.current_index, 0)
            self.assertEqual(service.path, first)
            self.assertTrue(service.previous_track())
            self.assertEqual(service.current_index, 1)
            self.assertEqual(service.path, second)

    def test_service_single_loop_restarts_current_track_when_finished(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a-song.mp3").write_bytes(b"demo")
            (root / "b-song.mp3").write_bytes(b"demo")
            player = FakePlayer()
            service = MusicService(root, player=player, audio_output=FakeAudioOutput())
            service.playback_mode = "single_loop"

            service.handle_track_finished()

            self.assertEqual(service.current_index, 0)
            self.assertEqual(player.seek_position, 0)
            self.assertEqual(player.play_calls, 1)

    def test_service_advances_when_player_reports_end_of_media(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a-song.mp3").write_bytes(b"demo")
            (root / "b-song.mp3").write_bytes(b"demo")
            service = MusicService(root, player=FakePlayer(), audio_output=FakeAudioOutput())

            service._sync_media_status(QMediaPlayer.EndOfMedia)

            self.assertEqual(service.current_index, 1)


        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a-song.mp3").write_bytes(b"demo")
            (root / "b-song.mp3").write_bytes(b"demo")
            player = FakePlayer()
            service = MusicService(root, player=player, audio_output=FakeAudioOutput(), current_index=1)

            service.playback_mode = "sequence"
            service.handle_track_finished()
            self.assertEqual(service.current_index, 1)
            self.assertEqual(player.stop_calls, 1)

            service.playback_mode = "list_loop"
            service.handle_track_finished()
            self.assertEqual(service.current_index, 0)


if __name__ == "__main__":
    unittest.main()

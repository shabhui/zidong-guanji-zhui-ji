# AutoShutdownQt Music Folder Seek Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add folder-based song selection and draggable playback position controls to the existing music player.

**Architecture:** Extend `music_service.py` to manage a folder playlist, selected track, duration, position, and seek delegation. Extend `AppController` with persisted folder/current-index settings and QML-facing properties/slots. Expand the existing music window with folder selection, track list, and seek slider.

**Tech Stack:** Python 3.12, PySide6 `QMediaPlayer`/`QAudioOutput`, QML, unittest.

---

### Task 1: Music service playlist and seek

**Files:**
- Modify: `AutoShutdownQt/music_service.py`
- Test: `AutoShutdownQt/tests/test_music_service.py`

- [ ] Write failing tests for scanning multiple sorted MP3s, selecting track by index, duration/position formatting, and seek delegation.
- [ ] Run `python -m unittest AutoShutdownQt/tests/test_music_service.py -v` and verify RED.
- [ ] Implement `find_mp3_tracks`, playlist state, `select_track`, `seek`, position/duration properties, and `format_ms`.
- [ ] Run the same test and verify GREEN.

### Task 2: Persist folder and current track

**Files:**
- Modify: `AutoShutdownQt/settings_service.py`
- Modify: `AutoShutdownQt/controller.py`
- Test: `AutoShutdownQt/tests/test_practical_enhancements.py`

- [ ] Write failing tests for default `musicFolder`, `musicCurrentIndex`, controller playlist properties, selecting tracks, and seeking.
- [ ] Run focused controller/settings tests and verify RED.
- [ ] Add settings defaults and controller properties/slots: `musicFolder`, `musicTracksJson`, `musicCurrentIndex`, `musicPositionMs`, `musicDurationMs`, `musicPositionText`, `musicDurationText`, `chooseMusicFolder`, `playMusicTrack`, `seekMusic`.
- [ ] Run focused tests and verify GREEN.

### Task 3: QML folder picker, track list, and seek slider

**Files:**
- Modify: `AutoShutdownQt/qml/Main.qml`
- Test: `AutoShutdownQt/tests/test_e5e8_ui_regressions.py`

- [ ] Write failing static QML test for `FolderDialog`, `controller.chooseMusicFolder`, track list, `controller.playMusicTrack(index)`, `controller.seekMusic`, and position/duration labels.
- [ ] Run the static test and verify RED.
- [ ] Add QML imports and UI controls to the existing music window.
- [ ] Run the static test and verify GREEN.

### Task 4: Full verification

**Files:**
- Test: all tests

- [ ] Run `python -m unittest discover AutoShutdownQt/tests -v`.
- [ ] Fix any failures with TDD.
- [ ] Report changed behavior and test result.

# AutoShutdownQt Music Folder and Seek Controls Design

## Goal

Upgrade the music feature from a single-root MP3 autoplay helper into a simple local music player with folder selection, multi-song playback, and seek controls.

## User Experience

- The music window includes a “选择音乐文件夹” button.
- Choosing a folder scans that folder for `.mp3` files and shows them in a song list.
- Clicking a song starts playing that song.
- The app remembers the selected folder and selected song index.
- If no folder has been selected, the player falls back to the project root.
- Startup autoplay remains controlled by the existing Settings switch.
- Autoplay plays the remembered song if available; otherwise it plays the first song in the current folder.
- The music window shows current position and total duration as `MM:SS / MM:SS` or `HH:MM:SS / HH:MM:SS` for long audio.
- A progress slider updates during playback and can be dragged to seek.

## Architecture

`music_service.py` becomes responsible for folder scanning, playlist state, track selection, playback, volume, duration, position, and seeking. It still wraps `QMediaPlayer` and `QAudioOutput` so QML and `AppController` stay media-backend agnostic.

`AppController` persists and exposes:

- `musicFolder`
- `musicTracksJson`
- `musicCurrentIndex`
- `musicPositionMs`
- `musicDurationMs`
- `musicPositionText`
- `musicDurationText`
- existing autoplay, title, playing, available, and volume properties

`main.py` injects the real `MusicService`; tests can keep using fakes or the null service to avoid real media probing.

## UI Components

The existing dedicated music window is expanded:

- Song title and folder path summary.
- “选择音乐文件夹” button.
- Track list with one row per MP3.
- Play/Pause and Stop buttons.
- Seek slider with current and total time text.
- Volume slider.

The Settings autoplay switch remains unchanged.

## Data Flow

1. Settings load `musicFolder`, `musicCurrentIndex`, `musicAutoplayEnabled`, and `musicVolume`.
2. The real music service scans the configured folder or project root.
3. QML reads `musicTracksJson` for the list.
4. User selects a folder through a Qt folder picker slot; controller asks service to scan it, persists the path, and emits `musicChanged`.
5. User selects a track; controller delegates to service, updates current index, persists, and emits `musicChanged`.
6. QMediaPlayer position/duration signals update service state and notify the controller, which updates QML bindings.
7. User drags the progress slider; QML calls `seekMusic(positionMs)`.

## Error Handling

- Missing or empty folder: no crash; list is empty and title shows “未找到音乐文件”.
- Invalid saved folder: fall back to project root.
- Invalid track index: ignore the play request and log a clear message.
- Backend playback errors: log and keep the app usable.

## Testing

Add or update tests for:

- Folder scan returns sorted project-root MP3 files.
- Folder scan returns multiple tracks.
- Selecting a track updates title/source/current index.
- Seeking delegates to the player.
- Duration and position formatting.
- Persisted music folder/current index defaults and round trip.
- Controller folder/track/seek slots delegate to service.
- QML includes folder picker, track list, seek slider, and time labels.

## Scope Boundaries

This remains a local MP3 player only. No remote streaming, lyrics, album art, playlists beyond one selected folder, shuffle, repeat mode, or non-MP3 support is included.

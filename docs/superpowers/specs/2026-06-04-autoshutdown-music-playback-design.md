# AutoShutdownQt Music Playback Design

## Goal

Add a local music playback feature that starts automatically when AutoShutdownQt opens, while letting the user disable startup autoplay in Settings. The feature should use the MP3 file already placed in the project root and should not interfere with shutdown scheduling, dry-run safety, tray behavior, scripts, or triggers.

## User Experience

- On app launch, AutoShutdownQt searches the project root for the first `.mp3` file.
- If startup autoplay is enabled, the app begins playing that file automatically.
- The main UI gets a clear Music entry that opens a dedicated music player window.
- The music window shows the current song name and provides play/pause, stop, and volume controls.
- Settings gets a switch labeled for startup music autoplay. Turning it off persists the preference and prevents autoplay on the next launch.
- If no MP3 is found, the app starts normally, logs the missing-file state, and the music window shows that no music file is available.

## Architecture

Add a small `music_service.py` module responsible for finding and playing the local MP3. It wraps PySide6 multimedia objects (`QMediaPlayer` and `QAudioOutput`) behind a narrow interface so the controller and QML do not handle media setup directly.

Extend `AppController` with music-facing properties and slots:

- `musicAutoplayEnabled`: persisted setting exposed to Settings.
- `musicAvailable`: whether an MP3 was found.
- `musicTitle`: display name for the selected MP3.
- `musicPlaying`: playback state for the UI.
- `musicVolume`: volume percent.
- `playMusic()`, `pauseMusic()`, `stopMusic()`, and `requestMusicWindow()` style slots as needed by QML.

The app initializes the music service after creating the controller. If `musicAutoplayEnabled` is true and a file exists, playback starts once the app is ready.

## UI Components

Add a dedicated QML music player window, either as a component under `qml/components/` or inline if the existing app structure makes that simpler. The window should match the current Fluent Neon / starry glass styling and remain separate from the main command center content.

Main UI changes:

- Add a Music button in a low-disruption location, preferably the title bar or Settings area.
- Add a Settings switch for startup autoplay.
- Keep the existing navigation and power-action workflow unchanged.

Music window controls:

- Song title or “未找到音乐文件”.
- Play/Pause button.
- Stop button.
- Volume slider.

## Data Flow

1. `AppController` loads settings, including the new autoplay preference.
2. `music_service.py` scans the project root for `.mp3` files and stores the selected path.
3. On launch, if autoplay is enabled and music is available, the controller starts playback.
4. QML binds to controller properties to update title, availability, playback state, and volume.
5. User actions in QML call controller slots, which delegate to `music_service.py`.
6. Setting changes persist through the existing settings service.

## Error Handling

- Missing MP3: no exception should escape app startup; log a clear message and show unavailable state in the music window.
- Multimedia backend failure: log the playback error and leave the app usable.
- Unsupported/corrupt MP3: treat as playback failure, not an application failure.

## Testing

Add or update tests for:

- MP3 discovery from the project root.
- No-file case returns unavailable state without crashing.
- Autoplay setting defaults to enabled and persists when toggled off.
- Controller playback slots delegate correctly to the music service using test doubles.
- QML static regression checks for the music entry, player window, and Settings autoplay switch.

## Scope Boundaries

This feature only plays local MP3 files from the project root. It does not add playlists, remote streaming, lyric display, file picking, or background music tied to shutdown events. Those can be considered later if needed.

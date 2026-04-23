<div id="top"></div>

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/evangruhlkey/spotify-voice-control">
    <img src="assets/voiceskip-logo.svg" alt="Spotify Voice Control" width="80" height="80">
  </a>

  <h3 align="center">Spotify Voice Control</h3>

  <p align="center">
    A voice control utility for Spotify (and any app that listens to system media keys)
    ·
    <a href="https://github.com/evangruhlkey/spotify-voice-control/issues">Report Bug</a>
    ·
    <a href="https://github.com/evangruhlkey/spotify-voice-control/issues">Request Feature</a>
  </p>
</div>

![Spotify Voice Control](assets/image.png)

_Local speech on your PC, then media keys. No cloud for recognition._

### Built With

- [Python 3.10+](https://www.python.org/)
- [Vosk](https://alphacephei.com/vosk/) (offline speech)
- [sounddevice](https://python-sounddevice.readthedocs.io/) and [NumPy](https://numpy.org/)
- [spotipy](https://github.com/plamere/spotipy) (Spotify Web API when enabled in config)
- [pystray](https://github.com/moses-palmer/pystray) and [Pillow](https://python-pillow.org/) (system tray)

### Prerequisites

- [Windows 10 or newer](https://www.microsoft.com/windows)
- [Python 3.10+](https://www.python.org/downloads/)
- A working **microphone** as the default input (Settings, System, Sound, Input)
- The **Vosk** English model folder that ships with this repo (`vosk-model-small-en-us-0.15`), already referenced in `config.json`
- **Spotify Premium** is not required for normal use (media keys). Some Web API behavior may depend on your Spotify account and region.

### Installation

1. `git clone https://github.com/evangruhlkey/spotify-voice-control.git` and open that folder.

2. Install packages:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -U pip
   python -m pip install -r requirements.txt
   ```

3. The `vosk-model-small-en-us-0.15` folder should sit next to `main.py` with the same name as `model_path` in `config.json` (it already is in the default config).

4. Run **`python main.py`**.

**Spotify API (optional).** If you want API playback and the “connect to spotify” login flow, [create a Spotify app](https://developer.spotify.com/dashboard), add redirect `http://127.0.0.1:8888/callback`, put your `client_id` and `client_secret` in `config.json` under `spotify` (or use `SPOTIPY_CLIENT_ID` / `SPOTIPY_CLIENT_SECRET`), and set `"use_api": true`. The first time, your browser may open; the token is stored in `spotify_token.cache`.

### Usage

1. Run `python main.py`. The tray icon runs in the background; use **Enabled** to turn voice commands on or off, **Exit** to quit.
2. Say natural phrases you define in `config.json` under `commands`. Defaults include things like **“next song”**, **“skip this song”**, **“go forward”** for the next track.
3. Say **“previous song”**, **“go back a song”**, **“last song”** (and similar) for the previous track.
4. Say **“play music”**, **“resume music”**, **“unpause”** to play or resume (uses the system play or pause media key, or Spotify `start_playback` if the API is on).
5. Say **“pause the music”**, **“stop the music”**, **“pause it”** to pause or toggle playback.
6. Say **“open spotify”**, **“launch spotify”** to start or focus the Spotify desktop app (no API needed).
7. Say **“connect to spotify”** (or your listed phrases) to run Spotify account login in the browser when Web API is enabled.
8. Edit `config.json` to add more phrases. Longer phrases are matched before shorter ones. Use `command_cooldown_sec` if one line triggers twice.
9. Logs go to `spotify-voice-control.log` by default. Set `"log_level": "DEBUG"` to see more detail.

_Note: If the app stops responding, force quit with **Ctrl+C** in the console, or use **Exit** from the tray, then start again with `python main.py`._

## Future plans

Wake word or push-to-talk mode to cut down on random triggers. Maybe a faster core in another language later.

<!-- CONTRIBUTING -->

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### License

Add a `LICENSE` file when you publish. Third-party trademarks (e.g. Spotify) belong to their owners.

### Project layout

| File | Purpose |
|------|---------|
| `main.py` | Entry point, config, tray |
| `audio_listener.py` | Mic input and Vosk |
| `command_parser.py` | Phrase matching |
| `media_controller.py` | Windows media keys |
| `spotify_client.py` | Optional Spotify API |
| `spotify_launcher.py` | Launch or focus Spotify |

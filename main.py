"""
Spotify Voice Control: always-on mic, offline Vosk speech, Windows media keys, optional Spotify Web API.
Run: python main.py
"""
from __future__ import annotations

import json
import logging
import os
import sys
import threading
import time
from typing import Any, Dict

import media_controller
import spotify_client
import spotify_launcher

from command_parser import ParseResult, build_phrase_index, match_text

DEFAULT_CONFIG: Dict[str, Any] = {
    "model_path": "model",
    "sample_rate": 16000,
    "block_samples": 2000,
    "command_cooldown_sec": 1.2,
    "continuous_use_partial": False,
    "log_file": "spotify-voice-control.log",
    "log_level": "INFO",
    "tray": True,
    "spotify": {
        "use_api": False,
        "client_id": "",
        "client_secret": "",
        "redirect_uri": "http://127.0.0.1:8888/callback",
        "cache_path": "spotify_token.cache",
        "launch_exe": "",
    },
    "commands": {
        "next": [
            "skip to the next song",
            "go to the next track",
            "play the next one",
            "play the next song",
            "i want the next song",
            "skip this song",
            "skip to the next",
            "the next one",
            "next one",
            "next track",
            "next song",
            "skip song",
            "move forward",
            "go forward",
            "forward a song",
            "forward track",
        ],
        "previous": [
            "go back a song",
            "go back to the last",
            "play the previous one",
            "play the last song",
            "back to the last song",
            "the last one",
            "last one",
            "previous one",
            "previous track",
            "last track",
            "previous song",
            "last song",
            "go back",
            "back a song",
            "back one song",
            "back track",
        ],
        "play": [
            "play music",
            "resume music",
            "resume playback",
            "start the music",
            "start music",
            "start playing",
            "continue music",
            "continue playing",
            "keep playing",
            "unpause",
        ],
        "pause": [
            "stop the music",
            "stop playback",
            "pause playback",
            "toggle play pause",
            "toggle pause",
            "pause the music",
            "pause the song",
            "pause it",
            "pause music",
            "pause song",
            "play pause",
        ],
        "connect": [
            "connect to spotify",
            "log in to spotify",
            "login to spotify",
            "authorize spotify",
            "link my spotify",
            "spotify login",
        ],
        "open_spotify": [
            "open the spotify app",
            "open spotify",
            "launch spotify",
            "start spotify",
            "show spotify",
            "bring up spotify",
        ],
    },
}


def _app_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def load_config() -> Dict[str, Any]:
    path = os.path.join(_app_dir(), "config.json")
    if not os.path.isfile(path):
        return dict(DEFAULT_CONFIG)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    out = dict(DEFAULT_CONFIG)
    out.update(data)
    if "commands" in data and isinstance(data["commands"], dict):
        out["commands"] = {**DEFAULT_CONFIG["commands"], **data["commands"]}
    if "spotify" in data and isinstance(data["spotify"], dict):
        out["spotify"] = {**DEFAULT_CONFIG["spotify"], **data["spotify"]}
    return out


def setup_logging(log_file: str, level: str) -> None:
    lv = getattr(logging, (level or "INFO").upper(), logging.INFO)
    path = log_file
    if not os.path.isabs(path):
        path = os.path.join(_app_dir(), path)
    root = logging.getLogger()
    root.setLevel(min(lv, logging.DEBUG))
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    ch.setLevel(lv)
    root.addHandler(ch)
    fh = logging.FileHandler(path, encoding="utf-8")
    fh.setFormatter(fmt)
    fh.setLevel(logging.DEBUG)
    root.addHandler(fh)


def _dispatch(r: ParseResult, sp: object | None, cfg: Dict[str, Any]) -> None:
    if r.action == "next":
        logging.info("Action: next track (matched: %r)", r.matched)
        spotify_client.next_track(sp, media_controller.next_track)
    elif r.action == "previous":
        logging.info("Action: previous (matched: %r)", r.matched)
        spotify_client.previous_track(sp, media_controller.previous_track)
    elif r.action == "play":
        logging.info("Action: play / resume (matched: %r)", r.matched)
        spotify_client.play_music(sp, media_controller.play_pause)
    elif r.action == "pause":
        logging.info("Action: play/pause (matched: %r)", r.matched)
        spotify_client.play_pause(sp, media_controller.play_pause)
    elif r.action == "connect":
        logging.info("Action: connect Spotify (matched: %r)", r.matched)
        if not sp:
            logging.warning(
                "Spotify API is disabled or not configured. Set spotify.use_api and "
                "client_id / client_secret in config.json (see README), then pip install spotipy"
            )
            return
        spotify_client.connect_accounts(sp)
    elif r.action == "open_spotify":
        logging.info("Action: open Spotify app (matched: %r)", r.matched)
        spotify_launcher.open_spotify(cfg)


def main() -> None:
    if sys.platform != "win32":
        print("This application only supports Windows.", file=sys.stderr)
        sys.exit(1)

    cfg = load_config()
    setup_logging(str(cfg.get("log_file", "spotify-voice-control.log")), str(cfg.get("log_level", "INFO")))
    log = logging.getLogger("main")

    use_spotify = bool((cfg.get("spotify") or {}).get("use_api"))
    if use_spotify and not spotify_client.spotipy_available():
        log.error("Spotify is enabled in config but spotipy is not installed. Run: pip install spotipy")
    sp_client: object | None = spotify_client.build_client(cfg, _app_dir()) if use_spotify and spotify_client.spotipy_available() else None
    if use_spotify and sp_client is None and spotify_client.spotipy_available():
        log.warning("Spotify API enabled; add client_id and client_secret to config (or set SPOTIPY_* env vars).")
    if use_spotify and sp_client is not None:
        log.info("Spotify Web API: enabled (playback commands go to Spotify; failures fall back to media keys).")

    model_path = cfg.get("model_path", "model")
    if not os.path.isabs(str(model_path)):
        model_path = os.path.join(_app_dir(), str(model_path))

    phrase_index = build_phrase_index(cfg.get("commands") or {})  # type: ignore[arg-type]
    cooldown = float(cfg.get("command_cooldown_sec", 1.2))
    use_partial = bool(cfg.get("continuous_use_partial", False))

    from audio_listener import AudioListener  # import after path resolved

    try:
        listener = AudioListener(
            str(model_path),
            int(cfg.get("sample_rate", 16000)),
            int(cfg.get("block_samples", 2000)),
        )
    except FileNotFoundError as e:
        log.error("%s", e)
        sys.exit(1)

    stop = threading.Event()
    enabled = threading.Event()
    enabled.set()
    last_fire = [0.0]  # mutable from nested functions

    def try_handle(text: str) -> None:
        if not (text or "").strip():
            return
        if not enabled.is_set():
            return
        r = match_text(text, phrase_index)
        if r.action == "none":
            log.debug("No match: %r", text)
            return
        now = time.time()
        if now - last_fire[0] < cooldown:
            log.debug("Cooldown skip (%s)", r.action)
            return
        last_fire[0] = now
        _dispatch(r, sp_client, cfg)
        listener.reset()

    def listen_thread() -> None:
        def on_final(t: str) -> None:
            log.debug("Final segment: %r", t)
            try_handle(t)

        on_partial = (lambda p: try_handle(p)) if use_partial else None
        if use_partial:
            log.info("Partial matching enabled (snappier, more false triggers).")
        listener.listen_continuous(
            lambda: not stop.is_set(),
            on_final,
            on_partial,
        )

    t = threading.Thread(target=listen_thread, name="listen", daemon=True)
    t.start()

    use_tray = bool(cfg.get("tray", True))
    if use_tray:
        try:
            import pystray
        except ImportError:
            use_tray = False
            log.warning("pystray not installed; run without tray. pip install pystray Pillow")

    if use_tray:
        from PIL import Image, ImageDraw
        from pystray import Menu, MenuItem

        def on_quit2(icon: pystray.Icon, _item: object) -> None:
            stop.set()
            icon.stop()

        w, h = 64, 64
        im = Image.new("RGBA", (w, h), (30, 30, 30, 255))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([4, 4, w - 4, h - 4], radius=8, outline=(100, 200, 120, 255), width=3)
        d.text((6, 20), "SVC", fill=(200, 255, 200, 255))

        tray_icon = pystray.Icon(
            "SpotifyVoiceControl",
            im,
            "Spotify Voice Control. Always listening. Use the menu to enable, disable, or exit.",
            Menu(
                MenuItem(
                    "Enabled",
                    lambda: (enabled.clear() if enabled.is_set() else enabled.set()) or None,
                    checked=lambda i: enabled.is_set(),  # type: ignore[misc,arg-type]
                ),
                MenuItem("Exit", on_quit2),
            ),
        )
        log.info("Spotify Voice Control is running (mic on). Say a command. Tray: enable, disable, or exit.")
        tray_icon.run()
    else:
        log.info("Spotify Voice Control (no tray). Mic is on. Ctrl+C to stop.")
        try:
            while not stop.is_set():
                time.sleep(0.2)
        except KeyboardInterrupt:
            stop.set()


if __name__ == "__main__":
    main()

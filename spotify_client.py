"""
Optional Spotify Web API (spotipy). Triggers one-time browser login; token is cached to disk.
Falls back to system media keys when the API is disabled, missing credentials, or a call fails.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

SCOPES = "user-read-playback-state user-modify-playback-state"

try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
except ImportError:  # pragma: no cover
    spotipy = None
    SpotifyOAuth = None  # type: ignore[misc, assignment]


def spotipy_available() -> bool:
    return spotipy is not None and SpotifyOAuth is not None


def build_client(cfg: Dict[str, Any], app_dir: str) -> Optional[Any]:
    if not spotipy_available():
        return None
    s = cfg.get("spotify") or {}
    if not s.get("use_api"):
        return None
    cid = (s.get("client_id") or os.environ.get("SPOTIPY_CLIENT_ID") or "").strip()
    csec = (s.get("client_secret") or os.environ.get("SPOTIPY_CLIENT_SECRET") or "").strip()
    if not cid or not csec:
        logger.warning("spotify.use_api is true but client_id/client_secret are empty")
        return None
    redirect = s.get("redirect_uri") or "http://127.0.0.1:8888/callback"
    cache = s.get("cache_path") or "spotify_token.cache"
    if not os.path.isabs(str(cache)):
        cache = os.path.join(app_dir, str(cache))
    auth = SpotifyOAuth(  # type: ignore[union-attr]
        client_id=cid,
        client_secret=csec,
        redirect_uri=redirect,
        scope=SCOPES,
        cache_path=cache,
        open_browser=True,
    )
    return spotipy.Spotify(auth_manager=auth, retries=1, status_retries=0)  # type: ignore[union-attr]


def connect_accounts(sp: Any) -> bool:
    """Force OAuth: opens browser the first time; validates token. Say e.g. 'connect to spotify'."""
    try:
        u = sp.current_user()
        name = (u or {}).get("display_name") or (u or {}).get("id") or "account"
        logger.info("Spotify connected as: %s", name)
        return True
    except Exception as e:  # noqa: BLE001
        logger.exception("Spotify connect failed: %s", e)
        return False


def _try_api(sp: Any, name: str, fn: Any) -> bool:
    try:
        fn()
        return True
    except Exception as e:  # noqa: BLE001
        logger.warning("Spotify %s failed, using media keys: %s", name, e)
        return False


def next_track(sp: Optional[Any], media_next: Any) -> None:
    if sp and _try_api(sp, "next_track", sp.next_track):
        return
    media_next()


def previous_track(sp: Optional[Any], media_prev: Any) -> None:
    if sp and _try_api(sp, "previous_track", sp.previous_track):
        return
    media_prev()


def play_music(sp: Optional[Any], media_fallback: Any) -> None:
    """Resume or start playback (Spotify: start_playback; media: play/pause key — toggles on some setups)."""
    if sp and _try_api(sp, "start_playback", sp.start_playback):
        return
    media_fallback()


def play_pause(sp: Optional[Any], media_play_pause: Any) -> None:
    if not sp:
        media_play_pause()
        return
    try:
        pb = sp.current_playback()
        if pb and pb.get("is_playing"):
            if not _try_api(sp, "pause_playback", sp.pause_playback):
                media_play_pause()
        else:
            if not _try_api(sp, "start_playback", sp.start_playback):
                media_play_pause()
    except Exception as e:  # noqa: BLE001
        logger.warning("Spotify play/pause (read state) failed, using media keys: %s", e)
        media_play_pause()

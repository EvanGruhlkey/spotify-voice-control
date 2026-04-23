"""
Start or focus the Spotify desktop app (no Web API). Uses the spotify: protocol and common install paths.
"""
from __future__ import annotations

import logging
import os
import sys
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def _candidate_exe_paths() -> List[str]:
    return [
        os.path.join(os.environ.get("APPDATA", ""), "Spotify", "Spotify.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Spotify", "Spotify.exe"),
        os.path.join(os.environ.get("PROGRAMFILES", ""), "Spotify", "Spotify.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", "") or "", "Spotify", "Spotify.exe"),
    ]


def open_spotify(cfg: Dict[str, Any]) -> bool:
    """
    Try: config path → spotify: URI → known Spotify.exe locations.
    Returns True if a launch was attempted and likely succeeded.
    """
    s = cfg.get("spotify") or {}
    custom = (s.get("launch_exe") or "").strip()
    if custom:
        if os.path.isfile(custom):
            try:
                os.startfile(custom)  # type: ignore[attr-defined]
                logger.info("Launched Spotify (spotify.launch_exe): %s", custom)
                return True
            except OSError as e:
                logger.warning("Could not start %s: %s", custom, e)
        else:
            logger.warning("spotify.launch_exe is set but file not found: %s", custom)

    if sys.platform == "win32":
        try:
            os.startfile("spotify:")  # type: ignore[attr-defined]
            logger.info("Opened Spotify via spotify: URI")
            return True
        except OSError as e:
            logger.debug("spotify: URI failed: %s", e)

    for path in _candidate_exe_paths():
        if path and os.path.isfile(path):
            try:
                os.startfile(path)  # type: ignore[attr-defined]
                logger.info("Launched Spotify: %s", path)
                return True
            except OSError as e:
                logger.debug("Failed to start %s: %s", path, e)

    logger.error(
        "Spotify not found. Install the desktop app, or set spotify.launch_exe in config.json "
        "to the full path of Spotify.exe"
    )
    return False

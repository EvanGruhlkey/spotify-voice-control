"""
Map recognized free-text to actions: next | previous | play | pause | connect | open_spotify | none
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

Action = str  # "next" | "previous" | "pause" | "none"


@dataclass(frozen=True)
class ParseResult:
    action: Action
    matched: Optional[str] = None


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def build_phrase_index(commands: Dict[str, list]) -> List[Tuple[str, str]]:
    """Longer phrases first so we prefer specific matches over substrings."""
    rows: list[tuple[str, str]] = []
    for action_key, phrases in commands.items():
        if action_key not in ("next", "previous", "play", "pause", "connect", "open_spotify"):
            continue
        for p in phrases:
            n = _norm(p)
            if n:
                rows.append((n, action_key))
    rows.sort(key=lambda t: -len(t[0]))
    return rows


def match_text(text: str, phrase_index: List[Tuple[str, str]]) -> ParseResult:
    n = _norm(text)
    if not n:
        return ParseResult("none")
    for phrase, action in phrase_index:
        if phrase in n:
            return ParseResult(action, phrase)
    return ParseResult("none")

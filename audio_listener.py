"""
Microphone capture (sounddevice) + Vosk offline recognition.
No cloud APIs. Model path must point to a Vosk model directory.
"""
from __future__ import annotations

import json
import logging
import os
import threading
from typing import Callable, Optional

import numpy as np
import sounddevice as sd
from vosk import KaldiRecognizer, Model

logger = logging.getLogger(__name__)


class AudioListener:
    def __init__(self, model_path: str, sample_rate: int, block_samples: int) -> None:
        self._sample_rate = sample_rate
        self._block_samples = max(512, int(block_samples))
        self._model = Model(model_path)
        self._lock = threading.Lock()
        self._rec = KaldiRecognizer(self._model, sample_rate)

    def reset(self) -> None:
        with self._lock:
            self._rec = KaldiRecognizer(self._model, self._sample_rate)

    def _float_chunk_to_vosk(self, indata: np.ndarray) -> bytes:
        if indata.size == 0:
            return b""
        audio_i16 = (indata * 32767.0).clip(-32768, 32767).astype(np.int16)
        return audio_i16.tobytes()

    def listen_continuous(
        self,
        should_run: Callable[[], bool],
        on_final: Callable[[str], None],
        on_partial: Optional[Callable[[str], None]] = None,
    ) -> None:
        """
        Stream the mic while should_run is True. Invokes on_final for each
        Vosk finalized segment. Optionally on_partial for low-latency (more false triggers).
        """
        self.reset()
        with sd.InputStream(
            channels=1,
            samplerate=self._sample_rate,
            blocksize=self._block_samples,
            dtype="float32",
        ) as stream:
            while should_run():
                try:
                    indata, overflowed = stream.read(self._block_samples)
                except Exception:  # noqa: BLE001
                    logger.exception("read failed")
                    break
                if overflowed:
                    logger.debug("input overflow")
                if indata.size == 0:
                    continue
                chunk = self._float_chunk_to_vosk(indata)
                if not chunk:
                    continue
                final_t: Optional[str] = None
                partial_t: Optional[str] = None
                with self._lock:
                    if self._rec.AcceptWaveform(chunk):
                        j = json.loads(self._rec.Result() or "{}")
                        t = (j.get("text") or "").strip()
                        if t:
                            final_t = t
                    elif on_partial is not None:
                        p = json.loads(self._rec.PartialResult() or "{}")
                        pt = (p.get("partial") or "").strip()
                        if pt:
                            partial_t = pt
                if final_t is not None:
                    logger.debug("final segment: %s", final_t)
                    on_final(final_t)
                elif partial_t is not None and on_partial is not None:
                    on_partial(partial_t)
        logger.info("Continuous listen stopped.")

    def listen_while(
        self,
        should_continue: Callable[[], bool],
    ) -> str:
        """
        Open mic, stream PCM to Vosk until `should_continue` is False.
        Returns best-effort final transcript (may be empty).
        """
        self.reset()
        text_parts: list[str] = []
        with sd.InputStream(
            channels=1,
            samplerate=self._sample_rate,
            blocksize=self._block_samples,
            dtype="float32",
        ) as stream:
            while should_continue():
                try:
                    indata, overflowed = stream.read(self._block_samples)
                except Exception:  # noqa: BLE001
                    logger.exception("read failed")
                    break
                if overflowed:
                    logger.debug("input overflow")
                if indata.size == 0:
                    continue
                chunk = self._float_chunk_to_vosk(indata)
                if not chunk:
                    continue
                with self._lock:
                    if self._rec.AcceptWaveform(chunk):
                        j = json.loads(self._rec.Result() or "{}")
                        t = (j.get("text") or "").strip()
                        if t:
                            text_parts.append(t)
                            logger.debug("final segment: %s", t)
                    else:
                        p = json.loads(self._rec.PartialResult() or "{}")
                        pt = (p.get("partial") or "").strip()
                        if pt:
                            logger.debug("partial: %s", pt)
        with self._lock:
            j = json.loads(self._rec.FinalResult() or "{}")
            t = (j.get("text") or "").strip()
            if t:
                text_parts.append(t)
        out = " ".join(text_parts).strip()
        logger.info("Heard: %r", out)
        return out

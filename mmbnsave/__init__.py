"""Decode Mega Man Battle Network saves into a common progress model.

    from mmbnsave import read_progress
    progress = read_progress("playground/save files/m1.sav")
"""
from pathlib import Path

from .engine import DecodedSave, SaveError, decode, identify
from .progress import Progress, build_progress

__all__ = ["DecodedSave", "Progress", "SaveError", "decode", "identify", "build_progress", "read_progress"]


def read_progress(path_or_bytes) -> Progress:
    data = path_or_bytes if isinstance(path_or_bytes, (bytes, bytearray)) else Path(path_or_bytes).read_bytes()
    return build_progress(decode(bytes(data)))

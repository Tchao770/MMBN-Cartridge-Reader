"""One progress model shared by every game, so the UI is written once.

Conventions a layout follows to feed this model:
  * fields named ``zenny``, ``hp_max``, ``play_time_frames`` → ``stats``
  * named flags starting with ``star_``                     → ``stars``
  * the ``[story]`` table                                   → ``story``
  * the ``[library]`` table                                 → ``library``
  * every other field                                       → ``extras``
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .engine import DecodedSave

CORE_STATS = ("zenny", "hp_max", "play_time_frames")
FRAMES_PER_SECOND = 60


@dataclass
class Story:
    value: int
    label: str | None
    chapter: int | None
    chapters: int | None
    reached_final: bool


@dataclass
class Library:
    standard_owned: int
    standard_total: int
    secret_owned: list[str]
    secret_total: int
    groups: dict[str, dict[str, int]]
    missing: list[str]

    @property
    def percent(self) -> float:
        return round(100 * self.standard_owned / self.standard_total, 1) if self.standard_total else 0.0


@dataclass
class Progress:
    game_id: str
    game_name: str
    checksum_ok: bool
    story: Story | None
    stars: dict[str, bool]
    library: Library | None
    stats: dict[str, int | str]
    extras: dict[str, dict]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        if self.library:
            d["library"]["percent"] = self.library.percent
        return d


def format_play_time(frames: int) -> str:
    minutes = frames // (FRAMES_PER_SECOND * 60)
    return f"{minutes // 60}h {minutes % 60:02d}m"


def _story(save: DecodedSave) -> Story | None:
    spec = save.layout.story
    if not spec:
        return None
    value = save.fields[spec["field"]]
    shift = spec.get("chapter_shift")
    final = spec.get("final")
    return Story(
        value=value,
        label=save.layout.story_labels.get(value),
        chapter=(value >> shift) + 1 if shift is not None else None,
        chapters=spec.get("chapters"),
        reached_final=final is not None and value >= final,
    )


def _library(save: DecodedSave) -> Library | None:
    lay = save.layout
    if lay.library_flag_offset is None:
        return None
    owned = {cid for cid in lay.library_chips if save.flag(lay.library_flag_offset + cid)}
    standard = [cid for cid in lay.library_chips if cid not in lay.library_secret]
    groups = {}
    for name, (first, last) in lay.library_groups.items():
        ids = [cid for cid in lay.library_chips if first <= cid <= last]
        groups[name] = {"owned": len(owned.intersection(ids)), "total": len(ids)}
    return Library(
        standard_owned=sum(1 for cid in standard if cid in owned),
        standard_total=len(standard),
        secret_owned=[lay.library_chips[c] for c in sorted(lay.library_secret & owned)],
        secret_total=len(lay.library_secret),
        groups=groups,
        missing=[lay.library_chips[c] for c in sorted(standard) if c not in owned],
    )


def build_progress(save: DecodedSave) -> Progress:
    lay = save.layout
    warnings = []
    if not save.checksum_ok:
        warnings.append(
            f"Checksum mismatch (stored {save.checksum_stored:#x}, computed {save.checksum_computed:#x}): "
            "the game itself would reject this save. Values below may be garbage."
        )

    stats: dict[str, int | str] = {}
    extras: dict[str, dict] = {}
    for name, value in save.fields.items():
        spec = lay.fields[name]
        if spec.max is not None and not isinstance(value, bool) and value > spec.max:
            warnings.append(f"{name} = {value} is above the game's maximum of {spec.max} (edited save?)")
        if name in CORE_STATS:
            stats[name] = value
        elif lay.story and name == lay.story.get("field"):
            continue
        else:
            extras[name] = {"value": value, "max": spec.max}
    if "play_time_frames" in stats:
        stats["play_time"] = format_play_time(stats["play_time_frames"])

    return Progress(
        game_id=lay.id,
        game_name=lay.name,
        checksum_ok=save.checksum_ok,
        story=_story(save),
        stars={k: v for k, v in save.flags.items() if k.startswith("star_")},
        library=_library(save),
        stats=stats,
        extras=extras,
        warnings=warnings,
    )

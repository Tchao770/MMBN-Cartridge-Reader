"""Load per-game save layouts from the TOML files in ``layouts/``.

A layout is pure data: where each value lives in the save, how the checksum is
computed, which flags mean what. Adding a game means writing a new TOML file,
not new Python.
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

LAYOUT_DIR = Path(__file__).parent / "layouts"

FIELD_TYPES = {"u8": 1, "u16": 2, "u32": 4, "bool": 1}


@dataclass(frozen=True)
class FieldSpec:
    name: str
    offset: int
    type: str
    max: int | None = None

    @property
    def size(self) -> int:
        return FIELD_TYPES[self.type]


@dataclass(frozen=True)
class Layout:
    id: str
    name: str
    region: str
    save_length: int
    signature_offset: int
    signature: bytes
    rom_game_codes: tuple[str, ...]
    checksum: dict
    flag_base: int
    flag_bit_order: str
    named_flags: dict[str, int]
    fields: dict[str, FieldSpec]
    story: dict
    story_labels: dict[int, str]
    library_flag_offset: int | None
    library_chips: dict[int, str]
    library_secret: frozenset[int]
    library_groups: dict[str, tuple[int, int]] = field(default_factory=dict)


def _parse(raw: dict) -> Layout:
    game = raw["game"]
    sig = game["signature"]
    flags = raw.get("flags", {})
    lib = raw.get("library", {})
    fields = {}
    for name, spec in raw.get("fields", {}).items():
        if spec["type"] not in FIELD_TYPES:
            raise ValueError(f"{game['id']}: field {name!r} has unknown type {spec['type']!r}")
        fields[name] = FieldSpec(name, spec["offset"], spec["type"], spec.get("max"))
    story = dict(raw.get("story", {}))
    labels = {int(k): v for k, v in story.pop("labels", {}).items()}
    return Layout(
        id=game["id"],
        name=game["name"],
        region=game.get("region", ""),
        save_length=game["save_length"],
        signature_offset=sig["offset"],
        signature=sig["ascii"].encode("ascii"),
        rom_game_codes=tuple(game.get("rom_game_codes", ())),
        checksum=raw.get("checksum", {}),
        flag_base=flags.get("base", 0),
        flag_bit_order=flags.get("bit_order", "msb"),
        named_flags=dict(flags.get("named", {})),
        fields=fields,
        story=story,
        story_labels=labels,
        library_flag_offset=lib.get("flag_offset"),
        library_chips={int(k): v for k, v in lib.get("chips", {}).items()},
        library_secret=frozenset(lib.get("secret", ())),
        library_groups={k: (v["first"], v["last"]) for k, v in lib.get("groups", {}).items()},
    )


@cache
def all_layouts() -> tuple[Layout, ...]:
    layouts = []
    for path in sorted(LAYOUT_DIR.glob("*.toml")):
        with path.open("rb") as f:
            layouts.append(_parse(tomllib.load(f)))
    return tuple(layouts)


def get_layout(game_id: str) -> Layout:
    for layout in all_layouts():
        if layout.id == game_id:
            return layout
    raise KeyError(f"No layout for game {game_id!r}")

"""Generic save decoder: identify the game, verify the checksum, read fields and flags."""
from __future__ import annotations

from dataclasses import dataclass

from .layout import FieldSpec, Layout, all_layouts


class SaveError(Exception):
    """The bytes can't be decoded as a save for any known game."""


@dataclass
class DecodedSave:
    layout: Layout
    data: bytes
    checksum_ok: bool
    checksum_stored: int | None
    checksum_computed: int | None
    fields: dict[str, int | bool]
    flags: dict[str, bool]

    def flag(self, index: int) -> bool:
        return read_flag(self.layout, self.data, index)


def is_blank(data: bytes) -> bool:
    """All 0x00 or all 0xFF: nothing saved, or a dead battery / bad contact."""
    return len(set(data)) <= 1 and (not data or data[0] in (0x00, 0xFF))


def identify(data: bytes) -> Layout:
    """Pick the layout whose signature (e.g. a build-ID string) appears at its offset."""
    for layout in all_layouts():
        end = layout.signature_offset + len(layout.signature)
        if data[layout.signature_offset:end] == layout.signature:
            return layout
    if is_blank(data):
        raise SaveError("Save is blank (all 0x00 or 0xFF) — no game saved, or a dead battery / bad read")
    raise SaveError("Save doesn't match any known game signature")


def read_field(data: bytes, spec: FieldSpec) -> int | bool:
    raw = data[spec.offset:spec.offset + spec.size]
    if len(raw) != spec.size:
        raise SaveError(f"Field {spec.name!r} at {spec.offset:#x} is past the end of the save")
    value = int.from_bytes(raw, "little")
    return bool(value) if spec.type == "bool" else value


def read_flag(layout: Layout, data: bytes, index: int) -> bool:
    byte = data[layout.flag_base + index // 8]
    bit = index % 8
    mask = (0x80 >> bit) if layout.flag_bit_order == "msb" else (1 << bit)
    return bool(byte & mask)


def compute_checksum(layout: Layout, data: bytes) -> tuple[int, int]:
    """Return (stored, computed) for a layout's checksum. Only `byte_sum` exists so far."""
    spec = layout.checksum
    if spec.get("kind") != "byte_sum":
        raise NotImplementedError(f"checksum kind {spec.get('kind')!r}")
    off = spec["offset"]
    stored = int.from_bytes(data[off:off + 4], "little")
    region = bytearray(data[spec["start"]:spec["end"]])
    rel = off - spec["start"]
    region[rel:rel + 4] = b"\0\0\0\0"   # the game zeroes the field before summing
    computed = (sum(region) + spec.get("add", 0)) & 0xFFFFFFFF
    return stored, computed


def decode(data: bytes, layout: Layout | None = None) -> DecodedSave:
    """Decode a raw save (32 KB cart dump or 64 KB emulator .sav both work)."""
    layout = layout or identify(data)
    if len(data) < layout.save_length:
        raise SaveError(f"Save is {len(data)} bytes; {layout.name} needs {layout.save_length}")

    stored = computed = None
    checksum_ok = True
    if layout.checksum:
        stored, computed = compute_checksum(layout, data)
        checksum_ok = stored == computed

    return DecodedSave(
        layout=layout,
        data=bytes(data),
        checksum_ok=checksum_ok,
        checksum_stored=stored,
        checksum_computed=computed,
        fields={name: read_field(data, spec) for name, spec in layout.fields.items()},
        flags={name: read_flag(layout, data, idx) for name, idx in layout.named_flags.items()},
    )

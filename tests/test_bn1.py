"""Golden-file tests for BN1.

Every expected value here was cross-checked against the Silenthal/bn1 disassembly
(see the header of mmbnsave/layouts/bn1.toml) — not just copied from the decoder's output.
"""
from pathlib import Path

import pytest

from mmbnsave import SaveError, decode, read_progress

SAVES = Path(__file__).parent.parent / "playground" / "save files"
M1 = SAVES / "m1.sav"                # 32 KB, 100% save (looks edited: 65535 battles)
ORGANIC = SAVES / "mmbn1.2104.sav"   # 64 KB emulator save, mid-postgame


def test_identifies_bn1_by_build_id():
    assert decode(M1.read_bytes()).layout.id == "bn1"
    assert decode(ORGANIC.read_bytes()).layout.id == "bn1"


@pytest.mark.parametrize("path", [M1, ORGANIC])
def test_checksum_matches_game_algorithm(path):
    save = decode(path.read_bytes())
    assert save.checksum_ok, (hex(save.checksum_stored), hex(save.checksum_computed))


def test_m1_complete_save():
    p = read_progress(M1)
    assert p.stars == {"star_game_cleared": True}
    assert p.story.value == 84 and p.story.label == "Final" and p.story.chapter == 6
    assert (p.library.standard_owned, p.library.standard_total) == (175, 175)
    assert p.library.secret_owned == ["Bass"]
    assert p.library.groups["navi"] == {"owned": 48, "total": 48}
    assert p.stats["hp_max"] == 1000
    assert p.stats["zenny"] == 16530
    assert p.stats["play_time"] == "27h 38m"           # 5,971,938 frames / 60
    assert p.extras["hp_memories"]["value"] == 45      # 100 + 45*20 = 1000 HP
    assert [p.extras[f"buster_{s}"]["value"] for s in ("attack", "speed", "charge")] == [4, 4, 4]
    assert p.warnings == []


def test_organic_save():
    p = read_progress(ORGANIC)
    assert p.stars == {"star_game_cleared": False}     # star is only set after the credits
    assert p.story.value == 84
    assert p.library.standard_owned == 77
    assert p.library.secret_owned == []
    assert p.library.groups["navi"]["owned"] == 9
    assert p.stats["hp_max"] == 820
    assert p.extras["hp_memories"]["value"] == 36      # 100 + 36*20 = 820 HP
    assert p.stats["play_time"] == "12h 18m"           # 2,658,641 frames / 60
    # 0xFFFFF zenny is above the game's own 999,999 cap → flagged, not silently clamped
    assert p.stats["zenny"] == 1048575
    assert any("zenny" in w for w in p.warnings)


def test_hp_formula_consistent():
    """HP max must equal 100 + 20 * HPMemory (key_item.S) — catches a wrong offset for either."""
    for path in (M1, ORGANIC):
        p = read_progress(path)
        assert p.stats["hp_max"] == 100 + 20 * p.extras["hp_memories"]["value"]


def test_cart_sized_dump_equals_emulator_save():
    """A real cart is 32 KB; emulator .sav files can be 64 KB. Only the first 0x2308 bytes matter."""
    full = ORGANIC.read_bytes()
    assert read_progress(full[:0x8000]).to_dict() == read_progress(full).to_dict()


def test_corrupted_save_fails_checksum():
    data = bytearray(M1.read_bytes())
    data[0x284] ^= 0x01                                # flip one bit of zenny
    p = read_progress(bytes(data))
    assert not p.checksum_ok
    assert any("Checksum" in w for w in p.warnings)


@pytest.mark.parametrize("fill", [0x00, 0xFF])
def test_blank_save_is_reported(fill):
    with pytest.raises(SaveError, match="blank"):
        decode(bytes([fill]) * 0x8000)


def test_unknown_game_is_rejected():
    with pytest.raises(SaveError, match="signature"):
        decode((SAVES / "m2.sav").read_bytes())

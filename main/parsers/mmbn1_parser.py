import struct
from base_parser import BaseMMBNParser

class MMBN1Parser(BaseMMBNParser):
    """Specialized Decoder Blueprint for Battle Network 1 (Slot 1)."""

    LIBRARY_START = 0x0460
    TOTAL_CHIPS_IN_GAME = 176

    NAVI_META = {
        128: "Roll",
        131: "GutsMan",
        134: "ProtoMan",
        137: "FireMan",
        140: "NumberMan",
        143: "StoneMan",
        146: "IceMan",
        149: "ColorMan",
        152: "ElecMan",
        155: "BombMan",
        158: "MagicMan",
        161: "WoodMan",
        164: "SkullMan",
        167: "SharkMan",
    }

    def run_extraction_pipeline(self):
        # 1. Decode Game-Specific Currencies and HP Offsets
        # Unpack as integer directly from tuple indices [0]
        raw_hp = struct.unpack("<H", self.raw_bytes[0x022C:0x022E])[0]
        raw_zenny = struct.unpack("<I", self.raw_bytes[0x0224:0x0228])[0]

        # 2. Assign and Roll-up Properties directly to Base Class State
        self.max_hp = raw_hp
        self.zenny = min(raw_zenny, 999999)  # Handle UI visual overflows safely
        self.game_completed_star = self.read_bit(0x0001, 4)

        hours = self.raw_bytes[0x0018]
        minutes = self.raw_bytes[0x0019]
        self.playtime = f"{hours}h {minutes}m"

    def extract_navi_boss_chips(self) -> dict:
        unlocked_boss_chips = {}
        for base_id, navi_name in self.NAVI_META.items():
            navi_tier_status = {}
            for tier_offset, tier_label in enumerate(["V1", "V2", "V3"]):
                target_chip_id = base_id + tier_offset
                byte_idx = (target_chip_id - 1) // 8
                bit_idx = (target_chip_id - 1) % 8

                navi_tier_status[tier_label] = self.read_bit(
                    self.LIBRARY_START + byte_idx, bit_idx
                )
            unlocked_boss_chips[navi_name] = navi_tier_status

        # Extract Bass (Chip #176)
        bass_byte_idx = (176 - 1) // 8
        bass_bit_idx = (176 - 1) % 8
        unlocked_boss_chips["Bass"] = {
            "SecretStandalone": self.read_bit(
                self.LIBRARY_START + bass_byte_idx, bass_bit_idx
            )
        }

        return {
            "boss_library_matrix": unlocked_boss_chips,
            "total_collected": sum(
                sum(t.values()) for t in unlocked_boss_chips.values()
            ),
            "all_navi_chips_found": all(
                all(t.values()) for t in unlocked_boss_chips.values()
            ),
        }

    def extract_megaman_powerups(self) -> dict:
        raw_atk = self.raw_bytes[0x0224]
        raw_spd = self.raw_bytes[0x0225]
        raw_chg = self.raw_bytes[0x0226]
        total_powerups = raw_atk + raw_spd + raw_chg
        hp_memories = (self.max_hp - 100) // 20

        return {
            "buster_levels": {
                "attack": raw_atk + 1,
                "speed": raw_spd + 1,
                "charge": raw_chg + 1,
            },
            "total_powerups_distributed": total_powerups,
            "all_powerups_found": total_powerups == 12,
            "hp_stats": {
                "max_hp_value": self.max_hp,
                "hp_memories_consumed": hp_memories,
                "all_hp_memories_found": hp_memories == 45,
            },
        }

    def parse_save_block(self) -> dict:
        try:
            # Step 1: Run the mandatory base class alignment pipeline
            self.run_extraction_pipeline()

            # Step 2: Fetch nested sub-structures
            chip_completion = self.parse_bitmask_range(
                self.LIBRARY_START, self.TOTAL_CHIPS_IN_GAME
            )
            powerups = self.extract_megaman_powerups()
            navi_chips = self.extract_navi_boss_chips()

            # Step 3: Compute localized arithmetic records
            total_earned = (
                chip_completion["total_collected"]
                + powerups["hp_stats"]["hp_memories_consumed"]
                + powerups["total_powerups_distributed"]
            )
            max_possible = self.TOTAL_CHIPS_IN_GAME + 45 + 12
            overall_pct = round((total_earned / max_possible) * 100, 2)

            # Step 4: Map cleanly directly back to MainOrchestrator variables
            return {
                "game": "Mega Man Battle Network 1",
                "variant": "Standard Edition",
                "status": "SUCCESS",
                "zenny": self.zenny,
                "max_hp": self.max_hp,
                "playtime": self.playtime,
                "game_completed_star": self.game_completed_star,
                "completion_percentage": f"{overall_pct}%",
                "chip_completion": chip_completion,
                "powerups": powerups,
                "navi_chips": navi_chips,
            }
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}


# Main hardware module interface hook execution
def parse_save_block(raw_bytes: bytes) -> dict:
    parser_instance = MMBN1Parser(raw_bytes)
    return parser_instance.parse_save_block()

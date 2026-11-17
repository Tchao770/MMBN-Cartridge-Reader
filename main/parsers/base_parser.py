import abc


class BaseMMBNParser(abc.ABC):
    """Abstract Base Class providing universal binary manipulation methods

    and a standardized telemetry payload contract for the whole series.
    """

    def __init__(self, raw_bytes: bytes):
        self.raw_bytes = raw_bytes

        # Universal Core Stats initialized at zero, populated by child extraction routines
        self.zenny = 0
        self.max_hp = 100
        self.game_completed_star = False
        self.playtime = "0h 0m"

    def read_bit(self, offset: int, bit_index: int) -> bool:
        """Universal utility to check an individual flag bit."""
        if offset >= len(self.raw_bytes):
            return False
        return (self.raw_bytes[offset] & (1 << bit_index)) != 0

    def parse_bitmask_range(self, start_offset: int, total_items: int) -> dict:
        """Universal routine to unpack continuous chip libraries and flag tables."""
        catalog = {}
        total_collected = 0
        total_bytes = (total_items + 7) // 8

        for byte_idx in range(total_bytes):
            current_offset = start_offset + byte_idx
            if current_offset >= len(self.raw_bytes):
                break
            current_byte = self.raw_bytes[current_offset]

            for bit_idx in range(8):
                global_id = (byte_idx * 8) + bit_idx + 1
                if global_id <= total_items:
                    is_unlocked = (current_byte & (1 << bit_idx)) != 0
                    catalog[f"chip_{global_id:03d}"] = is_unlocked
                    if is_unlocked:
                        total_collected += 1

        return {
            "catalog_flags": catalog,
            "total_collected": total_collected,
            "all_chips_retrieved": total_collected == total_items,
            "percentage_complete": round((total_collected / total_items) * 100, 2)
            if total_items > 0
            else 0.0,
        }

    @abc.abstractmethod
    def run_extraction_pipeline(self):
        """Forces the child class to assign self.zenny, self.max_hp, self.game_completed_star,

        and self.playtime using its unique internal hex offsets.
        """
        pass

    @abc.abstractmethod
    def parse_save_block(self) -> dict:
        """Compiles the final structural dictionary payload."""
        pass

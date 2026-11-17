import struct

def parse_save_block(raw_bytes):
    """Parses Mega Man Battle Network 3 and identifies White vs Blue versions."""
    try:
        # Checksum algorithm validation
        stored_chk = struct.unpack("<H", raw_bytes[0x1DD8:0x1DDA])[0]
        raw_sum = sum(raw_bytes[0x0000:0x57B0])
        
        calc_white = (raw_sum + 0x16) & 0xFFFF
        calc_blue = (raw_sum + 0x22) & 0xFFFF
        
        variant = "White Version" if stored_chk == calc_white else "Blue Version" if stored_chk == calc_blue else "Custom/Unknown"
        
        hours = raw_bytes[0x0012]
        minutes = raw_bytes[0x0013]
        zenny = struct.unpack("<I", raw_bytes[0x001C:0x0020])[0]
        bugfrags = struct.unpack("<H", raw_bytes[0x0020:0x0022])[0]
        max_hp = struct.unpack("<H", raw_bytes[0x011C:0x011E])[0]
        
        return {
            "game": "Mega Man Battle Network 3",
            "variant": variant,
            "zenny": zenny,
            "bugfrags": bugfrags,
            "max_hp": max_hp,
            "playtime": f"{hours}h {minutes}m",
            "status": "SUCCESS"
        }
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

import struct

def parse_save_block(raw_bytes):
    """Parses Mega Man Battle Network 6 VOLT engine parameters."""
    try:
        # Detect Gregar vs Falzar via text markers
        variant = "Cybeast Gregar" if b"GREGAR" in raw_bytes else "Cybeast Falzar" if b"FALZAR" in raw_bytes else "Standard"
        
        zenny = struct.unpack("<I", raw_bytes[0x0030:0x0034])[0]
        bugfrags = struct.unpack("<H", raw_bytes[0x0034:0x0036])[0]
        max_hp = struct.unpack("<H", raw_bytes[0x0154:0x0156])[0]
        
        return {
            "game": "Mega Man Battle Network 6",
            "variant": variant,
            "zenny": zenny,
            "bugfrags": bugfrags,
            "max_hp": max_hp,
            "playtime": "Unknown (VOLT Encoded)",
            "status": "SUCCESS"
        }
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

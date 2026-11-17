import struct

def parse_save_block(raw_bytes):
    """Parses Mega Man Battle Network 2 layouts."""
    try:
        hours = raw_bytes[0x0012]
        minutes = raw_bytes[0x0013]
        zenny = struct.unpack("<I", raw_bytes[0x001C:0x0020])[0]
        bugfrags = struct.unpack("<H", raw_bytes[0x0020:0x0022])[0]
        max_hp = struct.unpack("<H", raw_bytes[0x011C:0x011E])[0]
        
        return {
            "game": "Mega Man Battle Network 2",
            "variant": "Standard Edition",
            "zenny": zenny,
            "bugfrags": bugfrags,
            "max_hp": max_hp,
            "playtime": f"{hours}h {minutes}m",
            "status": "SUCCESS"
        }
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

# MMBN-Cartridge-Reader

Reads Mega Man Battle Network save data (from a GBA cartridge or an emulator `.sav`) and turns it into collector-friendly progress: story chapter, title-screen stars, chip library, HP, zenny, play time.

## Save decoder (`mmbnsave/`)

```
python -m mmbnsave "playground/save files/m1.sav"          # human-readable summary
python -m mmbnsave "playground/save files/m1.sav" --json   # full progress model
python -m pytest                                            # golden-file tests
```

Requires Python 3.11+ (uses the standard-library `tomllib`; no other dependencies).

- **Each game's save layout is data**, in `mmbnsave/layouts/<game>.toml`: offsets, types, checksum, flags, chip list. Adding a game means writing a TOML file, not new Python.
- **Offsets come from the community disassemblies**, with the source of each one noted in the layout file. BN1 uses [Silenthal/bn1](https://github.com/Silenthal/bn1). `tools/gen_bn1_tables.py` regenerates the chip and story tables from it.
- **The game's own checksum is verified** before any values are trusted. Blank (all `00`/`FF`) saves are reported, which can mean a dead battery or a bad read.
- **Cart dumps (32 KB) and emulator saves (64 KB) decode identically.**

| Game | Layout | Status |
|---|---|---|
| BN1 (USA) | `bn1.toml` | ✅ verified against 2 saves |
| BN2–BN6 | — | old parsers in `main/parsers/` still to be migrated |

`main/parsers/mmbn1_parser.py` is superseded by `mmbnsave` (several of its offsets were wrong).

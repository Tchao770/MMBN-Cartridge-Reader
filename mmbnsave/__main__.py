"""CLI: python -m mmbnsave SAVE [SAVE ...] [--json]"""
import argparse
import json
import sys

from . import SaveError, read_progress


def print_summary(path, p):
    print(f"== {path}")
    print(f"   {p.game_name}   checksum: {'OK' if p.checksum_ok else 'BAD'}")
    if p.story:
        s = p.story
        chapter = f"scenario {s.chapter}/{s.chapters}, " if s.chapter else ""
        print(f"   Story:    {chapter}{s.label or s.value}{'  (final)' if s.reached_final else ''}")
    for name, on in p.stars.items():
        print(f"   Star:     {name.removeprefix('star_').replace('_', ' ')}: {'★' if on else '☆'}")
    if p.library:
        lib = p.library
        print(f"   Library:  {lib.standard_owned}/{lib.standard_total} ({lib.percent}%)"
              + (f"  + secret: {', '.join(lib.secret_owned)}" if lib.secret_owned else ""))
        for g, c in lib.groups.items():
            print(f"             {g}: {c['owned']}/{c['total']}")
    st = p.stats
    if st:
        print(f"   Stats:    HP {st.get('hp_max')}   Zenny {st.get('zenny'):,}   Time {st.get('play_time')}")
    for name, e in p.extras.items():
        cap = f"/{e['max']}" if e["max"] is not None else ""
        print(f"   {name:<17} {e['value']}{cap}")
    for w in p.warnings:
        print(f"   ! {w}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mmbnsave", description=__doc__)
    ap.add_argument("saves", nargs="+")
    ap.add_argument("--json", action="store_true", help="print the full progress model as JSON")
    args = ap.parse_args(argv)
    status = 0
    for path in args.saves:
        try:
            p = read_progress(path)
        except (SaveError, OSError) as e:
            print(f"== {path}\n   ! {e}", file=sys.stderr)
            status = 1
            continue
        if args.json:
            print(json.dumps({"file": path, **p.to_dict()}, indent=2))
        else:
            print_summary(path, p)
    return status


if __name__ == "__main__":
    sys.exit(main())

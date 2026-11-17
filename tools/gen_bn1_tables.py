"""Print TOML tables (chip names, story flags) extracted from the BN1 disassembly.

Usage: python3 -I gen_bn1_tables.py /path/to/bn1
"""
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])

chips = {}
for line in (root / "include/constants/battlechip.inc").read_text().splitlines():
    m = re.match(r"\s*\.set CD_(\w+),\s*(\d+)", line)
    if m:
        chips[int(m.group(2))] = m.group(1).replace("_", "-")

enum = (root / "include/mmbn.h").read_text()
body = re.search(r"typedef enum StoryFlag \{(.*?)\} StoryFlag;", enum, re.S).group(1)
story = {}
for name, val in re.findall(r"FLAG_STORY_(\w+)=(\d+)", body):
    story[int(val)] = name.replace("_", " ").title()

print("[library.chips]")
for cid in sorted(chips):
    if cid == 0:
        continue  # Buster, not a library chip
    print(f'{cid} = "{chips[cid]}"')
print()
print("[story.labels]")
for val in sorted(story):
    print(f'{val} = "{story[val]}"')

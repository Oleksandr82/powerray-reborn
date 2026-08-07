"""
Diffs two parameter snapshots produced by dump_params.py --save, to find
what changed between two drone states (e.g. before/after arming).

Usage:
  venv\\Scripts\\python.exe scripts\\diff_params.py before.json after.json
"""
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument('before')
parser.add_argument('after')
args = parser.parse_args()

with open(args.before) as f:
    before = json.load(f)
with open(args.after) as f:
    after = json.load(f)

all_ids = sorted(set(before) | set(after))
changed = []
added = []
removed = []

for pid in all_ids:
    b = before.get(pid)
    a = after.get(pid)
    if b is None:
        added.append(pid)
    elif a is None:
        removed.append(pid)
    elif b['value'] != a['value']:
        changed.append((pid, b['value'], a['value'], a.get('type', b.get('type'))))

print(f"Before: {len(before)} params, After: {len(after)} params")
print(f"\n=== Changed params ({len(changed)}) ===")
for pid, bv, av, t in changed:
    print(f"  {pid}: {bv} -> {av}  (type={t})")

if added:
    print(f"\n=== Only in AFTER ({len(added)}) ===")
    for pid in added:
        print(f"  {pid} = {after[pid]['value']}")

if removed:
    print(f"\n=== Only in BEFORE ({len(removed)}) ===")
    for pid in removed:
        print(f"  {pid} = {before[pid]['value']}")

if not changed and not added and not removed:
    print("\nNo differences found.")

"""
Dumps all PX4 parameters from the FCU via the running cockpit server's
Socket.IO channel and searches for anything related to activation/lock/unlock,
so we can see if there is a writable parameter gating the "NOT ACTIVATED"
STATUSTEXT / arm rejection.

Usage: venv\\Scripts\\python.exe scripts\\dump_params.py [--filter activat]
"""
import argparse
import time
import socketio

parser = argparse.ArgumentParser()
parser.add_argument('--filter', default='', help='Case-insensitive substring filter on param name')
parser.add_argument('--seconds', type=float, default=15.0, help='How long to collect params')
parser.add_argument('--url', default='http://localhost:5000')
parser.add_argument('--save', default='', help='Path to save a JSON snapshot of {id: {value, type}} for later diffing')
args = parser.parse_args()

sio = socketio.Client()
params = {}
types = {}

@sio.on('param')
def on_param(data):
    params[data['id']] = data['value']
    types[data['id']] = data.get('type')

print(f"Connecting to {args.url} ...")
sio.connect(args.url)
time.sleep(1.0)

print("Requesting full parameter list (this can take a few seconds)...")
import requests
try:
    requests.get(args.url.rstrip('/') + '/params', timeout=5)
except Exception as e:
    print(f"(GET /params request note: {e})")

t0 = time.time()
while time.time() - t0 < args.seconds:
    time.sleep(0.5)
    print(f"\r  collected {len(params)} params so far...", end='', flush=True)
print()

sio.disconnect()

print(f"\n=== Total parameters collected: {len(params)} ===")
if args.save:
    import json
    snapshot = {k: {'value': v, 'type': types.get(k)} for k, v in params.items()}
    with open(args.save, 'w') as f:
        json.dump(snapshot, f, indent=2, sort_keys=True)
    print(f"Saved snapshot to {args.save}")

if args.filter:
    needle = args.filter.lower()
    matches = {k: v for k, v in params.items() if needle in k.lower()}
    print(f"\nParams matching '{args.filter}':")
    for k, v in sorted(matches.items()):
        print(f"  {k} = {v}  (type={types.get(k)})")
    if not matches:
        print("  (no matches)")
else:
    for k, v in sorted(params.items()):
        print(f"  {k} = {v}  (type={types.get(k)})")

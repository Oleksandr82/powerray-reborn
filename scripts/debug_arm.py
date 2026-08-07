"""
Automated cockpit test client — acts like the browser, but scriptable.
Connects via Socket.IO to the running cockpit server, subscribes to all
relevant events, sends an ARM command, and prints everything the server
sends back (telemetry, ack, cmd_sent, cmd_error, statustext) for a fixed
observation window. Useful for debugging without needing manual browser
clicks each time.

Usage:  venv\\Scripts\\python.exe scripts\\debug_arm.py [--disarm] [--seconds 8]
"""
import argparse
import time
import socketio

parser = argparse.ArgumentParser()
parser.add_argument('--disarm', action='store_true', help='Send disarm instead of arm')
parser.add_argument('--seconds', type=float, default=8.0, help='How long to observe after sending')
parser.add_argument('--url', default='http://localhost:5000')
args = parser.parse_args()

sio = socketio.Client()
events = []

def log(name):
    def handler(data=None):
        ts = time.strftime('%H:%M:%S')
        events.append((ts, name, data))
        print(f"[{ts}] {name}: {data}")
    return handler

for ev in ['connect', 'disconnect', 'status', 'telemetry', 'attitude', 'battery',
           'position', 'ack', 'cmd_error', 'cmd_sent', 'statustext', 'param']:
    sio.on(ev, log(ev))

print(f"Connecting to {args.url} ...")
sio.connect(args.url)
time.sleep(1.0)  # let initial 'status'/'telemetry' snapshot arrive

do_arm = not args.disarm
print(f"\n>>> Sending arm={do_arm} ...\n")
sio.emit('arm', {'arm': do_arm})

time.sleep(args.seconds)

print(f"\n=== Summary: {len(events)} events received in observation window ===")
ack_events = [e for e in events if e[1] in ('ack', 'cmd_error', 'statustext')]
if ack_events:
    print("Relevant response events:")
    for ts, name, data in ack_events:
        print(f"  [{ts}] {name}: {data}")
else:
    print("No ack/cmd_error/statustext events were received at all — the FCU gave no direct "
          "reply to the arm command within the observation window.")

sio.disconnect()

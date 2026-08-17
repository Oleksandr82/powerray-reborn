"""
PowerRay Web UI — Backend v2
MAVLink FCU + Camera Ambarella JSON + Video stream + Sonar
"""
import threading, time, math, socket, json, struct
from flask import Flask, render_template, Response, request, jsonify
from flask_socketio import SocketIO, emit
from pymavlink import mavutil

app = Flask(__name__)
app.config['SECRET_KEY'] = 'powerray'
sio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')

# --- Config ---
FCU_IP   = '192.168.1.12';  FCU_PORT  = 20002
CAM_IP   = '192.168.1.100'; CAM_CMD   = 7878; CAM_DATA = 8787; CAM_HTTP = 80
SONAR_IP = '192.168.1.100'; SONAR_PORT = 7700
PSE_IP   = '192.168.1.1';  PSE_PORT   = 5000   # Sonar PSE_230252

MODES = {0:'STABILIZE',1:'ACRO',2:'ALT_HOLD',3:'AUTO',
         4:'GUIDED',7:'CIRCLE',9:'SURFACE',16:'POSHOLD',19:'MANUAL'}

# --- MAVLink parameter type helpers ---
# The PARAM_VALUE/PARAM_SET wire format always carries the value in a 4-byte
# float field, but for non-float parameter types that field is a raw bit
# reinterpretation (memcpy) of the real value, NOT a numeric cast. E.g. the
# integer 1 is transmitted as the float whose bit pattern equals 0x00000001
# (~1.4e-45), not as 1.0. We must reinterpret/re-encode using struct
# accordingly, based on each parameter's MAV_PARAM_TYPE, or integer-typed
# params (very common in this drone's PV_* namespace) show as denormalized
# garbage on read and get corrupted on write.
PARAM_TYPE_FORMATS = {
    1: 'B',   # MAV_PARAM_TYPE_UINT8
    2: 'b',   # MAV_PARAM_TYPE_INT8
    3: 'H',   # MAV_PARAM_TYPE_UINT16
    4: 'h',   # MAV_PARAM_TYPE_INT16
    5: 'I',   # MAV_PARAM_TYPE_UINT32
    6: 'i',   # MAV_PARAM_TYPE_INT32
    9: 'f',   # MAV_PARAM_TYPE_REAL32
    # UINT64/INT64/REAL64 (7,8,10) don't fit in the 4-byte wire field —
    # left unhandled; such params (rare/absent here) fall back to raw float.
}

def decode_param_value(raw_value, param_type):
    """Reinterpret the raw wire float according to the parameter's real type."""
    fmt = PARAM_TYPE_FORMATS.get(param_type)
    if not fmt or fmt == 'f':
        return raw_value
    raw_bytes = struct.pack('<f', raw_value)
    return struct.unpack('<' + fmt, raw_bytes)[0]

def encode_param_value(value, param_type):
    """Encode a real (int or float) value into the raw wire float for this type."""
    fmt = PARAM_TYPE_FORMATS.get(param_type)
    if not fmt or fmt == 'f':
        return float(value)
    raw_bytes = struct.pack('<' + fmt, int(round(value)))
    return struct.unpack('<f', raw_bytes)[0]

# Caches each parameter's real MAV_PARAM_TYPE, keyed by name — populated as
# PARAM_VALUE messages arrive, used by /param/set to encode writes correctly.
param_types = {}

# --- État global ---
state = {
    'mav_connected': False,
    'cam_connected': False,
    'cam_token': 0,
    'sonar_connected': False,
    'armed': False,
    'mode': 'UNKNOWN',
    'custom_mode': 0,
    'nav_mode': 'UNKNOWN',   # 'STABLE_IMAGE' or 'DEPTH_FIXED', from HEARTBEAT.base_mode bit 0
    'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0,
    'battery_v': 0.0, 'battery_a': 0.0, 'battery_pct': 0,
    'depth': 0.0, 'vx': 0.0, 'vy': 0.0, 'vz': 0.0,
    'params': {},
}
mav = None
mav_lock = threading.Lock()

# ═══════════════════════════════════════════
# MAVLink
# ═══════════════════════════════════════════
def broadcast(event, data):
    sio.emit(event, data, namespace='/')

def mav_thread():
    global mav
    while True:
        try:
            print(f"[MAV] Connexion {FCU_IP}:{FCU_PORT}...")
            m = mavutil.mavlink_connection(f'tcp:{FCU_IP}:{FCU_PORT}', source_system=255)
            hb = m.wait_heartbeat(timeout=10)
            if not hb:
                raise Exception("Heartbeat timeout")
            with mav_lock:
                mav = m
            state['mav_connected'] = True
            print(f"[MAV] Connecte sysid={m.target_system}")
            broadcast('status', {'mav': True, 'cam': state['cam_connected'], 'sonar': state['sonar_connected']})
            mav_loop(m)
        except Exception as e:
            print(f"[MAV] {e}")
        state['mav_connected'] = False
        mav = None
        broadcast('status', {'mav': False, 'cam': state['cam_connected'], 'sonar': state['sonar_connected']})
        time.sleep(3)

def mav_loop(m):
    last_hb = 0
    while True:
        now = time.time()
        if now - last_hb > 1.0:
            m.mav.heartbeat_send(
                mavutil.mavlink.MAV_TYPE_GCS,
                mavutil.mavlink.MAV_AUTOPILOT_INVALID, 0, 0, 0)
            last_hb = now

        msg = m.recv_match(blocking=True, timeout=0.1)
        if msg is None:
            continue
        t = msg.get_type()

        if t == 'HEARTBEAT' and msg.get_srcSystem() == 2:
            cm = msg.custom_mode
            bm = msg.base_mode
            state['mode']  = MODES.get(cm, f'MODE_{cm}')
            state['custom_mode'] = cm
            state['armed'] = bool(bm & 0x80)
            state['nav_mode'] = 'DEPTH_FIXED' if (bm & 0x01) else 'STABLE_IMAGE'
            broadcast('telemetry', {'mode': state['mode'], 'armed': state['armed'],
                                     'nav_mode': state['nav_mode']})

        elif t == 'ATTITUDE':
            state['roll']  = round(math.degrees(msg.roll),  1)
            state['pitch'] = round(math.degrees(msg.pitch), 1)
            state['yaw']   = round(math.degrees(msg.yaw),   1)
            broadcast('attitude', {'roll': state['roll'], 'pitch': state['pitch'], 'yaw': state['yaw']})

        elif t == 'SYS_STATUS':
            state['battery_v']   = round(msg.voltage_battery / 1000, 2)
            state['battery_a']   = round(msg.current_battery / 100,  1)
            state['battery_pct'] = msg.battery_remaining
            broadcast('battery', {'v': state['battery_v'], 'a': state['battery_a'], 'pct': state['battery_pct']})

        elif t == 'LOCAL_POSITION_NED':
            state['depth'] = round(-msg.z,  2)
            state['vx']    = round(msg.vx,  2)
            state['vy']    = round(msg.vy,  2)
            state['vz']    = round(msg.vz,  2)
            broadcast('position', {'depth': state['depth'],
                                   'vx': state['vx'], 'vy': state['vy'], 'vz': state['vz']})

        elif t == 'COMMAND_ACK':
            results = ['ACCEPTED','TEMP_REJECTED','DENIED','UNSUPPORTED','FAILED','IN_PROGRESS']
            print(f"[MAV] COMMAND_ACK cmd={msg.command} result={msg.result}")
            broadcast('ack', {'cmd': msg.command, 'result': msg.result,
                              'text': results[msg.result] if msg.result < len(results) else str(msg.result)})

        elif t == 'STATUSTEXT':
            print(f"[MAV] STATUSTEXT sev={msg.severity} text={msg.text}")
            broadcast('statustext', {'severity': msg.severity, 'text': msg.text})

        elif t == 'MANUAL_CONTROL' and msg.get_srcSystem() == 2:
            # The FCU echoes back the control inputs it's currently acting on
            # (msg_id 69) — this reflects the PHYSICAL RC joystick position
            # whenever the drone is being flown from the real remote, not
            # just our own on-screen joystick sends.
            broadcast('rc_input', {'x': msg.x, 'y': msg.y, 'z': msg.z, 'r': msg.r})

        elif t == 'PARAM_VALUE':
            param_types[msg.param_id] = msg.param_type
            decoded = decode_param_value(msg.param_value, msg.param_type)
            state['params'][msg.param_id] = decoded
            broadcast('param', {'id': msg.param_id, 'value': decoded, 'type': msg.param_type,
                                'index': msg.param_index, 'count': msg.param_count})

# ═══════════════════════════════════════════
# Camera Ambarella JSON (7878 + 8787)
# ═══════════════════════════════════════════
cam_cmd_sock = None
cam_data_sock = None
cam_lock = threading.Lock()

def cam_connect():
    """Connect to camera. Sequence: start_session -> token -> viewfinder -> RTSP active."""
    global cam_cmd_sock
    with cam_lock:
        try:
            if cam_cmd_sock is not None:
                try: cam_cmd_sock.close()
                except: pass
            cam_cmd_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cam_cmd_sock.settimeout(15)
            cam_cmd_sock.connect((CAM_IP, CAM_CMD))
            # 1. start_session — RTOS responds in ~1s
            cam_cmd_sock.sendall(b'{"token":0,"msg_id":257}')
            resp = cam_cmd_sock.recv(4096)
            print(f"[CAM] start_session raw: {resp}")
            data = json.loads(resp.decode())
            if data.get('rval') != 0:
                raise Exception(f"start_session failed rval={data.get('rval')}")
            token = data['param']
            print(f"[CAM] token: {token!r}")
            state['cam_token'] = token
            cam_cmd_sock.settimeout(5)
            # 2. reset_viewfinder — activates RTSP pipeline
            cam_cmd_sock.sendall(json.dumps({'token': token, 'msg_id': 259, 'param': 'none_force'}).encode())
            resp2 = cam_cmd_sock.recv(4096)
            vf = json.loads(resp2.decode())
            print(f"[CAM] viewfinder: {vf}")
            time.sleep(1.5)  # let RTOS pipeline start
            state['cam_connected'] = True
            print(f"[CAM] Connected token={token}")
            broadcast('status', {'mav': state['mav_connected'], 'cam': True, 'sonar': state['sonar_connected']})
            return {'ok': True, 'token': token}
        except Exception as e:
            try: cam_cmd_sock.close()
            except: pass
            cam_cmd_sock = None
            state['cam_connected'] = False
            return {'ok': False, 'error': str(e)}

def cam_send(cmd: dict) -> dict:
    global cam_cmd_sock
    with cam_lock:
        try:
            if cam_cmd_sock is None:
                return {'error': 'camera not connected - call /cam/connect first'}
            cam_cmd_sock.sendall(json.dumps(cmd).encode())
            resp = cam_cmd_sock.recv(4096)
            return json.loads(resp.decode())
        except Exception as e:
            cam_cmd_sock = None
            state['cam_connected'] = False
            return {'error': str(e)}

def video_stream_rtsp():
    """Relay RTSP -> MJPEG via OpenCV. Requires active viewfinder (cam_connect)."""
    import cv2
    url = 'rtsp://192.168.1.100/live'
    print(f"[RTSP] Connecting {url}")
    cap = cv2.VideoCapture(url)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    if not cap.isOpened():
        print(f"[RTSP] Failed — viewfinder not active?")
        return
    print("[RTSP] Stream open")
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[RTSP] stream ended")
                break
            _, jpg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpg.tobytes() + b'\r\n')
    except Exception as e:
        print(f"[RTSP] error: {e}")
    finally:
        cap.release()

# ═══════════════════════════════════════════
# Sonar FCU binary protocol (7700)
# ═══════════════════════════════════════════
sonar_sock = None
sonar_lock = threading.Lock()

def sonar_connect():
    global sonar_sock
    with sonar_lock:
        try:
            sonar_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sonar_sock.settimeout(5)
            sonar_sock.connect((SONAR_IP, SONAR_PORT))
            state['sonar_connected'] = True
            broadcast('status', {'mav': state['mav_connected'], 'cam': state['cam_connected'], 'sonar': True})
            return {'ok': True}
        except Exception as e:
            sonar_sock = None
            state['sonar_connected'] = False
            return {'ok': False, 'error': str(e)}

def sonar_send(cmd_byte, data=b''):
    global sonar_sock
    with sonar_lock:
        try:
            if sonar_sock is None:
                return {'error': 'sonar not connected'}
            pkt = bytes([0xAA, 0x55, 0, 0, 0, 0, 0, 0,
                         cmd_byte, (len(data)>>8)&0xFF, len(data)&0xFF]) + data
            sonar_sock.sendall(pkt)
            resp = sonar_sock.recv(4096)
            return {'raw': resp.hex(), 'len': len(resp)}
        except Exception as e:
            sonar_sock = None
            state['sonar_connected'] = False
            return {'error': str(e)}

# ═══════════════════════════════════════════
# Sonar PSE (192.168.1.1:5000)
# ═══════════════════════════════════════════
pse_sock   = None
pse_lock   = threading.Lock()
pse_buf    = b''
pse_state  = {
    'connected': False,
    'streaming': False,
    'depth': 0.0,
    'temp': None,
    'bat': None,
    'last_col': [],
}

def pse_connect():
    global pse_sock, pse_buf
    with pse_lock:
        try:
            if pse_sock:
                try: pse_sock.close()
                except: pass
            pse_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            pse_sock.settimeout(5)
            pse_sock.connect((PSE_IP, PSE_PORT))
            pse_sock.settimeout(3)
            banner = pse_sock.recv(256)
            print(f"[PSE] banner: {banner}")
            pse_state['connected'] = True
            pse_buf = b''
            broadcast('status', {'mav': state['mav_connected'], 'cam': state['cam_connected'], 'sonar': True})
            return {'ok': True, 'banner': banner.decode(errors='replace').strip()}
        except Exception as e:
            pse_sock = None
            pse_state['connected'] = False
            return {'ok': False, 'error': str(e)}

def pse_send(cmd_byte, data=b''):
    global pse_sock
    with pse_lock:
        if pse_sock is None:
            return {'error': 'PSE not connected'}
        try:
            pkt = bytes([0xAA, 0x55, 0, 0, 0, 0, 0, 0,
                         cmd_byte, (len(data) >> 8) & 0xFF, len(data) & 0xFF]) + data
            pse_sock.sendall(pkt)
            pse_sock.settimeout(3)
            resp = pse_sock.recv(4096)
            return _pse_parse(resp)
        except socket.timeout:
            return {'raw': '', 'timeout': True}
        except Exception as e:
            pse_sock = None
            pse_state['connected'] = False
            return {'error': str(e)}

def _pse_parse(data):
    if not data or len(data) < 11:
        return {'raw': data.hex() if data else ''}
    if data[0] != 0xAA or data[1] != 0x55:
        return {'raw': data.hex(), 'text': data.decode(errors='replace')}
    cmd = data[8]
    data_len = (data[9] << 8) | data[10]
    payload = data[11:11 + data_len] if len(data) >= 11 + data_len else b''

    if cmd == 0xB1 and len(payload) >= 2:
        temp = ((payload[0] << 8) + payload[1]) / 10
        pse_state['temp'] = temp
        return {'cmd': 'temp', 'temp': temp}
    elif cmd == 0xB3 and len(payload) >= 2:
        bat = ((payload[0] << 8) + payload[1]) / 10
        pse_state['bat'] = bat
        return {'cmd': 'bat', 'bat': bat}
    elif cmd == 0xC3:
        ver = payload[:12].decode(errors='replace').rstrip('\x00')
        return {'cmd': 'version', 'version': ver, 'raw': payload.hex()}
    elif cmd == 0xFF and len(payload) >= 1:
        return {'cmd': 'ack', 'for': hex(payload[0])}
    elif cmd == 0xB4:
        col = _pse_decode_image(payload)
        pse_state['last_col'] = col
        return {'cmd': 'image', 'col': col, 'depth': pse_state['depth']}
    elif cmd == 0x10:
        return {'cmd': 'ack_open'}
    else:
        return {'cmd': hex(cmd), 'raw': data.hex(), 'len': len(data)}

def _pse_decode_image(payload):
    if not payload:
        return []
    col = [int(b) for b in payload]
    mx = max(col) if col else 1
    if mx > 0:
        col = [int(v * 255 / mx) for v in col]
    return col

def pse_stream_thread():
    global pse_buf
    while pse_state['streaming'] and pse_state['connected'] and pse_sock:
        try:
            chunk = pse_sock.recv(8192)
            if not chunk:
                break
            pse_buf += chunk
            while len(pse_buf) >= 11:
                if pse_buf[0] != 0xAA or pse_buf[1] != 0x55:
                    pse_buf = pse_buf[1:]
                    continue
                data_len = (pse_buf[9] << 8) | pse_buf[10]
                total = 11 + data_len
                if len(pse_buf) < total:
                    break
                pkt = pse_buf[:total]
                pse_buf = pse_buf[total:]
                parsed = _pse_parse(pkt)
                if parsed.get('cmd') == 'image':
                    broadcast('sonar_col', {'col': parsed['col'], 'depth': pse_state['depth']})
                elif parsed.get('cmd') == 'temp':
                    broadcast('sonar_temp', {'temp': parsed['temp']})
                elif parsed.get('cmd') == 'bat':
                    broadcast('sonar_bat', {'bat': parsed['bat']})
        except socket.timeout:
            continue
        except Exception as e:
            print(f"[PSE] stream error: {e}")
            break
    pse_state['streaming'] = False

# ═══════════════════════════════════════════
# Flask routes
# ═══════════════════════════════════════════
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sonar_ui')
def sonar_ui():
    return render_template('sonar.html')

@app.route('/param_dictionary.json')
def param_dictionary():
    """Serves the static parameter interpretation dictionary (name -> desc/
    type/range/unit), loaded from config/param_dictionary.json. Kept as a
    separate flat file so it can be edited/extended without touching code."""
    import os
    path = os.path.join(os.path.dirname(__file__), 'config', 'param_dictionary.json')
    try:
        with open(path, 'r') as f:
            return jsonify(json.load(f))
    except FileNotFoundError:
        return jsonify({})

@app.route('/state')
def get_state():
    return jsonify({k: v for k, v in state.items() if k != 'params'})

@app.route('/arm', methods=['POST'])
def arm():
    if not mav: return jsonify({'error': 'MAVLink not connected'})
    do_arm = request.json.get('arm', True)
    with mav_lock:
        mav.mav.command_long_send(
            mav.target_system, mav.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0, 1.0 if do_arm else 0.0, 0,0,0,0,0,0)
    return jsonify({'status': 'sent', 'arm': do_arm})

@app.route('/nav_mode', methods=['POST'])
def set_nav_mode():
    """Set the navigation mode (Stable Image / Depth-Fixed) — reverse-engineered
    and confirmed as bit 0 of HEARTBEAT.base_mode (0=Stable Image, 1=Depth-Fixed).
    Confirmed working via MAVLink SET_MODE, same effect as the RC's mode button."""
    if not mav: return jsonify({'error': 'MAVLink not connected'})
    want = request.json.get('nav_mode', 'STABLE_IMAGE')
    current_bm = 1 if state.get('nav_mode') == 'DEPTH_FIXED' else 0
    new_bit = 1 if want == 'DEPTH_FIXED' else 0
    new_bm = (current_bm & ~1) | new_bit
    with mav_lock:
        mav.mav.set_mode_send(mav.target_system, new_bm, state.get('custom_mode', 0))
    return jsonify({'status': 'sent', 'requested_base_mode': new_bm})

@app.route('/mode', methods=['POST'])
def set_mode():
    if not mav: return jsonify({'error': 'MAVLink not connected'})
    mode_name = request.json.get('mode', 'MANUAL')
    mode_map  = {v:k for k,v in MODES.items()}
    cm = mode_map.get(mode_name, 19)
    with mav_lock:
        mav.mav.set_mode_send(mav.target_system, 1, cm)
    return jsonify({'status': 'sent', 'mode': mode_name})

def _send_emergency_surface():
    """Force SURFACE mode and make sure the drone is armed so it can
    actually rise (a disarmed FCU won't act on the mode change)."""
    if not mav:
        return {'error': 'MAVLink not connected'}
    with mav_lock:
        mav.mav.set_mode_send(mav.target_system, 1, 9)  # 9 = SURFACE
        if not state.get('armed'):
            mav.mav.command_long_send(
                mav.target_system, mav.target_component,
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                0, 1.0, 0,0,0,0,0,0)
    return {'status': 'sent', 'mode': 'SURFACE'}

@app.route('/surface', methods=['POST'])
def surface():
    result = _send_emergency_surface()
    if 'error' in result: return jsonify(result)
    return jsonify(result)

@app.route('/control', methods=['POST'])
def manual_control():
    if not mav: return jsonify({'error': 'MAVLink not connected'})
    d = request.json
    with mav_lock:
        mav.mav.manual_control_send(
            mav.target_system,
            int(d.get('x',0)), int(d.get('y',0)),
            int(d.get('z',0)), int(d.get('r',0)), 0)
    return jsonify({'status': 'sent'})

@app.route('/params')
def get_params():
    if not mav: return jsonify({'error': 'MAVLink not connected'})
    with mav_lock:
        mav.mav.param_request_list_send(mav.target_system, mav.target_component)
    return jsonify({'status': 'requesting'})

@app.route('/param/get/<param_id>')
def get_param(param_id):
    if not mav: return jsonify({'error': 'MAVLink not connected'})
    with mav_lock:
        mav.mav.param_request_read_send(
            mav.target_system, mav.target_component,
            param_id.encode(), -1)
    return jsonify({'status': 'requesting', 'id': param_id})

@app.route('/param/set', methods=['POST'])
def set_param():
    if not mav: return jsonify({'error': 'MAVLink not connected'})
    d = request.json
    param_id = d['id']
    # Use the real type learned from a previous PARAM_VALUE for this param
    # (falls back to REAL32 if we've never seen it, e.g. set before loading).
    param_type = param_types.get(param_id, mavutil.mavlink.MAV_PARAM_TYPE_REAL32)
    wire_value = encode_param_value(float(d['value']), param_type)
    with mav_lock:
        mav.mav.param_set_send(
            mav.target_system, mav.target_component,
            param_id.encode(), wire_value,
            param_type)
    return jsonify({'status': 'sent', 'type': param_type})

@app.route('/cam/connect', methods=['POST'])
def cam_connect_route():
    return jsonify(cam_connect())

@app.route('/cam/<action>', methods=['POST'])
def cam_action(action):
    T = state['cam_token']
    cmds = {
        'info':      {'token': T, 'msg_id': 11},
        'battery':   {'token': T, 'msg_id': 13},
        'settings':  {'token': T, 'msg_id': 3},
        'photo':     {'token': T, 'msg_id': 769},
        'rec_start': {'token': T, 'msg_id': 513},
        'rec_stop':  {'token': T, 'msg_id': 514},
        'vf_start':  {'token': T, 'msg_id': 259, 'param': 'none_force'},
        'vf_stop':   {'token': T, 'msg_id': 260},
        'space':     {'token': T, 'msg_id': 5, 'type': 'free'},
        'files':     {'token': T, 'msg_id': 6, 'type': 'total'},
    }
    if action not in cmds:
        return jsonify({'error': 'unknown action'})
    return jsonify(cam_send(cmds[action]))

@app.route('/video')
def video():
    if not state['cam_connected']:
        result = cam_connect()
        if not result.get('ok'):
            print(f"[VIDEO] cam_connect failed: {result.get('error')}")
    return Response(video_stream_rtsp(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/sonar/connect', methods=['POST'])
def sonar_connect_route():
    return jsonify(sonar_connect())

@app.route('/sonar/<action>', methods=['POST'])
def sonar_action(action):
    cmds = {'open':0x10,'close':0x11,'temp':0xB0,'battery':0xB2,'version':0xC2}
    if action not in cmds:
        return jsonify({'error': 'unknown action'})
    return jsonify(sonar_send(cmds[action]))

@app.route('/pse/connect', methods=['POST'])
def pse_connect_route():
    return jsonify(pse_connect())

@app.route('/pse/open', methods=['POST'])
def pse_open():
    pse_state['streaming'] = True
    t = threading.Thread(target=pse_stream_thread, daemon=True)
    t.start()
    return jsonify(pse_send(0x10))

@app.route('/pse/close', methods=['POST'])
def pse_close():
    pse_state['streaming'] = False
    return jsonify(pse_send(0x11))

@app.route('/pse/version', methods=['POST'])
def pse_version():
    return jsonify(pse_send(0xC2))

@app.route('/pse/battery', methods=['POST'])
def pse_battery():
    r = pse_send(0xB2)
    if 'bat' in r: pse_state['bat'] = r['bat']
    return jsonify(r)

@app.route('/pse/temp', methods=['POST'])
def pse_temp():
    r = pse_send(0xB0)
    if 'temp' in r: pse_state['temp'] = r['temp']
    return jsonify(r)

@app.route('/pse/data')
def pse_data():
    return jsonify({
        'col':   pse_state['last_col'],
        'depth': pse_state['depth'],
        'temp':  pse_state['temp'],
        'bat':   pse_state['bat'],
        'connected': pse_state['connected'],
        'streaming': pse_state['streaming'],
    })

@app.route('/pse/status')
def pse_status():
    return jsonify({
        'connected': pse_state['connected'],
        'streaming': pse_state['streaming'],
        'ip': PSE_IP,
        'port': PSE_PORT,
    })

# ═══════════════════════════════════════════
# SocketIO
# ═══════════════════════════════════════════
@sio.on('connect')
def on_connect():
    emit('status', {
        'mav':   state['mav_connected'],
        'cam':   state['cam_connected'],
        'sonar': state['sonar_connected'],
    })
    if state['mav_connected']:
        emit('telemetry', {'mode': state['mode'],       'armed': state['armed']})
        emit('battery',   {'v': state['battery_v'],     'a': state['battery_a'], 'pct': state['battery_pct']})
        emit('attitude',  {'roll': state['roll'],        'pitch': state['pitch'], 'yaw': state['yaw']})
        emit('position',  {'depth': state['depth'],      'vx': state['vx'], 'vy': state['vy'], 'vz': state['vz']})

@sio.on('joystick')
def on_joystick(data):
    if not mav or not state['mav_connected']: return
    with mav_lock:
        mav.mav.manual_control_send(
            mav.target_system,
            int(data.get('x',0)), int(data.get('y',0)),
            int(data.get('z',0)), int(data.get('r',0)), 0)

@sio.on('arm')
def on_arm(data):
    if not mav:
        emit('cmd_error', {'msg': 'Cannot ARM: not connected to flight controller (FCU Off)'})
        return
    do_arm = data.get('arm', True)
    with mav_lock:
        mav.mav.command_long_send(
            mav.target_system, mav.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0, 1.0 if do_arm else 0.0, 0,0,0,0,0,0)
    emit('cmd_sent', {'cmd': 'arm', 'arm': do_arm})

@sio.on('set_mode')
def on_set_mode(data):
    if not mav:
        emit('cmd_error', {'msg': 'Cannot set mode: not connected to flight controller (FCU Off)'})
        return
    mode_map = {v:k for k,v in MODES.items()}
    cm = mode_map.get(data.get('mode','MANUAL'), 19)
    with mav_lock:
        mav.mav.set_mode_send(mav.target_system, 1, cm)

@sio.on('emergency_surface')
def on_emergency_surface(data=None):
    result = _send_emergency_surface()
    if 'error' in result:
        emit('cmd_error', {'msg': 'Emergency surface failed: ' + result['error']})
    else:
        emit('cmd_sent', {'cmd': 'emergency_surface', 'mode': 'SURFACE'})

# ═══════════════════════════════════════════
if __name__ == '__main__':
    threading.Thread(target=mav_thread, daemon=True).start()
    print("[UI] http://localhost:5000")
    sio.run(app, host='0.0.0.0', port=5000, debug=False)

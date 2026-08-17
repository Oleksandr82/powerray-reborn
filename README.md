# erebus-io-powerray

A Python + PowerShell toolkit for controlling the **PowerVision PowerRay** underwater drone without the official Vision+ Android app.

This is personal reverse engineering / maker work. We own the submarine, we documented what it speaks, we built a web UI to talk to it. Nothing fancy, just curiosity and a soldering iron mindset applied to TCP packets.

> **Disclaimer**: Not affiliated with or endorsed by PowerVision. PowerVision® and PowerRay® are trademarks of PowerVision Technology Group. Use at your own risk.

---

## Community fork notice

This repository is maintained as a public community continuation at:

- https://github.com/Oleksandr82/powerray-reborn

Original upstream project:

- https://github.com/Erebus-io/erebus-io-powerray

Goal of this fork:

- Keep the toolkit usable for existing PowerRay owners.
- Accept practical fixes and documentation improvements.
- Preserve interoperability-focused reverse engineering work.

Scope and expectations:

- Community-maintained project with best-effort support.
- Stability and repairability are prioritized over frequent feature releases.

---

## What's working

| Feature | Status |
|---------|--------|
| MAVLink telemetry (50 Hz) | ✅ Fully working |
| Navigation control (ARM / SET_MODE / joystick) | ✅ Fully working |
| 358 PX4 parameter read + write | ✅ Fully working |
| Ambarella camera JSON API | ✅ Fully working (token/session) |
| RTSP live video in browser | ✅ Working (requires camera session open) |
| Sonar binary protocol | 📖 Documented, port currently closed |
| PSE fishfinder sonar | 🔧 Partially — TCP banner, UDP not captured yet |
| RC PRASC10 remote control | ❓ Unknown UDP protocol |

---

## Network map

The PowerRay creates a WiFi AP (`PRA_Station_400314`). Once connected:

| IP | Role | Key ports |
|----|------|-----------|
| 192.168.1.11 | Base station (HLK-RM08K WiFi module) | 8080 (MAVLink broadcast), 80 (HTTP) |
| 192.168.1.12 | Flight controller (PX4 custom) | **20002 TCP** — MAVLink v1 |
| 192.168.1.100 | Camera module (Ambarella A12) | **7878** JSON API, **554** RTSP, **80** HTTP, **23** Telnet |
| 192.168.1.103 | RC controller PRASC10 | UDP (unknown) |

---

## Quick start

### Offline field kit (recommended)

For fully-offline use in the field (no internet required after one-time setup):

1. **Once, with internet**: double-click `Setup-Offline.cmd` — creates a bundled `venv\` and installs all dependencies locally.
2. **At the water**: double-click `Start-Cockpit.cmd` — starts the server and opens the browser automatically.
3. **When done**: double-click `Stop-Cockpit.cmd`.

See `INSTRUCTIONS.html` for the full illustrated field guide.

### Manual / development setup

### Requirements

```bash
pip install flask flask-socketio pymavlink opencv-python
```

### Run the web UI

```bash
cd web-ui
python -u server.py
```

Then open **http://localhost:5000** in your browser.

**Important**: If you want camera access, close the Vision+ app on the tablet first. The Ambarella daemon only allows one client at a time.

---

## Web UI features

- **Attitude indicator** — animated artificial horizon (roll/pitch)
- **Compass** — rotating, driven by live MAVLink yaw
- **Battery** — voltage, current, percentage with color bar
- **Navigation control** — ARM/DISARM, mode selector, dual joystick (mouse + Gamepad API)
- **Camera** — connect, photo, record, viewfinder toggle
- **Live video** — RTSP → OpenCV → MJPEG relay in the browser
- **Parameters** — search + live SET for all 358 PX4 params
- **Sonar UI** — at `/sonar_ui`, with waterfall canvas and demo mode

---

## PowerShell scripts

Quick scripts for testing without the full UI:

| Script | What it does |
|--------|-------------|
| `powerray_telemetry.ps1` | Decode and print MAVLink stream |
| `powerray_cam.ps1` | Test camera JSON API (7878) |
| `powerray_connect.ps1` | Basic TCP connection test |
| `ray_ctrl.ps1` | MAVLink control sequence test |
| `scan_powerray.ps1` | Port scan the submarine |

---

## Protocol docs

See [`docs/`](docs/) for detailed protocol documentation:

- [`mavlink-protocol.md`](docs/mavlink-protocol.md) — MAVLink messages, control sequence, modes
- [`camera-json-api.md`](docs/camera-json-api.md) — Ambarella JSON commands (msg_id table)
- [`sonar-protocol.md`](docs/sonar-protocol.md) — Binary sonar frame format
- [`hardware.md`](docs/hardware.md) — Hardware internals, process list, filesystem
- [`network-map.md`](docs/network-map.md) — Full network map with port status

---

## Legal

See [LEGAL_CHECK.md](LEGAL_CHECK.md) for the full legal analysis.

Short version: all code in this repo is original. Protocol documentation is factual/functional (not copyrightable). Reverse engineering for interoperability is explicitly permitted under EU Directive 2009/24/EC Article 6, implemented in France as Article L122-6-1 CPI.

---

## Contributing

Contributions are welcome, especially for:

- Reliability fixes for field use
- Hardware/protocol validation on real devices
- Documentation quality and reproducibility
- UI ergonomics and diagnostics

Suggested workflow:

1. Fork this repository.
2. Create a feature branch.
3. Keep commits focused and explain behavior changes.
4. Open a pull request with test notes or reproduction steps.

When relevant, include:

- Device firmware version
- Network capture details
- Exact hardware variant (sub + controller + fishfinder)

---

## Upstream sync policy

This fork tracks the original project as `upstream` and periodically imports useful changes.

Typical local sync flow:

```bash
git fetch upstream
git merge upstream/master
git push origin master
```

---

## License

MIT — see [LICENSE](LICENSE).

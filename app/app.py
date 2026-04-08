#!/usr/bin/env python3
import os
import sys
import json
import time
import threading
import subprocess
from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO

# Add debug folder to path
sys.path.append("/debug")

# =========================
# Imports
# =========================
try:
    from AirPodsClient import AirPodsClient
except ImportError:
    from airpods import AirPodsClient

from system.battery import Battery, Component       # battery.py
from system.control import Control                 # control.py
from system.l2cap import run_linux_l2cap, exchange_keys  # l2cap.py
from system.ble_parser import parse_proximity_message, ble_scan_loop  # proximity.py / BLE

# =========================
# AirPods Client & Helpers
# =========================
AIRPODS_MAC = "XX:XX:XX:XX:XX:XX"  # replace if known
client = AirPodsClient(AIRPODS_MAC)
battery_manager = Battery()
control = Control()

# =========================
# Flask + WebSocket
# =========================
STATIC_DIR = "/debug/static"
app = Flask(__name__, static_folder=STATIC_DIR)
socketio = SocketIO(app, cors_allowed_origins="*")

# =========================
# Recorder State
# =========================
recording = []
record_enabled = False
record_lock = threading.Lock()

# =========================
# Event Hook
# =========================
def on_packet(data):
    global recording
    hexdata = data.hex()

    # Update battery state
    battery_manager.parse_packet(data)

    # BLE Proximity parsing
    prox_info = parse_proximity_message(data)

    # Record packets
    if record_enabled:
        with record_lock:
            recording.append({"ts": time.time(), "data": hexdata, "proximity": prox_info})

    # Emit combined state
    state = client.state()
    state["battery"] = {
        "Headset": {"level": battery_manager.get_headset_level(), "status": battery_manager.get_state(Component.HEADSET).status},
        "Left": {"level": battery_manager.get_left_level(), "status": battery_manager.get_state(Component.LEFT).status},
        "Right": {"level": battery_manager.get_right_level(), "status": battery_manager.get_state(Component.RIGHT).status},
        "Case": {"level": battery_manager.get_case_level(), "status": battery_manager.get_state(Component.CASE).status},
    }
    state["proximity"] = prox_info or {}
    socketio.emit("state", state)

client.on_packet = on_packet

# =========================
# REST API Endpoints
# =========================
@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")

@app.route("/connect")
def connect():
    try:
        client.connect()
        return jsonify({"status": "connected"})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/state")
def state():
    state = client.state()
    state["battery"] = {
        "Headset": {"level": battery_manager.get_headset_level(), "status": battery_manager.get_state(Component.HEADSET).status},
        "Left": {"level": battery_manager.get_left_level(), "status": battery_manager.get_state(Component.LEFT).status},
        "Right": {"level": battery_manager.get_right_level(), "status": battery_manager.get_state(Component.RIGHT).status},
        "Case": {"level": battery_manager.get_case_level(), "status": battery_manager.get_state(Component.CASE).status},
    }
    return jsonify(state)

@app.route("/noise/<int:mode>")
def noise(mode):
    try:
        client.set_noise(mode)
        return jsonify({"status": "ok", "mode": mode})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/ca/<int:enabled>")
def ca(enabled):
    try:
        client.set_ca(bool(enabled))
        return jsonify({"status": "ok", "enabled": bool(enabled)})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/adaptive/<int:level>")
def adaptive(level):
    try:
        level = max(0, min(100, level))
        client.set_adaptive(level)
        return jsonify({"status": "ok", "level": level})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/raw", methods=["POST"])
def raw():
    try:
        hexdata = request.data.decode().strip()
        data = bytes.fromhex(hexdata)
        client.send(data)
        return jsonify({"status": "sent", "data": hexdata})
    except Exception as e:
        return jsonify({"error": str(e)})

# =========================
# Recording API
# =========================
@app.route("/record/start")
def record_start():
    global recording, record_enabled
    with record_lock:
        recording = []
        record_enabled = True
    return jsonify({"recording": True})

@app.route("/record/stop")
def record_stop():
    global record_enabled
    record_enabled = False
    return jsonify({"recording": False})

@app.route("/record/save")
def record_save():
    try:
        with record_lock:
            with open("/debug/capture.json", "w") as f:
                json.dump(recording, f, indent=2)
        return jsonify({"saved_packets": len(recording)})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/record/replay")
def record_replay():
    try:
        count = 0
        with record_lock:
            for pkt in recording:
                client.send(bytes.fromhex(pkt["data"]))
                count += 1
        return jsonify({"replayed": count})
    except Exception as e:
        return jsonify({"error": str(e)})

# =========================
# Bluetooth Scan & Pair
# =========================
@app.route("/scan")
def scan():
    try:
        output = subprocess.check_output(["timeout", "10", "hcitool", "scan"], text=True)
        devices = []
        for line in output.splitlines():
            if "\t" in line:
                mac, name = line.strip().split("\t")
                devices.append({"mac": mac, "name": name})
        devices = [d for d in devices if "AirPods" in d["name"]]
        return jsonify({"devices": devices})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/pair/<mac>")
def pair(mac):
    try:
        cmd = f"echo -e 'pair {mac}\\nconnect {mac}\\ntrust {mac}\\nexit' | bluetoothctl"
        subprocess.check_output(cmd, shell=True, text=True)
        return jsonify({"status": "paired", "mac": mac})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================
# WebSocket Events
# =========================
@socketio.on("connect")
def ws_connect():
    state = client.state()
    state["battery"] = {
        "Headset": {"level": battery_manager.get_headset_level(), "status": battery_manager.get_state(Component.HEADSET).status},
        "Left": {"level": battery_manager.get_left_level(), "status": battery_manager.get_state(Component.LEFT).status},
        "Right": {"level": battery_manager.get_right_level(), "status": battery_manager.get_state(Component.RIGHT).status},
        "Case": {"level": battery_manager.get_case_level(), "status": battery_manager.get_state(Component.CASE).status},
    }
    socketio.emit("state", state)

# =========================
# Main
# =========================
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5050)
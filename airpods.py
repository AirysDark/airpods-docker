import socket
import threading
import time
import debug

debug.start_debug("airpods") 
PSM = 0x1001

# =========================
# Core Packets
# =========================
HANDSHAKE = bytes.fromhex("00 00 04 00 01 00 02 00 00 00 00 00 00 00 00 00")
FEATURE_ENABLE = bytes.fromhex("04 00 04 00 4d 00 ff 00 00 00 00 00 00 00")
ENABLE_NOTIFICATIONS = bytes.fromhex("04 00 04 00 0F 00 FF FF FF FF")

# =========================
# AirPods Client
# =========================
class AirPodsClient:
    def __init__(self, mac):
        self.mac = mac
        self.sock = None
        self.state = {
            "battery": {},
            "noise_mode": None,
            "in_ear": {},
            "ca_enabled": None,
            "ca_level": None,
            "head": None,
            "last_packet": None
        }
        self.lock = threading.Lock()
        self.on_packet = None

    # =========================
    # Connection
    # =========================
    def connect(self):
        self.sock = socket.socket(
            socket.AF_BLUETOOTH,
            socket.SOCK_SEQPACKET,
            socket.BTPROTO_L2CAP
        )
        self.sock.connect((self.mac, PSM))

        self.initialize()

        threading.Thread(target=self.receiver, daemon=True).start()
        print("[+] Connected to AirPods")

    def send(self, data):
        if self.sock:
            self.sock.send(data)

    # =========================
    # Initialization
    # =========================
    def initialize(self):
        self.send(HANDSHAKE)
        time.sleep(0.3)
        self.send(FEATURE_ENABLE)
        time.sleep(0.3)
        self.send(ENABLE_NOTIFICATIONS)

    # =========================
    # Receiver
    # =========================
    def receiver(self):
        while True:
            try:
                data = self.sock.recv(1024)
                if data:
                    self.parse(data)

                    # External hook (WebSocket / recorder)
                    if self.on_packet:
                        self.on_packet(data)

            except Exception as e:
                print("[ERROR RX]", e)
                break

    # =========================
    # Packet Parser
    # =========================
    def parse(self, data):
        with self.lock:
            self.state["last_packet"] = data.hex()

            # -------------------------
            # Battery
            # -------------------------
            if data[4:6] == b'\x04\x00':
                count = data[6]
                idx = 7
                battery = {}

                for _ in range(count):
                    comp = data[idx]
                    level = data[idx + 2]
                    status = data[idx + 3]

                    name = {
                        0x02: "Right",
                        0x04: "Left",
                        0x08: "Case"
                    }.get(comp, "Unknown")

                    battery[name] = {
                        "level": level,
                        "status": status
                    }

                    idx += 5

                self.state["battery"] = battery

            # -------------------------
            # Noise Mode
            # -------------------------
            elif data[4:6] == b'\x09\x00' and data[6] == 0x0D:
                mode = data[7]
                self.state["noise_mode"] = {
                    1: "Off",
                    2: "ANC",
                    3: "Transparency",
                    4: "Adaptive"
                }.get(mode, "Unknown")

            # -------------------------
            # Ear Detection
            # -------------------------
            elif data[4:6] == b'\x06\x00':
                def decode(v):
                    return {
                        0: "In Ear",
                        1: "Out",
                        2: "Case"
                    }.get(v, "Unknown")

                self.state["in_ear"] = {
                    "Primary": decode(data[6]),
                    "Secondary": decode(data[7])
                }

            # -------------------------
            # Conversational Awareness Level
            # -------------------------
            elif data[4:6] == b'\x4B\x00':
                self.state["ca_level"] = data[9]

            # -------------------------
            # CA Enabled State
            # -------------------------
            elif data[4:6] == b'\x09\x00' and data[6] == 0x28:
                self.state["ca_enabled"] = (data[7] == 1)

            # -------------------------
            # Head Tracking (basic)
            # -------------------------
            elif len(data) > 55:
                try:
                    orientation = (
                        int.from_bytes(data[43:45], "little", signed=True),
                        int.from_bytes(data[45:47], "little", signed=True),
                        int.from_bytes(data[47:49], "little", signed=True),
                    )

                    accel = (
                        int.from_bytes(data[51:53], "little", signed=True),
                        int.from_bytes(data[53:55], "little", signed=True),
                    )

                    self.state["head"] = {
                        "orientation": orientation,
                        "accel": accel
                    }
                except:
                    pass

    # =========================
    # Commands
    # =========================
    def set_noise(self, mode):
        pkt = bytes.fromhex(f"04 00 04 00 09 00 0D {mode:02x} 00 00 00")
        self.send(pkt)

    def set_ca(self, enabled):
        val = 1 if enabled else 2
        pkt = bytes.fromhex(f"04 00 04 00 09 00 28 {val:02x} 00 00 00")
        self.send(pkt)

    def set_adaptive(self, level):
        level = max(0, min(100, level))
        pkt = bytes.fromhex(f"04 00 04 00 09 00 2E {level:02x} 00 00 00")
        self.send(pkt)
        
debug.end_debug("airpods") 
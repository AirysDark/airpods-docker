#!/usr/bin/env python3
"""
control.py - AirPods AACP Control Command Helper

Generates and sends AACP control command packets to AirPods over L2CAP/Bumble.

Usage example:

    from control import Control
    control = Control()
    # Enable Ear Detection
    packet = control.build_packet("ear_detection", data1=0x01)
    control.send_packet(sock, packet)
"""

from typing import Dict
import logging
import socket

logger = logging.getLogger("airpods_control")
logging.basicConfig(level=logging.INFO)

# -------------------------
# Base Header and Opcode
# -------------------------
BASE_HEADER = bytes.fromhex("04 00 04 00")
OPCODE_CONTROL = 0x09  # Control command opcode (16-bit little endian)

# -------------------------
# Identifiers Table
# -------------------------
IDENTIFIERS: Dict[str, int] = {
    "mic_mode": 0x01,
    "button_send_mode": 0x05,
    "owns_connection": 0x06,
    "ear_detection": 0x0A,
    "voice_trigger": 0x12,
    "single_click": 0x14,
    "double_click": 0x15,
    "click_hold": 0x16,
    "double_click_interval": 0x17,
    "click_hold_interval": 0x18,
    "listening_mode_configs": 0x1A,
    "one_bud_anc_mode": 0x1B,
    "crown_rotation_direction": 0x1C,
    "listening_mode": 0x0D,
    "auto_answer_mode": 0x1E,
    "chime_volume": 0x1F,
    "connect_automatically": 0x20,
    "volume_swipe_interval": 0x23,
    "call_management_config": 0x24,
    "volume_swipe_mode": 0x25,
    "adaptive_volume_config": 0x26,
    "software_mute": 0x27,
    "conversation_detect": 0x28,
    "ssl": 0x29,
    "hearing_aid_enrolled_enabled": 0x2C,
    "auto_anc_strength": 0x2E,
    "hps_gain_swipe": 0x2F,
    "hrm_enable": 0x30,
    "in_case_tone_config": 0x31,
    "siri_multitone": 0x32,
    "hearing_assist": 0x33,
    "allow_off_listening_mode": 0x34,
    "sleep_detection": 0x35,
    "allow_auto_connect": 0x36,
    "ppe_toggle": 0x37,
    "ppe_cap_level": 0x38,
    "raw_gestures": 0x39,
    "temporary_pairing": 0x3A,
    "dynamic_end_of_charge": 0x3B,
    "system_siri": 0x3C,
    "hearing_aid_generic": 0x3D,
    "uplink_eq_bud": 0x3E,
    "uplink_eq_source": 0x3F,
    "in_case_tone_volume": 0x40,
    "disable_button_input": 0x41,
}

class Control:
    """Helper class to build and send AACP control commands."""

    def __init__(self):
        self.base_header = BASE_HEADER
        self.opcode = OPCODE_CONTROL

    def build_packet(self, identifier_name: str,
                     data1: int = 0x00,
                     data2: int = 0x00,
                     data3: int = 0x00,
                     data4: int = 0x00) -> bytes:
        """
        Build a control command packet.

        Args:
            identifier_name: key from IDENTIFIERS dict
            data1-data4: payload bytes (default 0x00)

        Returns:
            bytes: AACP control packet
        """
        if identifier_name not in IDENTIFIERS:
            raise ValueError(f"Unknown identifier: {identifier_name}")
        identifier = IDENTIFIERS[identifier_name]
        packet = self.base_header + bytes([
            self.opcode & 0xFF,
            0x00,  # opcode high byte (little endian)
            identifier,
            data1,
            data2,
            data3,
            data4
        ])
        logger.debug(f"Built packet for {identifier_name}: {packet.hex()}")
        return packet

    def send_packet(self, sock: socket.socket, packet: bytes):
        """
        Send a control packet over a connected L2CAP/Bumble socket.

        Args:
            sock: open socket/channel object
            packet: bytes to send
        """
        try:
            sock.send(packet)
            logger.info(f"Packet sent: {packet.hex()}")
        except Exception as e:
            logger.error(f"Failed to send packet: {e}")

# -------------------------
# Example Usage
# -------------------------
if __name__ == "__main__":
    PSM = 0x1001  # L2CAP PSM for proximity/control
    BDADDR = "00:1A:7D:DA:71:13"  # Replace with actual AirPods MAC

    control = Control()
    packet = control.build_packet("ear_detection", data1=0x01)

    try:
        sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP)
        sock.connect((BDADDR, PSM))
        control.send_packet(sock, packet)
    except Exception as e:
        logger.error(f"Could not connect: {e}")
    finally:
        sock.close()
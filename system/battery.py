#!/usr/bin/env python3
import logging
from typing import Dict, Optional, Callable
from dataclasses import dataclass

# =========================
# Logging
# =========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("battery")

# =========================
# Battery Enums
# =========================
class Component:
    HEADSET = 0x01
    RIGHT = 0x02
    LEFT = 0x04
    CASE = 0x08

class BatteryStatus:
    CHARGING = 0x01
    DISCHARGING = 0x02
    DISCONNECTED = 0x04

# =========================
# Battery State
# =========================
@dataclass
class BatteryState:
    level: int = 0                  # 0-100, 0 = unknown
    status: int = BatteryStatus.DISCONNECTED

# =========================
# Battery Manager
# =========================
class Battery:
    def __init__(self):
        # Current states
        self.states: Dict[int, BatteryState] = {
            Component.HEADSET: BatteryState(),
            Component.LEFT: BatteryState(),
            Component.RIGHT: BatteryState(),
            Component.CASE: BatteryState()
        }
        self.primary_pod: Optional[int] = None
        self.secondary_pod: Optional[int] = None
        # Optional callback hooks
        self.on_status_change: Optional[Callable[[], None]] = None
        self.on_primary_change: Optional[Callable[[], None]] = None

    def reset(self):
        for comp in self.states:
            self.states[comp] = BatteryState()
        self.primary_pod = None
        self.secondary_pod = None
        self._trigger_status_change()

    def parse_packet(self, packet: bytes) -> bool:
        """Parse AirPods battery status packet"""
        if not packet or packet[0] != 0x04:
            return False

        battery_count = packet[6]
        if battery_count > 3 or len(packet) != 7 + 5 * battery_count:
            return False

        pods_in_packet = []

        for i in range(battery_count):
            offset = 7 + 5 * i
            comp_type = packet[offset]
            spacer = packet[offset + 1]
            level = packet[offset + 2]
            status = packet[offset + 3]
            end_byte = packet[offset + 4]

            if spacer != 0x01 or end_byte != 0x01:
                return False

            self.states[comp_type] = BatteryState(level, status)

            if comp_type in [Component.LEFT, Component.RIGHT, Component.HEADSET]:
                pods_in_packet.append(comp_type)

        # Determine primary and secondary
        if pods_in_packet:
            self.primary_pod = pods_in_packet[0]
            if len(pods_in_packet) >= 2:
                self.secondary_pod = pods_in_packet[1]
            self._trigger_primary_change()

        self._trigger_status_change()
        return True

    def parse_encrypted_packet(self, packet: bytes, is_left_primary: bool, pod_in_case: bool, is_headset: bool):
        """Parse a 16-byte encrypted battery packet"""
        if len(packet) != 16:
            return False

        # Determine left/right bytes
        left_index = 1 if is_left_primary else 2
        right_index = 2 if is_left_primary else 1

        raw_left = packet[left_index]
        raw_right = packet[right_index]
        raw_case = packet[3]

        def format_battery(byte_val: int):
            charging = bool(byte_val & 0x80)
            level = byte_val & 0x7F
            return charging, level

        left_charging, left_level = format_battery(raw_left)
        right_charging, right_level = format_battery(raw_right)
        case_charging, case_level = format_battery(raw_case)

        # Update states
        self.states[Component.LEFT] = BatteryState(left_level, BatteryStatus.CHARGING if left_charging else BatteryStatus.DISCHARGING)
        self.states[Component.RIGHT] = BatteryState(right_level, BatteryStatus.CHARGING if right_charging else BatteryStatus.DISCHARGING)
        if pod_in_case:
            self.states[Component.CASE] = BatteryState(case_level, BatteryStatus.CHARGING if case_charging else BatteryStatus.DISCHARGING)
        if is_headset:
            self.states[Component.HEADSET] = BatteryState(left_level, BatteryStatus.CHARGING if left_charging else BatteryStatus.DISCHARGING)
            self.primary_pod = Component.HEADSET

        # Primary/Secondary pods
        self.primary_pod = Component.LEFT if is_left_primary else Component.RIGHT
        self.secondary_pod = Component.RIGHT if is_left_primary else Component.LEFT

        self._trigger_primary_change()
        self._trigger_status_change()
        return True

    # -------------------------
    # Accessors
    # -------------------------
    def get_state(self, component: int) -> BatteryState:
        return self.states.get(component, BatteryState())

    def is_charging(self, component: int) -> bool:
        return self.states.get(component, BatteryState()).status == BatteryStatus.CHARGING

    def is_available(self, component: int) -> bool:
        return self.states.get(component, BatteryState()).status != BatteryStatus.DISCONNECTED

    # -------------------------
    # Callbacks / Signals
    # -------------------------
    def _trigger_status_change(self):
        if self.on_status_change:
            self.on_status_change()

    def _trigger_primary_change(self):
        if self.on_primary_change:
            self.on_primary_change()

    # -------------------------
    # Convenience getters
    # -------------------------
    def get_primary_pod(self) -> Optional[int]:
        return self.primary_pod

    def get_secondary_pod(self) -> Optional[int]:
        return self.secondary_pod

    def get_left_level(self) -> int:
        return self.get_state(Component.LEFT).level

    def get_right_level(self) -> int:
        return self.get_state(Component.RIGHT).level

    def get_case_level(self) -> int:
        return self.get_state(Component.CASE).level

    def get_headset_level(self) -> int:
        return self.get_state(Component.HEADSET).level
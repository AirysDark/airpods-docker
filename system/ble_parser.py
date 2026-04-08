#!/usr/bin/env python3
"""
ble_parser.py

Parses Apple AirPods BLE Proximity Pairing Messages and provides live scanning.

Requires:
    pip install bleak colorama
"""

import asyncio
import logging
from typing import Dict, Optional
from colorama import Fore, Style

try:
    from bleak import BleakScanner, BLEDevice, AdvertisementData
except ImportError:
    BleakScanner = None
    logging.warning("Bleak not installed, BLE scanning disabled")

# -------------------------
# Logger setup
# -------------------------
logger = logging.getLogger("ble_parser")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter(f"{Fore.CYAN}[%(levelname)s]{Style.RESET_ALL} %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

# -------------------------
# Constants
# -------------------------
APPLE_ID = 0x004C
PROX_PREFIX = 0x07
PROXITY_KEY_TYPES = {0x01: "IRK", 0x04: "ENC_KEY"}

# -------------------------
# Parsing Proximity Message
# -------------------------
def parse_proximity_message(data: bytes) -> Optional[Dict]:
    """Parse Apple Proximity Pairing BLE message."""
    if len(data) < 11 or data[0] != PROX_PREFIX:
        return None

    result = {}
    result["paired"] = data[2] == 0x01
    result["model"] = (data[3] << 8) | data[4]

    status = data[5]
    result["status_byte"] = status
    result["primary_left"] = bool(status & 0x20)
    result["this_pod_in_case"] = bool(status & 0x40)

    # Ear detection (XOR logic)
    are_values_flipped = not result["primary_left"]
    result["left_in_ear"] = ((status & 0x08) != 0) if are_values_flipped ^ result["this_pod_in_case"] else ((status & 0x02) != 0)
    result["right_in_ear"] = ((status & 0x02) != 0) if are_values_flipped ^ result["this_pod_in_case"] else ((status & 0x08) != 0)

    # Pods battery
    pods_batt = data[6]
    result["left_batt"] = pods_batt >> 4 if result["primary_left"] else pods_batt & 0x0F
    result["right_batt"] = pods_batt & 0x0F if result["primary_left"] else pods_batt >> 4

    # Case battery and flags
    flags_case = data[7]
    result["case_batt"] = flags_case >> 4
    result["right_charging"] = bool(flags_case & 0x01)
    result["left_charging"] = bool(flags_case & 0x02)
    result["case_charging"] = bool(flags_case & 0x04)

    # Lid state
    result["lid_state"] = (data[8] >> 3) & 0x01
    result["lid_counter"] = data[8] & 0x07

    # Device color & connection state
    result["device_color"] = data[9]
    result["connection_state"] = data[10]

    return result

# -------------------------
# Helper to format hex
# -------------------------
def hexdump(data: bytes) -> str:
    return " ".join(f"{b:02X}" for b in data)

# -------------------------
# Live BLE scan (async)
# -------------------------
async def ble_scan_loop(timeout: int = 10):
    if BleakScanner is None:
        logger.warning("Bleak not installed, cannot scan.")
        return

    async def callback(device: BLEDevice, adv: AdvertisementData):
        mdata = adv.manufacturer_data.get(APPLE_ID)
        if mdata and mdata[0] == PROX_PREFIX:
            info = parse_proximity_message(mdata)
            if info:
                logger.info(f"AirPods BLE detected: {info}")

    scanner = BleakScanner(callback)
    await scanner.start()
    logger.info(f"Scanning for AirPods BLE for {timeout}s...")
    await asyncio.sleep(timeout)
    await scanner.stop()
    logger.info("BLE scan completed.")

# -------------------------
# CLI Example
# -------------------------
def main():
    import argparse

    parser = argparse.ArgumentParser(description="AirPods BLE Parser / Scanner")
    parser.add_argument("--scan", action="store_true", help="Perform BLE scan")
    parser.add_argument("--timeout", type=int, default=10, help="Scan duration in seconds")
    parser.add_argument("--hex", type=str, help="Parse raw HEX Proximity message")
    args = parser.parse_args()

    if args.hex:
        data = bytes.fromhex(args.hex)
        parsed = parse_proximity_message(data)
        print(parsed)
    elif args.scan:
        asyncio.run(ble_scan_loop(timeout=args.timeout))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
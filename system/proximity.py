# airpods_ble/proximity.py
from typing import Any, Dict, List, Optional, Tuple

# -------------------------
# Proximity Key Types
# -------------------------
PROXIMITY_KEY_TYPES: Dict[int, str] = {
    0x01: "IRK",
    0x04: "ENC_KEY"
}

# -------------------------
# Parse Proximity Keys Response
# -------------------------
def parse_proximity_keys_response(data: bytes) -> Optional[List[Tuple[str, bytes]]]:
    """
    Parse a proximity keys response packet from AirPods.

    Args:
        data: raw bytes from L2CAP channel

    Returns:
        List of (key_type, key_bytes) or None if invalid
    """
    if len(data) < 7 or data[4] != 0x31:
        return None

    key_count: int = data[6]
    keys: List[Tuple[str, bytes]] = []
    offset: int = 7

    for _ in range(key_count):
        if offset + 3 >= len(data):
            break
        key_type: int = data[offset]
        key_length: int = data[offset + 2]
        offset += 4
        if offset + key_length > len(data):
            break
        key_bytes: bytes = data[offset:offset + key_length]
        keys.append((PROXIMITY_KEY_TYPES.get(key_type, f"TYPE_{key_type:02X}"), key_bytes))
        offset += key_length

    return keys

# -------------------------
# Parse Proximity Pairing Message
# -------------------------
def parse_proximity_pairing_message(msg: bytes) -> Dict[str, Any]:
    """
    Parse a BLE proximity pairing message for AirPods.

    Args:
        msg: raw BLE message bytes

    Returns:
        dict containing pairing, ear detection, battery, lid, and connection info
    """
    if len(msg) < 27 or msg[0] != 0x07:
        return {}

    result: Dict[str, Any] = {}
    result["paired"] = bool(msg[2])
    result["device_model"] = (msg[3] << 8) | msg[4]

    status = msg[5]
    result["status_byte"] = status
    result["pods_battery_byte"] = msg[6]
    result["flags_case_battery"] = msg[7]
    result["lid_indicator"] = msg[8]
    result["device_color"] = msg[9]
    result["connection_state"] = msg[10]

    primary_left = bool((status >> 5) & 1)
    is_this_pod_in_case = bool((status >> 6) & 1)
    are_values_flipped = primary_left ^ is_this_pod_in_case

    result["left_in_ear"] = ((status >> 3) & 1) if are_values_flipped else ((status >> 1) & 1)
    result["right_in_ear"] = ((status >> 1) & 1) if are_values_flipped else ((status >> 3) & 1)

    return result
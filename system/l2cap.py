# airpods_ble/l2cap.py
import asyncio
import logging
from asyncio import Queue, TimeoutError
from socket import socket as Socket
from typing import Any, List, Optional, Tuple
from .proximity import parse_proximity_keys_response

logger = logging.getLogger("airpods_ble.l2cap")
logger.setLevel(logging.INFO)

PSM_PROXIMITY: int = 0x1001
HANDSHAKE: bytes = bytes.fromhex("00 00 04 00 01 00 02 00 00 00 00 00 00 00 00 00")
KEY_REQ: bytes = bytes.fromhex("04 00 04 00 30 00 05 00")

# =========================
# Async Key Exchange
# =========================
async def exchange_keys(channel: Any, timeout: float = 5.0) -> Optional[List[Tuple[str, bytes]]]:
    """
    Exchange BLE keys with AirPods over an abstract channel.

    Args:
        channel: any object supporting 'send_pdu' and 'sink' callable
        timeout: seconds to wait for response

    Returns:
        List of tuples (key_type, key_bytes) or None on timeout
    """
    recv_q: Queue = Queue()
    channel.sink = lambda sdu: recv_q.put_nowait(sdu)

    logger.info("Sending handshake packet...")
    channel.send_pdu(HANDSHAKE)
    await asyncio.sleep(0.5)

    logger.info("Sending key request packet...")
    channel.send_pdu(KEY_REQ)

    try:
        pkt: bytes = await asyncio.wait_for(recv_q.get(), timeout)
        keys: Optional[List[Tuple[str, bytes]]] = parse_proximity_keys_response(pkt)
        return keys
    except TimeoutError:
        logger.warning("Timed out waiting for keys")
        return None

# =========================
# Linux L2CAP Direct Connection
# =========================
def run_linux_l2cap(bdaddr: str) -> None:
    """
    Directly connect to AirPods via L2CAP on Linux and fetch proximity keys.

    Args:
        bdaddr: AirPods Bluetooth MAC address
    """
    sock: Socket = Socket(Socket.AF_BLUETOOTH, Socket.SOCK_SEQPACKET, Socket.BTPROTO_L2CAP)
    try:
        logger.info(f"Connecting to {bdaddr} L2CAP PSM={PSM_PROXIMITY}")
        sock.connect((bdaddr, PSM_PROXIMITY))
        sock.send(HANDSHAKE)
        sock.send(KEY_REQ)

        while True:
            pkt: bytes = sock.recv(1024)
            keys = parse_proximity_keys_response(pkt)
            if keys:
                logger.info("Keys received successfully:")
                for name, k in keys:
                    logger.info(f"  {name}: {' '.join(f'{b:02X}' for b in k)}")
                break
    except Exception as e:
        logger.error(f"L2CAP error: {e}")
    finally:
        sock.close()
        logger.info("Connection closed")
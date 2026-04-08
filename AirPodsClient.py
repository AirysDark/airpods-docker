#!/usr/bin/env python3
"""
AirPodsClient.py
Provides a class interface for interacting with the AirPods Web API
Exposes connect, state, noise, raw, and record commands
"""

import requests

class AirPodsClient:
    """
    Client for controlling the AirPods Web API
    """

    def __init__(self, api_url: str = "http://localhost:5000"):
        self.api_url = api_url

    def connect(self):
        """Connect to the AirPods"""
        try:
            r = requests.get(f"{self.api_url}/connect")
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"error": str(e)}

    def state(self):
        """Get current state of AirPods"""
        try:
            r = requests.get(f"{self.api_url}/state")
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"error": str(e)}

    def noise(self, mode: int):
        """Set noise mode"""
        try:
            r = requests.get(f"{self.api_url}/noise/{mode}")
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"error": str(e)}

    def raw(self, hex_str: str):
        """Send raw hex command"""
        try:
            r = requests.post(f"{self.api_url}/raw", data=hex_str)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"error": str(e)}

    def record(self, action: str):
        """
        Control recording: 'start', 'stop', 'save', or 'replay'
        """
        if action not in ["start", "stop", "save", "replay"]:
            return {"error": "Invalid action"}
        try:
            r = requests.get(f"{self.api_url}/record/{action}")
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"error": str(e)}


# Demo usage when running directly
if __name__ == "__main__":
    client = AirPodsClient()
    print("Connecting:", client.connect())
    print("State:", client.state())
    print("Noise mode 1:", client.noise(1))
    print("Raw command 00FF:", client.raw("00FF"))
    print("Record start:", client.record("start"))
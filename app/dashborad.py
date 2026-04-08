#!/usr/bin/env python3
import os
import sys
import time
import requests
sys.path.append("/debug")

API = "http://localhost:5050"
REFRESH_INTERVAL = 0.5  # seconds

# =========================
# Helpers
# =========================
def bar(val, width=20):
    """Return a simple text-based progress bar for a percentage value."""
    filled = int((val / 100) * width)
    return "¦" * filled + "-" * (width - filled)

def draw_graph(values, width=50, height=10):
    """Return a 2D list representing a vertical bar graph for console display."""
    graph = [[" " for _ in range(width)] for _ in range(height)]
    if not values:
        return graph
    max_val = max(values) if max(values) != 0 else 1
    for i, v in enumerate(values[-width:]):
        h = int((v / max_val) * (height - 1))
        for y in range(h):
            graph[height - 1 - y][i] = "¦"
    return graph

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

# =========================
# Main Logging Dashboard
# =========================
def logging_dashboard():
    head_history = []

    while True:
        try:
            data = requests.get(f"{API}/state", timeout=1).json()
        except Exception:
            print("Unable to fetch state from API.")
            time.sleep(REFRESH_INTERVAL)
            continue

        battery = data.get("battery", {})
        mode = data.get("noise_mode", "Unknown")
        ca = data.get("ca_enabled", False)
        head = data.get("head", {}).get("orientation", [0,0,0])

        # Track X-axis
        head_history.append(head[0] if head else 0)
        if len(head_history) > 100:
            head_history.pop(0)

        clear_console()
        print("=== AirPods Logging Dashboard ===")
        print(f"Noise Mode: {mode} | Conversational Awareness: {ca}")
        print("-"*40)

        # Battery display
        for comp in ["Left", "Right", "Case"]:
            if comp in battery:
                lvl = battery[comp]["level"]
                status = battery[comp]["status"]
                print(f"{comp:5}: {lvl:3}% [{bar(lvl)}] | Status: {status}")

        # Head Tracking
        print("\nHead Tracking (X-axis):")
        graph = draw_graph(head_history, width=50, height=10)
        for line in graph:
            print("".join(line))

        # Footer
        print("\nControls: Use web UI at http://localhost:5050")
        print(f"Refreshing every {REFRESH_INTERVAL} seconds...")
        time.sleep(REFRESH_INTERVAL)

# =========================
# Entry
# =========================
if __name__ == "__main__":
    logging_dashboard()
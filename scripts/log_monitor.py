# scripts/log_monitor.py

# ==============================================================================
# Govee LAN API Plus – Log Monitor
# --------------------------------
#
# Description:
# Watches the Frida-generated MQTT log file for changes and triggers extraction
# of the most recent Govee MQTT payload using a filesystem observer and
# background thread.
#
# Author: Jimmy Hickman
# License: MIT
# ==============================================================================

import os
import sys
import time
import json
import re
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add root path to sys.path to support relative imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.govee_device import GoveeDevice
from models.govee_diy_scene import GoveeDIYScene
from scripts.frida_govee_mqtt_extractor import extract_and_generate_mqtt_payload


class LogChangeHandler(FileSystemEventHandler):
    """Handles filesystem events on the MQTT log file."""

    def __init__(self, log_path, on_detected):
        self.log_path = log_path
        self.last_size = os.path.getsize(log_path) if os.path.exists(log_path) else 0
        self.on_detected = on_detected

    def on_modified(self, event):
        if event.src_path == self.log_path:
            new_size = os.path.getsize(self.log_path)
            if new_size > self.last_size:
                self.last_size = new_size
                self.on_detected()


def wait_for_log_update(log_path, on_detected, device: GoveeDevice, scene: GoveeDIYScene, timeout=60):
    """
    Monitors the log file for MQTT scene trigger and extracts the payload.

    Args:
        log_path (str): Path to the log file being monitored.
        on_detected (function): Callback when a valid update is detected.
        device (GoveeDevice): The selected Govee device object.
        scene (GoveeDIYScene): The scene object selected by the user.
        timeout (int): Max time to wait for scene trigger (in seconds).
    """
    triggered = threading.Event()

    def wrapper():
        # Brief delay ensures the message is fully written to disk
        time.sleep(0.25)
        print("🔍 Log file updated. Attempting to extract MQTT payload...")
        success = extract_and_generate_mqtt_payload(device, scene)
        if success:
            print("✅ Scene generated. Returning to scene list.")
            triggered.set()

    # Start filesystem observer
    event_handler = LogChangeHandler(log_path, wrapper)
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(log_path), recursive=False)
    observer.start()

    print("⏳ Waiting for MQTT scene trigger... (press Enter to cancel)")

    # Enable keyboard interrupt with `Enter`
    def listen_for_cancel(triggered_event):
        import select
        while not triggered_event.is_set():
            if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
                sys.stdin.readline()
                print("❌ User cancelled.")
                triggered_event.set()
                break

    input_thread = threading.Thread(target=listen_for_cancel, args=(triggered,))
    input_thread.daemon = True
    input_thread.start()

    try:
        triggered.wait(timeout)
        if not triggered.is_set():
            print("⚠️ Timeout: No scene trigger detected.")
            try:
                import termios
                termios.tcflush(sys.stdin, termios.TCIFLUSH)
            except Exception:
                pass
    finally:
        observer.stop()
        observer.join()
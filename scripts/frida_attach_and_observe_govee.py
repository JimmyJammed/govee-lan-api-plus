# scripts/frida_attach_and_observe_govee.py

# ==============================================================================
# Govee LAN API Plus – Frida MQTT Observer
# ----------------------------------------
#
# Description:
# This script attaches to the Govee Android app using Frida and logs MQTT payloads
# published over the LAN, which are used to control DIY scenes.
#
# The captured payloads are written to `logs/frida_govee_mqtt_output.log`.
#
# Author: Jimmy Hickman
# License: MIT
# ==============================================================================

import os
import sys
import time
import subprocess
import frida

from dotenv import load_dotenv
load_dotenv()

from typing import Optional

# --- Configuration ---

# Load environment variables
FRIDA_SERVER_IP_ADDRESS = os.getenv("FRIDA_SERVER_IP_ADDRESS", "127.0.0.1")
FRIDA_SERVER_PORT = int(os.getenv("FRIDA_SERVER_PORT", 27042))
FRIDA_LAUNCH_DELAY = int(os.getenv("FRIDA_LAUNCH_DELAY", 5))
FRIDA_LOG_FILE_PATH = os.path.abspath(os.getenv("FRIDA_LOG_FILE_PATH", "logs/frida_govee_mqtt_output.log"))
FRIDA_SERVER_BINARY_PATH = os.path.abspath(os.getenv("FRIDA_SERVER_BINARY_PATH", "bin/frida-server-16.7.10-android-arm64"))
FRIDA_LOG_MQQT_URI_FILE_PATH = os.path.abspath(os.getenv("FRIDA_LOG_MQQT_URI_FILE_PATH", "frida_log_mqtt_uri.js"))
FRIDA_SERVER_CLIENT_PATH = os.getenv("FRIDA_SERVER_CLIENT_PATH", "/data/local/tmp/frida-server")

sys.stdout.reconfigure(line_buffering=True)

# --- Ensure Log Directory Exists ---
os.makedirs(os.path.dirname(FRIDA_LOG_FILE_PATH), exist_ok=True)
open(FRIDA_LOG_FILE_PATH, "w").close()  # Clear previous log content

def start_frida_server():
    """Start the Frida server on the connected Android device via ADB."""
    print("\n🚀 Starting Frida server on device...")

    subprocess.run(["adb", "push", FRIDA_SERVER_BINARY_PATH, FRIDA_SERVER_CLIENT_PATH])
    subprocess.run(["adb", "shell", "chmod", "+x", FRIDA_SERVER_CLIENT_PATH])
    subprocess.run(["adb", "shell", f"su -c '{FRIDA_SERVER_CLIENT_PATH} -l 0.0.0.0:{FRIDA_SERVER_PORT} &'"])
    subprocess.run(["adb", "forward", f"tcp:{FRIDA_SERVER_PORT}", f"tcp:{FRIDA_SERVER_PORT}"])

    print("⏳ Waiting for Frida server to be ready...")
    time.sleep(2)
    print("✅ Frida server is running!")

def get_govee_app_id() -> Optional[str]:
    """Return the PID of the Govee app running on the connected device."""
    try:
        result = subprocess.run(
            ["frida-ps", "-H", f"{FRIDA_SERVER_IP_ADDRESS}:{FRIDA_SERVER_PORT}", "-ai"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if "com.govee.home" in line:
                    return line.split()[0]  # PID
            print("❌ Govee app not found in the process list.")
        else:
            print(f"❌ Error fetching app ID: {result.stderr}")
    except Exception as e:
        print(f"❌ Failed to get Govee app ID: {e}")
    return None


def attach_frida_to_app(app_id: str):
    """Attach to the Govee app using Frida and hook MQTT payloads."""
    print(f"\n🔌 Attaching to Govee app with ID {app_id}...")

    with open(FRIDA_LOG_MQQT_URI_FILE_PATH, "r", encoding="utf-8") as f:
        script_source = f.read()

    device = frida.get_device_manager().add_remote_device(f"{FRIDA_SERVER_IP_ADDRESS}:{FRIDA_SERVER_PORT}")
    session = device.attach(int(app_id))
    script = session.create_script(script_source)

    print(f"📄 Writing logs to: {FRIDA_LOG_FILE_PATH}")

    def on_message(message, data):
        if message["type"] == "send":
            log_mqtt_event(message["payload"] + "\n")
        elif message["type"] == "error":
            print(f"❌ Frida error: {message['stack']}")

    script.on("message", on_message)
    script.load()

    print("🟢 MQTT observer is running. Waiting for hooks to settle...")

    for i in range(FRIDA_LAUNCH_DELAY, 0, -1):
        print(f"⏳ Preparing to capture... {i}")
        time.sleep(1)

    print("\n📲 Trigger the scene in the Govee app, then press Enter to stop logging.")
    input()

    print("\n🛑 Stopping Frida observer...")
    session.detach()


def log_mqtt_event(event_data: str):
    """Append an MQTT event string to the log file."""
    try:
        with open(FRIDA_LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(event_data)
            log_file.flush()
            os.fsync(log_file.fileno())
    except Exception as e:
        print(f"❌ Error writing to log file: {e}")


def main():
    """Entrypoint for running the MQTT observer script."""
    start_frida_server()
    app_id = get_govee_app_id()
    if app_id:
        print(f"Govee App ID: {app_id}")
        attach_frida_to_app(app_id)
    else:
        print("❌ No app ID found. Please ensure the Govee app is running on your device.")


if __name__ == "__main__":
    main()
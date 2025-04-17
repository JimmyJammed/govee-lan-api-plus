# scripts/lan_discover_govee_devices.py

# ==============================================================================
# Govee LAN API Plus – LAN Device Discovery
# -----------------------------------------
#
# Description:
# This script sends a multicast UDP scan request to discover Govee devices
# available on the local network using the LAN control protocol.
#
# Devices that respond with valid LAN metadata are returned as dictionaries
# containing IP address, device ID, SKU, and model name.
#
# Author: Jimmy Hickman
# License: MIT
# ==============================================================================

import socket
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configurable via .env
LAN_IP_ADDRESS_HELPER_MULTICAST_GROUP = os.getenv("LAN_IP_ADDRESS_HELPER_MULTICAST_GROUP", "239.255.255.250")
LAN_IP_ADDRESS_HELPER_SEND_PORT = int(os.getenv("LAN_IP_ADDRESS_HELPER_SEND_PORT", 4001))
LAN_IP_ADDRESS_HELPER_RECEIVE_PORT = int(os.getenv("LAN_IP_ADDRESS_HELPER_RECEIVE_PORT", 4002))
LAN_IP_ADDRESS_HELPER_TIMEOUT = int(os.getenv("LAN_IP_ADDRESS_HELPER_TIMEOUT", 3))

# Discovery message formatted according to Govee LAN protocol
SCAN_MESSAGE = json.dumps({
    "msg": {
        "cmd": "scan",
        "data": {
            "account_topic": "reserve"
        }
    }
}).encode("utf-8")


def discover_govee_devices():
    """Sends a multicast discovery packet and listens for Govee LAN device responses."""
    print(f"📡 Sending scan request to {LAN_IP_ADDRESS_HELPER_MULTICAST_GROUP}:{LAN_IP_ADDRESS_HELPER_SEND_PORT}...")

    # Send multicast discovery message
    send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    send_sock.sendto(SCAN_MESSAGE, (LAN_IP_ADDRESS_HELPER_MULTICAST_GROUP, LAN_IP_ADDRESS_HELPER_SEND_PORT))
    send_sock.close()

    # Listen for responses from devices
    recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    recv_sock.bind(("", LAN_IP_ADDRESS_HELPER_RECEIVE_PORT))
    recv_sock.settimeout(LAN_IP_ADDRESS_HELPER_TIMEOUT)

    print(f"⏳ Listening for responses on port {LAN_IP_ADDRESS_HELPER_RECEIVE_PORT} for {LAN_IP_ADDRESS_HELPER_TIMEOUT} seconds...")
    start = time.time()
    found_devices = []

    while time.time() - start < LAN_IP_ADDRESS_HELPER_TIMEOUT:
        try:
            data, addr = recv_sock.recvfrom(2048)
            response = json.loads(data.decode("utf-8"))
            ip = addr[0]
            device_info = response.get("msg", {}).get("data", {})

            print(f"✅ Found: IP={ip}, ID={device_info.get('device')}, "
                  f"SKU={device_info.get('sku')}, Model={device_info.get('device_name')}")

            found_devices.append({
                "ip": ip,
                "device": device_info.get("device"),
                "sku": device_info.get("sku"),
                "model": device_info.get("device_name")
            })

        except socket.timeout:
            break
        except Exception as e:
            print(f"⚠️  Error decoding response: {e}")

    recv_sock.close()
    return found_devices


def main():
    print("🔍 Discovering Govee LAN devices...")
    devices = discover_govee_devices()
    if not devices:
        print("❌ No devices found.")


if __name__ == "__main__":
    main()
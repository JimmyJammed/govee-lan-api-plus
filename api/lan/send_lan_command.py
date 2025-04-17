# api/lan/send_lan_command.py

# ==============================================================================
# Govee LAN API Plus – LAN Command Sender
# ---------------------------------------
#
# Description:
# This module provides a function for sending UDP commands directly
# to Govee smart devices over the local network (LAN).
#
# Author: Jimmy Hickman
# License: MIT
# ==============================================================================

import socket
import json
import logging

# Configure logging format
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

def send_lan_command(cmd: dict, device_ip: str, device_port: int) -> None:
    """
    Sends a UDP JSON command to a Govee device over LAN.

    Args:
        cmd (dict): The JSON-serializable command payload to send.
        device_ip (str): The IP address of the target Govee device.
        device_port (int): The port to send the UDP packet to (usually 4003).
    """
    message = json.dumps(cmd)
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.sendto(message.encode('utf-8'), (device_ip, device_port))
    udp_socket.close()

    logging.info(f"📤 Sent LAN command to {device_ip}:{device_port} → {message}")
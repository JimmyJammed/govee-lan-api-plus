# models/govee_device.py

# ==============================================================================
# Govee LAN API Plus – GoveeDevice Model
# --------------------------------------
#
# Description:
# Represents a Govee smart device, including its basic info and runtime state.
#
# This model is used throughout the LAN and Cloud API toolchain to manage
# connected devices and send commands.
#
# Author: Jimmy Hickman
# License: MIT
# ==============================================================================

class GoveeDevice:
    def __init__(self, device_id: str, name: str, sku: str, ip: str = ""):
        """
        Initialize a GoveeDevice.

        Args:
            device_id (str): The unique device ID
            name (str): The user-friendly device name (e.g. "RGBIC String Light")
            sku (str): The device model/SKU (e.g. "H6001")
            ip (str, optional): LAN IP address of the device. Defaults to "".
        """
        self.id = device_id
        self.name = name
        self.sku = sku

        self.online = False
        self.power_state = "off"
        self.brightness = 0
        self.color = {"r": 0, "g": 0, "b": 0}
        self.color_temp_in_kelvin = None

        self.ip = ip
        self.port = 4003  # Default LAN UDP command port for Govee devices
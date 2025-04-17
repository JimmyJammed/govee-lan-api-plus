# models/govee_diy_scene.py

# ==============================================================================
# Govee LAN API Plus – GoveeDIYScene Model
# ----------------------------------------
#
# Description:
# Represents a custom DIY scene that can be applied to Govee smart devices.
#
# This model is used for mapping scenes to devices and referencing them
# when sending LAN or MQTT commands.
#
# Author: Jimmy Hickman
# License: MIT
# ==============================================================================

class GoveeDIYScene:
    def __init__(self, value: int, name: str):
        """
        Initialize a DIY Scene object.

        Args:
            value (int): The scene's numeric value ID (e.g. 123456)
            name (str): The user-friendly name of the scene (e.g. "Sunset Glow")
        """
        self.value = int(value)
        self.name = name
        self.devices = []  # List of device IDs this scene is associated with

    def __repr__(self) -> str:
        """
        Return a string representation for debugging and logs.
        """
        return f"GoveeDIYScene(value={self.value}, name='{self.name}')"
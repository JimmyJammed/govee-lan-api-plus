# models/govee_mqtt_diy_scene.py

# ==============================================================================
# Govee LAN API Plus – GoveeMqttDiyScene Model
# --------------------------------------------
#
# Description:
# Represents a captured MQTT payload structure used to trigger a DIY Scene
# over LAN using Govee's internal messaging format.
#
# Author: Jimmy Hickman
# License: MIT
# ==============================================================================

from typing import List

class GoveeMqttDiyScene:
    """
    A model representing a Govee MQTT DIY Scene payload.

    These objects are typically extracted from the Govee app's network traffic
    and can be replayed locally via LAN to trigger DIY scenes.
    """

    def __init__(
        self,
        accountTopic: str,
        cmd: str,
        transaction: str,
        type: int,
        write: str,
        command: List[str]
    ):
        """
        Initialize an MQTT DIY scene payload.

        Args:
            accountTopic (str): The account-level MQTT topic (e.g. "GA/abc123...")
            cmd (str): Command type (usually "ptReal" for DIY scenes)
            transaction (str): Transaction ID associated with the request
            type (int): Message type (usually 1)
            write (str): Indicates if this is a write operation ("true" or "false")
            command (List[str]): Base64-encoded command payloads
        """
        self.accountTopic = accountTopic
        self.cmd = cmd
        self.transaction = transaction
        self.type = type
        self.write = write
        self.command = command

    def to_dict(self) -> dict:
        """
        Convert the object to a dictionary suitable for logging or debugging.

        Returns:
            dict: Dictionary with all internal properties.
        """
        return {
            "accountTopic": self.accountTopic,
            "cmd": self.cmd,
            "transaction": self.transaction,
            "type": self.type,
            "write": self.write,
            "command": self.command,
        }
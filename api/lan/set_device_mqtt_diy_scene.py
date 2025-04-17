# api/lan/set_device_mqtt_diy_scene.py

# ==============================================================================
# Govee LAN API Plus – Set MQTT DIY Scene via LAN
# ------------------------------------------------
#
# Description:
# Sends a pre-captured MQTT DIY scene payload to a specific Govee device
# using the LAN UDP protocol.
#
# Author: Jimmy Hickman
# License: MIT
# ==============================================================================

from api.lan.send_lan_command import send_lan_command

from models.govee_mqtt_diy_scene import GoveeMqttDiyScene
from models.govee_device import GoveeDevice

def set_device_mqtt_diy_scene(
    govee_device: GoveeDevice,
    govee_mqtt_diy_scene: GoveeMqttDiyScene
) -> None:
    """
    Sends a stored MQTT DIY scene to a Govee device over LAN.

    Args:
        govee_device (GoveeDevice): The target device to send the command to.
        govee_mqtt_diy_scene (GoveeMqttDiyScene): The DIY scene payload captured from MQTT.
    """
    payload = {
        "msg": {
            "accountTopic": govee_mqtt_diy_scene.accountTopic,
            "cmd": govee_mqtt_diy_scene.cmd,
            "cmdVersion": 0,
            "data": {
                "command": govee_mqtt_diy_scene.command,
                "write": govee_mqtt_diy_scene.write
            },
            "transaction": govee_mqtt_diy_scene.transaction,
            "type": govee_mqtt_diy_scene.type
        },
        "device": govee_device.id,
        "cmd": govee_mqtt_diy_scene.cmd
    }

    send_lan_command(payload, govee_device.ip, govee_device.port)
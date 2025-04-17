# ==============================================================================
# Govee LAN API Plus – Device Factory
# -----------------------------------
#
# Description:
# Auto-generated module containing GoveeDevice factory objects.
# Each device is initialized with its ID, name, SKU, and (optionally)
# LAN IP address, along with attached DIY scenes and MQTT DIY scene
# mappings.
#
# NOTE: This file is overwritten automatically by
#       generate_device_and_scene_factories.py.
#
# Author: Jimmy Hickman
# License: MIT
# ==============================================================================

from types import SimpleNamespace
from models.govee_device import GoveeDevice
from models.govee_diy_scene import GoveeDIYScene
from models.govee_mqtt_diy_scene import GoveeMqttDiyScene
from factories.device_mqtt_diy_scene_factory import *

all_devices = []

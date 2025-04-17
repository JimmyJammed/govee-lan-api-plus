# scripts/generate_device_and_scene_factories.py

# ==============================================================================
# Govee LAN API Plus – Device Factory Generator
# ---------------------------------------------
#
# Description:
# Generates the factories/device_factory.py file, which defines
# GoveeDevice objects with attached DIY and MQTT scenes.
#
# Author: Jimmy Hickman
# License: MIT
# ==============================================================================

import os
import re
from collections import defaultdict
from types import SimpleNamespace

from models.govee_diy_scene import GoveeDIYScene
from models.govee_device import GoveeDevice

DEVICE_FACTORY_FILE_PATH = os.path.abspath(os.getenv("DEVICE_FACTORY_FILE_PATH", "factories/device_factory.py"))
DEVICE_FACTORY_TEMPLATE_FILE_PATH = os.path.abspath(os.getenv("DEVICE_FACTORY_TEMPLATE_PATH", "templates/device_factory_template.py"))

def sanitize_var_name(name: str) -> str:
    """Convert device or scene name into a safe lowercase variable name."""
    name = re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_")
    return name.lower()

def generate_device_and_scene_factories(devices: dict) -> None:
    """
    Generate the device_factory.py file based on the provided device definitions.
    This includes:
    - One variable per device
    - A scenes namespace per device
    - A final all_devices list export
    """
    os.makedirs(os.path.dirname(DEVICE_FACTORY_FILE_PATH), exist_ok=True)

    device_to_scenes = defaultdict(list)
    scene_registry = {}

    # Deduplicate scenes and track device associations
    for device in devices.values():
        for scene in device.diy_scenes:
            scene_key = (scene.name, scene.value)
            if scene_key not in scene_registry:
                shared_scene = GoveeDIYScene(value=scene.value, name=scene.name)
                scene_registry[scene_key] = shared_scene

            shared_scene = scene_registry[scene_key]
            shared_scene.devices.append(device.id)
            device_to_scenes[device.id].append(shared_scene)

    with open(DEVICE_FACTORY_FILE_PATH, "w", encoding="utf-8") as f:
        # Start from template but remove any all_devices = lines
        with open(DEVICE_FACTORY_TEMPLATE_FILE_PATH, "r", encoding="utf-8") as tpl:
            for line in tpl:
                if not line.strip().startswith("all_devices ="):
                    f.write(line)

        var_names = []

        # Device declarations
        for device in devices.values():
            var_name = sanitize_var_name(device.name)
            var_names.append(var_name)

            if device.ip:
                f.write(f'{var_name} = GoveeDevice("{device.id}", "{device.name}", "{device.sku}", ip="{device.ip}")\n')
            else:
                f.write(f'{var_name} = GoveeDevice("{device.id}", "{device.name}", "{device.sku}")\n')

            # Scenes namespace
            f.write(f"{var_name}.scenes = SimpleNamespace(\n")
            for scene in device_to_scenes[device.id]:
                scene_var = f"{sanitize_var_name(scene.name)}_{scene.value}"
                f.write(f'    {scene_var}=GoveeDIYScene("{scene.value}", "{scene.name}"),\n')
            f.write(")\n\n")

        # Final export list
        f.write("all_devices = [\n")
        for name in var_names:
            f.write(f"    {name},\n")
        f.write("]\n")

    print(f"✅ Generated {len(var_names)} devices in {DEVICE_FACTORY_FILE_PATH}")
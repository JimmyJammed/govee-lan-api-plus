# scripts/frida_govee_mqtt_extractor.py

# ==============================================================================
# Govee LAN API Plus – MQTT DIY Scene Extractor
# ---------------------------------------------
#
# Description:
# Parses MQTT messages captured by Frida from the Govee app,
# extracts DIY scene command data, and generates Python factory
# variables for reuse.
#
# These are saved to:
# - factories/device_mqtt_diy_scene_factory.py
# - (and optionally appended to factories/device_factory.py)
#
# Author: Jimmy Hickman
# License: MIT
# ==============================================================================

import json
import re
import os
import sys
from typing import Optional

# Enable root path imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.govee_device import GoveeDevice
from models.govee_diy_scene import GoveeDIYScene

# --- Configuration ---

# Load environment variables
FRIDA_LOG_FILE_PATH = os.path.abspath(os.getenv("FRIDA_LOG_FILE_PATH", "logs/frida_govee_mqtt_output.log"))
DEVICE_FACTORY_FILE_PATH = os.path.abspath(os.getenv("DEVICE_FACTORY_FILE_PATH", "factories/device_factory.py"))
DEVICE_MQTT_DIY_SCENE_FACTORY_FILE_PATH = os.path.abspath(os.getenv("DEVICE_MQTT_DIY_SCENE_FACTORY_FILE_PATH", "factories/device_mqtt_diy_scene_factory.py"))
DEVICE_MQTT_DIY_SCENE_FACTORY_TEMPLATE_FILE_PATH = os.path.abspath(os.getenv("DEVICE_MQTT_DIY_SCENE_FACTORY_TEMPLATE_PATH", "templates/device_mqtt_diy_scene_factory_template.py"))

# ------------------------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------------------------

def sanitize_var_name(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", name.strip()).lower()

def make_var_name(device: GoveeDevice, scene: GoveeDIYScene) -> str:
    device_name = sanitize_var_name(device.name)
    scene_name = sanitize_var_name(scene.name)
    return f"{device_name}_{scene_name}_{scene.value}"

def extract_json_from_line(line: str) -> Optional[dict]:
    try:
        match = re.search(r'Message: (.+)$', line)
        if match:
            return json.loads(match.group(1))
    except Exception:
        pass
    return None

def format_constructor_arg(value):
    if isinstance(value, str):
        return f"'{value}'"
    return json.dumps(value)

# ------------------------------------------------------------------------------
# MQTT Command Parsing
# ------------------------------------------------------------------------------

def append_new_commands(new_var_name: str, cmd: dict, device: GoveeDevice, scene: GoveeDIYScene):
    scene_blocks = {}

    # Read existing lines or template
    if os.path.exists(DEVICE_MQTT_DIY_SCENE_FACTORY_FILE_PATH):
        with open(DEVICE_MQTT_DIY_SCENE_FACTORY_FILE_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
    elif os.path.exists(DEVICE_MQTT_DIY_SCENE_FACTORY_TEMPLATE_FILE_PATH):
        with open(DEVICE_MQTT_DIY_SCENE_FACTORY_TEMPLATE_FILE_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
    else:
        raise FileNotFoundError("Missing both factory file and template file for MQTT scenes.")

    # Remove placeholder line if present
    lines = [line for line in lines if line.strip() != "all_mqtt_diy_scenes = []"]

    # Parse scene blocks
    current_var = None
    current_block = []
    for line in lines:
        if "all_mqtt_diy_scenes" in line:
            break
        if re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*GoveeMqttDiyScene\(", line):
            if current_var and current_block:
                scene_blocks[current_var] = current_block
            current_var = line.split("=")[0].strip()
            current_block = [line]
        elif current_block is not None:
            current_block.append(line)

    if current_var and current_block:
        scene_blocks[current_var] = current_block

    # Construct new scene
    cmd_args = []
    for key in ["accountTopic", "cmd", "transaction", "type", "write", "command"]:
        if key in cmd:
            val = "true" if key == "write" and isinstance(cmd[key], bool) else cmd[key]
            cmd_args.append(f"{key}={format_constructor_arg(val)}")

    scene_blocks[new_var_name] = [f"{new_var_name} = GoveeMqttDiyScene({', '.join(cmd_args)})\n\n"]

    # Write updated file
    with open(DEVICE_MQTT_DIY_SCENE_FACTORY_FILE_PATH, "w", encoding="utf-8") as f:
        with open(DEVICE_MQTT_DIY_SCENE_FACTORY_TEMPLATE_FILE_PATH, "r", encoding="utf-8") as tpl:
            template_lines = tpl.readlines()
            f.writelines([line for line in template_lines if line.strip() != "all_mqtt_diy_scenes = []"])

        for var in sorted(scene_blocks):
            f.writelines(scene_blocks[var])

        f.write("all_mqtt_diy_scenes = [\n")
        for var in sorted(scene_blocks):
            f.write(f"    {var},\n")
        f.write("]\n")

# ------------------------------------------------------------------------------
# Append to device_factory.py
# ------------------------------------------------------------------------------

def append_mqtt_scene_to_device_factory(var_name: str, device: GoveeDevice):
    if not os.path.exists(DEVICE_FACTORY_FILE_PATH):
        print(f"❌ Device factory file not found: {DEVICE_FACTORY_FILE_PATH}")
        return

    with open(DEVICE_FACTORY_FILE_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    device_var = sanitize_var_name(device.name)
    namespace_start = None
    namespace_end = None

    for i, line in enumerate(lines):
        if line.strip() == f"{device_var}.mqtt_diy_scenes = SimpleNamespace(":
            namespace_start = i
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == ")":
                    namespace_end = j
                    break
            break

    new_line = f"    {var_name}={var_name},\n"

    if namespace_start is not None and namespace_end is not None:
        if any(var_name in line for line in lines[namespace_start:namespace_end]):
            print(f"⚠️ Scene '{var_name}' already exists in mqtt_diy_scenes for {device_var}")
            return
        lines.insert(namespace_end, new_line)
    else:
        insert_index = None
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{device_var} = GoveeDevice("):
                insert_index = i
        if insert_index is not None:
            while insert_index < len(lines) and lines[insert_index].strip() != "":
                insert_index += 1
            lines.insert(insert_index + 1, f"{device_var}.mqtt_diy_scenes = SimpleNamespace(\n")
            lines.insert(insert_index + 2, new_line)
            lines.insert(insert_index + 3, ")\n\n")

    with open(DEVICE_FACTORY_FILE_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"✅ Added {var_name} to mqtt_diy_scenes for {device_var}")

# ------------------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------------------

def extract_and_generate_mqtt_payload(device: GoveeDevice, scene: GoveeDIYScene) -> bool:
    if not os.path.exists(FRIDA_LOG_FILE_PATH):
        print(f"❌ Log file not found: {FRIDA_LOG_FILE_PATH}")
        return False

    with open(FRIDA_LOG_FILE_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in reversed(lines):
        entry = extract_json_from_line(line)
        if entry and "msg" in entry:
            msg = entry["msg"]
            if all(k in msg for k in ["accountTopic", "cmd", "data", "transaction", "type"]):
                cmd = {
                    "accountTopic": msg["accountTopic"],
                    "cmd": msg["cmd"],
                    "transaction": msg["transaction"],
                    "type": msg["type"]
                }
                cmd.update({
                    k: v for k, v in msg.get("data", {}).items()
                    if k in ["write", "command", "color", "colorTemInKelvin", "val", "open", "version"]
                })
                var_name = make_var_name(device, scene)
                append_new_commands(var_name, cmd, device, scene)
                append_mqtt_scene_to_device_factory(var_name, device)
                print(f"✅ Added or updated command '{var_name}' in factory.")
                return True

    print("⚠️ No valid MQTT payloads found in logs.")
    return False

def main():
    pass

if __name__ == "__main__":
    main()

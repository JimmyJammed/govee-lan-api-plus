# scripts/run_govee_setup.py

# ===============================================================================
# Govee LAN API Plus – Setup Wizard
# ------------------------------------------------------------------------------
# Author : Jimmy Hickman
# License: MIT
# File   : run_govee_setup.py
# Desc   : Main wizard CLI for syncing Govee devices, capturing DIY scenes,
#          updating LAN IPs, and sending MQTT DIY scene commands via local control.
#          This script integrates Govee Cloud and LAN APIs with Frida observation
#          tools and dynamic Python factory generation.
# ===============================================================================

import os
import sys
import re
import time
import signal
import subprocess
import importlib
from types import SimpleNamespace

from dotenv import load_dotenv, set_key
load_dotenv()

from scripts.generate_device_and_scene_factories import sanitize_var_name, generate_device_and_scene_factories
from scripts.select_from_list import select_from_list
from scripts.frida_govee_mqtt_extractor import extract_and_generate_mqtt_payload
from scripts.lan_discover_govee_devices import discover_govee_devices
from scripts.log_monitor import wait_for_log_update

from api.cloud.get_devices import get_govee_devices
from api.cloud.get_device_diy_scenes import get_device_diy_scenes
from api.lan.set_device_mqtt_diy_scene import set_device_mqtt_diy_scene

from models.govee_device import GoveeDevice
from models.govee_diy_scene import GoveeDIYScene
from models.govee_mqtt_diy_scene import GoveeMqttDiyScene

from factories.device_factory import all_devices
import factories.device_mqtt_diy_scene_factory as mqtt_scene_factory

# --- Configuration ---

# Load environment variables
ENV_FILE_PATH = os.path.join(os.path.dirname(__file__), ".env")
GOVEE_API_KEY = os.getenv("GOVEE_API_KEY")
FRIDA_LAUNCH_DELAY = int(os.getenv("FRIDA_LAUNCH_DELAY", 5))
FRIDA_LOG_FILE_PATH = os.path.abspath(os.getenv("FRIDA_LOG_FILE_PATH", "logs/frida_govee_mqtt_output.log"))
DEVICE_FACTORY_FILE_PATH = os.path.abspath(os.getenv("DEVICE_FACTORY_FILE_PATH", "factories/device_factory.py"))

def update_env_file(filepath, key, value, comment=""):
    updated = False
    new_lines = []

    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith(f"{key}="):
                    # Preserve inline comment if it exists
                    existing_comment = ""
                    if "#" in line:
                        parts = line.split("#", 1)
                        existing_comment = parts[1].strip()
                        if not existing_comment:
                            existing_comment = comment
                    else:
                        existing_comment = comment

                    # Rebuild the line with updated value
                    updated_line = f'{key}="{value}"'
                    if existing_comment:
                        updated_line += f"  # {existing_comment}"
                    new_lines.append(updated_line + "\n")
                    updated = True
                else:
                    new_lines.append(line)

    if not updated:
        new_line = f'{key}="{value}"'
        if comment:
            new_line += f"  # {comment}"
        new_lines.append(new_line + "\n")

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

def prompt_for_govee_api_key_if_needed():
    global GOVEE_API_KEY
    
    if not GOVEE_API_KEY or GOVEE_API_KEY.strip() == "":
        print("🔐 Govee API Key is not set.")
        GOVEE_API_KEY = input("Please enter your Govee API Key: ").strip()
        if not GOVEE_API_KEY:
            print("❌ API key is required to continue.")
            sys.exit(1)
        print("💾 Saving key to .env...")
        update_env_file(
            ENV_FILE_PATH,
            "GOVEE_API_KEY",
            GOVEE_API_KEY,
            comment="Set your Govee Cloud API Key here. Reference: https://developer.govee.com/reference/apply-you-govee-api-key"
        )
        load_dotenv(ENV_FILE_PATH, override=True)
        print("✅ API key saved and environment reloaded.")

def sync_govee_devices(api_key: str):
    print("\n🔄 Syncing devices from Cloud API...")
    devices = get_govee_devices(api_key=api_key)
    print(f"Found {len(devices)} devices in the cloud.")

    print("🎨 Fetching scenes for each device...")
    for device in devices.values():
        scenes = get_device_diy_scenes(device.id, device.sku, api_key=api_key)
        print(f"Found {len(scenes)} scenes for device {device.name} ({device.id})")
        device.diy_scenes = [GoveeDIYScene(value=s["value"], name=s["name"]) for s in scenes]

    print("📡 Discovering devices on LAN...")
    lan_devices = discover_govee_devices()
    lan_device_map = {d["device"].lower(): d["ip"] for d in lan_devices if d.get("device") and d.get("ip")}

    print("🔗 Linking device LAN IPs to cloud devices...")
    for device in devices.values():
        if device.id.lower() in lan_device_map:
            device.ip = lan_device_map[device.id.lower()]

    print("🏗️ Generating factories...")
    generate_device_and_scene_factories(devices)
    print("🎬 Reloading MQTT DIY Scene captures...")
    refresh_mqtt_diy_scene_factories()
    print("✅ Sync complete!")

def reload_device_factory():
    import factories.device_factory as df
    importlib.reload(df)
    if len(df.all_devices) > 0:
        print("♻️ Reloaded devices from disk.")
    return df.all_devices

def load_devices_from_factory():
    try:
        return reload_device_factory()
    except Exception as e:
        print(f"⚠️ Failed to reload factory devices: {e}")
        return None

def capture_scene_mqtt(api_key: str):
    print("\n🔍 Fetching Govee devices...")

    devices = load_devices_from_factory()
    if devices:
        print(f"📦 Loaded {len(devices)} devices from factory.")
    else:
        print("☁️ Fetching devices from Govee Cloud API...")
        devices = list(get_govee_devices(api_key=api_key).values())

    device_list = list(devices)

    while True:
        print("\n📱 Available Devices:")
        for i, d in enumerate(device_list, 1):
            print(f"{i}. {d.name} ({d.id})")

        selected_device_index = input("\nSelect a device (or enter to 👈 go back): ").strip()
        if selected_device_index == "":
            print("👋 Leaving MQTT Scene Capturing.")
            return

        try:
            selected_device = device_list[int(selected_device_index) - 1]
        except (IndexError, ValueError):
            print("❌ Invalid device selection. Try again.")
            continue

        print(f"\n🎯 Selected device: {selected_device.name} ({selected_device.id})")

        if hasattr(selected_device, "scenes") and isinstance(selected_device.scenes, SimpleNamespace):
            scene_dict = vars(selected_device.scenes)
            if scene_dict:
                print(f"📦 Using {len(scene_dict)} cached DIY scenes for this device.")
                selected_device.diy_scenes = list(scene_dict.values())
            else:
                print(f"☁️ Fetching DIY scenes for {selected_device.name} from Cloud...")
                scene_options = get_device_diy_scenes(selected_device.id, selected_device.sku, api_key=GOVEE_API_KEY)
                selected_device.diy_scenes = [
                    GoveeDIYScene(value=opt["value"], name=opt["name"]) for opt in scene_options
                ]
        else:
            print(f"☁️ Fetching DIY scenes for {selected_device.name} from Cloud...")
            scene_options = get_device_diy_scenes(selected_device.id, selected_device.sku, api_key=api_key)
            selected_device.diy_scenes = [
                GoveeDIYScene(value=opt["value"], name=opt["name"]) for opt in scene_options
            ]

        if not selected_device.diy_scenes:
            print("❌ No DIY scenes found for this device.")
            continue

        while True:
            print(f"\n🎬 Scenes for {selected_device.name}:")
            for i, scene in enumerate(selected_device.diy_scenes, 1):
                print(f"{i}. {scene.name} ({scene.value})")

            selected_scene_index = input("\nSelect a scene (or enter to 👈 go back): ").strip()
            if selected_scene_index == "":
                break

            try:
                selected_scene = selected_device.diy_scenes[int(selected_scene_index) - 1]
            except (IndexError, ValueError):
                print("❌ Invalid scene selection. Try again.")
                continue

            while True:
                print(f"\n🎬 Selected scene: {selected_scene.name} ({selected_scene.value})")

                print("📡 Starting Frida MQTT observer (running in background)...")
                frida_proc = subprocess.Popen(
                    ["python3", "scripts/frida_attach_and_observe_govee.py"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setsid
                )
                # TEMP DEBUG MODE: show logs live
                # frida_proc = subprocess.Popen(
                #     ["python3", "scripts/frida_attach_and_observe_govee.py"]
                # )

                print("⏳ Preparing MQTT hook...")
                for i in range(FRIDA_LAUNCH_DELAY, 0, -1):
                    print(f"   Waiting for hooks to activate... {i}")
                    time.sleep(1)
                print("🪝 Hooks ready! You may now trigger the scene you want to capture from the Govee app.")

                from scripts.log_monitor import wait_for_log_update

                triggered = False

                def on_mqtt_triggered():
                    nonlocal triggered
                    triggered = True
                    print("📡 Detected MQTT payload in log!")

                wait_for_log_update(FRIDA_LOG_FILE_PATH, on_mqtt_triggered, selected_device, selected_scene, timeout=60)

                try:
                    import termios
                    termios.tcflush(sys.stdin, termios.TCIFLUSH)
                except Exception:
                    pass

                print("\n🛑 Stopping Frida observer...")
                try:
                    if frida_proc.poll() is None:
                        os.killpg(os.getpgid(frida_proc.pid), signal.SIGTERM)
                        frida_proc.wait()
                except ProcessLookupError:
                    print("⚠️  Frida process already exited.")

                print("\n📦 Extracting MQTT payload...")
                extract_and_generate_mqtt_payload(selected_device, selected_scene)
                print("✅ Scene captured!")

                while True:
                    another = input("\n➕ Would you like to capture another scene? (y/n): ").strip().lower()
                    if another == "y":
                        break
                    elif another == "n":
                        return
                    else:
                        print("❌ Invalid input. Please enter 'y' or 'n'.")
                break

def send_mqtt_scene():
    print("\n📡 Send LAN MQTT DIY Scene")

    devices = load_devices_from_factory()
    if not devices:
        print("❌ No devices loaded from factory.")
        return

    print("\n📱 Available Devices:")
    for i, d in enumerate(devices, 1):
        print(f"{i}. {d.name} ({d.id})")

    selected_device_index = input("\nSelect a device (or enter to 👈 go back): ").strip()
    if selected_device_index == "":
        return

    try:
        selected_device = devices[int(selected_device_index) - 1]
    except (IndexError, ValueError):
        print("❌ Invalid device selection.")
        return

    scene_dict = {}
    if hasattr(selected_device, "mqtt_diy_scenes"):
        scene_dict = vars(selected_device.mqtt_diy_scenes)

    if not scene_dict:
        print("❌ No MQTT DIY scenes found for this device.")
        return

    scene_names = list(scene_dict.keys())

    while True:
        print(f"\n🎬 MQTT DIY Scenes for {selected_device.name}:")
        print("0. 🔁 All Scenes (Loop Thru)")
        for i, var_name in enumerate(scene_names, 1):
            print(f"{i}. {var_name}")

        selected_scene_index = input("\nSelect a scene to send (or enter to 👈 go back): ").strip()
        if selected_scene_index == "":
            print("👋 Done sending scenes.\n")
            break

        if selected_scene_index == "0":
            print(f"\n🔁 Sending ALL scenes for {selected_device.name}...\n")
            for var_name in scene_names:
                selected_scene = scene_dict[var_name]
                print(f"📨 Sending '{var_name}'...")
                set_device_mqtt_diy_scene(selected_device, selected_scene)
                print("✅ Sent. Waiting 3s...\n")
                time.sleep(3)
            print("🎉 Finished sending all scenes!\n")
            continue

        try:
            selected_scene_name = scene_names[int(selected_scene_index) - 1]
            selected_scene = scene_dict[selected_scene_name]
        except (IndexError, ValueError):
            print("❌ Invalid scene selection.")
            continue

        print(f"\n📨 Sending scene '{selected_scene_name}' to {selected_device.name} ({selected_device.id})...")
        set_device_mqtt_diy_scene(selected_device, selected_scene)
        print("✅ Scene sent!")

def refresh_device_ips():
    print("\n📡 Refreshing LAN IP addresses...")

    lan_devices = discover_govee_devices()
    if not lan_devices:
        print("❌ No devices found on LAN.")
        return

    # Build map of device ID → IP
    lan_ip_map = {d["device"]: d["ip"] for d in lan_devices if d.get("device") and d.get("ip")}
    if not lan_ip_map:
        print("❌ No valid IPs found.")
        print("Note: Make sure your Govee devices are powered on and connected to the same network but NOT the MITM Wi-Fi you setup on your machine.")
        return

    print(f"🔍 Updating device_factory.py with IPs for {len(lan_ip_map)} devices...")

    if not os.path.exists(DEVICE_FACTORY_FILE_PATH):
        print("❌ device_factory.py not found.")
        return

    with open(DEVICE_FACTORY_FILE_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    device_line_regex = re.compile(r'^(\w+)\s*=\s*GoveeDevice\("([^"]+)",\s*"([^"]+)",\s*"([^"]+)"(?:,\s*ip="[^"]*")?\)')
    updated_lines = []

    for line in lines:
        match = device_line_regex.match(line)
        if match:
            var_name, device_id, name, sku = match.groups()
            new_ip = lan_ip_map.get(device_id)
            if new_ip:
                updated_line = f'{var_name} = GoveeDevice("{device_id}", "{name}", "{sku}", ip="{new_ip}")\n'
                print(f"🔄 Updated {var_name} with IP {new_ip}")
                updated_lines.append(updated_line)
                continue
        updated_lines.append(line)

    with open(DEVICE_FACTORY_FILE_PATH, "w", encoding="utf-8") as f:
        f.writelines(updated_lines)

    print("✅ IP addresses updated in device_factory.py.")

def refresh_mqtt_diy_scene_factories():
    print("\n🔁 Refreshing MQTT DIY Scene Factory mappings...")

    if not os.path.exists(DEVICE_FACTORY_FILE_PATH):
        print("❌ device_factory.py not found.")
        return

    # Build mapping of device var name → list of mqtt scene var names
    device_to_scenes = {}
    all_scene_vars = vars(mqtt_scene_factory)
    for var_name, scene in all_scene_vars.items():
        if isinstance(scene, GoveeMqttDiyScene):
            device_prefix = var_name.split("_sc_")[0]
            device_to_scenes.setdefault(device_prefix, []).append(var_name)

    if not device_to_scenes:
        print("⚠️  No MQTT scene variables found in device_mqtt_diy_scene_factory.py")
        return

    # Read and parse existing factory lines
    with open(DEVICE_FACTORY_FILE_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    updated_lines = []
    inside_namespace = False
    current_device = None
    namespace_start_idx = None

    for i, line in enumerate(lines):
        # Detect start of mqtt_diy_scenes block
        match = re.match(r'^(\w+)\.mqtt_diy_scenes = SimpleNamespace\(', line)
        if match:
            inside_namespace = True
            current_device = match.group(1)
            namespace_start_idx = i
            continue

        # End of a namespace block
        if inside_namespace and line.strip() == ")":
            inside_namespace = False
            current_device = None
            namespace_start_idx = None
            continue

        # Skip lines inside old mqtt_diy_scenes block
        if inside_namespace:
            continue

        updated_lines.append(line)

        # After writing the device declaration, add the new mqtt_diy_scenes block if available
        device_match = re.match(r'^(\w+)\s*=\s*GoveeDevice\(', line)
        if device_match:
            device_var = device_match.group(1)
            scene_vars = device_to_scenes.get(device_var)
            if scene_vars:
                updated_lines.append(f"{device_var}.mqtt_diy_scenes = SimpleNamespace(\n")
                for sv in sorted(scene_vars):
                    updated_lines.append(f"    {sv}={sv},\n")
                updated_lines.append(")\n\n")
                print(f"✅ Added {len(scene_vars)} scenes to {device_var}.mqtt_diy_scenes")

    with open(DEVICE_FACTORY_FILE_PATH, "w", encoding="utf-8") as f:
        f.writelines(updated_lines)

    print("✅ MQTT DIY scene mappings refreshed in device_factory.py.")

def run_wizard():
    while True:
        print("\n👋 Welcome to the Govee LAN API Plus Tool!\nPlease select from the following options:")
        print("1. ☁️  Sync Devices from Govee Cloud API")
        print("2. 🛜 Refresh Device IP Addresses")
        print("3. 🎬 Capture DIY Scene MQTT Payloads")
        print("4. 🏭 Refresh MQTT DIY Scene Factories")
        print("5. 📡 Send LAN MQTT DIY Scene Command")

        choice = input("\nSelect an option (or enter to quit): ").strip()

        if choice == "1":
            sync_govee_devices(api_key=GOVEE_API_KEY)
        elif choice == "2":
            refresh_device_ips()
        elif choice == "3":
            capture_scene_mqtt(api_key=GOVEE_API_KEY)
        elif choice == "4":
            refresh_mqtt_diy_scene_factories()
        elif choice == "5":
            send_mqtt_scene()
        elif choice == "":
            print("✌️ Goodbye!")
            break
        else:
            print("❌ Invalid option. Please try again.")

def main():
    prompt_for_govee_api_key_if_needed()
    devices = load_devices_from_factory()
    if len(devices) == 0:
        print("\n👋 Welcome to the Govee LAN API Plus Tool!")
        print("\n🚀 Running first time setup in 3..")
        for i in range(2, 0, -1):
            print(f"{i}...")
            time.sleep(1)
        sync_govee_devices(api_key=GOVEE_API_KEY)
        run_wizard()
    else:
        run_wizard()

if __name__ == "__main__":
    main()
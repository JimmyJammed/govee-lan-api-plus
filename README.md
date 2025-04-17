# Govee LAN API Plus

An expansion of the Govee LAN API for automating device fetching, controlling smart devices, and even sending custom DIY Scene commands **over LAN** — with no need for cloud requests after setup.

This toolchain uses both the **Govee Cloud API** and **Frida-based MQTT interception** to capture and reuse custom DIY commands locally.

---

## ❓ Why Do I Need This?

This project was born out of frustration with the limitations of Govee’s official APIs — particularly the inability to trigger **DIY Scenes** using their LAN API. 

As someone who creates **Light & Sound shows** for Halloween and Christmas, keeping the lights synchronized with music and audio dialogue was nearly impossible using the Cloud API due to unpredictable **internet latency and request timing issues**.

This tool allows you to:

- Capture the exact MQTT payloads the Govee app sends when triggering DIY Scenes
- Replay them instantly over your local network programmatically *(I use a Raspberry Pi for my Light & Sound shows)*
- Achieve **perfect timing** for shows, automations, and synced events
- Generate Python code automatically to scale your control across devices

Whether you're running a holiday show, building custom automations, or just want faster device control, this framework gives you **complete LAN-side access** to your Govee ecosystem.

### 🕺 Watch My Govee-Powered Light Show

Check out one of the synced Light & Sound shows this tool helped power with LAN DIY Scene control:
👉 [Stranger Things Halloween 2024 on YouTube 🎥](https://youtu.be/egxioHVotYc?si=oDVQX2V4J-dMQwuN&t=774)

---

## 🛠 Features

- 🔌 **LAN control of Govee smart devices**
- 🎨 Fetch and store custom **DIY scenes**
- 🧠 Frida-based **MQTT payload capture**
- 🛜 Local scene triggering without using the Cloud API
- 🏗 Dynamic **code generation** for all devices and scenes

---

## 📦 Requirements

### ✅ System Requirements

- macOS (Note: You can use other machines but I only tested this on a Macbook)
- Python 3.9+
- Homebrew
- Rooted Android device *(Note: You could potentially use a jailbroken iPhone or other devices, but you will need to swap out all the Frida scripts with whatever your device supports for intercepting MQTT messages)*
- Govee smart device(s) that support LAN Control
- Ethernet internet connection (for hosting Wi-Fi from MacBook)

---

### 🧰 Tools to Install on macOS

Provided here are the basic steps, but if you have any problems just use Google, AI, YouTube, etc for this part of the process as I will not be troubleshooting or assisting these steps.

1. **Install [Homebrew](https://brew.sh/):**
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install Python 3 (if not already installed):**
   ```bash
   brew install python
   ```

3. **Install ADB (Android Debug Bridge):**
   ```bash
   brew install android-platform-tools
   ```

4. **Install Frida CLI and Python bindings:**
   ```bash
   pip3 install frida-tools
   ```

5. **Download the correct `frida-server` binary** for your rooted Android device from:
   👉 https://github.com/frida/frida/releases

   - Place it into your repo’s `bin/` folder
   - Update the `.env` file variable `FRIDA_SERVER_BINARY_PATH` to use the same name as your binary file.

---

## 🔑 Getting a Govee Cloud API Key

1. Follow the steps provided in the official Govee API docs: [https://developer.govee.com/reference/apply-you-govee-api-key](https://developer.govee.com/reference/apply-you-govee-api-key)
4. Add the api key to your `.env` file like so:
   ```env
   GOVEE_API_KEY="your_api_key_here"
   ```

---

## 📡 Setting Up Your Network (MITM)

This project requires routing your Govee device and phone **through your MacBook**, so it can intercept LAN MQTT traffic.
Provided here are the basic steps, but if you have any problems just use Google, AI, YouTube, etc for this part of the process as I will not be troubleshooting or assisting these steps.

### 🛜 Configure MacBook as Wi-Fi Access Point

1. **Connect your Mac to the internet via Ethernet.**
2. **Discconnect from any Wi-Fi Networks**, but keep the actual Wi-Fi ON.
3. **Open System Settings → Sharing → Internet Sharing:**
   - Share your connection **from**: Ethernet (or USB LAN or however you connected your Macbook to the ethernet connection)
   - **To computers using**: Wi-Fi
   - Set up a network name/password of your choice (Keep it simple as you will need to connect your rooted phone and Govee devices to it)
4. **Enable Internet Sharing.**
5. **Connect your rooted Android phone to this new Wi-Fi.**
6. **In the Govee app on your phone:**
   - Set your Govee device’s Wi-Fi to the same network
   - Turn on **LAN Control**
7. Turn off Bluetooth on the phone to force Wi-Fi-only control (Govee App will bypass Wi-Fi commands if it can find the device within range on Bluetooth)

---

## 🤖 Preparing the Android Device (Frida)

Provided here are the basic steps, but if you have any problems just use Google, AI, YouTube, etc for this part of the process as I will not be troubleshooting or assisting these steps.

1. Make sure your phone is **rooted**
2. Enable **USB debugging** in developer settings
3. Connect via USB and authorize the device:
   ```bash
   adb devices
   adb shell
   exit
   ```
4. Test that your Frida server works by running this::
   ```bash
   adb shell "su -c '/data/local/tmp/frida-server &'"
   ```

---

## 🚀 First-Time Setup Instructions

1. Clone the repo:
   ```bash
   git clone https://github.com/yourname/govee-lan-api-plus.git
   cd govee-lan-api-plus
   ```

2. Generate the .env file from the sample one:
   ```bash
   cp .env.example .env
   ```

3. Create and activate a virtual environment (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Run the wizard:
   ```bash
   python3 main.py
   ```

---

### 💡 Sending MQTT DIY Scenes Programmatically

Once you have used ran the wizard and generated your device and scene mappings, you can then send LAN DIY Scene commands using the wizard OR programmatically from your own Python scripts like so:

```python
from factories.device_factory import * # Imports all the generated Device variables found in device_factory.py
from factories.device_mqtt_diy_scene_factory import * # Imports all the generated MQTT DIY Scene variables found in device_mqtt_diy_scene_factory.py
from api.lan.set_device_mqtt_diy_scene import set_device_mqtt_diy_scene # Imports the function used for sending MQTT commands via LAN.

# Send the DIY Scene to the device over LAN
set_device_mqtt_diy_scene(your_govee_device_variable, your_mqtt_diy_scene_variable) # Replace these with the actual generated device and scene variable from the factory files.
```

This allows you to integrate Govee DIY Scene control into your own:
- Automations *(Home Assistant, Raspberry Pi, Arduino, cron jobs, etc)*
- Light & Sound shows
- Scheduled effects
- Interactive control systems

You can access any generated device and scene using the variables listed in `factories/device_factory.py` and `factories/device_mqtt_diy_scene_factory.py`.

---

## ⚙️ .env Configuration

The only values you should really need to change are:

- GOVEE_API_KEY
- FRIDA_SERVER_BINARY_PATH

The rest of them are based on the requirements/specifications provided by Govee, Frida, etc.
However, although these values work for me they may be subject to change based on:

- Govee API/Hardware Changes
- Your network system and configuration
- General changes any of the required libraries, etc

So if you are having trouble I would suggest reviewing these values to ensure they align with current requirements, your network, etc.

```env
# Cloud API
GOVEE_API_KEY="your_api_key_here"

# Frida / Device Interception
FRIDA_SERVER_PORT=27042
FRIDA_SERVER_IP_ADDRESS="127.0.0.1"
FRIDA_LOG_FILE_PATH="logs/frida_govee_mqtt_output.log"
FRIDA_LAUNCH_DELAY=5
FRIDA_SERVER_BINARY_PATH="bin/frida-server"
FRIDA_LOG_MQQT_URI_FILE_PATH="frida_log_mqtt_uri.js"
FRIDA_SERVER_CLIENT_PATH="/data/local/tmp/frida-server"

# LAN Discovery
LAN_IP_ADDRESS_HELPER_MULTICAST_GROUP="239.255.255.250"
LAN_IP_ADDRESS_HELPER_SEND_PORT=4001
LAN_IP_ADDRESS_HELPER_RECEIVE_PORT=4002
LAN_IP_ADDRESS_HELPER_TIMEOUT=3

# Factories
DEVICE_FACTORY_PATH="factories/device_factory.py"
```

---

## 🍹 Buy Me a Drink

If this project saved you hours of frustration or helped light up your holidays 🎄🎃 — feel free to show some appreciation *(all proceeds will go towards more lights and props for my Light & Sound shows!)*:

[![Venmo Badge](https://img.shields.io/badge/Venmo-@JimmyJammed-blue?logo=venmo&logoColor=white&style=for-the-badge)](https://venmo.com/JimmyJammed)

Or scan the QR code below with the Venmo app:

![Venmo QR Code](./assets/venmo_qr_jimmyjammed.png)

---

## 💬 Need Help?

Open an issue or start a discussion in the [GitHub Issues](https://github.com/yourname/govee-lan-api-plus/issues) tab. Contributions welcome!

---

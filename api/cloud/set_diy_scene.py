# api/cloud/set_diy_scene.py

# ==============================================================================
# Govee LAN API Plus – Cloud DIY Scene Setter
# -------------------------------------------
#
# Description:
# This module triggers a DIY Scene on a specified Govee device using
# the Govee Cloud API. Use only if LAN control is unavailable.
#
# Reference: https://developer.govee.com/docs/cloud-api/control-device
#
# Author: Jimmy Hickman
# License: MIT
# ==============================================================================

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import requests
import uuid

from dotenv import load_dotenv
load_dotenv()

from models.govee_device import GoveeDevice

# Cloud API endpoint to control a Govee device
API_ENDPOINT = "https://openapi.api.govee.com/router/api/v1/device/control"

TEST_DEVICE_ID = ""  # Set an example device ID here
TEST_DEVICE_SKU = ""  # Set an example device SKU here
TEST_DIY_SCENE_ID = 123456789  # Set an example DIY scene ID here

def set_diy_scene(api_key: str, device_id: str, device_sku: str, scene_id: int) -> bool:
    """
    Set a DIY Scene on a Govee device using the Cloud API (new capability-based format).
    """
    headers = {
        "Govee-API-Key": api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "requestId": str(uuid.uuid4()),
        "payload": {
            "device": device_id,
            "sku": device_sku,
            "capability": {
                "type": "devices.capabilities.dynamic_scene",
                "instance": "diyScene",
                "value": scene_id
            }
        }
    }

    print("📤 Payload:")
    from pprint import pprint
    pprint(payload)

    try:
        response = requests.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        print(f"✅ Successfully set scene ID {scene_id} on {device_id}")
        return True
    except requests.exceptions.HTTPError as http_err:
        print(f"❌ HTTP error: {http_err}")
        if response is not None:
            print(f"❌ Response: {response.text}")
    except Exception as err:
        print(f"❌ Unexpected error: {err}")
    return False

if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    load_dotenv()
    api_key = os.getenv("GOVEE_API_KEY")

    if not api_key:
        print("❌ Missing GOVEE_API_KEY in environment.")
        exit(1)
        
    set_diy_scene(api_key, TEST_DEVICE_ID, TEST_DEVICE_SKU, TEST_DIY_SCENE_ID)

# api/cloud/get_device_diy_scenes.py

# ==============================================================================
# Govee LAN API Plus – DIY Scene Fetcher
# --------------------------------------
#
# Description:
# This module provides a function to query the Govee Cloud API and retrieve
# a list of DIY scene definitions available for a given device.
#
# Reference: https://developer.govee.com/docs/cloud-api/diy-scenes
#
# Author: Jimmy Hickman
# License: MIT
# ==============================================================================

import uuid
import requests

from typing import List, Dict

# Govee Cloud API endpoint for querying device DIY scenes
API_ENDPOINT = "https://openapi.api.govee.com/router/api/v1/device/diy-scenes"

def get_device_diy_scenes(device_id: str, sku: str, api_key: str) -> List[Dict]:
    """
    Fetch the list of DIY scene options for a given Govee device from the Cloud API.

    Args:
        device_id (str): The Govee device ID (e.g. "22:2C:F0:9F:A3:EA:39:8B")
        sku (str): The device SKU (e.g. "H6001")
        api_key (str): Govee Cloud API key

    Returns:
        List[Dict]: A list of DIY scene dictionaries, or an empty list if none are found
    """

    headers = {
        "Govee-API-Key": api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "requestId": str(uuid.uuid4()),
        "payload": {
            "device": device_id,
            "sku": sku
        }
    }

    try:
        response = requests.post(API_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()
        response_json = response.json()

        # Traverse the response payload to find the DIY scene capability
        capabilities = response_json.get("payload", {}).get("capabilities", [])
        for cap in capabilities:
            if (
                cap.get("type") == "devices.capabilities.dynamic_scene"
                and cap.get("instance") == "diyScene"
            ):
                return cap.get("parameters", {}).get("options", [])

        return []  # No matching capabilities found

    except requests.exceptions.HTTPError as http_err:
        print(f"❌ HTTP error occurred: {http_err}")
        if response is not None:
            print(f"❌ Response: {response.text}")
    except Exception as err:
        print(f"❌ An error occurred: {err}")

    return []
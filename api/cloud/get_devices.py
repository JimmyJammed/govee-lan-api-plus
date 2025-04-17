# api/cloud/get_devices.py

# ==============================================================================
# Govee LAN API Plus – Cloud Device Fetcher
# -----------------------------------------
#
# Description:
# This module retrieves all devices associated with the authenticated user's
# Govee account from the Cloud API. Each device is returned as a GoveeDevice object.
#
# Reference: https://developer.govee.com/docs/cloud-api/user-devices
#
# Author: Jimmy Hickman
# License: MIT
# ==============================================================================

import requests
from typing import Dict

from models.govee_device import GoveeDevice

# Govee Cloud API endpoint to fetch user's device list
API_ENDPOINT = "https://openapi.api.govee.com/router/api/v1/user/devices"

def get_govee_devices(api_key: str) -> Dict[str, GoveeDevice]:
    """
    Fetch all Govee devices associated with the user's account.

    Args:
        api_key (str): Govee Cloud API key.

    Returns:
        Dict[str, GoveeDevice]: A dictionary mapping device IDs to GoveeDevice objects.
    """
    headers = {
        "Govee-API-Key": api_key,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(API_ENDPOINT, headers=headers)
        response.raise_for_status()

        devices_data = response.json().get("data", [])
        devices = {}

        for device_info in devices_data:
            device_id = device_info.get("device")
            device_name = device_info.get("deviceName", "Unknown Device")
            sku = device_info.get("sku")

            if device_id and sku:
                devices[device_id] = GoveeDevice(device_id, device_name, sku)
            else:
                print(f"⚠️ Skipping device with missing ID or SKU: {device_info}")

        return devices

    except requests.exceptions.HTTPError as http_err:
        print(f"❌ HTTP error occurred: {http_err}")
        if response is not None:
            print(f"❌ Response content: {response.text}")
    except Exception as err:
        print(f"❌ An unexpected error occurred: {err}")

    return {}
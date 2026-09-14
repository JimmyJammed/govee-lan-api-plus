# Migration to 1.0

Historical implementation: [32aa676a359a2fb3586128b1887c7c902e30f5f9](https://github.com/JimmyJammed/govee-lan-api-plus/tree/32aa676a359a2fb3586128b1887c7c902e30f5f9). Old api/models/factories imports and generated Python configuration are replaced by govee_lan_api_plus imports and JSON profiles.

Map GoveeDevice to Device(id, sku, ip, name, port). Convert each stored MQTT packet into Scene(name, payload); retain the full msg/device/cmd structure required by your device. Do not execute old factory files as part of importing untrusted profiles.

Use await client.scene instead of set_device_mqtt_diy_scene, and await client.discover instead of discover_govee_devices. Reads now raise errors rather than returning empty data after failures. Requires Python 3.12. CLI simulation is default; --live explicitly selects hardware. No Frida binary is shipped.

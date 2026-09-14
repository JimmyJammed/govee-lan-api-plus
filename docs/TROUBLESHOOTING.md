# Troubleshooting

No devices: enable device LAN control, select the correct interface, and check local-network permission, firewall, VLAN isolation, and multicast routing. Some Govee models do not support LAN control.

Port in use: another process/transport owns UDP 4002. Use one shared transport. Missing response: verify device IP and model support. Cloud 401: check key; 429: wait before retrying. Scene sent but unchanged: captured packets are model/app-specific; reverify the payload.

Capture import error: install the optional extra. A Java runtime error in a hook needs a bridge bundled for the matching Frida version, not changes to the core LAN package.

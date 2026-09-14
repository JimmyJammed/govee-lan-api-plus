# Setup

Follow the README virtual-environment steps. The core uses only Python's standard library. `.[capture]` is optional and installs Frida; it is not needed for ordinary LAN operations.

Enable LAN control in the Govee app for each compatible device. Run `govee --live discover --output devices.json`, then `govee --live --profile devices.json status DEVICE_ID`. Use `--interface YOUR_LOCAL_IPV4` on machines with multiple network interfaces. UDP ports 4001/4002/4003 must be reachable. Commands must put global options before the subcommand.

Cloud discovery: export GOVEE_API_KEY and run `govee --live cloud`. Cloud devices do not automatically supply routable LAN addresses; use LAN discovery for that. The application does not implicitly load .env files.

Install the Light Show Manager 2.0 wheel, then run `python examples/light_show.py` for a complete simulated integration.

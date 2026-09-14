# Testing

Install `.[dev]`, run `python -m pytest`, and build with `python -m build`. Install the wheel into an empty environment and exercise discover/status/control/scene. Unit tests use simulated transports and fake sockets; they do not transmit to devices.

Test real discovery, status, each command, restoration, and scene replay separately on available hardware. Record network, device/firmware, app, and capture versions. A sent UDP packet is not a passing device test.

# API

`Device(id, sku, ip, name="", port=4003)` validates IPv4 address and port. `GoveeClient(transport=None)` uses live UDP unless a transport is supplied. Methods: `discover()`, `status(device)`, `power(device, bool)`, `brightness(device, 0..100)`, `color(device, r, g, b)`, `scene(device, Scene)`, and `restore(device, status)` are asynchronous.

`UDPTransport(timeout=3, interface="0.0.0.0", socket_factory=socket.socket)` serializes queries sharing port 4002. Cancellation drains the bounded blocking socket operation before releasing the port. Separate processes/transports cannot query the same interface simultaneously; bind failures are explicit.

`SimulatedTransport(devices=None)` implements the same interface and retains state for its lifetime. `sent` records submitted packets. Experimental scenes are recorded without pretending to interpret proprietary payloads.

`CloudClient(api_key, timeout=10, opener=urlopen).devices()` returns cloud inventory records. HTTP failures raise CloudError with a status; malformed responses raise ProtocolError; no error is converted into an empty inventory.

`Profile.load(path)` and `save(path)` use version 1 JSON. Devices have unique ids; scenes have unique names. `Scene(name, payload, experimental=True, verified={})` wraps a full LAN packet. `verified` can record model, firmware, app, and tool versions. Saving a profile does not establish hardware compatibility.

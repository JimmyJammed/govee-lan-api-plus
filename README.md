# Govee LAN API Plus

Python 3.12+ · MIT · 1.0.0

Control LAN-enabled lights with an asynchronous Python API, a simulation-first CLI, and portable device/scene profiles. Captured DIY payload replay is experimental and device-specific.

## Run locally

```sh
git clone https://github.com/JimmyJammed/govee-lan-api-plus.git
cd govee-lan-api-plus
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
govee discover
govee status demo-lantern
govee control demo-lantern --brightness 80
govee --profile examples/profile.json scene demo-lantern warm
```

These commands simulate a Lantern without hardware, credentials, or a rooted phone. Each CLI invocation starts fresh simulation state. Use the Python API to simulate a sequence.

## Python API

```python
import asyncio
from govee_lan_api_plus import GoveeClient, SimulatedTransport

async def main():
    client = GoveeClient(SimulatedTransport())
    device = (await client.discover())[0]
    original = await client.status(device)
    try:
        await client.brightness(device, 80)
    finally:
        await client.restore(device, original)

asyncio.run(main())
```

Live operations require `--live`; the Python default transport is live UDP. Successful writes mean **sent**, not confirmed execution. No perfect timing or universal scene support is promised.

[Setup](docs/GETTING_STARTED.md) · [API](docs/API.md) · [Customization](docs/CUSTOMIZATION.md) · [Architecture](docs/ARCHITECTURE.md) · [Migration](docs/MIGRATION.md) · [Capture](docs/CAPTURE.md) · [Compatibility](docs/COMPATIBILITY.md) · [Testing](docs/TESTING.md) · [Validation](docs/VALIDATION.md) · [Troubleshooting](docs/TROUBLESHOOTING.md) · [Contributing](CONTRIBUTING.md)

## License

[MIT](LICENSE). Original author and license notices remain applicable. No account-specific assets are included in the demo.

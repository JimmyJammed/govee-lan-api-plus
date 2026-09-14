# Compatibility

The maintained protocol follows [Govee LAN guidance](https://app-h5.govee.com/user-manual/wlan-guide) and the [cloud inventory API](https://developer.govee.com/reference/get-you-devices).

| Capability | Status |
| --- | --- |
| Discovery, power, brightness, RGB, status | Implemented; fixture-tested |
| Cloud inventory | Implemented; mocked HTTP tests |
| Captured DIY packet replay | Experimental; hardware unverified |
| Frida hook/app compatibility | User-supplied compiled hook; unverified |
| macOS Python | See VALIDATION |
| Linux/Raspberry Pi and Windows | Portable implementation; not physically verified here |

No actual device, firmware, or app version is certified by this release. Add dated evidence before claiming a combination works.

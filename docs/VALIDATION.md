# Validation — 2026-09-14

macOS arm64. Python 3.12.13, 3.13.15, and 3.14.6: 8 pytest cases passed on each interpreter. Tests cover control/restoration, profile round-trip and rejection, 401/429/500 responses, malformed cloud data, discovery deduplication, unavailable-device timeouts, and socket cleanup.

`python -m build --no-isolation` produced a wheel and source archive. The wheel was installed without dependencies in a separate environment. CLI discover/status/control/scene simulation and the Light Show Manager integration ran successfully against installed wheels.

Physical Govee devices, actual multicast, cloud credentials, Frida attachment, Raspberry Pi, and Windows were unavailable. Their behavior is unverified, not recorded as passing. The optional capture runner requires a user-supplied compatible hook; the old hook is not represented as current.

No package registry publication or hosted Actions validation is claimed.

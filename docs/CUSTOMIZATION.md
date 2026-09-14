# Customization

Use examples/profile.json as a schema example. Replace simulated devices with discovery results. Edit ordinary color/brightness scenes or import a captured packet as a Scene.payload. Keep private account topics out of shared examples.

Inject a Transport implementation for other networks or deterministic tests. Snapshot status before a show and restore it in the cleanup hook; restoration supports reported power, brightness, color, and temperature. It cannot restore a proprietary scene identifier not reported by the device.

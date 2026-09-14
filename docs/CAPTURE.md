# Experimental capture

Captured MQTT payload replay is not an official general-purpose Govee scene API. The app's internal classes and payloads may change. No current app/firmware combination has been verified in this release.

Install `.[capture]`. Install a matching Frida server from the official Frida releases on your own configured test device; no binary is bundled. Confirm client/server versions match with `python -c "import frida; print(frida.__version__)"` and the server's version command.

Use `python -m govee_lan_api_plus.capture PROCESS compiled-hook.js private-capture.jsonl` to attach over USB and record messages. Supply a hook compatible with your app and Frida version. Frida 17 Java hooks require the Java bridge to be bundled into the script. The legacy hook remains available at the historical revision linked in MIGRATION; it is not claimed compatible with current apps.

Inspect a captured packet, remove unrelated personal data, and store the complete LAN message under a named scene in a version 1 profile. The runner deliberately does not infer arbitrary payloads or generate Python source. Test one device and record model, firmware, app, and Frida versions before using a scene in a show.

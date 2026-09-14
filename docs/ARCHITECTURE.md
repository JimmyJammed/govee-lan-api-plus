# Architecture

models defines versioned data and errors. client separates high-level commands from UDP and simulated transports. cloud independently uses HTTPS inventory discovery. cli composes these interfaces. capture is optional tooling and does not affect LAN installation.

Discovery binds the listener before sending multicast, validates packets, and deduplicates by device ID. Socket operations are bounded and drained on cancellation. Device commands intentionally do not retry automatically: duplicate scene/relative operations may have side effects.

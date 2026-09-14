"""Portable, versioned device and scene profiles."""
from dataclasses import dataclass, field, asdict
import ipaddress
import json
from pathlib import Path
from typing import Any


class GoveeError(Exception):
    """Base error for callers to handle."""


class ProtocolError(GoveeError):
    pass


class CloudError(GoveeError):
    def __init__(self, status, message):
        self.status = status
        super().__init__(f'Cloud request failed ({status}): {message}')


@dataclass(frozen=True)
class Device:
    id: str
    sku: str
    ip: str
    name: str = ''
    port: int = 4003

    def __post_init__(self):
        if not self.id or not self.sku:
            raise ValueError('Device id and sku are required')
        ipaddress.IPv4Address(self.ip)
        if not 1 <= self.port <= 65535:
            raise ValueError('Invalid device port')


@dataclass(frozen=True)
class Scene:
    name: str
    payload: dict[str, Any]
    experimental: bool = True
    verified: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if not self.name or not isinstance(self.payload.get('msg'), dict):
            raise ValueError('Scene requires a name and msg payload')
        json.dumps(self.payload, allow_nan=False)


@dataclass
class Profile:
    devices: list[Device] = field(default_factory=list)
    scenes: list[Scene] = field(default_factory=list)
    version: int = 1

    @classmethod
    def load(cls, path):
        try:
            data = json.loads(Path(path).read_text())
            if data.get('version') != 1:
                raise ValueError('Unsupported profile version; expected 1')
            devices = [Device(**item) for item in data.get('devices', [])]
            scenes = [Scene(**item) for item in data.get('scenes', [])]
            if len({d.id for d in devices}) != len(devices):
                raise ValueError('Duplicate device ids')
            if len({s.name for s in scenes}) != len(scenes):
                raise ValueError('Duplicate scene names')
            return cls(devices, scenes)
        except (KeyError, TypeError, ValueError, AttributeError) as error:
            raise ProtocolError(f'Invalid profile: {error}') from error

    def save(self, path):
        Path(path).write_text(json.dumps(asdict(self), indent=2) + '\n')

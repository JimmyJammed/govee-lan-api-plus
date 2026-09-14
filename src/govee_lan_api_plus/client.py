"""Bounded UDP operations; discovery listens before sending its multicast scan."""
import asyncio
import json
import socket
import time
from typing import Protocol
from .models import Device, Scene, ProtocolError, GoveeError


class Transport(Protocol):
    async def send(self, device: Device, payload: dict) -> None: ...
    async def status(self, device: Device) -> dict: ...
    async def discover(self) -> list[Device]: ...


def _packet(command, data):
    return {'msg': {'cmd': command, 'data': data}}


class UDPTransport:
    def __init__(self, timeout=3.0, interface='0.0.0.0', socket_factory=socket.socket):
        if not 0 < timeout <= 60:
            raise ValueError('timeout must be between zero and 60 seconds')
        self.timeout, self.interface, self.socket_factory = timeout, interface, socket_factory
        # Govee uses a shared response port. Serialize queries per transport.
        self._query_lock = asyncio.Lock()

    def _send(self, device, payload):
        try:
            data = json.dumps(payload, allow_nan=False).encode()
            if len(data) > 65507:
                raise ProtocolError('Payload exceeds UDP limit')
            with self.socket_factory(socket.AF_INET, socket.SOCK_DGRAM) as sender:
                sender.settimeout(self.timeout)
                sender.sendto(data, (device.ip, device.port))
        except OSError as error:
            raise GoveeError(f'Could not send to {device.ip}: {error}') from error

    async def send(self, device, payload):
        await self._bounded_thread(self._send, device, payload)

    @staticmethod
    async def _bounded_thread(function, *args):
        task = asyncio.create_task(asyncio.to_thread(function, *args))
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            # Drain a bounded socket operation before releasing the response port.
            while not task.done():
                try:
                    await asyncio.shield(task)
                except asyncio.CancelledError:
                    continue
            if not task.cancelled():
                task.exception()
            raise

    def _query(self, device=None):
        replies = {}
        deadline = time.monotonic() + self.timeout
        try:
            with self.socket_factory(socket.AF_INET, socket.SOCK_DGRAM) as receiver:
                receiver.bind((self.interface, 4002))
                if device:
                    self._send(device, _packet('devStatus', {}))
                else:
                    with self.socket_factory(socket.AF_INET, socket.SOCK_DGRAM) as sender:
                        sender.settimeout(self.timeout)
                        sender.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
                        if self.interface != '0.0.0.0':
                            sender.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(self.interface))
                        sender.sendto(json.dumps(_packet('scan', {'account_topic': 'reserve'})).encode(), ('239.255.255.250', 4001))
                while time.monotonic() < deadline:
                    receiver.settimeout(max(.001, deadline - time.monotonic()))
                    try:
                        raw, address = receiver.recvfrom(65535)
                    except socket.timeout:
                        break
                    try:
                        msg = json.loads(raw)['msg']
                        data = msg['data']
                        if device and address[0] == device.ip and msg['cmd'] == 'devStatus' and isinstance(data, dict):
                            return data
                        if not device and msg['cmd'] == 'scan':
                            found = Device(data['device'], data['sku'], address[0], data.get('device_name', ''))
                            replies[found.id] = found
                    except (ValueError, KeyError, TypeError):
                        continue
        except OSError as error:
            raise GoveeError(f'LAN query failed: {error}') from error
        if device:
            raise GoveeError(f'No status response from {device.id} within {self.timeout}s')
        return list(replies.values())

    async def discover(self):
        async with self._query_lock:
            return await self._bounded_thread(self._query)

    async def status(self, device):
        async with self._query_lock:
            return await self._bounded_thread(self._query, device)


class SimulatedTransport:
    def __init__(self, devices=None):
        self.devices = devices if devices is not None else [Device('demo-lantern', 'SIMULATED', '127.0.0.1', 'Lantern')]
        self.states = {d.id: {'onOff': 1, 'brightness': 25, 'color': {'r': 255, 'g': 180, 'b': 80}, 'colorTemInKelvin': 0} for d in self.devices}
        self.sent = []

    async def discover(self):
        return list(self.devices)

    async def status(self, device):
        if device.id not in self.states:
            raise GoveeError('Unknown simulated device')
        return json.loads(json.dumps(self.states[device.id]))

    async def send(self, device, payload):
        state = await self.status(device)
        msg = payload['msg']
        self.sent.append((device.id, payload))
        if msg['cmd'] == 'turn':
            state['onOff'] = msg['data']['value']
        elif msg['cmd'] == 'brightness':
            state['brightness'] = msg['data']['value']
        elif msg['cmd'] == 'colorwc':
            state.update(msg['data'])
        self.states[device.id] = state


class GoveeClient:
    def __init__(self, transport: Transport | None = None):
        self.transport = transport or UDPTransport()

    async def discover(self):
        return await self.transport.discover()

    async def status(self, device):
        return await self.transport.status(device)

    async def power(self, device, on: bool):
        await self.transport.send(device, _packet('turn', {'value': int(on)}))
        # LAN turn uses value; simulator maps it to onOff below.
        return 'sent'

    async def brightness(self, device, value: int):
        if not isinstance(value, int) or not 0 <= value <= 100:
            raise ValueError('Brightness must be an integer from 0 to 100')
        await self.transport.send(device, _packet('brightness', {'value': value}))
        return 'sent'

    async def color(self, device, red: int, green: int, blue: int):
        if not all(isinstance(v, int) and 0 <= v <= 255 for v in (red, green, blue)):
            raise ValueError('RGB channels must be integers from 0 to 255')
        await self.transport.send(device, _packet('colorwc', {'color': {'r': red, 'g': green, 'b': blue}, 'colorTemInKelvin': 0}))
        return 'sent'

    async def restore(self, device, state):
        # Explicit known status fields only; do not replay arbitrary response keys.
        if 'color' in state:
            await self.transport.send(device, _packet('colorwc', {'color': state['color'], 'colorTemInKelvin': state.get('colorTemInKelvin', 0)}))
        if 'brightness' in state:
            await self.brightness(device, state['brightness'])
        if 'onOff' in state:
            await self.power(device, bool(state['onOff']))

    async def scene(self, device, scene: Scene):
        payload = json.loads(json.dumps(scene.payload))
        if 'device' in payload:
            payload['device'] = device.id
        await self.transport.send(device, payload)
        return 'sent'

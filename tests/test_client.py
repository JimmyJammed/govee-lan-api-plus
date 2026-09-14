import asyncio
import io
import json
import socket
from urllib.error import HTTPError
import pytest
from govee_lan_api_plus import *

@pytest.mark.asyncio
async def test_control_restore_and_scene():
    transport = SimulatedTransport()
    client = GoveeClient(transport)
    device = (await client.discover())[0]
    original = await client.status(device)
    assert await client.brightness(device, 90) == 'sent'
    await client.power(device, False)
    await client.color(device, 0, 0, 255)
    assert (await client.status(device))['brightness'] == 90
    await client.restore(device, original)
    assert await client.status(device) == original
    with pytest.raises(ValueError):
        await client.brightness(device, 101)
    with pytest.raises(ValueError):
        await client.color(device, -1, 0, 0)
    await client.scene(device, Scene('x', {'msg': {'cmd': 'ptReal', 'data': {}}}))
    assert transport.sent[-1][1]['msg']['cmd'] == 'ptReal'


def test_profile_roundtrip(tmp_path):
    file = tmp_path/'profile.json'
    profile = Profile([Device('a','test','127.0.0.1')])
    profile.save(file)
    assert Profile.load(file) == profile
    file.write_text('{"version": 0}')
    with pytest.raises(ProtocolError): Profile.load(file)
    file.write_text('{"version": 1,"devices": [{"id":"x"}]}')
    with pytest.raises(ProtocolError): Profile.load(file)


@pytest.mark.asyncio
@pytest.mark.parametrize('status', [401, 429, 500])
async def test_cloud_error(status):
    def opener(request, timeout):
        assert timeout == 10
        raise HTTPError(request.full_url,status,'error',{},None)
    with pytest.raises(CloudError) as error:
        await CloudClient('test', opener=opener).devices()
    assert error.value.status == status


@pytest.mark.asyncio
async def test_cloud_malformed_and_empty():
    with pytest.raises(ProtocolError):
        await CloudClient('test',opener=lambda *a,**k: io.BytesIO(b'invalid')).devices()
    assert await CloudClient('test',opener=lambda *a,**k: io.BytesIO(b'{"data":[]}')).devices() == []


class FakeSocket:
    def __init__(self, packets=()):
        self.packets = iter(packets)
        self.closed = False
        self.sent = []
    def __enter__(self): return self
    def __exit__(self,*_): self.closed = True
    def bind(self, address): self.bound = address
    def setsockopt(self,*_): pass
    def settimeout(self, value): assert value > 0
    def sendto(self, payload, address): self.sent.append((payload,address))
    def recvfrom(self, size):
        try: return next(self.packets)
        except StopIteration: raise socket.timeout


@pytest.mark.asyncio
async def test_discovery_deduplicates_and_closes():
    raw=json.dumps({'msg':{'cmd':'scan','data':{'device':'x','sku':'test'}}}).encode()
    receiver = FakeSocket([(b'invalid',('127.0.0.1',1)),(raw,('127.0.0.1',1)),(raw,('127.0.0.1',1))])
    sender = FakeSocket()
    sockets=iter([receiver,sender])
    devices = await UDPTransport(socket_factory=lambda *_: next(sockets)).discover()
    assert len(devices) == 1
    assert receiver.closed and sender.closed
    assert sender.sent[0][1] == ('239.255.255.250',4001)


@pytest.mark.asyncio
async def test_unavailable_status_closes_socket():
    receiver,sender=FakeSocket(),FakeSocket()
    sockets=iter([receiver,sender])
    with pytest.raises(GoveeError,match='No status response'):
        await UDPTransport(socket_factory=lambda *_: next(sockets)).status(Device('x','t','127.0.0.1'))
    assert receiver.closed and sender.closed

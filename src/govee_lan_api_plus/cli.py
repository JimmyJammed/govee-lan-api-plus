"""Govee CLI. Simulation is default; --live opts into physical devices."""
import argparse
import asyncio
from dataclasses import asdict
import json
import os
from . import GoveeClient, UDPTransport, SimulatedTransport, Profile, CloudClient, GoveeError


async def run(args):
    profile = Profile.load(args.profile) if args.profile else Profile()
    transport = UDPTransport(timeout=args.timeout, interface=args.interface) if args.live else SimulatedTransport(profile.devices or None)
    client = GoveeClient(transport)
    if args.command == 'discover':
        devices = await client.discover()
        if args.output:
            Profile(devices=devices).save(args.output)
        return [asdict(d) for d in devices]
    if args.command == 'cloud':
        if not args.live:
            return [{'device': 'demo-lantern', 'sku': 'SIMULATED', 'deviceName': 'Lantern'}]
        return await CloudClient(os.environ.get('GOVEE_API_KEY'), args.timeout).devices()
    devices = profile.devices or (await client.discover())
    device = next((d for d in devices if d.id == args.device), None)
    if device is None:
        raise ValueError('Unknown device; discover first or supply a profile')
    if args.command == 'status':
        return await client.status(device)
    if args.command == 'scene':
        scene = next((s for s in profile.scenes if s.name == args.name), None)
        if scene is None:
            raise ValueError('Scene not found in profile')
        result = await client.scene(device, scene)
    elif args.power is not None:
        result = await client.power(device, args.power == 'on')
    elif args.brightness is not None:
        result = await client.brightness(device, args.brightness)
    else:
        result = await client.color(device, *args.color)
    return {'device': device.id, 'result': result, 'simulated': not args.live}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--profile')
    parser.add_argument('--timeout', type=float, default=3)
    parser.add_argument('--interface', default='0.0.0.0')
    subs = parser.add_subparsers(dest='command', required=True)
    discover = subs.add_parser('discover')
    discover.add_argument('--output')
    subs.add_parser('cloud')
    status = subs.add_parser('status')
    status.add_argument('device')
    control = subs.add_parser('control')
    control.add_argument('device')
    options = control.add_mutually_exclusive_group(required=True)
    options.add_argument('--power', choices=['on', 'off'])
    options.add_argument('--brightness', type=int)
    options.add_argument('--color', type=int, nargs=3, metavar=('R', 'G', 'B'))
    scene = subs.add_parser('scene')
    scene.add_argument('device')
    scene.add_argument('name')
    args = parser.parse_args()
    try:
        print(json.dumps(asyncio.run(run(args)), indent=2))
    except (GoveeError, ValueError, OSError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()

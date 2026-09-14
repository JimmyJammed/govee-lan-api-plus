"""pip install light-show-manager>=2 (or the release wheel) before running."""
import asyncio
from govee_lan_api_plus import GoveeClient, SimulatedTransport
from lightshow import LightShowManager, Show

async def main():
    client = GoveeClient(SimulatedTransport())
    device = (await client.discover())[0]
    async def before(show, context):
        context['state'] = await client.status(device)
    async def after(show, context):
        if 'state' in context:
            await client.restore(device, context['state'])
    show = Show('lantern', .1)
    show.add_async_event(0, lambda: client.brightness(device, 100))
    async with LightShowManager([show], pre_show=before, post_show=after) as manager:
        await manager.run_show('lantern')
    print(await client.status(device))

if __name__ == '__main__':
    asyncio.run(main())

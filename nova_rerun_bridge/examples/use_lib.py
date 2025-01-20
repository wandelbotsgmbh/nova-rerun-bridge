import asyncio

from nova.core.nova import Nova

from nova_rerun_bridge import NovaRerunBridge


async def test():
    nova = Nova()
    async with NovaRerunBridge(nova) as nova_bridge:
        await nova_bridge.setup_blueprint()
        await nova_bridge.fetch_and_log_collision_scenes()


if __name__ == "__main__":
    asyncio.run(test())

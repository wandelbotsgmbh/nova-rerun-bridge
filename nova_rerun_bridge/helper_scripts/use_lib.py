import asyncio

from nova.core.nova import Nova

from nova_rerun_bridge import NovaRerunBridge


async def test():
    nova = Nova()
    nova_bridge = NovaRerunBridge(nova)
    await nova_bridge.setup_blueprint()


if __name__ == "__main__":
    asyncio.run(test())

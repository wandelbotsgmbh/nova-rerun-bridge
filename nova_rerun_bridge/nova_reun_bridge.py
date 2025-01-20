from typing import Dict

import rerun as rr
from nova.api import models
from nova.core.nova import Nova

from nova_rerun_bridge.blueprint import send_blueprint
from nova_rerun_bridge.collision_scene import log_collision_scenes


class NovaRerunBridge:
    """Bridge between Nova and Rerun for visualization.

    This class provides functionality to visualize Nova data in Rerun.
    It handles trajectoy, collision scenes, blueprints and proper cleanup of resources.

    Example:
        ```python
        from nova.core.nova import Nova
        from nova_rerun_bridge import NovaRerunBridge

        async def main():
            nova = Nova()
            async with NovaRerunBridge(nova) as bridge:
                await bridge.setup_blueprint()
                await bridge.log_collision_scenes()

        ```

    Args:
        nova (Nova): Instance of Nova client
        spawn (bool, optional): Whether to spawn Rerun viewer. Defaults to True.
    """

    def __init__(self, nova: Nova, spawn: bool = True) -> None:
        self.nova = nova
        if spawn:
            rr.init(application_id="nova", recording_id="nova_live", spawn=True)

    async def setup_blueprint(self) -> None:
        """Configure and send blueprint configuration to Rerun.

        Fetches motion groups from Nova and configures visualization layout.
        """
        motion_groups = await self.nova._api_client.motion_group_api.list_motion_groups("cell")
        motion_group_list = [
            active_motion_group.motion_group for active_motion_group in motion_groups.instances
        ]
        send_blueprint(motion_group_list)

    async def fetch_and_log_collision_scenes(self) -> Dict[str, models.CollisionScene]:
        """Fetch and log all collision scenes from Nova to Rerun."""
        collision_scenes = (
            await self.nova._api_client.store_collision_scenes_api.list_stored_collision_scenes(
                cell=self.nova.cell()._cell_id
            )
        )
        log_collision_scenes(collision_scenes)
        return collision_scenes

    async def fetch_and_log_collision_scene(
        self, scene_id: str
    ) -> Dict[str, models.CollisionScene]:
        """Log a specific collision scene by its ID.

        Args:
            scene_id (str): The ID of the collision scene to log

        Raises:
            ValueError: If scene_id is not found in stored collision scenes
        """
        collision_scenes = (
            await self.nova._api_client.store_collision_scenes_api.list_stored_collision_scenes(
                cell=self.nova.cell()._cell_id
            )
        )

        if scene_id not in collision_scenes:
            raise ValueError(f"Collision scene with ID {scene_id} not found")

        log_collision_scenes({scene_id: collision_scenes[scene_id]})
        return {scene_id: collision_scenes[scene_id]}

    def log_collision_scene(self, collision_scenes: Dict[str, models.CollisionScene]) -> None:
        log_collision_scenes(collision_scenes=collision_scenes)

    async def __aenter__(self) -> "NovaRerunBridge":
        """Context manager entry point.

        Returns:
            NovaRerunBridge: Self reference for context manager usage.
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit point, ensures cleanup."""
        await self.cleanup()

    async def cleanup(self) -> None:
        """Cleanup resources and close Nova API client connection."""
        if hasattr(self.nova, "_api_client"):
            await self.nova._api_client.close()

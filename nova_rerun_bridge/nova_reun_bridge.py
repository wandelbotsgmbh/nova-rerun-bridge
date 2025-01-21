from datetime import datetime
from typing import Dict

import rerun as rr
from loguru import logger
from nova import MotionGroup
from nova.api import models
from nova.core.nova import Nova

from nova_rerun_bridge.blueprint import send_blueprint
from nova_rerun_bridge.collision_scene import log_collision_scenes
from nova_rerun_bridge.consts import RECORDING_INTERVAL
from nova_rerun_bridge.trajectory import TimingMode, log_motion


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
            recording_id = f"nova_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            rr.init(application_id="nova", recording_id=recording_id, spawn=True)
        logger.add(sink=rr.LoggingHandler("logs/handler"))

    async def setup_blueprint(self) -> None:
        """Configure and send blueprint configuration to Rerun.

        Fetches motion groups from Nova and configures visualization layout.
        """
        cell = self.nova.cell()

        controllers = await cell.controllers()
        motion_groups = []

        if not controllers:
            logger.warning("No controllers found")
            return

        for controller in controllers:
            async with controller[0] as motion_group:
                motion_groups.append(motion_group.motion_group_id)

        send_blueprint(motion_groups)

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

    async def log_motion(
        self, motion_id: str, timing_mode=TimingMode.CONTINUE, time_offset: float = 0
    ) -> None:
        # Fetch motion details from api
        motion = await self.nova._api_client.motion_api.get_planned_motion(
            self.nova.cell()._cell_id, motion_id
        )
        optimizer_config = (
            await self.nova._api_client.motion_group_infos_api.get_optimizer_configuration(
                self.nova.cell()._cell_id, motion.motion_group
            )
        )
        trajectory = await self.nova._api_client.motion_api.get_motion_trajectory(
            self.nova.cell()._cell_id, motion_id, int(RECORDING_INTERVAL * 1000)
        )

        motion_groups = await self.nova._api_client.motion_group_api.list_motion_groups(
            self.nova.cell()._cell_id
        )
        motion_motion_group = next(
            (mg for mg in motion_groups.instances if mg.motion_group == motion.motion_group), None
        )

        collision_scenes = (
            await self.nova._api_client.store_collision_scenes_api.list_stored_collision_scenes(
                cell=self.nova.cell()._cell_id
            )
        )

        log_motion(
            motion_id=motion_id,
            model_from_controller=motion_motion_group.model_from_controller,
            motion_group=motion.motion_group,
            optimizer_config=optimizer_config,
            trajectory=trajectory.trajectory,
            collision_scenes=collision_scenes,
            time_offset=time_offset,
            timing_mode=timing_mode,
        )

    async def log_trajectory(
        self,
        joint_trajectory: models.JointTrajectory,
        tcp: str,
        motion_group: MotionGroup,
        timing_mode=TimingMode.CONTINUE,
        time_offset: float = 0,
    ) -> None:
        load_plan_response = await motion_group._load_planned_motion(joint_trajectory, tcp)
        await self.log_motion(
            load_plan_response.motion, timing_mode=timing_mode, time_offset=time_offset
        )

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

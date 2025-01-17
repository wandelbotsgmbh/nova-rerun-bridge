import rerun as rr
from nova.core.nova import Nova

from nova_rerun_bridge.blueprint import send_blueprint
from nova_rerun_bridge.collision_scene import log_collision_scenes


class NovaRerunBridge:
    def __init__(self, nova: Nova, spawn: bool = True):
        self.nova = nova
        if spawn:
            rr.init(application_id="nova", recording_id="nova_live", spawn=True)

    async def setup_blueprint(self):
        # Configure logging blueprints only if motion_group_list has changed
        motion_groups = await self.nova._api_client.motion_group_api.list_motion_groups("cell")
        motion_group_list = [
            active_motion_group.motion_group for active_motion_group in motion_groups.instances
        ]
        send_blueprint(motion_group_list)

    async def log_collision_scenes(self):
        # Fetch collision scenes and log them
        collision_scenes = (
            await self.nova._api_client.store_collision_scenes_api.list_stored_collision_scenes(
                cell=self.nova.cell()._cell_id
            )
        )
        log_collision_scenes(collision_scenes)

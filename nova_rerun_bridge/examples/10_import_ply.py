import asyncio

import numpy as np
import rerun as rr
import trimesh
from nova import MotionSettings
from nova.actions import jnt, ptp
from nova.core.nova import Nova
from nova.types import Pose

from nova_rerun_bridge import NovaRerunBridge
from nova_rerun_bridge.consts import TIME_INTERVAL_NAME


async def test():
    async with Nova() as nova, NovaRerunBridge(nova) as bridge:
        await bridge.setup_blueprint()

        # Load PLY file
        mesh = trimesh.load("example_data/bin_everything_05.ply")

        # Extract vertex positions and colors
        positions = np.array(mesh.vertices)

        # Create rotation matrix for 180 degrees around X axis
        rotation = np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1]])

        # Apply rotation to positions
        positions = positions @ rotation

        # Apply translation [x, y, z]
        translation = np.array([0, -500, 1200])
        positions = positions + translation

        # If colors exist in the PLY, use them, otherwise use default color
        if hasattr(mesh.visual, "vertex_colors"):
            colors = mesh.visual.vertex_colors[:, :3]  # RGB only, drop alpha
        else:
            colors = np.ones_like(positions) * 128  # Default gray color

        rr.set_time_seconds(TIME_INTERVAL_NAME, 0)
        # Log points to rerun
        rr.log("motion/pointcloud", rr.Points3D(positions, colors=colors))

        # Find green points (high G, low R/B values)
        green_mask = (colors[:, 1] > 100) & (colors[:, 0] < 100) & (colors[:, 2] < 100)
        green_points = positions[green_mask]

        if len(green_points) == 0:
            print("No green points found!")
            return

        # Select first green point
        target_point = green_points[0]

        cell = nova.cell()
        controllers = await cell.controllers()
        controller = controllers[0]

        # Connect to the controller and activate motion groups
        async with controller[0] as motion_group:
            home_joints = await motion_group.joints()
            tcp_names = await motion_group.tcp_names()
            tcp = tcp_names[0]

            actions = [
                jnt(home_joints),
                ptp(Pose((target_point[0], target_point[1], target_point[2], np.pi, 0, 0))),
                jnt(home_joints),
            ]

            # you can update the settings of the action
            for action in actions:
                action.settings = MotionSettings(tcp_velocity_limit=200)

            joint_trajectory = await motion_group.plan(actions, tcp)

            await bridge.log_actions(actions)
            await bridge.log_trajectory(joint_trajectory, tcp, motion_group)
            await motion_group.execute(joint_trajectory, tcp, actions=actions)

        await nova.close()


if __name__ == "__main__":
    asyncio.run(test())

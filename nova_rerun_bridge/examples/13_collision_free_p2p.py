import asyncio

import numpy as np
from nova import MotionSettings
from nova.actions import Linear, ptp
from nova.api import models
from nova.core.exceptions import PlanTrajectoryFailed
from nova.core.nova import Nova
from nova.types import Pose
from wandelbots_api_client.models import PlanCollisionFreePTPRequest

from nova_rerun_bridge import NovaRerunBridge


async def build_collision_world(
    nova: Nova, cell_name: str, robot_setup: models.OptimizerSetup
) -> str:
    collision_api = nova._api_client.store_collision_components_api
    scene_api = nova._api_client.store_collision_scenes_api

    # define static colliders, e.g. workpiece
    random_vertices = [1000, 1000, 0] + 1000 * np.random.random((1000, 3))
    collider = models.Collider(
        shape=models.ColliderShape(
            models.ConvexHull2(vertices=random_vertices.tolist(), shape_type="convex_hull")
        )
    )
    await collision_api.store_collider(cell=cell_name, collider="workpiece", collider2=collider)

    # define TCP collider geometry
    tool_collider = models.Collider(
        shape=models.ColliderShape(
            models.Box2(size_x=100, size_y=100, size_z=100, shape_type="box", box_type="FULL")
        )
    )
    await collision_api.store_collision_tool(
        cell=cell_name, tool="tool_box", request_body={"tool_collider": tool_collider}
    )

    # define robot link geometries
    robot_link_colliders = await collision_api.get_default_link_chain(
        cell=cell_name, motion_group_model=robot_setup.motion_group_type
    )
    await collision_api.store_collision_link_chain(
        cell=cell_name, link_chain="robot_links", collider=robot_link_colliders
    )

    # assemble scene
    scene = models.CollisionScene(
        colliders={"workpiece": collider},
        motion_groups={
            "motion_group": models.CollisionMotionGroup(
                tool={"tool_geometry": tool_collider}, link_chain=robot_link_colliders
            )
        },
    )
    scene_id = "collision_scene"
    await scene_api.store_collision_scene(
        cell_name, scene_id, models.CollisionSceneAssembly(scene=scene)
    )
    return scene_id


async def test():
    async with Nova() as nova, NovaRerunBridge(nova) as bridge:
        await bridge.setup_blueprint()

        cell = nova.cell()
        controller = await cell.ensure_virtual_robot_controller(
            "ur5",
            models.VirtualControllerTypes.UNIVERSALROBOTS_MINUS_UR5E,
            models.Manufacturer.UNIVERSALROBOTS,
        )

        robot_setup = await nova._api_client.motion_group_infos_api.get_optimizer_configuration(
            "cell", controller[0].motion_group_id, "Flange"
        )

        await build_collision_world(nova, "cell", robot_setup)

        await bridge.log_collision_scenes()

        # Connect to the controller and activate motion groups
        async with controller[0] as motion_group:
            tcp = "Flange"

            home = await motion_group.tcp_pose(tcp)
            home_joints = await motion_group.joints()

            actions = [
                action
                for _ in range(3)
                for action in [
                    ptp(home),
                    Linear(target=Pose((50, 20, 30, 0, 0, 0)) @ home),
                    Linear(target=Pose((100, 20, 30, 0, 0, 0)) @ home),
                    Linear(target=Pose((50, 20, 30, 0, 0, 0)) @ home),
                    ptp(home),
                ]
            ]

            for action in actions:
                action.settings = MotionSettings(tcp_velocity_limit=200)

            # Plan collision free PTP
            """
            robot_setup: OptimizerSetup = Field(description="The robot setup as returned from [getOptimizerConfiguration](getOptimizerConfiguration) endpoint.")
            start_joint_position: List[Union[StrictFloat, StrictInt]]
            target: PlanCollisionFreePTPRequestTarget
            static_colliders: Optional[Dict[str, Collider]] = Field(default=None, description="A collection of identifiable colliders.")
            collision_motion_group: Optional[CollisionMotionGroup] = Field(default=None, description="Collision motion group considered during the motion planning. ")
            """
            await nova._api_client.motion_api.plan_collision_free_ptp(
                cell="cell",
                plan_collision_free_ptp_request=PlanCollisionFreePTPRequest(
                    robot_setup=robot_setup,
                    start_joint_position=[1.169, -1.57, 1.36, 1.029, 1.289, 1.279],
                    target=models.PlanCollisionFreePTPRequestTarget([400, 0, 100, 0, 0, 0]),
                ),
            )

            try:
                joint_trajectory = await motion_group.plan(actions, tcp)
                await bridge.log_actions(actions)
                await bridge.log_trajectory(joint_trajectory, tcp, motion_group)
                await motion_group.execute(joint_trajectory, tcp, actions=actions)
            except PlanTrajectoryFailed as e:
                await bridge.log_actions(actions)
                await bridge.log_trajectory(e.error.joint_trajectory, tcp, motion_group)
                await bridge.log_error_feedback(e.error.error_feedback)
                return

        # await cell.delete_robot_controller(controller.name)


if __name__ == "__main__":
    asyncio.run(test())

import asyncio

from nova import Controller, Nova
from nova.actions import MotionSettings, Pose, jnt, ptp
from numpy import pi

from nova_rerun_bridge import NovaRerunBridge
from nova_rerun_bridge.trajectory import TimingMode

"""
Example: Show an external axis with a robot moving in a cell.

Prerequisites:
- A cell with a robot with an positioner (external) axis: setup a yaskawa-ar1440 and import the yaskawa-ar1440-with-external-axis.yaml in the settings app
- Set mounting of 16@yaskawa to yaskawa-ar1440-16-mounting
"""


async def move_robot(controller: Controller, bridge: NovaRerunBridge):
    async with controller[0] as motion_group:
        tcp_names = await motion_group.tcp_names()
        tcp = tcp_names[0]
        home_joints = await motion_group.joints()

        current_pose = await motion_group.tcp_pose(tcp)

        actions = [
            jnt(home_joints),
            ptp(current_pose @ Pose((0, 0, -100, 0, -pi / 2, 0))),
            ptp(current_pose @ Pose((-500, 0, 0, 0, -pi / 2, 0))),
            jnt(home_joints),
        ]

        for action in actions:
            action.settings = MotionSettings(tcp_velocity_limit=200)

        trajectory = await motion_group.plan(actions, tcp)
        await bridge.log_trajectory(trajectory, tcp, motion_group, timing_mode=TimingMode.SYNC)


async def move_positioner(controller: Controller, bridge: NovaRerunBridge):
    async with controller[16] as motion_group:
        actions = [jnt([0, 0]), jnt([pi / 4, pi / 4]), jnt([-pi / 4, -pi / 4]), jnt([0, 0])]

        trajectory = await motion_group.plan(actions, "")
        await bridge.log_trajectory(trajectory, "", motion_group, timing_mode=TimingMode.SYNC)


async def main():
    nova = Nova()
    bridge = NovaRerunBridge(nova)
    await bridge.setup_blueprint()
    cell = nova.cell()
    yaskawa = await cell.controller("yaskawa")
    await asyncio.gather(
        move_robot(yaskawa, bridge=bridge), move_positioner(yaskawa, bridge=bridge)
    )
    await nova.close()
    await bridge.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

import asyncio

from nova import Controller, Nova
from nova.actions import jnt, ptp
from numpy import pi

from nova_rerun_bridge import NovaRerunBridge
from nova_rerun_bridge.trajectory import TimingMode

"""
Example: Show an external axis with a robot moving in a cell.

Prerequisites:
- A cell with a robot with an external axis: setup a yaskawa-ar1440 and import the yaskawa-ar1440-with-external-axis.yaml in the settings app
"""


async def move_robot(controller: Controller, bridge: NovaRerunBridge):
    async with controller[0] as motion_group:
        home_joints = await motion_group.joints()
        tcp_names = await motion_group.tcp_names()
        tcp = tcp_names[0]

        current_pose = await motion_group.tcp_pose(tcp)
        target_pose = current_pose @ (100, 0, 0, 0, 0, 0)
        actions = [jnt(home_joints), ptp(target_pose), jnt(home_joints)]

        trajectory = await motion_group.plan(actions, tcp)
        await bridge.log_trajectory(trajectory, tcp, motion_group, timing_mode=TimingMode.SYNC)


async def move_axis(controller: Controller, bridge: NovaRerunBridge):
    async with controller[16] as motion_group:
        actions = [jnt([0, 0]), jnt([pi / 4, pi]), jnt([0, 0])]

        trajectory = await motion_group.plan(actions, "")
        await bridge.log_trajectory(trajectory, "", motion_group, timing_mode=TimingMode.SYNC)


async def main():
    nova = Nova()
    bridge = NovaRerunBridge(nova)
    await bridge.setup_blueprint()
    cell = nova.cell()
    yaskawa = await cell.controller("yaskawa")
    await asyncio.gather(move_robot(yaskawa, bridge=bridge), move_axis(yaskawa, bridge=bridge))
    await nova.close()
    await bridge.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

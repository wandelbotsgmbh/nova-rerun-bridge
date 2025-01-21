import asyncio

from nova import Controller, Nova
from nova.actions import jnt, ptp

from nova_rerun_bridge import NovaRerunBridge
from nova_rerun_bridge.trajectory import TimingMode

"""
Example: Move multiple robots simultaneously.

Prerequisites:
- A cell with two robots: one named "ur" and another named "kuka".
"""


async def move_robot(controller: Controller, nova_bridge: NovaRerunBridge):
    async with controller[0] as motion_group:
        home_joints = await motion_group.joints()
        tcp_names = await motion_group.tcp_names()
        tcp = tcp_names[0]

        current_pose = await motion_group.tcp_pose(tcp)
        target_pose = current_pose @ (100, 0, 0, 0, 0, 0)
        actions = [jnt(home_joints), ptp(target_pose), jnt(home_joints)]

        trajectory = await motion_group.plan(actions, tcp)
        await nova_bridge.log_trajectory(trajectory, tcp, motion_group, timing_mode=TimingMode.SYNC)

        await motion_group.plan_and_execute(actions, tcp)


async def main():
    nova = Nova()
    nova_bridge = NovaRerunBridge(nova)
    await nova_bridge.setup_blueprint()
    cell = nova.cell()
    ur = await cell.controller("ur")
    kuka = await cell.controller("kuka")
    await asyncio.gather(
        move_robot(ur, nova_bridge=nova_bridge), move_robot(kuka, nova_bridge=nova_bridge)
    )
    await nova.close()
    await nova_bridge.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

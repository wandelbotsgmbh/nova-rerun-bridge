import asyncio
from typing import Dict, List

import rerun as rr
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from nova import Nova
from nova.api import models

from nova_rerun_bridge.collision_scene import extract_link_chain_and_tcp
from nova_rerun_bridge.consts import RECORDING_INTERVAL, SCHEDULE_INTERVAL, TIME_INTERVAL_NAME
from nova_rerun_bridge.dh_robot import DHRobot
from nova_rerun_bridge.motion_storage import load_processed_motions, save_processed_motion
from nova_rerun_bridge.nova_reun_bridge import NovaRerunBridge
from nova_rerun_bridge.robot_visualizer import RobotVisualizer
from nova_rerun_bridge.trajectory import log_trajectory

# Global run flags
job_running = False
first_run = True
previous_motion_group_list = []


async def fetch_and_process_motion(
    motion_id: str,
    model_from_controller: str,
    motion_group: str,
    optimizer_config: models.OptimizerSetup,
    trajectory: List[models.TrajectorySample],
    collision_scenes: Dict[str, models.CollisionScene],
):
    """
    Fetch and process a single motion if not processed already.
    """

    # Initialize DHRobot and Visualizer
    robot = DHRobot(optimizer_config.dh_parameters, optimizer_config.mounting)

    collision_link_chain, collision_tcp = extract_link_chain_and_tcp(collision_scenes)

    visualizer = RobotVisualizer(
        robot=robot,
        robot_model_geometries=optimizer_config.safety_setup.robot_model_geometries,
        tcp_geometries=optimizer_config.safety_setup.tcp_geometries,
        static_transform=False,
        base_entity_path=f"motion/{motion_group}",
        glb_path=f"models/{model_from_controller}.glb",
        collision_link_chain=collision_link_chain,
        collision_tcp=collision_tcp,
    )

    # Calculate time offset
    processed_motions = load_processed_motions()
    time_offset = sum(m[1] for m in processed_motions)
    trajectory_time = trajectory[-1].time
    print(f"Time offset: {time_offset}", flush=True)

    rr.set_time_seconds(TIME_INTERVAL_NAME, time_offset)

    # Process trajectory points
    log_trajectory(
        motion_id=motion_id,
        robot=robot,
        visualizer=visualizer,
        trajectory=trajectory,
        optimizer_config=optimizer_config,
        timer_offset=time_offset,
    )

    # Save the processed motion ID and trajectory time
    save_processed_motion(motion_id, trajectory_time)


async def process_motions():
    """
    Fetch and process all unprocessed motions.
    """
    global job_running
    global first_run
    global previous_motion_group_list

    nova = Nova()
    nova_bridge = NovaRerunBridge(nova, spawn=first_run)

    motion_group_infos_api = nova._api_client.motion_group_infos_api
    motion_api = nova._api_client.motion_api
    motion_group_api = nova._api_client.motion_group_api

    try:
        motions = await motion_api.list_motions("cell")
        if motions:
            if first_run:
                # Mark all existing motions as processed with 0 time
                # so they won't get re-logged.
                for mid in motions.motions:
                    save_processed_motion(mid, 0)
                first_run = False

            processed_motions = load_processed_motions()
            processed_motion_ids = {m[0] for m in processed_motions}

            time_offset = sum(m[1] for m in processed_motions)
            rr.set_time_seconds(TIME_INTERVAL_NAME, time_offset)

            # Filter out already processed motions
            new_motions = [
                motion_id for motion_id in motions.motions if motion_id not in processed_motion_ids
            ]

            for motion_id in new_motions:
                print(f"Processing motion {motion_id}.", flush=True)
                collision_scenes = await nova_bridge.fetch_and_log_collision_scenes()

                # Fetch motion details
                motion = await motion_api.get_planned_motion("cell", motion_id)
                optimizer_config = await motion_group_infos_api.get_optimizer_configuration(
                    "cell", motion.motion_group
                )
                trajectory = await motion_api.get_motion_trajectory(
                    "cell", motion_id, int(RECORDING_INTERVAL * 1000)
                )

                # Configure logging blueprints only if motion_group_list has changed
                motion_groups = await motion_group_api.list_motion_groups("cell")
                motion_group_list = [
                    active_motion_group.motion_group
                    for active_motion_group in motion_groups.instances
                ]
                if motion_group_list != previous_motion_group_list:
                    await nova_bridge.setup_blueprint()
                    previous_motion_group_list = motion_group_list

                if motion_id in processed_motion_ids:
                    continue

                motion_motion_group = next(
                    (
                        mg
                        for mg in motion_groups.instances
                        if mg.motion_group == motion.motion_group
                    ),
                    None,
                )

                await fetch_and_process_motion(
                    motion_id=motion_id,
                    model_from_controller=motion_motion_group.model_from_controller,
                    motion_group=motion.motion_group,
                    optimizer_config=optimizer_config,
                    trajectory=trajectory.trajectory,
                    collision_scenes=collision_scenes,
                )

    except Exception as e:
        print(f"Error during job execution: {e}", flush=True)
    finally:
        job_running = False
        await nova._api_client.close()


async def main():
    """Main entry point for the application."""
    # Setup scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        process_motions,
        trigger=IntervalTrigger(seconds=SCHEDULE_INTERVAL),
        id="process_motions_job",
        name=f"Process motions every {SCHEDULE_INTERVAL} seconds",
        replace_existing=True,
    )
    scheduler.start()

    try:
        while True:
            await asyncio.sleep(3600)  # Keep the loop running
    except (KeyboardInterrupt, SystemExit):
        print("Shutting down gracefully.")
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    asyncio.run(main())

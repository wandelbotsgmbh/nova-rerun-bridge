import asyncio
from typing import Any, Dict, List, Tuple

import numpy as np
import rerun as rr
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from nova import Nova
from nova.api import models
from scipy.spatial.transform import Rotation

from nova_rerun_bridge.consts import RECORDING_INTERVAL, SCHEDULE_INTERVAL, TIME_INTERVAL_NAME
from nova_rerun_bridge.dh_robot import DHRobot
from nova_rerun_bridge.motion_storage import load_processed_motions, save_processed_motion
from nova_rerun_bridge.nova_reun_bridge import NovaRerunBridge
from nova_rerun_bridge.robot_visualizer import RobotVisualizer

# Global run flags
job_running = False
first_run = True
previous_motion_group_list = []


def log_joint_data(
    trajectory: List[models.TrajectorySample], times_column, optimizer_config: models.OptimizerSetup
) -> None:
    """
    Log joint-related data (position, velocity, acceleration, torques) from a trajectory as columns.
    """
    # Initialize lists for each joint and each data type (assuming 6 joints)
    num_joints = 6
    joint_data = {
        "velocity": [[] for _ in range(num_joints)],
        "acceleration": [[] for _ in range(num_joints)],
        "position": [[] for _ in range(num_joints)],
        "torque": [[] for _ in range(num_joints)],
        "velocity_lower_limit": [[] for _ in range(num_joints)],
        "velocity_upper_limit": [[] for _ in range(num_joints)],
        "acceleration_lower_limit": [[] for _ in range(num_joints)],
        "acceleration_upper_limit": [[] for _ in range(num_joints)],
        "position_lower_limit": [[] for _ in range(num_joints)],
        "position_upper_limit": [[] for _ in range(num_joints)],
        "torque_limit": [[] for _ in range(num_joints)],
    }

    # Collect data from the trajectory
    for point in trajectory:
        for i in range(num_joints):
            joint_data["velocity"][i].append(point.joint_velocity.joints[i])
            joint_data["acceleration"][i].append(point.joint_acceleration.joints[i])
            joint_data["position"][i].append(point.joint_position.joints[i])
            if point.joint_torques and len(point.joint_torques.joints) > i:
                joint_data["torque"][i].append(point.joint_torques.joints[i])

            # Collect joint limits
            joint_data["velocity_lower_limit"][i].append(
                -optimizer_config.safety_setup.global_limits.joint_velocity_limits[i]
            )
            joint_data["velocity_upper_limit"][i].append(
                optimizer_config.safety_setup.global_limits.joint_velocity_limits[i]
            )
            joint_data["acceleration_lower_limit"][i].append(
                -optimizer_config.safety_setup.global_limits.joint_acceleration_limits[i]
            )
            joint_data["acceleration_upper_limit"][i].append(
                optimizer_config.safety_setup.global_limits.joint_acceleration_limits[i]
            )
            joint_data["position_lower_limit"][i].append(
                optimizer_config.safety_setup.global_limits.joint_position_limits[i].lower_limit
            )
            joint_data["position_upper_limit"][i].append(
                optimizer_config.safety_setup.global_limits.joint_position_limits[i].upper_limit
            )
            if point.joint_torques and len(point.joint_torques.joints) > i:
                joint_data["torque_limit"][i].append(
                    optimizer_config.safety_setup.global_limits.joint_torque_limits[i]
                )

    # Send columns if data is not empty
    for data_type, data in joint_data.items():
        for i in range(num_joints):
            if data[i]:
                rr.send_columns(
                    f"motion/joint_{data_type}_{i + 1}",
                    times=[times_column],
                    components=[rr.components.ScalarBatch(data[i])],
                )


def log_tcp_pose(trajectory: List[models.TrajectorySample], times_column):
    """
    Log TCP pose (position + orientation) data.
    """
    tcp_positions = []
    tcp_rotations = []

    # Collect data from the trajectory
    for point in trajectory:
        # Collect TCP position
        tcp_positions.append(
            [point.tcp_pose.position.x, point.tcp_pose.position.y, point.tcp_pose.position.z]
        )

        # Convert and collect TCP orientation as axis-angle
        rotation_vector = [
            point.tcp_pose.orientation.x,
            point.tcp_pose.orientation.y,
            point.tcp_pose.orientation.z,
        ]
        rotation = Rotation.from_rotvec(rotation_vector)
        angle = rotation.magnitude()
        axis_angle = rotation.as_rotvec() / angle if angle != 0 else [0, 0, 0]
        tcp_rotations.append(rr.RotationAxisAngle(axis=axis_angle, angle=angle))

    rr.send_columns(
        "motion/tcp_position",
        times=[times_column],
        components=[
            rr.Transform3D.indicator(),
            rr.components.Translation3DBatch(tcp_positions),
            rr.components.RotationAxisAngleBatch(tcp_rotations),
        ],
    )


def log_scalar_values(
    trajectory: List[models.TrajectorySample], times_column, optimizer_config: models.OptimizerSetup
):
    """
    Log scalar values such as TCP velocity, acceleration, orientation velocity/acceleration, time, and location.
    """
    scalar_data = {
        "tcp_velocity": [],
        "tcp_acceleration": [],
        "tcp_orientation_velocity": [],
        "tcp_orientation_acceleration": [],
        "time": [],
        "location_on_trajectory": [],
        "tcp_velocity_limit": [],
        "tcp_orientation_velocity_lower_limit": [],
        "tcp_orientation_velocity_upper_limit": [],
        "tcp_acceleration_lower_limit": [],
        "tcp_acceleration_upper_limit": [],
        "tcp_orientation_acceleration_lower_limit": [],
        "tcp_orientation_acceleration_upper_limit": [],
    }

    # Collect data from the trajectory
    for point in trajectory:
        if point.tcp_velocity is not None:
            scalar_data["tcp_velocity"].append(point.tcp_velocity)
        if point.tcp_acceleration is not None:
            scalar_data["tcp_acceleration"].append(point.tcp_acceleration)
        if point.tcp_orientation_velocity is not None:
            scalar_data["tcp_orientation_velocity"].append(point.tcp_orientation_velocity)
        if point.tcp_orientation_acceleration is not None:
            scalar_data["tcp_orientation_acceleration"].append(point.tcp_orientation_acceleration)
        if point.time is not None:
            scalar_data["time"].append(point.time)
        if point.location_on_trajectory is not None:
            scalar_data["location_on_trajectory"].append(point.location_on_trajectory)
        if optimizer_config.safety_setup.global_limits.tcp_velocity_limit is not None:
            scalar_data["tcp_velocity_limit"].append(
                optimizer_config.safety_setup.global_limits.tcp_velocity_limit
            )
        if optimizer_config.safety_setup.global_limits.tcp_orientation_velocity_limit is not None:
            scalar_data["tcp_orientation_velocity_lower_limit"].append(
                -optimizer_config.safety_setup.global_limits.tcp_orientation_velocity_limit
            )
            scalar_data["tcp_orientation_velocity_upper_limit"].append(
                optimizer_config.safety_setup.global_limits.tcp_orientation_velocity_limit
            )
        if optimizer_config.safety_setup.global_limits.tcp_acceleration_limit is not None:
            scalar_data["tcp_acceleration_lower_limit"].append(
                -optimizer_config.safety_setup.global_limits.tcp_acceleration_limit
            )
            scalar_data["tcp_acceleration_upper_limit"].append(
                optimizer_config.safety_setup.global_limits.tcp_acceleration_limit
            )
        if (
            optimizer_config.safety_setup.global_limits.tcp_orientation_acceleration_limit
            is not None
        ):
            scalar_data["tcp_orientation_acceleration_lower_limit"].append(
                -optimizer_config.safety_setup.global_limits.tcp_orientation_acceleration_limit
            )
            scalar_data["tcp_orientation_acceleration_upper_limit"].append(
                optimizer_config.safety_setup.global_limits.tcp_orientation_acceleration_limit
            )

    # Send columns if data is not empty
    for key, values in scalar_data.items():
        if values:
            rr.send_columns(
                f"motion/{key}",
                times=[times_column],
                components=[rr.components.ScalarBatch(values)],
            )


def process_trajectory(
    robot: DHRobot,
    visualizer: RobotVisualizer,
    trajectory: List[models.TrajectorySample],
    optimizer_config: models.OptimizerSetup,
    timer_offset: float,
):
    """
    Process a single trajectory point and log relevant data.
    """
    times = np.array([timer_offset + point.time for point in trajectory])
    times_column = rr.TimeSecondsColumn(TIME_INTERVAL_NAME, times)
    rr.set_time_seconds(TIME_INTERVAL_NAME, timer_offset)

    # Calculate and log joint positions
    line_segments_batch = []
    for point in trajectory:
        joint_positions = robot.calculate_joint_positions(point.joint_position)
        line_segments_batch.append(joint_positions)

    rr.send_columns(
        "motion/dh_parameters",
        times=[times_column],
        components=[
            rr.LineStrips3D.indicator(),
            rr.components.LineStrip3DBatch(line_segments_batch),
            rr.components.ColorBatch([0.5, 0.5, 0.5, 1.0] * len(times)),
        ],
    )

    # Log the robot geometries
    visualizer.log_robot_geometries(trajectory, times_column)

    # Log TCP pose/orientation
    log_tcp_pose(trajectory, times_column)

    # Log joint data
    log_joint_data(trajectory, times_column, optimizer_config)

    # Log scalar data
    log_scalar_values(trajectory, times_column, optimizer_config)


def extract_link_chain_and_tcp(collision_scenes: dict) -> Tuple[List[Any], List[Any]]:
    """Extract link chain and TCP from collision scenes."""
    # Get first scene (name can vary)
    scene = next(iter(collision_scenes.values()), None)
    if not scene:
        return [], []

    # Try to get motion groups
    motion_group = next(iter(scene.motion_groups.values()), None)
    if not motion_group:
        return [], []

    return (getattr(motion_group, "link_chain", []), getattr(motion_group, "tool", []))


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

    # Log entire trajectory
    points = [
        [p.tcp_pose.position.x, p.tcp_pose.position.y, p.tcp_pose.position.z] for p in trajectory
    ]
    rr.log("motion/trajectory", rr.LineStrips3D([points], colors=[[1.0, 1.0, 1.0, 1.0]]))

    rr.log("logs", rr.TextLog(f"{motion_id}", level=rr.TextLogLevel.INFO))

    # Process trajectory points
    process_trajectory(robot, visualizer, trajectory, optimizer_config, time_offset)

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
    store_collision_scenes_api = nova._api_client.store_collision_scenes_api

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
                collision_scenes = await store_collision_scenes_api.list_stored_collision_scenes(
                    "cell"
                )
                await nova_bridge.log_collision_scenes()

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

from typing import Dict, List
import numpy as np
import rerun as rr
import asyncio
import trimesh
import wandelbots_api_client as wb
from robot_visualizer import RobotVisualizer
from hull_visualizer import HullVisualizer
from utils import get_api_client
from dh_robot import DHRobot
from motion_storage import load_processed_motions, save_processed_motion
from scipy.spatial.transform import Rotation as R
import rerun.blueprint as rrb
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Configuration Constants
SIZE = 10
RECORDING_INTERVAL = 0.016  # 16ms per point
SCHEDULE_INTERVAL = 5  # seconds
TIME_INTERVAL_NAME = f"time_interval_{RECORDING_INTERVAL}"

# Global run flags
job_running = False
first_run = True
previous_motion_group_list = []


def configure_joint_line_colors():
    """
    Log the visualization lines for joint limit boundaries.
    """
    for i in range(1, 7):
        prefix = f"motion/joint"
        rr.log(
            f"{prefix}_velocity_lower_limit_{i}",
            rr.SeriesLine(color=[255, 0, 0], name=f"joint_velocity_lower_limit_{i}"),
            timeless=True,
        )
        rr.log(
            f"{prefix}_velocity_upper_limit_{i}",
            rr.SeriesLine(color=[255, 0, 0], name=f"joint_velocity_upper_limit_{i}"),
            timeless=True,
        )

        rr.log(
            f"{prefix}_acceleration_lower_limit_{i}",
            rr.SeriesLine(color=[255, 0, 0], name=f"joint_acceleration_lower_limit_{i}"),
            timeless=True,
        )
        rr.log(
            f"{prefix}_acceleration_upper_limit_{i}",
            rr.SeriesLine(color=[255, 0, 0], name=f"joint_acceleration_upper_limit_{i}"),
            timeless=True,
        )

        rr.log(
            f"{prefix}_position_lower_limit_{i}",
            rr.SeriesLine(color=[255, 0, 0], name=f"joint_position_lower_limit_{i}"),
            timeless=True,
        )
        rr.log(
            f"{prefix}_position_upper_limit_{i}",
            rr.SeriesLine(color=[255, 0, 0], name=f"joint_position_upper_limit_{i}"),
            timeless=True,
        )

        rr.log(
            f"{prefix}_torque_limit_{i}",
            rr.SeriesLine(color=[255, 0, 0], name=f"joint_torques_lower_limit_{i}"),
            timeless=True,
        )


def configure_tcp_line_colors():
    """
    Configure time series lines for motion data.
    """
    series_specs = [
        ("tcp_velocity", [255, 255, 255]),
        ("tcp_acceleration", [255, 255, 255]),
        ("tcp_orientation_velocity", [255, 255, 255]),
        ("tcp_orientation_acceleration", [255, 255, 255]),
        ("time", [255, 255, 255]),
        ("location_on_trajectory", [255, 255, 255]),
        ("tcp_acceleration_lower_limit", [255, 0, 0]),
        ("tcp_acceleration_upper_limit", [255, 0, 0]),
        ("tcp_orientation_acceleration_lower_limit", [255, 0, 0]),
        ("tcp_orientation_acceleration_upper_limit", [255, 0, 0]),
        ("tcp_velocity_limit", [255, 0, 0]),
        ("tcp_orientation_velocity_limit", [255, 0, 0]),
    ]
    for name, color in series_specs:
        rr.log(f"motion/{name}", rr.SeriesLine(color=color, name=name), timeless=True)


def joint_content_lists():
    """
    Generate content lists for joint-related time series.
    """
    velocity_contents = [f"motion/joint_velocity_{i}" for i in range(1, 7)]
    velocity_limits = [f"motion/joint_velocity_lower_limit_{i}" for i in range(1, 7)] + [
        f"motion/joint_velocity_upper_limit_{i}" for i in range(1, 7)
    ]

    accel_contents = [f"motion/joint_acceleration_{i}" for i in range(1, 7)]
    accel_limits = [f"motion/joint_acceleration_lower_limit_{i}" for i in range(1, 7)] + [
        f"motion/joint_acceleration_upper_limit_{i}" for i in range(1, 7)
    ]

    pos_contents = [f"motion/joint_position_{i}" for i in range(1, 7)]
    pos_limits = [f"motion/joint_position_lower_limit_{i}" for i in range(1, 7)] + [
        f"motion/joint_position_upper_limit_{i}" for i in range(1, 7)
    ]

    torque_contents = [f"motion/joint_torque_{i}" for i in range(1, 7)]
    torque_limits = [f"motion/joint_torque_limit_{i}" for i in range(1, 7)]

    return (
        velocity_contents,
        velocity_limits,
        accel_contents,
        accel_limits,
        pos_contents,
        pos_limits,
        torque_contents,
        torque_limits,
    )


def get_default_blueprint(motion_group_list: list):
    """
    get logging blueprints for visualization.
    """

    # Contents for the Spatial3DView
    contents = ["motion/**", "colliders/**"] + [f"{group}/**" for group in motion_group_list]

    time_ranges = rrb.VisibleTimeRange(
        TIME_INTERVAL_NAME,
        start=rrb.TimeRangeBoundary.cursor_relative(seconds=-2),
        end=rrb.TimeRangeBoundary.cursor_relative(seconds=2),
    )
    plot_legend = rrb.PlotLegend(visible=False)

    (
        velocity_contents,
        velocity_limits,
        accel_contents,
        accel_limits,
        pos_contents,
        pos_limits,
        torque_contents,
        torque_limits,
    ) = joint_content_lists()

    return rrb.Blueprint(
        rrb.Horizontal(
            rrb.Spatial3DView(contents=contents, name="Motion"),
            rrb.Tabs(
                rrb.Vertical(
                    rrb.TimeSeriesView(
                        contents=["motion/tcp_velocity/**", "motion/tcp_velocity_limit/**"],
                        name="TCP velocity",
                        time_ranges=time_ranges,
                        plot_legend=plot_legend,
                    ),
                    rrb.TimeSeriesView(
                        contents=[
                            "motion/tcp_acceleration/**",
                            "motion/tcp_acceleration_lower_limit/**",
                            "motion/tcp_acceleration_upper_limit/**",
                        ],
                        name="TCP acceleration",
                        time_ranges=time_ranges,
                        plot_legend=plot_legend,
                    ),
                    rrb.TimeSeriesView(
                        contents=[
                            "motion/tcp_orientation_velocity/**",
                            "motion/tcp_orientation_velocity_limit/**",
                        ],
                        name="TCP orientation velocity",
                        time_ranges=time_ranges,
                        plot_legend=plot_legend,
                    ),
                    rrb.TimeSeriesView(
                        contents=[
                            "motion/tcp_orientation_acceleration/**",
                            "motion/tcp_orientation_acceleration_lower_limit/**",
                            "motion/tcp_orientation_acceleration_upper_limit/**",
                        ],
                        name="TCP orientation acceleration",
                        time_ranges=time_ranges,
                        plot_legend=plot_legend,
                    ),
                    rrb.TextLogView(origin="/logs", name="Logs"),
                    name="Trajectory quantities",
                    row_shares=[1, 1, 1, 1, 0.5],
                ),
                rrb.Vertical(
                    rrb.TimeSeriesView(
                        contents=velocity_contents + velocity_limits,
                        name="Joint velocity",
                        time_ranges=time_ranges,
                        plot_legend=plot_legend,
                    ),
                    rrb.TimeSeriesView(
                        contents=accel_contents + accel_limits,
                        name="Joint acceleration",
                        time_ranges=time_ranges,
                        plot_legend=plot_legend,
                    ),
                    rrb.TimeSeriesView(
                        contents=pos_contents + pos_limits,
                        name="Joint position",
                        time_ranges=time_ranges,
                        plot_legend=plot_legend,
                    ),
                    rrb.TimeSeriesView(
                        contents=torque_contents + torque_limits,
                        name="Joint torque",
                        time_ranges=time_ranges,
                        plot_legend=plot_legend,
                    ),
                    name="Joint quantities",
                ),
                rrb.TimeSeriesView(
                    contents="motion/time",
                    name="Time trajectory",
                    time_ranges=time_ranges,
                    plot_legend=plot_legend,
                ),
                rrb.TimeSeriesView(
                    contents="motion/location_on_trajectory",
                    name="Location on trajectory",
                    time_ranges=time_ranges,
                    plot_legend=plot_legend,
                ),
            ),
            column_shares=[1, 0.3],
        ),
        collapse_panels=True,
    )


def configure_logging_blueprints(motion_group_list: list):
    """
    Configure logging blueprints for visualization.
    """

    configure_tcp_line_colors()
    configure_joint_line_colors()

    rr.send_blueprint(get_default_blueprint(motion_group_list))


def log_joint_data(
    trajectory: List[wb.models.TrajectorySample],
    times_column,
    optimizer_config: wb.models.OptimizerSetup,
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


def log_tcp_pose(trajectory: List[wb.models.TrajectorySample], times_column):
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
        rotation = R.from_rotvec(rotation_vector)
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
    trajectory: List[wb.models.TrajectorySample],
    times_column,
    optimizer_config: wb.models.OptimizerSetup,
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

def log_colliders_once(colliders: Dict[str, wb.models.Collider]):
    for collider_id, collider in colliders.items():
            
        # Default components
        default_position = wb.models.Vector3d(x=0.0, y=0.0, z=0.0)
        default_orientation = wb.models.Vector3d(x=0.0, y=0.0, z=0.0)
        
        # Check pose and its components
        pose = collider.pose if collider.pose is not None else wb.models.Pose(
            position=default_position,
            orientation=default_orientation
        )
        
        # Handle position - convert list to Vector3d if needed
        if isinstance(pose.position, list):
            position = wb.models.Vector3d(
                x=float(pose.position[0]),
                y=float(pose.position[1]),
                z=float(pose.position[2])
            )
        else:
            position = pose.position if hasattr(pose, 'position') and pose.position is not None else default_position

        # Handle orientation - convert list to Vector3d if needed
        if isinstance(pose.orientation, list):
            orientation = wb.models.Vector3d(
                x=float(pose.orientation[0]),
                y=float(pose.orientation[1]),
                z=float(pose.orientation[2])
            )
        else:
            orientation = pose.orientation if hasattr(pose, 'orientation') and pose.orientation is not None else default_orientation
        
        pose = wb.models.Pose(position=position, orientation=orientation)
        
        rotation_vector = [pose.orientation.x, pose.orientation.y, pose.orientation.z]
        rotation = R.from_rotvec(rotation_vector)
        angle = rotation.magnitude() if rotation.magnitude() != 0 else 0.0
        axis_angle = rotation.as_rotvec() / angle if angle != 0 else [1, 0, 0]

        if collider.shape.actual_instance.shape_type == "sphere":            
            rr.log(
                f"colliders/{collider_id}",
                rr.Ellipsoids3D(
                    radii=[collider.shape.actual_instance.radius, collider.shape.actual_instance.radius, collider.shape.actual_instance.radius],
                    centers=[[pose.position.x, pose.position.y, pose.position.z]],
                    colors=[(221, 193, 193, 255)],
                ),
                timeless=True,
            )
        
        elif collider.shape.actual_instance.shape_type == "box":
            rr.log(
                f"colliders/{collider_id}",
                rr.Boxes3D(
                    centers=[[pose.position.x, pose.position.y, pose.position.z]],
                    half_sizes=[collider.shape.actual_instance.size_x, collider.shape.actual_instance.size_y, collider.shape.actual_instance.size_z],
                    colors=[(221, 193, 193, 255)],
                ),
                timeless=True,
            )

        elif collider.shape.actual_instance.shape_type == "capsule":
            height = collider.shape.actual_instance.cylinder_height
            radius = collider.shape.actual_instance.radius
            
            # Generate trimesh capsule
            capsule = trimesh.creation.capsule(height=height, radius=radius, count=[6, 8])
            
            # Extract vertices and faces for solid visualization
            vertices = np.array(capsule.vertices)
            
            # Transform vertices to world position
            transform = np.eye(4)
            transform[:3,3] = [pose.position.x, pose.position.y, pose.position.z - height/2]
            rot_mat = R.from_rotvec(np.array([pose.orientation.x, pose.orientation.y, pose.orientation.z]))
            transform[:3,:3] = rot_mat.as_matrix()
            
            vertices = np.array([transform @ np.append(v, 1) for v in vertices])[:,:3]
            
            polygons = HullVisualizer.compute_hull_outlines_from_points(vertices)

            if polygons:
                line_segments = [p.tolist() for p in polygons]
                rr.log(
                    f"colliders/{collider_id}",
                    rr.LineStrips3D(
                        line_segments, radii=rr.Radius.ui_points(0.75), colors=[[221, 193, 193, 255]]
                    ),
                    static=True,
                    timeless=True,
                )

        elif collider.shape.actual_instance.shape_type == "convex_hull":            
            polygons = HullVisualizer.compute_hull_outlines_from_points(collider.shape.actual_instance.vertices)

            if polygons:
                line_segments = [p.tolist() for p in polygons]
                rr.log(
                    f"colliders/{collider_id}",
                    rr.LineStrips3D(
                        line_segments, radii=rr.Radius.ui_points(0.75), colors=[[221, 193, 193, 255]]
                    ),
                    static=True,
                    timeless=True,
                )

def process_trajectory(
    robot: DHRobot,
    visualizer: RobotVisualizer,
    trajectory: List[wb.models.TrajectorySample],
    optimizer_config: wb.models.OptimizerSetup,
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
        "motion/joints",
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


async def fetch_and_process_motion(
    motion_id,
    model_from_controller,
    optimizer_config: wb.models.OptimizerSetup,
    trajectory: List[wb.models.TrajectorySample],
):
    """
    Fetch and process a single motion if not processed already.
    """

    # Initialize DHRobot and Visualizer
    robot = DHRobot(optimizer_config.dh_parameters, optimizer_config.mounting)
    visualizer = RobotVisualizer(
        robot=robot,
        robot_model_geometries=optimizer_config.safety_setup.robot_model_geometries,
        tcp_geometries=optimizer_config.safety_setup.tcp_geometries,
        static_transform=False,
        base_entity_path="motion",
        glb_path=f"models/{model_from_controller}.glb",
    )

    print(f"Processing motion trajectory for {motion_id}.", flush=True)

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

    configure_tcp_line_colors()
    configure_joint_line_colors()

    # Save the processed motion ID and trajectory time
    save_processed_motion(motion_id, trajectory_time)


async def process_motions():
    """
    Fetch and process all unprocessed motions.
    """
    global job_running
    global first_run
    global previous_motion_group_list

    client = get_api_client()
    motion_api = wb.api.MotionApi(api_client=client)
    motion_group_infos_api = wb.api.MotionGroupInfosApi(api_client=client)
    motion_group_api = wb.api.MotionGroupApi(api_client=client)
    store_collision_api = wb.api.StoreCollisionComponentsApi(api_client=client)

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

            for motion_id in motions.motions:
                colliders = await store_collision_api.list_stored_colliders("cell")
                log_colliders_once(colliders)

                # Fetch motion details
                motion = await motion_api.get_planned_motion("cell", motion_id)
                optimizer_config = await motion_group_infos_api.get_optimizer_configuration(
                    "cell", motion.motion_group
                )
                trajectory = await motion_api.get_motion_trajectory("cell", motion_id, int(RECORDING_INTERVAL*1000))

                # Configure logging blueprints only if motion_group_list has changed
                motion_groups = await motion_group_api.list_motion_groups("cell")
                motion_group_list = [
                    active_motion_group.motion_group
                    for active_motion_group in motion_groups.instances
                ]
                if motion_group_list != previous_motion_group_list:
                    configure_logging_blueprints(motion_group_list=motion_group_list)
                    previous_motion_group_list = motion_group_list

                if motion_id in processed_motion_ids:
                    continue

                motion_motion_group = next((mg for mg in motion_groups.instances if mg.motion_group == motion.motion_group), None)

                await fetch_and_process_motion(
                    motion_id=motion_id,
                    model_from_controller=motion_motion_group.model_from_controller,
                    optimizer_config=optimizer_config,
                    trajectory=trajectory.trajectory,
                )

    except Exception as e:
        print(f"Error during job execution: {e}", flush=True)
    finally:
        job_running = False
        await client.close()


async def main():
    """Main entry point for the application."""
    # Initialize Rerun
    rr.init(application_id="nova", recording_id="nova_live", spawn=True)

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

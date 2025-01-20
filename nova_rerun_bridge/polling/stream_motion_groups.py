import asyncio

import numpy as np
import rerun as rr
from nova import Nova
from scipy.spatial.transform import Rotation as R

from nova_rerun_bridge import colors
from nova_rerun_bridge.dh_robot import DHRobot
from nova_rerun_bridge.hull_visualizer import HullVisualizer
from nova_rerun_bridge.robot_visualizer import RobotVisualizer

# Constants
RECORDING_INTERVAL = 0.016  # 16ms per point
TIME_INTERVAL_NAME = f"time_interval_{RECORDING_INTERVAL}"


def log_safety_zones_once(motion_group: str, optimizer_config, robot: DHRobot):
    """
    Log hull outlines for the safety zones defined in the optimizer configuration.
    """
    mounting_transform = optimizer_config.mounting

    for zone in optimizer_config.safety_setup.safety_zones:
        geom = zone.geometry
        zone_id = zone.id
        entity_path = f"{motion_group}/zones/zone_{zone_id}"

        if geom.compound is not None:
            child_geoms = geom.compound.child_geometries
            polygons = HullVisualizer.compute_hull_outlines_from_geometries(child_geoms)
        elif geom.convex_hull is not None:

            class ChildWrapper:
                pass

            c = ChildWrapper()
            c.convex_hull = geom.convex_hull
            polygons = HullVisualizer.compute_hull_outlines_from_geometries([c])
        else:
            polygons = []

        accumulated = robot.pose_to_matrix(mounting_transform)
        polygons = apply_transform_to_polygons(polygons, accumulated)

        # Log polygons as wireframe outlines
        if polygons:
            line_segments = [p.tolist() for p in polygons]  # convert numpy arrays to lists
            rr.log(
                entity_path,
                rr.LineStrips3D(
                    line_segments, radii=rr.Radius.ui_points(0.75), colors=[[221, 193, 193, 255]]
                ),
                static=True,
                timeless=True,
            )


def apply_transform_to_polygons(polygons, transform):
    """
    Apply a transformation matrix to a list of polygons.
    """
    transformed_polygons = []
    for polygon in polygons:
        # Convert polygon to homogeneous coordinates
        homogeneous_polygon = np.hstack((polygon, np.ones((polygon.shape[0], 1))))
        # Apply the transformation
        transformed_polygon = np.dot(transform, homogeneous_polygon.T).T
        # Convert back to 3D coordinates
        transformed_polygons.append(transformed_polygon[:, :3])
    return transformed_polygons


def log_joint_positions_once(motion_group: str, robot: DHRobot, joint_position):
    """Compute and log joint positions for a robot."""
    joint_positions = robot.calculate_joint_positions(joint_position)
    line_segments = [
        [joint_positions[i], joint_positions[i + 1]] for i in range(len(joint_positions) - 1)
    ]
    segment_colors = [colors.colors[i % len(colors.colors)] for i in range(len(line_segments))]

    rr.log(
        f"{motion_group}/dh_parameters",
        rr.LineStrips3D(line_segments, colors=segment_colors),
        static=True,
    )


class MotionGroupProcessor:
    def __init__(self):
        self.last_tcp_pose = {}

    def tcp_pose_changed(self, motion_group: str, tcp_pose) -> bool:
        """Check if the TCP pose has changed compared to the last logged value."""
        last_pose = self.last_tcp_pose.get(motion_group)
        current_position = [tcp_pose.position.x, tcp_pose.position.y, tcp_pose.position.z]
        current_rotation = [tcp_pose.orientation.x, tcp_pose.orientation.y, tcp_pose.orientation.z]

        if last_pose is None:
            # No previous pose, consider it as changed
            self.last_tcp_pose[motion_group] = (current_position, current_rotation)
            return True

        last_position, last_rotation = last_pose
        if current_position != last_position or current_rotation != last_rotation:
            # Update the cache and return True if either position or rotation has changed
            self.last_tcp_pose[motion_group] = (current_position, current_rotation)
            return True

        return False

    def log_tcp_orientation(self, motion_group: str, tcp_pose):
        """Log TCP orientation and position."""
        rotation_vector = [tcp_pose.orientation.x, tcp_pose.orientation.y, tcp_pose.orientation.z]
        rotation = R.from_rotvec(rotation_vector)
        angle = rotation.magnitude() if rotation.magnitude() != 0 else 0.0
        axis_angle = rotation.as_rotvec() / angle if angle != 0 else [0, 0, 0]

        rr.log(
            f"{motion_group}/tcp_position",
            rr.Transform3D(
                translation=[tcp_pose.position.x, tcp_pose.position.y, tcp_pose.position.z],
                rotation=rr.RotationAxisAngle(axis=axis_angle, angle=angle),
            ),
            static=True,
        )


async def process_motion_group_state():
    """Process motion group states and log data efficiently."""
    print("Starting motion group state processing...", flush=True)

    nova = Nova()
    motion_group_infos_api = nova._api_client.motion_group_infos_api
    motion_group_api = nova._api_client.motion_group_api
    processor = MotionGroupProcessor()

    rr.init(application_id="nova", recording_id="nova_live", spawn=True)
    rr.set_time_seconds(TIME_INTERVAL_NAME, 0)

    # Fetch active motion groups
    motion_groups = await motion_group_api.list_motion_groups("cell")

    print(f"Active motion groups: {motion_groups.instances}", flush=True)

    for active_motion_group in motion_groups.instances:
        motion_group = active_motion_group.motion_group
        optimizer_config = await motion_group_infos_api.get_optimizer_configuration(
            "cell", motion_group
        )

        # Initialize DHRobot and Visualizer
        robot = DHRobot(optimizer_config.dh_parameters, optimizer_config.mounting)
        visualizer = RobotVisualizer(
            robot=robot,
            robot_model_geometries=optimizer_config.safety_setup.robot_model_geometries,
            tcp_geometries=optimizer_config.safety_setup.tcp_geometries,
            static_transform=True,
            base_entity_path=motion_group,
            albedo_factor=[0, 255, 100],
            glb_path=f"models/{active_motion_group.model_from_controller}.glb",
        )

        # Log safety zones (only once)
        log_safety_zones_once(motion_group, optimizer_config, robot)

        print(f"Subscribing to motion group {motion_group}", flush=True)
        async for state in motion_group_infos_api.stream_motion_group_state("cell", motion_group):
            if processor.tcp_pose_changed(motion_group, state.state.tcp_pose):
                # Log joint positions
                log_joint_positions_once(motion_group, robot, state.state.joint_position)

                # Log robot geometries
                visualizer.log_robot_geometry(state.state.joint_position)

                processor.log_tcp_orientation(motion_group, state.state.tcp_pose)

            await asyncio.sleep(0.01)  # Prevents CPU overuse

    await nova._api_client.close()


if __name__ == "__main__":
    asyncio.run(process_motion_group_state())

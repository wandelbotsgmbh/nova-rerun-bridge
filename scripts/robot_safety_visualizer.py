from typing import List
import numpy as np
import rerun as rr
import trimesh
from scipy.spatial.transform import Rotation
from wandelbots_api_client.models import PlannerPose, Quaternion, Vector3d
from dh_robot import DHRobot
import wandelbots_api_client as wb


class RobotVisualizer:
    def __init__(
        self,
        robot: DHRobot,
        robot_model_geometries,
        tcp_geometries,
        static_transform: bool = True,
        base_entity_path: str = "robot",
        albedo_factor: list = [255, 255, 255],
    ):
        """
        :param robot: DHRobot instance
        :param robot_model_geometries: List of geometries for each link
        :param tcp_geometries: TCP geometries (similar structure to link geometries)
        :param static_transform: If True, transforms are logged as static, else temporal.
        :param base_entity_path: A base path prefix for logging the entities (e.g. motion group name)
        :param albedo_factor: A list representing the RGB values [R, G, B] to apply as the albedo factor.
        """
        self.robot = robot
        self.link_geometries = {}
        self.tcp_geometries = tcp_geometries
        self.logged_meshes = set()
        self.static_transform = static_transform
        self.base_entity_path = base_entity_path.rstrip("/")
        self.albedo_factor = albedo_factor

        # Group geometries by link
        for gm in robot_model_geometries:
            self.link_geometries.setdefault(gm.link_index, []).append(gm.geometry)

    def geometry_pose_to_matrix(self, init_pose):
        # Convert init_pose to PlannerPose and then to a matrix via the robot
        p = PlannerPose(
            position=Vector3d(
                x=init_pose.position.x, y=init_pose.position.y, z=init_pose.position.z
            ),
            orientation=Quaternion(
                x=init_pose.orientation.x,
                y=init_pose.orientation.y,
                z=init_pose.orientation.z,
                w=init_pose.orientation.w,
            ),
        )
        return self.robot.pose_to_matrix(p)

    def compute_forward_kinematics(self, joint_values):
        """Compute link transforms using the robot's methods."""
        accumulated = self.robot.pose_to_matrix(self.robot.mounting)
        transforms = [accumulated.copy()]
        for dh_param, joint_rot in zip(self.robot.dh_parameters, joint_values.joints):
            transform = self.robot.dh_transform(dh_param, joint_rot)
            accumulated = accumulated @ transform
            transforms.append(accumulated.copy())
        return transforms

    def rotation_matrix_to_axis_angle(self, Rm):
        """Use scipy for cleaner axis-angle extraction."""
        rot = Rotation.from_matrix(Rm)
        angle = rot.magnitude()
        axis = rot.as_rotvec() / angle if angle > 1e-8 else np.array([1.0, 0.0, 0.0])
        return axis, angle

    def init_geometry(self, entity_path: str, capsule):
        """Generic method to log a single geometry, either capsule or box."""

        if entity_path not in self.logged_meshes:
            if capsule:
                radius = capsule.radius
                height = capsule.cylinder_height

                # Slightly shrink the capsule if static to reduce z-fighting
                if self.static_transform:
                    radius *= 0.99
                    height *= 0.99

                # Create capsule and retrieve normals
                cap_mesh = trimesh.creation.capsule(radius=radius, height=height)
                vertex_normals = cap_mesh.vertex_normals.tolist()

                rr.log(
                    entity_path,
                    rr.Mesh3D(
                        vertex_positions=cap_mesh.vertices.tolist(),
                        triangle_indices=cap_mesh.faces.tolist(),
                        vertex_normals=vertex_normals,
                        albedo_factor=self.albedo_factor,
                    ),
                )
                self.logged_meshes.add(entity_path)
            else:
                # fallback to a box
                rr.log(entity_path, rr.Boxes3D(half_sizes=[[50, 50, 50]]))
                self.logged_meshes.add(entity_path)

    def log_robot_geometry(self, joint_position):
        transforms = self.compute_forward_kinematics(joint_position)

        def log_geometry(entity_path, transform, geom):
            """Helper function to log a single geometry."""
            self.init_geometry(entity_path, geom.capsule)
            translation = transform[:3, 3]
            Rm = transform[:3, :3]
            axis, angle = self.rotation_matrix_to_axis_angle(Rm)
            rr.log(
                entity_path,
                rr.InstancePoses3D(
                    translations=[translation.tolist()],
                    rotation_axis_angles=[
                        rr.RotationAxisAngle(axis=axis.tolist(), angle=float(angle))
                    ],
                ),
                static=self.static_transform,
                timeless=self.static_transform,
            )

        # Log link geometries
        for link_index, geometries in self.link_geometries.items():
            link_transform = transforms[link_index]
            for i, geom in enumerate(geometries):
                entity_path = f"{self.base_entity_path}/links/link_{link_index}/geometry_{i}"
                final_transform = link_transform @ self.geometry_pose_to_matrix(geom.init_pose)
                log_geometry(entity_path, final_transform, geom)

        # Log TCP geometries
        if self.tcp_geometries:
            tcp_transform = transforms[-1]  # the final frame transform
            for i, geom in enumerate(self.tcp_geometries):
                entity_path = f"{self.base_entity_path}/tcp/geometry_{i}"
                final_transform = tcp_transform @ self.geometry_pose_to_matrix(geom.init_pose)
                log_geometry(entity_path, final_transform, geom)

    def log_robot_geometries(self, trajectory: List[wb.models.TrajectorySample], times_column):
        """
        Log the robot geometries for each link and TCP as separate entities.

        Args:
            trajectory (List[wb.models.TrajectorySample]): The list of trajectory sample points.
            times_column (rr.TimeSecondsColumn): The time column associated with the trajectory points.
        """
        link_positions = {}
        link_rotations = {}

        def collect_geometry_data(entity_path, transform, geom):
            """Helper to collect geometry data for a given entity."""
            self.init_geometry(entity_path, geom.capsule)
            translation = transform[:3, 3].tolist()
            Rm = transform[:3, :3]
            axis, angle = self.rotation_matrix_to_axis_angle(Rm)
            if entity_path not in link_positions:
                link_positions[entity_path] = []
                link_rotations[entity_path] = []
            link_positions[entity_path].append(translation)
            link_rotations[entity_path].append(rr.RotationAxisAngle(axis=axis, angle=angle))

        for point in trajectory:
            transforms = self.compute_forward_kinematics(point.joint_position)

            # Collect data for link geometries
            for link_index, geometries in self.link_geometries.items():
                link_transform = transforms[link_index]
                for i, geom in enumerate(geometries):
                    entity_path = f"{self.base_entity_path}/links/link_{link_index}/geometry_{i}"
                    final_transform = link_transform @ self.geometry_pose_to_matrix(geom.init_pose)
                    collect_geometry_data(entity_path, final_transform, geom)

            # Collect data for TCP geometries
            if self.tcp_geometries:
                tcp_transform = transforms[-1]  # End-effector transform
                for i, geom in enumerate(self.tcp_geometries):
                    entity_path = f"{self.base_entity_path}/tcp/geometry_{i}"
                    final_transform = tcp_transform @ self.geometry_pose_to_matrix(geom.init_pose)
                    collect_geometry_data(entity_path, final_transform, geom)

        # Send collected columns for all geometries
        for entity_path, positions in link_positions.items():
            rr.send_columns(
                entity_path,
                times=[times_column],
                components=[
                    rr.Transform3D.indicator(),
                    rr.components.Translation3DBatch(positions),
                    rr.components.RotationAxisAngleBatch(link_rotations[entity_path]),
                ],
            )

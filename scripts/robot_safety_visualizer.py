import re
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
        glb_path: str = "",
    ):
        """
        :param robot: DHRobot instance
        :param robot_model_geometries: List of geometries for each link
        :param tcp_geometries: TCP geometries (similar structure to link geometries)
        :param static_transform: If True, transforms are logged as static, else temporal.
        :param base_entity_path: A base path prefix for logging the entities (e.g. motion group name)
        :param albedo_factor: A list representing the RGB values [R, G, B] to apply as the albedo factor.
        :param glb_path: Path to the GLB file for the robot model.
        """
        self.robot = robot
        self.link_geometries = {}
        self.tcp_geometries = tcp_geometries
        self.logged_meshes = set()
        self.static_transform = static_transform
        self.base_entity_path = base_entity_path.rstrip("/")
        self.albedo_factor = albedo_factor
        self.scene = trimesh.load(glb_path, file_type="glb")

        self.edge_data = self.scene.graph.transforms.edge_data

        # This will hold the names of discovered joints (e.g. ["robot_J00", "robot_J01", ...])
        self.joint_names: List[str] = []

        # After loading, auto-discover any child nodes that match *_J0n
        self.discover_joints()

        # Group geometries by link
        for gm in robot_model_geometries:
            self.link_geometries.setdefault(gm.link_index, []).append(gm.geometry)
    

    def discover_joints(self):
        """
        Find all child node names that contain '_J0' followed by digits or '_FLG'.
        We store joints in a sorted list so that e.g. J00 < J01 < J02, followed by FLG nodes.
        """
        joint_pattern = re.compile(r"_J0(\d+)")
        flg_pattern = re.compile(r"_FLG")
        matches = []
        flg_nodes = []
    
        for (parent, child), data in self.edge_data.items():
            # Check for joints
            joint_match = joint_pattern.search(child)
            if joint_match:
                j_idx = int(joint_match.group(1))
                matches.append((j_idx, child))
            
            # Check for FLG
            flg_match = flg_pattern.search(child)
            if flg_match:
                flg_nodes.append(child)
    
        matches.sort(key=lambda x: x[0])
        self.joint_names = [name for _, name in matches] + flg_nodes
        print("Discovered nodes:", self.joint_names)

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
    
    def gamma_lift_single_color(self, color: np.ndarray, gamma: float = 0.8) -> np.ndarray:
        """
        Apply gamma correction to a single RGBA color in-place.
        color: shape (4,) with [R, G, B, A] in 0..255, dtype=uint8
        gamma: < 1.0 brightens midtones, > 1.0 darkens them.
        """
        rgb_float = color[:3].astype(np.float32) / 255.0
        rgb_float = np.power(rgb_float, gamma)
        color[:3] = (rgb_float * 255.0).astype(np.uint8)

        return color
    
    def get_transform_matrix(self):
        """
        Creates a transformation matrix that converts from glTF's right-handed Y-up 
        coordinate system to Rerun's right-handed Z-up coordinate system.
        
        Returns:
            np.ndarray: A 4x4 transformation matrix
        """
        # Convert from glTF's Y-up to Rerun's Z-up coordinate system
        return np.array([
            [1.0, 0.0, 0.0, 0.0],  # X stays the same
            [0.0, 0.0, -1.0, 0.0], # Y becomes -Z 
            [0.0, 1.0, 0.0, 0.0],  # Z becomes Y
            [0.0, 0.0, 0.0, 1.0]   # Homogeneous coordinate
        ])

    def init_mesh(self, entity_path: str, geom, joint_name):
        """Generic method to log a single geometry, either capsule or box."""

        if entity_path not in self.logged_meshes:

            # scale mesh to mm            
            transform = np.eye(4)
            mesh_scale_matrix = np.eye(4)
            mesh_scale_matrix[:3, :3] *= 1000
            transform = transform @ mesh_scale_matrix
            transformed_mesh = geom.copy()

            transformed_mesh.apply_transform(transform)

            if transformed_mesh.visual is not None:
                transformed_mesh.visual = transformed_mesh.visual.to_color()

            vertex_colors = None
            if transformed_mesh.visual and hasattr(transformed_mesh.visual, "vertex_colors"):
                vertex_colors = transformed_mesh.visual.vertex_colors 
            
            rr.log(
                entity_path,
                rr.Mesh3D(
                    vertex_positions=transformed_mesh.vertices,
                    triangle_indices=transformed_mesh.faces,
                    vertex_normals=getattr(transformed_mesh, "vertex_normals", None),
                    albedo_factor=self.gamma_lift_single_color(vertex_colors, gamma=0.5),
                ),
            )

            self.logged_meshes.add(entity_path)

    def init_geometry(self, entity_path: str, capsule, link_index):
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

        def log_geometry(entity_path, transform):
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

        # Log robot joint geometries
        for link_index, joint_name in enumerate(self.joint_names):
            link_transform = transforms[link_index]

            dumped = self.scene.dump()
            for geom in dumped:
                entity_path = f"{self.base_entity_path}/links/link_{link_index}/mesh/{geom.metadata.get('node')}"

                # calculate the inverse transform to get the mesh in the correct position
                cumulative_transform, _ = self.scene.graph.get(frame_to=joint_name)
                ctransform = cumulative_transform.copy()
                inverse_transform = np.linalg.inv(ctransform)

                # scale positions to mm
                inverse_transform[:3, 3] *= 1000

                root_transform = self.get_transform_matrix()
                
                transform = root_transform @ inverse_transform

                final_transform = link_transform @ transform
                
                self.init_mesh(entity_path, geom, joint_name)
                log_geometry(entity_path, final_transform)

        # Log link geometries
        for link_index, geometries in self.link_geometries.items():
            link_transform = transforms[link_index]
            for i, geom in enumerate(geometries):
                entity_path = f"{self.base_entity_path}/links/link_{link_index}/geometry_{i}"
                final_transform = link_transform @ self.geometry_pose_to_matrix(geom.init_pose)
                
                self.init_geometry(entity_path, geom.capsule, link_index)
                log_geometry(entity_path, final_transform)

        # Log TCP geometries
        if self.tcp_geometries:
            tcp_transform = transforms[-1]  # the final frame transform
            for i, geom in enumerate(self.tcp_geometries):
                entity_path = f"{self.base_entity_path}/tcp/geometry_{i}"
                final_transform = tcp_transform @ self.geometry_pose_to_matrix(geom.init_pose)

                self.init_geometry(entity_path, geom.capsule, link_index)
                log_geometry(entity_path, final_transform)

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
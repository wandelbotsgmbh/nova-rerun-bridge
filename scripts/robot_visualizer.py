import re
import numpy as np
import rerun as rr
import trimesh
from scipy.spatial.transform import Rotation
from typing import List


class RealRobotVisualizer:
    def __init__(
        self,
        glb_path: str,
        root_path: str = "robot",
        position_scale: float = 1000.0,
        mesh_scale: float = 1000.0,
        axis_length: float = 100.0,
    ):
        self.scene = trimesh.load(glb_path, file_type="glb")
        self.root_path = root_path
        self.edge_data = self.scene.graph.transforms.edge_data
        self.position_scale = position_scale
        self.mesh_scale = mesh_scale
        self.logged_meshes = set()
        self.axis_length = axis_length
        self.albedo_factor = [1.0, 1.0, 1.0, 1.0]

        # This will hold the names of discovered joints (e.g. ["robot_J00", "robot_J01", ...])
        self.joint_names: List[str] = []

        # Build & log once
        self.build_and_log()

        # After loading, auto-discover any child nodes that match *_J0n
        self.discover_joints()

    def discover_joints(self):
        """
        Find all child node names that contain '_J0' followed by digits.
        We store them in a sorted list so that e.g. J00 < J01 < J02.
        """
        pattern = re.compile(r"_J0(\d+)")
        matches = []

        for (parent, child), data in self.edge_data.items():
            # If child's name matches e.g. 'whatever_J05'
            match = pattern.search(child)
            if match:
                j_idx = int(match.group(1))
                matches.append((j_idx, child))

        matches.sort(key=lambda x: x[0])
        self.joint_names = [name for _, name in matches]
        print("Discovered joints:", self.joint_names)

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

    def matrix_to_axis_angle(self, rotation_matrix: np.ndarray):
        rotation = Rotation.from_matrix(rotation_matrix)
        axis_angle = rotation.as_rotvec()
        angle = np.linalg.norm(axis_angle)
        if angle < 1e-10:
            return np.array([1.0, 0.0, 0.0]), 0.0
        axis = axis_angle / angle
        return axis, angle

    def transform_matrix_for_transforms(self, matrix: np.ndarray):
        transform = matrix.copy()
        transform[:3, 3] *= self.position_scale
        return transform

    def transform_matrix_for_meshes(self, matrix: np.ndarray):
        transform = matrix
        mesh_scale_matrix = np.eye(4)
        mesh_scale_matrix[:3, :3] *= self.mesh_scale
        transform = transform @ mesh_scale_matrix
        return transform

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
    
    def get_mesh_pivot(self, mesh):
        """Get the pivot point of a mesh that was exported from Blender."""
        # Get transform if available in scene graph
        node_name = mesh.metadata.get("node")
        if node_name in self.scene.graph:
            # Get world transform for this node
            world_transform = self.scene.graph[node_name][0]
            # Extract translation component (last column of 4x4 matrix)
            pivot = world_transform[:3, 3]
            return pivot
            
        # Fallback to bounds center if no transform found
        return mesh.bounds_center
    
    def log_geometry(self, entity_path: str, node_name: str, parent_name: str):
        dumped = self.scene.dump()
        for geom in dumped:
            if geom.metadata.get("node") == node_name:
                
                # Get the transform from the node to the parent
                cumulative_transform, _ = self.scene.graph.get(frame_to=node_name)
                
                inverse_transform = np.linalg.inv(cumulative_transform)


                transform = inverse_transform
                mesh_scale_matrix = np.eye(4)
                mesh_scale_matrix[:3, :3] *= self.mesh_scale
                transform = transform @ mesh_scale_matrix

                parent_to_child = self.edge_data.get((parent_name, node_name), {}).get("matrix", np.eye(4))
                transformed_mesh = geom.copy()
                pivot = self.get_mesh_pivot(geom) * 1000

                transformed_mesh.apply_transform(transform)

                if transformed_mesh.visual is not None:
                    transformed_mesh.visual = transformed_mesh.visual.to_color()

                vertex_colors = None
                if transformed_mesh.visual and hasattr(transformed_mesh.visual, "vertex_colors"):
                    vertex_colors = transformed_mesh.visual.vertex_colors 
                
                rr.log(
                    entity_path,
                    rr.Mesh3D(
                        vertex_positions=transformed_mesh.vertices - pivot,
                        triangle_indices=transformed_mesh.faces,
                        vertex_normals=getattr(transformed_mesh, "vertex_normals", None),
                        albedo_factor=self.gamma_lift_single_color(vertex_colors, gamma=0.5),
                    ),
                )
                self.logged_meshes.add(entity_path)
                    

    def build_hierarchy(self, parent_node: str, parent_path: str = ""):
        for (parent, child), data in self.edge_data.items():
            if parent == parent_node:
                transform = data["matrix"]
                transformed_matrix = self.transform_matrix_for_transforms(transform)

                translation = transformed_matrix[:3, 3]
                rotation_matrix = transformed_matrix[:3, :3]
                entity_path = f"{parent_path}/{child}" if parent_path else child
                    
                axis, angle = self.matrix_to_axis_angle(rotation_matrix)
                rr.log(
                    f"{self.root_path}/{entity_path}",
                    rr.Transform3D(
                        translation=translation,
                        rotation=rr.RotationAxisAngle(axis=axis, angle=angle),
                        axis_length=self.axis_length,
                        relation=rr.TransformRelation.ParentFromChild,
                    ),
                    static=True,
                    timeless=True,
                )

                self.log_geometry(f"{self.root_path}/{entity_path}/mesh", child, parent)
                self.build_hierarchy(child, entity_path)

    def build_and_log(self):
        # Adjust "world" to the actual root node name if different
        rr.log(f"{self.root_path}", rr.ViewCoordinates.RIGHT_HAND_Y_UP, static=True, timeless=True)

        # Apply the additional transformation to the root path
        root_transform = self.get_transform_matrix()
        rotation_matrix = root_transform[:3, :3]
        axis, angle = self.matrix_to_axis_angle(rotation_matrix)
        rr.log(
            f"{self.root_path}",
            rr.Transform3D(
                rotation=rr.RotationAxisAngle(axis=axis, angle=angle),
                axis_length=self.axis_length,
            ),
            timeless=True,
        )
        
        self.build_hierarchy("world")

    def update_joint_rotation(self, joint_name: str, angle: float):
        """
        Add `angle` (radians) to the joint's existing local rotation around Z,
        as specified by the original glTF parent->child transform.
        
        Because we always read from edge_data, this function effectively does:
            total_z_rotation = (original_z_rotation) + angle
        on each call.
        
        If you want repeated calls to keep accumulating on top of the *last* call,
        then you must store the updated transform or angles in a field
        (e.g. self.local_transforms) rather than re-reading from edge_data each time.
        """

        # 1) Find the parent of this joint
        parent_name = None
        for (parent, child), _ in self.edge_data.items():
            if child == joint_name:
                parent_name = parent
                break
        if parent_name is None:
            print(f"Joint '{joint_name}' not found in edge_data. No update.")
            return

        # 2) Get the original transform from the glTF, then convert to your Rerun coords
        #original_matrix = self.edge_data[(parent_name, joint_name)]["matrix"]
        original_matrix, _ = self.scene.graph.get(frame_to=joint_name, frame_from=parent_name)
        transformed_matrix = self.transform_matrix_for_transforms(original_matrix)

        # 3) Extract current rotation as Euler angles
        R_old = transformed_matrix[:3, :3]
        eul = Rotation.from_matrix(R_old).as_euler('zyx', degrees=False)
        # eul = [rx, ry, rz], where eul[2] is the rotation around local Z

        # 4) Add the new angle to the existing Z rotation
        eul[1] += angle

        # 5) Build the updated rotation matrix
        R_new = Rotation.from_euler('zyx', eul, degrees=False).as_matrix()
        transformed_matrix[:3, :3] = R_new

        translation = transformed_matrix[:3, 3]
        axis, final_angle = self.matrix_to_axis_angle(R_new)

        full_path = self.get_full_entity_path(joint_name)

        rr.log(
            f"{self.root_path}/{full_path}",
            rr.Transform3D(
                translation=translation,
                rotation=rr.RotationAxisAngle(axis=axis, angle=final_angle),
                axis_length=self.axis_length,
                relation=rr.TransformRelation.ParentFromChild,
            ),
            static=True,
            timeless=True,
        )
        
        """
        print(
            f"update_joint_rotation('{joint_name}', {angle}): "
            f"Old Z={eul[2] - angle:.3f}, New Z={eul[2]:.3f}"
        )
        """


    def update_all_joints(self, angles: List[float]):
        """
        Bulk-update all discovered joints by passing a list of angles
        in numeric order: e.g. J00, then J01, then J02, ...
        """
        if len(angles) != len(self.joint_names):
            raise ValueError(
                f"Number of angles ({len(angles)}) does not match "
                f"number of discovered joints ({len(self.joint_names)})."
            )

        for joint_name, angle in zip(self.joint_names, angles):
            self.update_joint_rotation(joint_name, angle)

    def get_full_entity_path(self, node_name: str) -> str:
        """
        Build the path from the top-level child of 'world' all the way
        down to 'node_name', skipping 'world' itself.
        E.g. "UNIVERSALROBOTS_UR10E_J00/UNIVERSALROBOTS_UR10E_J01/UNIVERSALROBOTS_UR10E_J02"
        """
        path_parts = []
        current = node_name

        # Walk upward until we hit 'world' or can't find a parent
        while current and current.lower() != "world":
            path_parts.append(current)
            # Find the parent of 'current' by looking at edge_data
            found_parent = False
            for (possible_parent, possible_child) in self.edge_data.keys():
                if possible_child == current:
                    current = possible_parent
                    found_parent = True
                    break
            if not found_parent:
                # No parent found => this is a top-level node
                break

        # The path_parts list is from leaf -> root; reverse it
        path_parts.reverse()
        return "/".join(path_parts)

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import random
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import time
import math

class RubiksCube:
    def __init__(self, size_x, size_y, size_z):
        self.size_x = size_x
        self.size_y = size_y
        self.size_z = size_z
        self.rotation_x = 20
        self.rotation_y = 45
        self.cube_size = 1.0
        self.gap = 0.1
        self.solve_step = 0
        
        # Animation variables
        self.is_animating = False
        self.animation_progress = 0.0
        self.animation_speed = 0.1
        self.current_rotation = None
        self.animation_cubes = []
        
        # Bright colors for each face
        self.colors = [
            [1.0, 0.0, 0.0],  # Red - Left (X=0)
            [0.0, 1.0, 0.0],  # Green - Right (X=max)
            [0.0, 0.0, 1.0],  # Blue - Bottom (Y=0)
            [1.0, 1.0, 0.0],  # Yellow - Top (Y=max)
            [1.0, 0.5, 0.0],  # Orange - Back (Z=0)
            [1.0, 1.0, 1.0],  # White - Front (Z=max)
        ]
        
        # Generate solved state
        self.cubes = self.generate_solved_state()
        self.is_scrambled = False
        self.scramble_moves = []
        self.solve_moves = []
        
        print(f"Created {size_x}x{size_y}x{size_z} cube with {len(self.cubes)} small cubes")

    def generate_solved_state(self):
        """Generate the solved state of the cube"""
        cubes = []
        spacing = self.cube_size + self.gap
        
        # Center the cube around origin
        start_x = -(self.size_x - 1) * spacing / 2
        start_y = -(self.size_y - 1) * spacing / 2
        start_z = -(self.size_z - 1) * spacing / 2
        
        for x in range(self.size_x):
            for y in range(self.size_y):
                for z in range(self.size_z):
                    pos_x = start_x + x * spacing
                    pos_y = start_y + y * spacing
                    pos_z = start_z + z * spacing
                    
                    # Determine which faces are visible and their solved colors
                    colors = [-1, -1, -1, -1, -1, -1]  # [left, right, bottom, top, back, front]
                    
                    if x == 0: colors[0] = 0  # Left face - Red
                    if x == self.size_x - 1: colors[1] = 1  # Right face - Green
                    if y == 0: colors[2] = 2  # Bottom face - Blue
                    if y == self.size_y - 1: colors[3] = 3  # Top face - Yellow
                    if z == 0: colors[4] = 4  # Back face - Orange
                    if z == self.size_z - 1: colors[5] = 5  # Front face - White
                    
                    cubes.append({
                        'pos': [pos_x, pos_y, pos_z],
                        'colors': colors,
                        'grid_pos': [x, y, z],
                        'original_pos': [pos_x, pos_y, pos_z]
                    })
        
        return cubes

    def get_face_cubes(self, face, layer=0):
        """Get all cubes that belong to a specific face and layer"""
        face_cubes = []
        
        if face == 'R':  # Right face (X = max)
            target_x = self.size_x - 1 - layer
            face_cubes = [i for i, cube in enumerate(self.cubes) if cube['grid_pos'][0] == target_x]
        elif face == 'L':  # Left face (X = 0)
            target_x = layer
            face_cubes = [i for i, cube in enumerate(self.cubes) if cube['grid_pos'][0] == target_x]
        elif face == 'U':  # Up face (Y = max)
            target_y = self.size_y - 1 - layer
            face_cubes = [i for i, cube in enumerate(self.cubes) if cube['grid_pos'][1] == target_y]
        elif face == 'D':  # Down face (Y = 0)
            target_y = layer
            face_cubes = [i for i, cube in enumerate(self.cubes) if cube['grid_pos'][1] == target_y]
        elif face == 'F':  # Front face (Z = max)
            target_z = self.size_z - 1 - layer
            face_cubes = [i for i, cube in enumerate(self.cubes) if cube['grid_pos'][2] == target_z]
        elif face == 'B':  # Back face (Z = 0)
            target_z = layer
            face_cubes = [i for i, cube in enumerate(self.cubes) if cube['grid_pos'][2] == target_z]
        
        return face_cubes

    def rotate_matrix_90(self, matrix):
        """Rotate a 2D matrix 90 degrees clockwise"""
        n = len(matrix)
        rotated = [[None for _ in range(n)] for _ in range(n)]
        for i in range(n):
            for j in range(n):
                rotated[j][n-1-i] = matrix[i][j]
        return rotated

    def apply_rotation(self, face, clockwise=True):
        """Apply a rotation to a face"""
        if self.is_animating:
            return False
        
        # Start animation
        self.is_animating = True
        self.animation_progress = 0.0
        self.current_rotation = {
            'face': face,
            'clockwise': clockwise,
            'cubes': self.get_face_cubes(face),
            'axis': self.get_rotation_axis(face)
        }
        self.animation_cubes = self.current_rotation['cubes'][:]
        
        return True

    def get_rotation_axis(self, face):
        """Get the rotation axis for a face"""
        axes = {
            'R': (1, 0, 0),  # X axis
            'L': (1, 0, 0),  # X axis
            'U': (0, 1, 0),  # Y axis
            'D': (0, 1, 0),  # Y axis
            'F': (0, 0, 1),  # Z axis
            'B': (0, 0, 1),  # Z axis
        }
        return axes.get(face, (1, 0, 0))

    def update_animation(self):
        """Update animation state"""
        if not self.is_animating:
            return
        
        self.animation_progress += self.animation_speed
        
        if self.animation_progress >= 1.0:
            # Animation complete - apply the actual rotation
            self.complete_rotation()
            self.is_animating = False
            self.animation_progress = 0.0
            self.current_rotation = None
            self.animation_cubes = []

    def complete_rotation(self):
        """Complete the rotation by updating cube positions and colors"""
        if not self.current_rotation:
            return
        
        face = self.current_rotation['face']
        clockwise = self.current_rotation['clockwise']
        cube_indices = self.current_rotation['cubes']
        
        # Get the affected cubes
        cubes_to_rotate = [self.cubes[i] for i in cube_indices]
        
        # Create position matrix for the face
        if face in ['R', 'L']:
            # X-face: use Y-Z coordinates
            size_1, size_2 = self.size_y, self.size_z
            get_coords = lambda cube: (cube['grid_pos'][1], cube['grid_pos'][2])
            set_coords = lambda cube, y, z: cube['grid_pos'].__setitem__(1, y) or cube['grid_pos'].__setitem__(2, z)
        elif face in ['U', 'D']:
            # Y-face: use X-Z coordinates
            size_1, size_2 = self.size_x, self.size_z
            get_coords = lambda cube: (cube['grid_pos'][0], cube['grid_pos'][2])
            set_coords = lambda cube, x, z: cube['grid_pos'].__setitem__(0, x) or cube['grid_pos'].__setitem__(2, z)
        else:  # F, B
            # Z-face: use X-Y coordinates
            size_1, size_2 = self.size_x, self.size_y
            get_coords = lambda cube: (cube['grid_pos'][0], cube['grid_pos'][1])
            set_coords = lambda cube, x, y: cube['grid_pos'].__setitem__(0, x) or cube['grid_pos'].__setitem__(1, y)
        
        # Create matrix of cube references
        matrix = [[None for _ in range(size_2)] for _ in range(size_1)]
        for cube in cubes_to_rotate:
            coord1, coord2 = get_coords(cube)
            matrix[coord1][coord2] = cube
        
        # Rotate the matrix
        if clockwise:
            rotated_matrix = self.rotate_matrix_90(matrix)
        else:
            # Rotate 3 times for counter-clockwise
            rotated_matrix = matrix
            for _ in range(3):
                rotated_matrix = self.rotate_matrix_90(rotated_matrix)
        
        # Update cube positions and grid coordinates
        spacing = self.cube_size + self.gap
        start_x = -(self.size_x - 1) * spacing / 2
        start_y = -(self.size_y - 1) * spacing / 2
        start_z = -(self.size_z - 1) * spacing / 2
        
        for i in range(size_1):
            for j in range(size_2):
                cube = rotated_matrix[i][j]
                if cube:
                    # Update grid position
                    if face in ['R', 'L']:
                        set_coords(cube, i, j)
                        cube['pos'][1] = start_y + i * spacing
                        cube['pos'][2] = start_z + j * spacing
                    elif face in ['U', 'D']:
                        set_coords(cube, i, j)
                        cube['pos'][0] = start_x + i * spacing
                        cube['pos'][2] = start_z + j * spacing
                    else:  # F, B
                        set_coords(cube, i, j)
                        cube['pos'][0] = start_x + i * spacing
                        cube['pos'][1] = start_y + j * spacing
        
        # Rotate colors on each cube
        for cube in cubes_to_rotate:
            self.rotate_cube_colors(cube, face, clockwise)

    def rotate_cube_colors(self, cube, face, clockwise):
        """Rotate the colors on a cube based on face rotation"""
        colors = cube['colors'][:]
        
        # Color rotation mappings for each face
        if face == 'R':
            if clockwise:
                # Front->Up->Back->Down->Front
                cube['colors'][3] = colors[5]  # Top <- Front
                cube['colors'][4] = colors[3]  # Back <- Top
                cube['colors'][2] = colors[4]  # Bottom <- Back
                cube['colors'][5] = colors[2]  # Front <- Bottom
            else:
                cube['colors'][5] = colors[3]  # Front <- Top
                cube['colors'][2] = colors[5]  # Bottom <- Front
                cube['colors'][4] = colors[2]  # Back <- Bottom
                cube['colors'][3] = colors[4]  # Top <- Back
        
        elif face == 'L':
            if clockwise:
                # Front->Down->Back->Up->Front
                cube['colors'][2] = colors[5]  # Bottom <- Front
                cube['colors'][4] = colors[2]  # Back <- Bottom
                cube['colors'][3] = colors[4]  # Top <- Back
                cube['colors'][5] = colors[3]  # Front <- Top
            else:
                cube['colors'][3] = colors[5]  # Top <- Front
                cube['colors'][4] = colors[3]  # Back <- Top
                cube['colors'][2] = colors[4]  # Bottom <- Back
                cube['colors'][5] = colors[2]  # Front <- Bottom
        
        elif face == 'U':
            if clockwise:
                # Front->Right->Back->Left->Front
                cube['colors'][1] = colors[5]  # Right <- Front
                cube['colors'][4] = colors[1]  # Back <- Right
                cube['colors'][0] = colors[4]  # Left <- Back
                cube['colors'][5] = colors[0]  # Front <- Left
            else:
                cube['colors'][0] = colors[5]  # Left <- Front
                cube['colors'][4] = colors[0]  # Back <- Left
                cube['colors'][1] = colors[4]  # Right <- Back
                cube['colors'][5] = colors[1]  # Front <- Right
        
        elif face == 'D':
            if clockwise:
                # Front->Left->Back->Right->Front
                cube['colors'][0] = colors[5]  # Left <- Front
                cube['colors'][4] = colors[0]  # Back <- Left
                cube['colors'][1] = colors[4]  # Right <- Back
                cube['colors'][5] = colors[1]  # Front <- Right
            else:
                cube['colors'][1] = colors[5]  # Right <- Front
                cube['colors'][4] = colors[1]  # Back <- Right
                cube['colors'][0] = colors[4]  # Left <- Back
                cube['colors'][5] = colors[0]  # Front <- Left
        
        elif face == 'F':
            if clockwise:
                # Top->Right->Bottom->Left->Top
                cube['colors'][1] = colors[3]  # Right <- Top
                cube['colors'][2] = colors[1]  # Bottom <- Right
                cube['colors'][0] = colors[2]  # Left <- Bottom
                cube['colors'][3] = colors[0]  # Top <- Left
            else:
                cube['colors'][0] = colors[3]  # Left <- Top
                cube['colors'][2] = colors[0]  # Bottom <- Left
                cube['colors'][1] = colors[2]  # Right <- Bottom
                cube['colors'][3] = colors[1]  # Top <- Right
        
        elif face == 'B':
            if clockwise:
                # Top->Left->Bottom->Right->Top
                cube['colors'][0] = colors[3]  # Left <- Top
                cube['colors'][2] = colors[0]  # Bottom <- Left
                cube['colors'][1] = colors[2]  # Right <- Bottom
                cube['colors'][3] = colors[1]  # Top <- Right
            else:
                cube['colors'][1] = colors[3]  # Right <- Top
                cube['colors'][2] = colors[1]  # Bottom <- Right
                cube['colors'][0] = colors[2]  # Left <- Bottom
                cube['colors'][3] = colors[0]  # Top <- Left

    def scramble(self):
        """Scramble the cube with random moves"""
        if self.is_animating:
            return "Please wait for current animation to finish"
        
        print("Scrambling cube...")
        self.solve_step = 0
        self.is_scrambled = True
        self.scramble_moves = []
        
        # Generate random moves
        faces = ['R', 'L', 'U', 'D', 'F', 'B']
        num_moves = min(20, max(10, (self.size_x + self.size_y + self.size_z) * 3))
        
        for _ in range(num_moves):
            face = random.choice(faces)
            clockwise = random.choice([True, False])
            self.scramble_moves.append((face, clockwise))
        
        # Generate solve sequence (reverse of scramble)
        self.solve_moves = []
        for face, clockwise in reversed(self.scramble_moves):
            self.solve_moves.append((face, not clockwise))
        
        print(f"Generated {len(self.scramble_moves)} scramble moves")
        return f"Scrambling with {len(self.scramble_moves)} moves..."

    def execute_scramble_moves(self):
        """Execute one scramble move if available"""
        if not self.is_scrambled or not self.scramble_moves or self.is_animating:
            return False
        
        face, clockwise = self.scramble_moves.pop(0)
        return self.apply_rotation(face, clockwise)

    def solve_one_step(self):
        """Make one move towards solving the cube"""
        if not self.is_scrambled:
            return "Scramble the cube first!"
        
        if self.is_animating:
            return "Please wait for current animation to finish"
        
        if not self.solve_moves:
            self.is_scrambled = False
            return "🎉 Cube is already solved!"
        
        face, clockwise = self.solve_moves.pop(0)
        if self.apply_rotation(face, clockwise):
            self.solve_step += 1
            remaining = len(self.solve_moves)
            
            if remaining == 0:
                self.is_scrambled = False
                return f"🎉 Cube solved in {self.solve_step} steps!"
            else:
                direction = "clockwise" if clockwise else "counter-clockwise"
                return f"Step {self.solve_step}: {face} {direction}, {remaining} moves remaining"
        
        return "Animation in progress..."

    def reset_to_solved(self):
        """Reset cube to solved state"""
        if self.is_animating:
            return "Please wait for current animation to finish"
        
        self.cubes = self.generate_solved_state()
        self.solve_step = 0
        self.is_scrambled = False
        self.scramble_moves = []
        self.solve_moves = []
        return "Cube reset to solved state!"

    def reset_view(self):
        """Reset camera view"""
        self.rotation_x = 20
        self.rotation_y = 45
        return "View reset!"

    def draw_cube_face(self, vertices, color):
        """Draw a single face of a cube"""
        if len(color) == 3:
            glColor3fv(color)
        else:
            glColor4fv(color)
        glBegin(GL_QUADS)
        for vertex in vertices:
            glVertex3fv(vertex)
        glEnd()

    def draw_single_cube(self, cube_data, animated_transform=None):
        """Draw one small cube with optional animation transform"""
        x, y, z = cube_data['pos']
        colors = cube_data['colors']
        s = self.cube_size / 2
        
        glPushMatrix()
        
        # Apply animation transform if provided
        if animated_transform:
            axis, angle = animated_transform
            glTranslatef(x, y, z)
            glRotatef(angle, *axis)
            glTranslatef(-x, -y, -z)
        
        # Define all 8 vertices of the cube
        vertices = [
            [x-s, y-s, z-s],  # 0: left-bottom-back
            [x+s, y-s, z-s],  # 1: right-bottom-back
            [x+s, y+s, z-s],  # 2: right-top-back
            [x-s, y+s, z-s],  # 3: left-top-back
            [x-s, y-s, z+s],  # 4: left-bottom-front
            [x+s, y-s, z+s],  # 5: right-bottom-front
            [x+s, y+s, z+s],  # 6: right-top-front
            [x-s, y+s, z+s],  # 7: left-top-front
        ]
        
        # Define faces in order: [left, right, bottom, top, back, front]
        faces = [
            [vertices[0], vertices[3], vertices[7], vertices[4]],  # left
            [vertices[1], vertices[5], vertices[6], vertices[2]],  # right
            [vertices[0], vertices[4], vertices[5], vertices[1]],  # bottom
            [vertices[3], vertices[2], vertices[6], vertices[7]],  # top
            [vertices[0], vertices[1], vertices[2], vertices[3]],  # back
            [vertices[4], vertices[7], vertices[6], vertices[5]],  # front
        ]
        
        # Draw faces
        for i, face_vertices in enumerate(faces):
            color_idx = colors[i]
            if color_idx >= 0:  # Visible colored face
                self.draw_cube_face(face_vertices, self.colors[color_idx])
            else:  # Interior face
                self.draw_cube_face(face_vertices, [0.3, 0.3, 0.3])
        
        # Draw wireframe
        glColor3f(0.0, 0.0, 0.0)
        glLineWidth(1.0)
        edges = [
            [0,1], [1,2], [2,3], [3,0],  # back face
            [4,5], [5,6], [6,7], [7,4],  # front face
            [0,4], [1,5], [2,6], [3,7]   # connecting edges
        ]
        
        glBegin(GL_LINES)
        for edge in edges:
            glVertex3fv(vertices[edge[0]])
            glVertex3fv(vertices[edge[1]])
        glEnd()
        
        glPopMatrix()

    def draw(self):
        """Draw the entire cube"""
        # Update animation
        self.update_animation()
        
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Calculate camera distance
        max_size = max(self.size_x, self.size_y, self.size_z)
        camera_distance = max_size * 3
        
        # Position and rotate
        glTranslatef(0.0, 0.0, -camera_distance)
        glRotatef(self.rotation_x, 1, 0, 0)
        glRotatef(self.rotation_y, 0, 1, 0)
        
        # Calculate animation transform
        animated_transform = None
        if self.is_animating and self.current_rotation:
            axis = self.current_rotation['axis']
            angle = self.animation_progress * 90
            if not self.current_rotation['clockwise']:
                angle = -angle
            # Adjust direction for different faces
            face = self.current_rotation['face']
            if face in ['L', 'D', 'B']:
                angle = -angle
            animated_transform = (axis, angle)
        
        # Draw all cubes
        for i, cube in enumerate(self.cubes):
            # Apply animation to rotating cubes
            if self.is_animating and i in self.animation_cubes:
                self.draw_single_cube(cube, animated_transform)
            else:
                self.draw_single_cube(cube)

class ControlPanel:
    def __init__(self, cube, command_queue):
        self.cube = cube
        self.command_queue = command_queue
        self.root = None
        self.status_var = None
        self.scramble_progress = 0
        
    def create_panel(self):
        """Create the persistent control panel"""
        self.root = tk.Tk()
        self.root.title("Rubik's Cube Controls")
        self.root.geometry("320x550")
        self.root.resizable(False, False)
        
        # Position window on the right side of screen
        self.root.geometry("+1050+100")
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="🎲 Rubik's Cube", 
                               font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Cube info
        info_text = f"{self.cube.size_x}×{self.cube.size_y}×{self.cube.size_z} Cube"
        info_label = ttk.Label(main_frame, text=info_text, font=('Arial', 10))
        info_label.grid(row=1, column=0, columnspan=2, pady=(0, 15))
        
        # Status display
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="5")
        status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_var = tk.StringVar(value="Ready! Click 'Scramble' to start.")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                wraplength=280, justify=tk.LEFT)
        status_label.grid(row=0, column=0, sticky=tk.W)
        
        # New cube section
        new_cube_frame = ttk.LabelFrame(main_frame, text="New Cube", padding="10")
        new_cube_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Dimensions
        ttk.Label(new_cube_frame, text="Dimensions:").grid(row=0, column=0, sticky=tk.W, pady=2)
        dim_frame = ttk.Frame(new_cube_frame)
        dim_frame.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        self.x_var = tk.StringVar(value=str(self.cube.size_x))
        self.y_var = tk.StringVar(value=str(self.cube.size_y))
        self.z_var = tk.StringVar(value=str(self.cube.size_z))
        
        ttk.Entry(dim_frame, textvariable=self.x_var, width=3).grid(row=0, column=0, padx=2)
        ttk.Label(dim_frame, text="×").grid(row=0, column=1)
        ttk.Entry(dim_frame, textvariable=self.y_var, width=3).grid(row=0, column=2, padx=2)
        ttk.Label(dim_frame, text="×").grid(row=0, column=3)
        ttk.Entry(dim_frame, textvariable=self.z_var, width=3).grid(row=0, column=4, padx=2)
        
        ttk.Button(new_cube_frame, text="🆕 Create New Cube", 
                  command=self.create_new_cube).grid(row=2, column=0, pady=(5, 0))
        
        # Control buttons
        controls_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        controls_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(controls_frame, text="🔀 Scramble", 
                  command=self.scramble_cube).grid(row=0, column=0, columnspan=2, 
                                                   sticky=(tk.W, tk.E), pady=2)
        
        ttk.Button(controls_frame, text="⚡ Solve Step (SPACE)", 
                  command=self.solve_step).grid(row=1, column=0, columnspan=2, 
                                               sticky=(tk.W, tk.E), pady=2)
        
        ttk.Button(controls_frame, text="🔄 Reset View", 
                  command=self.reset_view).grid(row=2, column=0, padx=(0, 2), 
                                              sticky=(tk.W, tk.E), pady=2)
        
        ttk.Button(controls_frame, text="✅ Solve All", 
                  command=self.solve_all).grid(row=2, column=1, padx=(2, 0), 
                                             sticky=(tk.W, tk.E), pady=2)
        
        # Configure column weights
        controls_frame.columnconfigure(0, weight=1)
        controls_frame.columnconfigure(1, weight=1)
        
        # Instructions
        inst_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        inst_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        instructions = [
            "🖱️ Mouse: Drag to rotate view",
            "⏎ SPACE: One solving step", 
            "🔀 S: Start scrambling",
            "🔄 R: Reset camera view",
            "❌ ESC: Quit"
        ]
        
        for i, instruction in enumerate(instructions):
            ttk.Label(inst_frame, text=instruction, font=('Arial', 9)).grid(row=i, column=0, 
                                                                            sticky=tk.W, pady=1)
        
        # Animation info
        anim_frame = ttk.LabelFrame(main_frame, text="Animation", padding="10")
        anim_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        ttk.Label(anim_frame, text="• Real cube face rotations", font=('Arial', 9)).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(anim_frame, text="• Smooth 90° turns", font=('Arial', 9)).grid(row=1, column=0, sticky=tk.W)
        ttk.Label(anim_frame, text="• Authentic solving sequence", font=('Arial', 9)).grid(row=2, column=0, sticky=tk.W)
        
        # Start the update loop
        self.update_status()
        
    def create_new_cube(self):
        """Create a new cube with specified dimensions"""
        try:
            x = int(self.x_var.get())
            y = int(self.y_var.get())
            z = int(self.z_var.get())
            if x <= 0 or y <= 0 or z <= 0 or x > 8 or y > 8 or z > 8:
                messagebox.showerror("Error", "Dimensions must be between 1 and 8!")
                return
            self.command_queue.put(('new_cube', (x, y, z)))
            self.status_var.set(f"Creating new {x}×{y}×{z} cube...")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers!")
    
    def scramble_cube(self):
        self.command_queue.put(('scramble', None))
    
    def solve_step(self):
        self.command_queue.put(('solve_step', None))
    
    def reset_view(self):
        self.command_queue.put(('reset_view', None))
    
    def solve_all(self):
        self.command_queue.put(('solve_all', None))
    
    def update_status(self):
        """Update status from command queue"""
        try:
            while True:
                try:
                    status_msg = self.command_queue.get_nowait()
                    if isinstance(status_msg, str):
                        self.status_var.set(status_msg)
                except queue.Empty:
                    break
        except:
            pass
        
        if self.root:
            self.root.after(100, self.update_status)
    
    def run(self):
        """Run the control panel"""
        self.create_panel()
        self.root.mainloop()

def run_control_panel(cube, command_queue, status_queue):
    """Run the control panel in a separate thread"""
    panel = ControlPanel(cube, command_queue)
    # Set up bidirectional communication
    panel.command_queue = command_queue
    panel.status_queue = status_queue
    panel.run()

def main():
    # Start with default 3x3x3 cube
    size_x, size_y, size_z = 3, 3, 3
    
    print(f"Starting {size_x}x{size_y}x{size_z} Rubik's cube with real rotations...")
    
    # Initialize Pygame
    pygame.init()
    
    # Set up display
    width, height = 1000, 800
    screen = pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
    pygame.display.set_caption(f"3D Rubik's Cube ({size_x}x{size_y}x{size_z}) - Animated Rotations")
    
    # Set up OpenGL
    glEnable(GL_DEPTH_TEST)
    glClearColor(0.2, 0.2, 0.2, 1.0)
    
    # Set up perspective
    glMatrixMode(GL_PROJECTION)
    gluPerspective(60, width/height, 1, 100)
    glMatrixMode(GL_MODELVIEW)
    
    # Create the cube
    cube = RubiksCube(size_x, size_y, size_z)
    
    # Set up communication queues
    command_queue = queue.Queue()
    status_queue = queue.Queue()
    
    # Start control panel in separate thread
    panel_thread = threading.Thread(target=run_control_panel, 
                                   args=(cube, command_queue, status_queue), 
                                   daemon=True)
    panel_thread.start()
    
    # Control variables
    mouse_down = False
    last_mouse_pos = [0, 0]
    clock = pygame.time.Clock()
    
    # Auto-scramble progress
    auto_scramble_timer = 0
    
    print("🎲 Cube ready with animated rotations!")
    print("Features:")
    print("• Real Rubik's cube face rotations")  
    print("• Smooth 90-degree animated turns")
    print("• Authentic solve sequence (reverse of scramble)")
    print("• Use SPACE to solve step by step!")
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0  # Delta time in seconds
        
        # Auto-execute scramble moves
        if cube.is_scrambled and cube.scramble_moves and not cube.is_animating:
            auto_scramble_timer += dt
            if auto_scramble_timer >= 0.5:  # Execute move every 0.5 seconds
                if cube.execute_scramble_moves():
                    remaining = len(cube.scramble_moves)
                    if remaining > 0:
                        status_queue.put(f"Scrambling... {remaining} moves remaining")
                    else:
                        status_queue.put("Scramble complete! Press SPACE to solve step by step.")
                auto_scramble_timer = 0
        
        # Process commands from control panel
        try:
            while True:
                try:
                    command, data = command_queue.get_nowait()
                    if command == 'scramble':
                        result = cube.scramble()
                        status_queue.put(result)
                        auto_scramble_timer = 0
                    elif command == 'solve_step':
                        result = cube.solve_one_step()
                        status_queue.put(result)
                    elif command == 'reset_view':
                        result = cube.reset_view()
                        status_queue.put(result)
                    elif command == 'solve_all':
                        result = cube.reset_to_solved()
                        status_queue.put(result)
                    elif command == 'new_cube':
                        new_x, new_y, new_z = data
                        cube = RubiksCube(new_x, new_y, new_z)
                        pygame.display.set_caption(f"3D Rubik's Cube ({new_x}x{new_y}x{new_z}) - Animated Rotations")
                        status_queue.put(f"New {new_x}×{new_y}×{new_z} cube created!")
                except queue.Empty:
                    break
        except:
            pass
        
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE or event.key == K_q:
                    running = False
                elif event.key == K_SPACE:
                    result = cube.solve_one_step()
                    status_queue.put(result)
                elif event.key == K_s:
                    result = cube.scramble()
                    status_queue.put(result)
                    auto_scramble_timer = 0
                elif event.key == K_r:
                    result = cube.reset_view()
                    status_queue.put(result)
                # Manual face rotations for testing
                elif event.key == K_1:
                    cube.apply_rotation('R', True)
                elif event.key == K_2:
                    cube.apply_rotation('L', True)
                elif event.key == K_3:
                    cube.apply_rotation('U', True)
                elif event.key == K_4:
                    cube.apply_rotation('D', True)
                elif event.key == K_5:
                    cube.apply_rotation('F', True)
                elif event.key == K_6:
                    cube.apply_rotation('B', True)
                elif event.key == K_LEFT:
                    cube.rotation_y -= 5
                elif event.key == K_RIGHT:
                    cube.rotation_y += 5
                elif event.key == K_UP:
                    cube.rotation_x -= 5
                elif event.key == K_DOWN:
                    cube.rotation_x += 5
            
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_down = True
                    last_mouse_pos = pygame.mouse.get_pos()
            
            elif event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    mouse_down = False
            
            elif event.type == MOUSEMOTION:
                if mouse_down:
                    mouse_pos = pygame.mouse.get_pos()
                    dx = mouse_pos[0] - last_mouse_pos[0]
                    dy = mouse_pos[1] - last_mouse_pos[1]
                    
                    cube.rotation_y += dx * 0.3
                    cube.rotation_x += dy * 0.3
                    
                    last_mouse_pos = mouse_pos
        
        # Draw everything
        cube.draw()
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
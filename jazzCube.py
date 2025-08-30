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
import numpy as np

class RubiksCube:
    def __init__(self, size):
        self.size = size
        self.rotation_x = 20
        self.rotation_y = 45
        self.cube_size = 1.0
        self.gap = 0.1
        self.solve_step = 0
        
        # Animation variables
        self.is_animating = False
        self.animation_progress = 0.0
        self.animation_speed = 0.08  # Slower for smoother animation
        self.current_rotation = None
        
        # Color scheme - standard Rubik's cube colors
        self.colors = [
            [1.0, 1.0, 1.0],  # White - Front (positive Z)
            [1.0, 1.0, 0.0],  # Yellow - Back (negative Z)  
            [0.0, 1.0, 0.0],  # Green - Right (positive X)
            [0.0, 0.0, 1.0],  # Blue - Left (negative X)
            [1.0, 0.0, 0.0],  # Red - Top (positive Y)
            [1.0, 0.5, 0.0],  # Orange - Bottom (negative Y)
        ]
        
        # Initialize cube state - only store colors for visible faces
        self.reset_cube()
        self.move_history = []
        
        print(f"Created {size}x{size}x{size} cube with optimized rendering")

    def reset_cube(self):
        """Reset cube to solved state"""
        self.cube_state = {}
        
        # Only create cubes that have at least one visible face (on the exterior)
        for x in range(self.size):
            for y in range(self.size):
                for z in range(self.size):
                    # Only create cube if it's on the exterior
                    if (x == 0 or x == self.size-1 or 
                        y == 0 or y == self.size-1 or 
                        z == 0 or z == self.size-1):
                        
                        # Determine visible faces and their solved colors
                        faces = {}
                        if z == self.size-1: faces['front'] = 0   # White
                        if z == 0: faces['back'] = 1              # Yellow
                        if x == self.size-1: faces['right'] = 2   # Green
                        if x == 0: faces['left'] = 3              # Blue
                        if y == self.size-1: faces['top'] = 4     # Red
                        if y == 0: faces['bottom'] = 5            # Orange
                        
                        self.cube_state[(x, y, z)] = faces
        
        self.move_history = []
        self.is_scrambled = False
        print(f"Reset complete - tracking {len(self.cube_state)} exterior cubes")

    def get_face_positions(self, face, layer=0):
        """Get positions of cubes in a specific face/slice"""
        positions = []
        
        if face == 'R':  # Right face
            x = self.size - 1 - layer
            positions = [(x, y, z) for y in range(self.size) for z in range(self.size) 
                        if (x, y, z) in self.cube_state]
        elif face == 'L':  # Left face
            x = layer
            positions = [(x, y, z) for y in range(self.size) for z in range(self.size) 
                        if (x, y, z) in self.cube_state]
        elif face == 'U':  # Up face
            y = self.size - 1 - layer
            positions = [(x, y, z) for x in range(self.size) for z in range(self.size) 
                        if (x, y, z) in self.cube_state]
        elif face == 'D':  # Down face
            y = layer
            positions = [(x, y, z) for x in range(self.size) for z in range(self.size) 
                        if (x, y, z) in self.cube_state]
        elif face == 'F':  # Front face
            z = self.size - 1 - layer
            positions = [(x, y, z) for x in range(self.size) for y in range(self.size) 
                        if (x, y, z) in self.cube_state]
        elif face == 'B':  # Back face
            z = layer
            positions = [(x, y, z) for x in range(self.size) for y in range(self.size) 
                        if (x, y, z) in self.cube_state]
        
        return positions

    def rotate_face_positions(self, positions, face, clockwise=True):
        """Rotate the positions of cubes in a face"""
        if not positions:
            return {}
        
        # Group positions by their layer coordinate
        if face in ['R', 'L']:
            # X-axis rotation: rotate in YZ plane
            fixed_x = positions[0][0]
            coords = [(pos[1], pos[2]) for pos in positions]
            new_coords = self.rotate_2d_coords(coords, clockwise ^ (face == 'L'))
            new_positions = [(fixed_x, ny, nz) for ny, nz in new_coords]
        elif face in ['U', 'D']:
            # Y-axis rotation: rotate in XZ plane
            fixed_y = positions[0][1]
            coords = [(pos[0], pos[2]) for pos in positions]
            new_coords = self.rotate_2d_coords(coords, clockwise ^ (face == 'D'))
            new_positions = [(nx, fixed_y, nz) for nx, nz in new_coords]
        else:  # F, B
            # Z-axis rotation: rotate in XY plane
            fixed_z = positions[0][2]
            coords = [(pos[0], pos[1]) for pos in positions]
            new_coords = self.rotate_2d_coords(coords, clockwise ^ (face == 'B'))
            new_positions = [(nx, ny, fixed_z) for nx, ny in new_coords]
        
        # Create mapping from old to new positions
        position_mapping = {}
        for i, old_pos in enumerate(positions):
            position_mapping[old_pos] = new_positions[i]
        
        return position_mapping

    def rotate_2d_coords(self, coords, clockwise=True):
        """Rotate 2D coordinates 90 degrees around center"""
        if not coords:
            return []
        
        # Find center
        min_coord = min(coords)
        max_coord = max(coords)
        center = ((min_coord[0] + max_coord[0]) / 2, (min_coord[1] + max_coord[1]) / 2)
        
        rotated = []
        for x, y in coords:
            # Translate to origin
            tx, ty = x - center[0], y - center[1]
            # Rotate 90 degrees
            if clockwise:
                nx, ny = ty, -tx
            else:
                nx, ny = -ty, tx
            # Translate back
            rotated.append((nx + center[0], ny + center[1]))
        
        # Convert back to integers
        return [(round(x), round(y)) for x, y in rotated]

    def rotate_cube_colors(self, old_faces, face, clockwise=True):
        """Rotate colors on a cube when its position changes"""
        if not old_faces:
            return {}
        
        new_faces = old_faces.copy()
        
        # Rotate the face colors based on which face is being turned
        if face in ['R', 'L']:
            # X-axis rotation affects front, back, top, bottom faces
            cycle = ['front', 'top', 'back', 'bottom']
        elif face in ['U', 'D']:
            # Y-axis rotation affects front, right, back, left faces
            cycle = ['front', 'right', 'back', 'left']
        else:  # F, B
            # Z-axis rotation affects top, right, bottom, left faces
            cycle = ['top', 'right', 'bottom', 'left']
        
        # Apply rotation direction
        if not clockwise ^ (face in ['L', 'D', 'B']):
            cycle.reverse()
        
        # Rotate colors in the cycle
        if all(c in old_faces for c in cycle):
            temp = old_faces[cycle[0]]
            for i in range(len(cycle) - 1):
                if cycle[i+1] in old_faces:
                    new_faces[cycle[i]] = old_faces[cycle[i+1]]
            new_faces[cycle[-1]] = temp
        
        return new_faces

    def apply_rotation(self, face, layer=0, clockwise=True):
        """Apply a rotation to a face/slice"""
        if self.is_animating:
            return False
        
        # Get affected positions
        positions = self.get_face_positions(face, layer)
        if not positions:
            return False
        
        # Start animation
        self.is_animating = True
        self.animation_progress = 0.0
        self.current_rotation = {
            'face': face,
            'layer': layer,
            'clockwise': clockwise,
            'positions': positions,
            'axis': self.get_rotation_axis(face)
        }
        
        return True

    def get_rotation_axis(self, face):
        """Get rotation axis for a face"""
        axes = {
            'R': (1, 0, 0), 'L': (-1, 0, 0),
            'U': (0, 1, 0), 'D': (0, -1, 0),
            'F': (0, 0, 1), 'B': (0, 0, -1)
        }
        return axes.get(face, (1, 0, 0))

    def update_animation(self):
        """Update animation progress"""
        if not self.is_animating:
            return
        
        self.animation_progress += self.animation_speed
        
        if self.animation_progress >= 1.0:
            self.complete_rotation()
            self.is_animating = False

    def complete_rotation(self):
        """Complete the rotation by updating cube state"""
        if not self.current_rotation:
            return
        
        face = self.current_rotation['face']
        layer = self.current_rotation['layer']
        clockwise = self.current_rotation['clockwise']
        positions = self.current_rotation['positions']
        
        # Get new position mapping
        position_mapping = self.rotate_face_positions(positions, face, clockwise)
        
        # Create new cube state
        new_state = {}
        
        # Copy non-rotating cubes
        for pos, faces in self.cube_state.items():
            if pos not in positions:
                new_state[pos] = faces.copy()
        
        # Move and rotate the affected cubes
        for old_pos in positions:
            new_pos = position_mapping[old_pos]
            old_faces = self.cube_state[old_pos]
            new_faces = self.rotate_cube_colors(old_faces, face, clockwise)
            new_state[new_pos] = new_faces
        
        self.cube_state = new_state
        self.move_history.append((face, layer, clockwise))
        
        # Clear animation state
        self.current_rotation = None
        self.animation_progress = 0.0

    def scramble(self, num_moves=None):
        """Scramble the cube"""
        if self.is_animating:
            return "Animation in progress..."
        
        if num_moves is None:
            num_moves = max(20, self.size * 10)
        
        self.scramble_moves = []
        faces = ['R', 'L', 'U', 'D', 'F', 'B']
        
        for _ in range(num_moves):
            face = random.choice(faces)
            layer = random.randint(0, self.size - 1) if self.size > 3 else 0
            clockwise = random.choice([True, False])
            self.scramble_moves.append((face, layer, clockwise))
        
        self.is_scrambled = True
        return f"Generated {num_moves} scramble moves"

    def execute_next_scramble(self):
        """Execute next scramble move"""
        if not hasattr(self, 'scramble_moves') or not self.scramble_moves:
            return False
        
        if self.is_animating:
            return False
        
        face, layer, clockwise = self.scramble_moves.pop(0)
        return self.apply_rotation(face, layer, clockwise)

    def solve_step(self):
        """Perform one step of solving (reverse last move)"""
        if self.is_animating:
            return "Animation in progress..."
        
        if not self.move_history:
            return "Cube is already solved!"
        
        # Reverse the last move
        face, layer, clockwise = self.move_history.pop()
        if self.apply_rotation(face, layer, not clockwise):
            return f"Undid {face} move - {len(self.move_history)} moves remaining"
        
        return "Failed to apply move"

    def get_world_position(self, grid_pos):
        """Convert grid position to world coordinates"""
        x, y, z = grid_pos
        spacing = self.cube_size + self.gap
        world_x = (x - (self.size - 1) / 2) * spacing
        world_y = (y - (self.size - 1) / 2) * spacing
        world_z = (z - (self.size - 1) / 2) * spacing
        return [world_x, world_y, world_z]

    def draw_cube_face(self, vertices, color):
        """Draw a single face of a cube"""
        glColor3fv(color)
        glBegin(GL_QUADS)
        for vertex in vertices:
            glVertex3fv(vertex)
        glEnd()

    def draw_single_cube(self, position, faces):
        """Draw a single cube at given position"""
        world_pos = self.get_world_position(position)
        x, y, z = world_pos
        s = self.cube_size / 2
        
        # Apply animation rotation if this cube is being rotated
        glPushMatrix()
        
        if self.is_animating and position in self.current_rotation['positions']:
            # Rotate around face center
            face = self.current_rotation['face']
            axis = self.current_rotation['axis']
            angle = self.animation_progress * 90
            if not self.current_rotation['clockwise']:
                angle = -angle
            
            # Calculate rotation center
            if face in ['R', 'L']:
                center_x = (self.current_rotation['layer'] - (self.size-1)/2) * (self.cube_size + self.gap)
                glTranslatef(center_x, 0, 0)
                glRotatef(angle, *axis)
                glTranslatef(-center_x, 0, 0)
            elif face in ['U', 'D']:
                center_y = (self.current_rotation['layer'] - (self.size-1)/2) * (self.cube_size + self.gap)
                glTranslatef(0, center_y, 0)
                glRotatef(angle, *axis)
                glTranslatef(0, -center_y, 0)
            else:  # F, B
                center_z = (self.current_rotation['layer'] - (self.size-1)/2) * (self.cube_size + self.gap)
                glTranslatef(0, 0, center_z)
                glRotatef(angle, *axis)
                glTranslatef(0, 0, -center_z)
        
        # Cube vertices
        vertices = [
            [x-s, y-s, z-s], [x+s, y-s, z-s], [x+s, y+s, z-s], [x-s, y+s, z-s],  # back
            [x-s, y-s, z+s], [x+s, y-s, z+s], [x+s, y+s, z+s], [x-s, y+s, z+s],  # front
        ]
        
        # Face definitions
        face_vertices = {
            'front':  [vertices[4], vertices[7], vertices[6], vertices[5]],
            'back':   [vertices[1], vertices[0], vertices[3], vertices[2]],
            'right':  [vertices[5], vertices[6], vertices[2], vertices[1]],
            'left':   [vertices[0], vertices[4], vertices[7], vertices[3]],
            'top':    [vertices[3], vertices[7], vertices[6], vertices[2]],
            'bottom': [vertices[0], vertices[1], vertices[5], vertices[4]],
        }
        
        # Draw visible faces
        for face_name, color_idx in faces.items():
            if face_name in face_vertices:
                face_verts = face_vertices[face_name]
                color = self.colors[color_idx]
                self.draw_cube_face(face_verts, color)
        
        # Draw wireframe
        glColor3f(0.0, 0.0, 0.0)
        glLineWidth(1.5)
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
        self.update_animation()
        
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Camera positioning
        camera_distance = self.size * 4
        glTranslatef(0.0, 0.0, -camera_distance)
        glRotatef(self.rotation_x, 1, 0, 0)
        glRotatef(self.rotation_y, 0, 1, 0)
        
        # Draw only exterior cubes
        for position, faces in self.cube_state.items():
            self.draw_single_cube(position, faces)

class ControlPanel:
    def __init__(self, cube, command_queue):
        self.cube = cube
        self.command_queue = command_queue
        self.root = None
        self.status_var = None
        
    def create_panel(self):
        """Create the control panel"""
        self.root = tk.Tk()
        self.root.title("Rubik's Cube Controls")
        self.root.geometry("350x600")
        self.root.resizable(False, False)
        
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="🎲 Rubik's Cube", 
                               font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Cube info
        info_text = f"{self.cube.size}×{self.cube.size}×{self.cube.size} Cube"
        info_label = ttk.Label(main_frame, text=info_text, font=('Arial', 10))
        info_label.grid(row=1, column=0, columnspan=2, pady=(0, 15))
        
        # Status
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="5")
        status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_var = tk.StringVar(value="Ready! Optimized for larger cubes.")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                wraplength=300, justify=tk.LEFT)
        status_label.grid(row=0, column=0, sticky=tk.W)
        
        # New cube section
        new_cube_frame = ttk.LabelFrame(main_frame, text="New Cube", padding="10")
        new_cube_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(new_cube_frame, text="Size (1-15):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.size_var = tk.StringVar(value=str(self.cube.size))
        size_entry = ttk.Entry(new_cube_frame, textvariable=self.size_var, width=5)
        size_entry.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        ttk.Button(new_cube_frame, text="🆕 Create New Cube", 
                  command=self.create_new_cube).grid(row=1, column=0, columnspan=2, pady=(5, 0))
        
        # Controls
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
        
        ttk.Button(controls_frame, text="✅ Reset Cube", 
                  command=self.reset_cube).grid(row=2, column=1, padx=(2, 0), 
                                               sticky=(tk.W, tk.E), pady=2)
        
        controls_frame.columnconfigure(0, weight=1)
        controls_frame.columnconfigure(1, weight=1)
        
        # Manual rotations
        manual_frame = ttk.LabelFrame(main_frame, text="Manual Rotations", padding="10")
        manual_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        faces = [('R', 'Right'), ('L', 'Left'), ('U', 'Up'), ('D', 'Down'), ('F', 'Front'), ('B', 'Back')]
        for i, (face, name) in enumerate(faces):
            row = i // 2
            col = i % 2
            ttk.Button(manual_frame, text=f"{face} - {name}", 
                      command=lambda f=face: self.manual_rotation(f)).grid(
                          row=row, column=col, padx=2, pady=2, sticky=(tk.W, tk.E))
        
        manual_frame.columnconfigure(0, weight=1)
        manual_frame.columnconfigure(1, weight=1)
        
        # Instructions
        inst_frame = ttk.LabelFrame(main_frame, text="Instructions", padding="10")
        inst_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        instructions = [
            "🖱️ Mouse: Drag to rotate view",
            "⎵ SPACE: Undo last move", 
            "🔀 S: Start scrambling",
            "🔄 R: Reset camera view",
            "⌨️ 1-6: Manual face rotations",
            "⌨️ Hold SHIFT for counter-clockwise",
            "⌨ ESC: Quit"
        ]
        
        for i, instruction in enumerate(instructions):
            ttk.Label(inst_frame, text=instruction, font=('Arial', 8)).grid(row=i, column=0, 
                                                                            sticky=tk.W, pady=1)
        
        self.update_status()
        
    def create_new_cube(self):
        try:
            size = int(self.size_var.get())
            if size < 1 or size > 15:
                messagebox.showerror("Error", "Size must be between 1 and 15!")
                return
            self.command_queue.put(('new_cube', size))
            self.status_var.set(f"Creating new {size}×{size}×{size} cube...")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number!")
    
    def scramble_cube(self):
        self.command_queue.put(('scramble', None))
    
    def solve_step(self):
        self.command_queue.put(('solve_step', None))
    
    def reset_view(self):
        self.command_queue.put(('reset_view', None))
    
    def reset_cube(self):
        self.command_queue.put(('reset_cube', None))
    
    def manual_rotation(self, face):
        self.command_queue.put(('manual_rotation', face))
    
    def update_status(self):
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
        self.create_panel()
        self.root.mainloop()

def main():
    size = 3  # Start with 3x3x3
    
    print(f"Starting {size}×{size}×{size} Rubik's cube with face rotations...")
    
    pygame.init()
    
    width, height = 1000, 800
    screen = pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
    pygame.display.set_caption(f"3D Rubik's Cube ({size}×{size}×{size}) - Face Rotations")
    
    # OpenGL setup
    glEnable(GL_DEPTH_TEST)
    glClearColor(0.2, 0.2, 0.2, 1.0)
    
    glMatrixMode(GL_PROJECTION)
    gluPerspective(60, width/height, 1, 100)
    glMatrixMode(GL_MODELVIEW)
    
    cube = RubiksCube(size)
    
    # Communication queues
    command_queue = queue.Queue()
    status_queue = queue.Queue()
    
    # Control panel thread
    panel_thread = threading.Thread(target=lambda: ControlPanel(cube, command_queue).run(), daemon=True)
    panel_thread.start()
    
    # Control variables
    mouse_down = False
    last_mouse_pos = [0, 0]
    clock = pygame.time.Clock()
    keys_pressed = set()
    
    # Auto-scramble variables
    auto_scramble_timer = 0
    scramble_delay = 0.3  # seconds between moves
    
    print("🎲 Enhanced Rubik's Cube Features:")
    print("✅ Proper face/slice rotations")
    print("✅ Only exterior cubes rendered") 
    print("✅ Support for larger cubes (up to 15×15×15)")
    print("✅ Undo-based solving")
    print("✅ Smooth animations")
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        
        # Auto-execute scramble moves
        if hasattr(cube, 'is_scrambled') and cube.is_scrambled and hasattr(cube, 'scramble_moves'):
            if cube.scramble_moves and not cube.is_animating:
                auto_scramble_timer += dt
                if auto_scramble_timer >= scramble_delay:
                    if cube.execute_next_scramble():
                        remaining = len(cube.scramble_moves)
                        if remaining > 0:
                            status_queue.put(f"Scrambling... {remaining} moves left")
                        else:
                            status_queue.put("Scramble complete! Use SPACE to solve step by step.")
                            cube.is_scrambled = False
                    auto_scramble_timer = 0
        
        # Process commands
        try:
            while True:
                try:
                    command, data = command_queue.get_nowait()
                    if command == 'scramble':
                        result = cube.scramble()
                        status_queue.put(result)
                        auto_scramble_timer = 0
                    elif command == 'solve_step':
                        result = cube.solve_step()
                        status_queue.put(result)
                    elif command == 'reset_view':
                        cube.rotation_x = 20
                        cube.rotation_y = 45
                        status_queue.put("View reset!")
                    elif command == 'reset_cube':
                        cube.reset_cube()
                        status_queue.put("Cube reset to solved state!")
                    elif command == 'new_cube':
                        cube = RubiksCube(data)
                        pygame.display.set_caption(f"3D Rubik's Cube ({data}×{data}×{data}) - Face Rotations")
                        status_queue.put(f"New {data}×{data}×{data} cube created!")
                    elif command == 'manual_rotation':
                        if cube.apply_rotation(data):
                            status_queue.put(f"Applied {data} rotation")
                        else:
                            status_queue.put("Wait for animation to finish")
                except queue.Empty:
                    break
        except:
            pass
        
        # Send status updates to control panel
        try:
            while not status_queue.empty():
                msg = status_queue.get_nowait()
                command_queue.put(msg)
        except:
            pass
        
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            
            elif event.type == KEYDOWN:
                keys_pressed.add(event.key)
                
                if event.key == K_ESCAPE or event.key == K_q:
                    running = False
                elif event.key == K_SPACE:
                    result = cube.solve_step()
                    status_queue.put(result)
                elif event.key == K_s:
                    result = cube.scramble()
                    status_queue.put(result)
                    auto_scramble_timer = 0
                elif event.key == K_r:
                    cube.rotation_x = 20
                    cube.rotation_y = 45
                    status_queue.put("View reset!")
                
                # Manual face rotations with shift for counter-clockwise
                shift_pressed = K_LSHIFT in keys_pressed or K_RSHIFT in keys_pressed
                clockwise = not shift_pressed
                
                if event.key == K_1:  # R face
                    cube.apply_rotation('R', 0, clockwise)
                elif event.key == K_2:  # L face
                    cube.apply_rotation('L', 0, clockwise)
                elif event.key == K_3:  # U face
                    cube.apply_rotation('U', 0, clockwise)
                elif event.key == K_4:  # D face
                    cube.apply_rotation('D', 0, clockwise)
                elif event.key == K_5:  # F face
                    cube.apply_rotation('F', 0, clockwise)
                elif event.key == K_6:  # B face
                    cube.apply_rotation('B', 0, clockwise)
                
                # Arrow keys for camera
                elif event.key == K_LEFT:
                    cube.rotation_y -= 5
                elif event.key == K_RIGHT:
                    cube.rotation_y += 5
                elif event.key == K_UP:
                    cube.rotation_x -= 5
                elif event.key == K_DOWN:
                    cube.rotation_x += 5
            
            elif event.type == KEYUP:
                keys_pressed.discard(event.key)
            
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
        
        cube.draw()
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
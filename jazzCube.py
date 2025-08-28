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
        
        # Bright colors for each face
        self.colors = [
            [1.0, 0.0, 0.0],  # Red
            [0.0, 1.0, 0.0],  # Green
            [0.0, 0.0, 1.0],  # Blue
            [1.0, 1.0, 0.0],  # Yellow
            [1.0, 0.5, 0.0],  # Orange
            [1.0, 1.0, 1.0],  # White
        ]
        
        # Generate solved state and current state
        self.solved_state = self.generate_solved_state()
        self.current_state = self.copy_state(self.solved_state)
        self.is_scrambled = False
        
        print(f"Created {size_x}x{size_y}x{size_z} cube with {len(self.current_state)} small cubes")

    def copy_state(self, state):
        """Create a deep copy of a cube state"""
        return [{
            'pos': cube['pos'][:],
            'colors': cube['colors'][:],
            'grid_pos': cube['grid_pos'][:]
        } for cube in state]

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
                        'grid_pos': [x, y, z]
                    })
        
        return cubes

    def scramble(self):
        """Scramble the cube by randomizing colors on visible faces"""
        print("Scrambling cube...")
        self.solve_step = 0
        self.is_scrambled = True
        
        # Get all visible face positions
        visible_faces = []
        for i, cube in enumerate(self.current_state):
            for j, color in enumerate(cube['colors']):
                if color != -1:  # If it's a visible face
                    visible_faces.append((i, j))
        
        # Shuffle the colors among all visible faces
        if visible_faces:
            # Get all current colors from visible faces
            colors = [self.current_state[cube_idx]['colors'][face_idx] for cube_idx, face_idx in visible_faces]
            # Shuffle them
            random.shuffle(colors)
            # Assign back to faces
            for idx, (cube_idx, face_idx) in enumerate(visible_faces):
                self.current_state[cube_idx]['colors'][face_idx] = colors[idx]
        
        print("Cube scrambled!")
        return f"Cube scrambled! Press SPACE to solve step by step."

    def is_solved(self):
        """Check if the cube is in solved state"""
        for i, cube in enumerate(self.current_state):
            for j, color in enumerate(cube['colors']):
                if color != self.solved_state[i]['colors'][j]:
                    return False
        return True

    def solve_one_step(self):
        """Make one move towards solving the cube"""
        if not self.is_scrambled:
            return "Scramble the cube first!"
        
        if self.is_solved():
            return "🎉 Cube is already solved! Press 'Scramble' for a new challenge."
        
        # Find all incorrect faces
        incorrect_positions = []
        for i, cube in enumerate(self.current_state):
            for j, color in enumerate(cube['colors']):
                if color != -1 and color != self.solved_state[i]['colors'][j]:
                    incorrect_positions.append((i, j))
        
        if not incorrect_positions:
            return "🎉 Cube solved!"
        
        # Fix 1-5 faces per step (more for larger cubes)
        total_faces = sum(1 for cube in self.current_state for color in cube['colors'] if color != -1)
        fixes_per_step = max(1, min(5, len(incorrect_positions) // 15))
        
        to_fix = random.sample(incorrect_positions, min(fixes_per_step, len(incorrect_positions)))
        
        for cube_idx, face_idx in to_fix:
            self.current_state[cube_idx]['colors'][face_idx] = self.solved_state[cube_idx]['colors'][face_idx]
        
        self.solve_step += 1
        remaining = len(incorrect_positions) - len(to_fix)
        
        if remaining <= 0:
            self.is_scrambled = False
            return f"🎉 Cube solved in {self.solve_step} steps!"
        else:
            return f"Step {self.solve_step}: Fixed {len(to_fix)} faces, {remaining} remaining"

    def reset_to_solved(self):
        """Reset cube to solved state"""
        self.current_state = self.copy_state(self.solved_state)
        self.solve_step = 0
        self.is_scrambled = False
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

    def draw_single_cube(self, cube_data):
        """Draw one small cube"""
        x, y, z = cube_data['pos']
        colors = cube_data['colors']
        s = self.cube_size / 2
        
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

    def draw(self):
        """Draw the entire cube"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Calculate camera distance
        max_size = max(self.size_x, self.size_y, self.size_z)
        camera_distance = max_size * 3
        
        # Position and rotate
        glTranslatef(0.0, 0.0, -camera_distance)
        glRotatef(self.rotation_x, 1, 0, 0)
        glRotatef(self.rotation_y, 0, 1, 0)
        
        # Draw all cubes
        for cube in self.current_state:
            self.draw_single_cube(cube)

class ControlPanel:
    def __init__(self, cube, command_queue):
        self.cube = cube
        self.command_queue = command_queue
        self.root = None
        self.status_var = None
        
    def create_panel(self):
        """Create the persistent control panel"""
        self.root = tk.Tk()
        self.root.title("Rubik's Cube Controls")
        self.root.geometry("320x500")
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
        
        self.status_var = tk.StringVar(value="Ready! Scramble the cube to start.")
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
        inst_frame = ttk.LabelFrame(main_frame, text="Keyboard Controls", padding="10")
        inst_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        instructions = [
            "🖱️ Mouse: Drag to rotate",
            "⏎ SPACE: Solve one step", 
            "🔀 S: Scramble",
            "🔄 R: Reset view",
            "❌ ESC: Quit"
        ]
        
        for i, instruction in enumerate(instructions):
            ttk.Label(inst_frame, text=instruction, font=('Arial', 9)).grid(row=i, column=0, 
                                                                            sticky=tk.W, pady=1)
        
        # Start the update loop
        self.update_status()
        
    def create_new_cube(self):
        """Create a new cube with specified dimensions"""
        try:
            x = int(self.x_var.get())
            y = int(self.y_var.get())
            z = int(self.z_var.get())
            if x <= 0 or y <= 0 or z <= 0 or x > 10 or y > 10 or z > 10:
                messagebox.showerror("Error", "Dimensions must be between 1 and 10!")
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
    
    print(f"Starting {size_x}x{size_y}x{size_z} Rubik's cube...")
    
    # Initialize Pygame
    pygame.init()
    
    # Set up display
    width, height = 1000, 800
    screen = pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
    pygame.display.set_caption(f"3D Rubik's Cube ({size_x}x{size_y}x{size_z})")
    
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
    
    print("Cube ready! Use the control panel to interact.")
    
    running = True
    while running:
        # Process commands from control panel
        try:
            while True:
                try:
                    command, data = command_queue.get_nowait()
                    if command == 'scramble':
                        result = cube.scramble()
                        status_queue.put(result)
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
                        pygame.display.set_caption(f"3D Rubik's Cube ({new_x}x{new_y}x{new_z})")
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
                elif event.key == K_r:
                    result = cube.reset_view()
                    status_queue.put(result)
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
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()  
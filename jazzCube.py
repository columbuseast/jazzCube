import pygame
import math
from OpenGL.GL import *
from OpenGL.GLU import *
import random

class RubiksCube:
    def __init__(self, size_x, size_y, size_z):
        self.size_x = size_x
        self.size_y = size_y
        self.size_z = size_z
        self.rotation_x = 0
        self.rotation_y = 0
        self.cube_size = 0.9
        self.gap = 0.1
        
        # Colors for each face (RGB)
        self.colors = [
            (1.0, 0.0, 0.0),  # Red
            (0.0, 1.0, 0.0),  # Green
            (0.0, 0.0, 1.0),  # Blue
            (1.0, 1.0, 0.0),  # Yellow
            (1.0, 0.5, 0.0),  # Orange
            (1.0, 1.0, 1.0),  # White
        ]
        
        # Generate cube data
        self.cubes = self.generate_cubes()
    
    def generate_cubes(self):
        """Generate all small cubes with their positions and colors"""
        cubes = []
        
        # Calculate offsets to center the cube
        offset_x = (self.size_x - 1) * (self.cube_size + self.gap) / 2
        offset_y = (self.size_y - 1) * (self.cube_size + self.gap) / 2
        offset_z = (self.size_z - 1) * (self.cube_size + self.gap) / 2
        
        for x in range(self.size_x):
            for y in range(self.size_y):
                for z in range(self.size_z):
                    pos_x = x * (self.cube_size + self.gap) - offset_x
                    pos_y = y * (self.cube_size + self.gap) - offset_y
                    pos_z = z * (self.cube_size + self.gap) - offset_z
                    
                    # Assign colors based on position (faces)
                    cube_colors = [0, 0, 0, 0, 0, 0]  # Default black (interior)
                    
                    # Assign face colors for visible faces
                    if x == 0: cube_colors[0] = 0  # Left face - Red
                    if x == self.size_x - 1: cube_colors[1] = 1  # Right face - Green
                    if y == 0: cube_colors[2] = 2  # Bottom face - Blue
                    if y == self.size_y - 1: cube_colors[3] = 3  # Top face - Yellow
                    if z == 0: cube_colors[4] = 4  # Back face - Orange
                    if z == self.size_z - 1: cube_colors[5] = 5  # Front face - White
                    
                    cubes.append({
                        'position': (pos_x, pos_y, pos_z),
                        'colors': cube_colors
                    })
        
        return cubes
    
    def draw_single_cube(self, position, colors):
        """Draw a single small cube"""
        x, y, z = position
        size = self.cube_size / 2
        
        glPushMatrix()
        glTranslatef(x, y, z)
        
        # Define vertices of a cube
        vertices = [
            [-size, -size, -size], [size, -size, -size], [size, size, -size], [-size, size, -size],  # Back
            [-size, -size, size], [size, -size, size], [size, size, size], [-size, size, size]      # Front
        ]
        
        # Define faces (vertex indices)
        faces = [
            [0, 1, 2, 3],  # Back
            [4, 7, 6, 5],  # Front
            [0, 4, 5, 1],  # Bottom
            [2, 6, 7, 3],  # Top
            [0, 3, 7, 4],  # Left
            [1, 5, 6, 2],  # Right
        ]
        
        # Draw each face
        glBegin(GL_QUADS)
        for i, face in enumerate(faces):
            color_idx = colors[i]
            if color_idx >= 0:  # Only draw colored faces
                glColor3f(*self.colors[color_idx])
                for vertex_idx in face:
                    glVertex3fv(vertices[vertex_idx])
        glEnd()
        
        # Draw edges in black
        glColor3f(0.0, 0.0, 0.0)
        glLineWidth(2.0)
        
        edges = [
            [0, 1], [1, 2], [2, 3], [3, 0],  # Back face
            [4, 5], [5, 6], [6, 7], [7, 4],  # Front face
            [0, 4], [1, 5], [2, 6], [3, 7]   # Connecting edges
        ]
        
        glBegin(GL_LINES)
        for edge in edges:
            for vertex_idx in edge:
                glVertex3fv(vertices[vertex_idx])
        glEnd()
        
        glPopMatrix()
    
    def draw(self):
        """Draw the entire Rubik's cube"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Position camera
        gluLookAt(5, 5, 5, 0, 0, 0, 0, 1, 0)
        
        # Apply rotations
        glRotatef(self.rotation_x, 1, 0, 0)
        glRotatef(self.rotation_y, 0, 1, 0)
        
        # Draw all cubes
        for cube in self.cubes:
            self.draw_single_cube(cube['position'], cube['colors'])
    
    def scramble(self):
        """Scramble the cube colors randomly"""
        for cube in self.cubes:
            # Randomize colors for visible faces only
            for i in range(6):
                if cube['colors'][i] >= 0:  # If it's a visible face
                    cube['colors'][i] = random.randint(0, 5)

def draw_text(text, x, y):
    """Draw text on screen (simple overlay)"""
    pass  # Text rendering in OpenGL is complex, keeping interface simple

def main():
    pygame.init()
    
    # Get cube dimensions from user
    print("=== 3D Rubik's Cube Simulator ===")
    print("Enter the dimensions for your cube:")
    
    try:
        size_x = int(input("Width (X): "))
        size_y = int(input("Height (Y): "))
        size_z = int(input("Depth (Z): "))
        
        if size_x <= 0 or size_y <= 0 or size_z <= 0:
            print("Dimensions must be positive integers!")
            return
    except ValueError:
        print("Invalid input! Using default 3x3x3 cube.")
        size_x = size_y = size_z = 3
    
    print(f"\nCreating {size_x}x{size_y}x{size_z} Rubik's cube...")
    print("\nControls:")
    print("- Mouse: Click and drag to rotate")
    print("- SPACE: Scramble cube")
    print("- ESC: Exit")
    print("- R: Reset view")
    
    # Set up display
    display = (1200, 800)
    pygame.display.set_mode(display, pygame.DOUBLEBUF | pygame.OPENGL)
    pygame.display.set_caption(f"3D Rubik's Cube ({size_x}x{size_y}x{size_z})")
    
    # Set up OpenGL
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    
    # Set up lighting
    light_pos = [2.0, 2.0, 2.0, 1.0]
    light_color = [1.0, 1.0, 1.0, 1.0]
    glLightfv(GL_LIGHT0, GL_POSITION, light_pos)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, light_color)
    
    # Set up perspective
    gluPerspective(45, (display[0]/display[1]), 0.1, 50.0)
    
    # Create cube
    cube = RubiksCube(size_x, size_y, size_z)
    
    # Mouse control variables
    mouse_down = False
    last_mouse_pos = (0, 0)
    
    clock = pygame.time.Clock()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    cube.scramble()
                    print("Cube scrambled!")
                elif event.key == pygame.K_r:
                    cube.rotation_x = 0
                    cube.rotation_y = 0
                    print("View reset!")
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    mouse_down = True
                    last_mouse_pos = pygame.mouse.get_pos()
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    mouse_down = False
            
            elif event.type == pygame.MOUSEMOTION:
                if mouse_down:
                    mouse_pos = pygame.mouse.get_pos()
                    dx = mouse_pos[0] - last_mouse_pos[0]
                    dy = mouse_pos[1] - last_mouse_pos[1]
                    
                    cube.rotation_y += dx * 0.5
                    cube.rotation_x += dy * 0.5
                    
                    last_mouse_pos = mouse_pos
        
        # Auto-rotation (optional - comment out if not desired)
        # cube.rotation_y += 0.5
        
        # Draw everything
        cube.draw()
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()
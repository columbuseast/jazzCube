import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import random
import sys

class RubiksCube:
    def __init__(self, size_x, size_y, size_z):
        self.size_x = size_x
        self.size_y = size_y
        self.size_z = size_z
        self.rotation_x = 0
        self.rotation_y = 0
        self.cube_size = 1.0
        self.gap = 0.1
        
        # Bright colors that should be visible
        self.colors = [
            [1.0, 0.0, 0.0],  # Red
            [0.0, 1.0, 0.0],  # Green
            [0.0, 0.0, 1.0],  # Blue
            [1.0, 1.0, 0.0],  # Yellow
            [1.0, 0.5, 0.0],  # Orange
            [1.0, 1.0, 1.0],  # White
        ]
        
        print(f"Creating cube with {len(self.get_cube_positions())} small cubes...")

    def get_cube_positions(self):
        """Get all cube positions"""
        positions = []
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
                    
                    # Determine which faces are visible
                    visible_faces = {
                        'left': x == 0,
                        'right': x == self.size_x - 1,
                        'bottom': y == 0,
                        'top': y == self.size_y - 1,
                        'back': z == 0,
                        'front': z == self.size_z - 1
                    }
                    
                    positions.append({
                        'pos': [pos_x, pos_y, pos_z],
                        'visible': visible_faces,
                        'grid_pos': [x, y, z]
                    })
        
        return positions

    def draw_cube_face(self, vertices, color):
        """Draw a single face of a cube"""
        glColor3fv(color)
        glBegin(GL_QUADS)
        for vertex in vertices:
            glVertex3fv(vertex)
        glEnd()

    def draw_single_cube(self, position, visible_faces):
        """Draw one small cube"""
        x, y, z = position
        s = self.cube_size / 2  # half size
        
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
        
        # Define faces and their colors
        faces = [
            ('back', [vertices[0], vertices[1], vertices[2], vertices[3]], self.colors[4]),    # Orange
            ('front', [vertices[4], vertices[7], vertices[6], vertices[5]], self.colors[5]),   # White
            ('bottom', [vertices[0], vertices[4], vertices[5], vertices[1]], self.colors[2]),  # Blue
            ('top', [vertices[3], vertices[2], vertices[6], vertices[7]], self.colors[3]),     # Yellow
            ('left', [vertices[0], vertices[3], vertices[7], vertices[4]], self.colors[0]),    # Red
            ('right', [vertices[1], vertices[5], vertices[6], vertices[2]], self.colors[1]),   # Green
        ]
        
        # Draw visible faces
        for face_name, face_vertices, color in faces:
            if visible_faces.get(face_name, False):
                self.draw_cube_face(face_vertices, color)
            else:
                # Draw interior faces in dark gray
                self.draw_cube_face(face_vertices, [0.3, 0.3, 0.3])
        
        # Draw wireframe edges
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
        
        # Calculate appropriate camera distance
        max_size = max(self.size_x, self.size_y, self.size_z)
        camera_distance = max_size * 3
        
        # Position camera
        glTranslatef(0.0, 0.0, -camera_distance)
        
        # Apply rotations
        glRotatef(self.rotation_x, 1, 0, 0)
        glRotatef(self.rotation_y, 0, 1, 0)
        
        # Draw all cubes
        positions = self.get_cube_positions()
        for cube_data in positions:
            self.draw_single_cube(cube_data['pos'], cube_data['visible'])

def main():
    print("=== 3D Rubik's Cube Simulator ===")
    print("Enter the dimensions for your cube:")
    
    try:
        size_x = int(input("Width (X): "))
        size_y = int(input("Height (Y): "))
        size_z = int(input("Depth (Z): "))
        
        if size_x <= 0 or size_y <= 0 or size_z <= 0:
            print("Dimensions must be positive! Using 3x3x3.")
            size_x = size_y = size_z = 3
    except (ValueError, EOFError):
        print("Invalid input! Using default 3x3x3 cube.")
        size_x = size_y = size_z = 3
    
    print(f"\nCreating {size_x}x{size_y}x{size_z} Rubik's cube...")
    print("\nControls:")
    print("- Mouse: Click and drag to rotate")
    print("- Arrow keys: Rotate cube")
    print("- ESC/Q: Exit")
    print("- R: Reset view")
    
    # Initialize Pygame
    pygame.init()
    
    # Set up display
    width, height = 1000, 800
    screen = pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
    pygame.display.set_caption(f"3D Rubik's Cube ({size_x}x{size_y}x{size_z})")
    
    # Set up OpenGL
    glEnable(GL_DEPTH_TEST)
    glClearColor(0.2, 0.2, 0.2, 1.0)  # Gray background
    
    # Set up perspective
    glMatrixMode(GL_PROJECTION)
    gluPerspective(60, width/height, 1, 100)
    glMatrixMode(GL_MODELVIEW)
    
    # Create the cube
    cube = RubiksCube(size_x, size_y, size_z)
    
    # Control variables
    mouse_down = False
    last_mouse_pos = [0, 0]
    clock = pygame.time.Clock()
    
    print("Cube created! Window should be visible now.")
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE or event.key == K_q:
                    running = False
                elif event.key == K_r:
                    cube.rotation_x = 0
                    cube.rotation_y = 0
                    print("View reset!")
                elif event.key == K_LEFT:
                    cube.rotation_y -= 5
                elif event.key == K_RIGHT:
                    cube.rotation_y += 5
                elif event.key == K_UP:
                    cube.rotation_x -= 5
                elif event.key == K_DOWN:
                    cube.rotation_x += 5
            
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
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
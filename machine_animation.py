import pygame
import os
from pygame.locals import *
import PIL.Image  # For loading GIF frames

pygame.init()
FONT = pygame.font.SysFont(None, 28)  # Font for on-screen text

class Machine:
    def __init__(self, image_path, screen_width, screen_height, initial_y):
        self.image = pygame.image.load(image_path).convert_alpha()
        self.machine_name = os.path.splitext(os.path.basename(image_path))[0]
        self.machine_name = self.machine_name.replace("dumptruck", "Dump Truck").replace("bulldozer", "Bulldozer")\
                                         .replace("excavator", "Excavator").replace("cementmixer", "Cement Mixer")\
                                         .replace("cranetruck", "Crane Truck")
        
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Load GIF animations
        self.wheel_frames = []
        try:
            wheel_gif_path = f"{self.machine_name.lower().replace(' ', '_')}_wheel_animation.gif"
            wheel_gif = PIL.Image.open(wheel_gif_path)
            for frame_index in range(wheel_gif.n_frames):
                wheel_gif.seek(frame_index)
                frame = wheel_gif.convert('RGBA')
                pygame_surface = pygame.image.fromstring(
                    frame.tobytes(), frame.size, frame.mode
                )
                self.wheel_frames.append(pygame_surface)
        except Exception as e:
            print(f"Error loading wheel gif for {self.machine_name}: {e}")
            self.wheel_frames = []
        
        # Default wheel positions relative to the top-left of the image, not absolute
        self.wheel_positions = {
            'Dump Truck':  [(162, 300), (330, 316), (533, 318), (660, 314), (783, 311)],
            'Bulldozer':  [(120, 300)],
            'Excavator':  [(200, 300), (450, 300)],
            'Cement Mixer': [(321, 400), (521, 400), (684, 400), (841, 400)],
            'Crane Truck': [(105, 420), (330, 420), (480, 420), (630, 420)]
        }
        
        # Machine position & movement controls
        self.rect = self.image.get_rect()
        self.rect.x = screen_width // 2  # Center horizontally
        self.rect.y = initial_y  # Initial Y position (passed into constructor)
        self.speed = 50  # Movement step size, reduced speed
        self.y_speed = 50 # Y movement step size

        # Runtime-editable parameters
        self.wheel_offset_x = 0
        self.wheel_offset_y = 0
        self.wheel_scale = 1.0
        
        # Animation parameters
        self.current_frame = 0
        self.frame_delay = 2
        self.frame_counter = 0
        self.text_surface = FONT.render(self.machine_name, True, (255, 255, 255))
        self.text_rect = self.text_surface.get_rect()



    def update(self, keys):
        if keys[K_LEFT]:
            self.rect.x -= self.speed
        if keys[K_RIGHT]:
            self.rect.x += self.speed
        if keys[K_UP]:
             self.rect.y -= self.y_speed
        if keys[K_DOWN]:
            self.rect.y += self.y_speed
        
        # update the text position relative to machine's rect.
        self.text_rect.x = self.rect.x + 100
        self.text_rect.bottom = self.rect.top - 10 # Position text above image
        print(f'text_rect.x: {self.text_rect.x}, text_rect.bottom: {self.text_rect.bottom}')
        
        
        # Handle animation frame changes
        if self.wheel_frames:
            self.frame_counter += 1
            if self.frame_counter >= self.frame_delay:
                self.frame_counter = 0
                self.current_frame = (self.current_frame + 1) % len(self.wheel_frames)

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        
        # Draw vehicle name
        surface.blit(self.text_surface, self.text_rect)

        # Draw wheels
        if self.wheel_frames and self.machine_name in self.wheel_positions:
            current_wheel = self.wheel_frames[self.current_frame]

            for pos in self.wheel_positions[self.machine_name]:
                wheel_x = self.rect.x + int(pos[0] * self.wheel_scale) + self.wheel_offset_x
                wheel_y = self.rect.y + int(pos[1] * self.wheel_scale) + self.wheel_offset_y
                surface.blit(current_wheel, (wheel_x, wheel_y))


def main():
    screen_width = 1920
    screen_height = 1080
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Vehicle Animation with Editable Parameters")
    clock = pygame.time.Clock()

    machine_files = [f for f in os.listdir(".") if f.endswith('.png')]
    
    # Position each machine at a different Y
    initial_y_positions = [200, 400, 600, 800, 900] #  Adjust these y values as needed

    machines = [Machine(os.path.join(".", f), screen_width, screen_height, initial_y_positions[i % len(initial_y_positions)]) for i,f in enumerate(machine_files)]
    
    running = True
    while running:
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                running = False
        
        screen.fill((32, 33, 36))
        for machine in machines:
            machine.update(keys)
            machine.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()
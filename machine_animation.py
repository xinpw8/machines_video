import pygame
import os
from pygame.locals import *
import math

class Machine:
    def __init__(self, image_path, screen_width, screen_height):
        self.image = pygame.image.load(image_path)
        self.wheel_frames = []
        
        # Get machine name from image path and load corresponding wheel animation
        self.machine_name = os.path.splitext(os.path.basename(image_path))[0]
        try:
            import PIL.Image
            wheel_gif = PIL.Image.open(f"{self.machine_name}_wheel_animation.gif")
            for frame_index in range(wheel_gif.n_frames):
                wheel_gif.seek(frame_index)
                frame = wheel_gif.convert('RGBA')
                pygame_surface = pygame.image.fromstring(
                    frame.tobytes(), frame.size, frame.mode)
                self.wheel_frames.append(pygame_surface)
        except Exception as e:
            print(f"Error loading wheel gif for {self.machine_name}: {e}")
            self.wheel_frames = []

        self.wheel_positions = {
            'dumptruck': [  # Keep original working coordinates
                (162, 555), (330, 571), (533, 573), 
                (660, 569), (783, 566)
            ],
            'bulldozer': [  # Keep original working coordinates
                (120, 560)
            ],
            'excavator': [  # Keep original working coordinates
                (200, 570), (450, 570)  
            ],
            'cementmixer': [  # Basically working
                (321, 900), (521, 900), (684, 900), (841, 900)
            ],
            'cranetruck': [ # Doesn't work - wheels way too high
                (180, 920), (330, 920), (480, 920), (630, 920)
            ]
        }.get(self.machine_name, []) 
        
        # Scale cement mixer wheels by 1.2
        if self.machine_name == 'cementmixer' and self.wheel_frames:
            scaled_frames = []
            for frame in self.wheel_frames:
                w, h = frame.get_size()
                sw, sh = int(w * 1.2), int(h * 1.2)
                scaled_frames.append(pygame.transform.scale(frame, (sw, sh)))
            self.wheel_frames = scaled_frames

        self.current_frame = 0
        self.frame_delay = 2
        self.frame_counter = 0
        
        self.rect = self.image.get_rect()
        self.rect.x = screen_width
        self.rect.centery = screen_height / 2
        if self.machine_name == 'cranetruck':
            self.rect.bottom = screen_height - 300  # Adjust offset to taste
        self.state = "entering"
        self.pause_timer = 0
        self.speed = 15
    def update(self):
        moving = False
        if self.state == "entering" and self.rect.centerx > 960:
            self.rect.x -= self.speed
            moving = True
        elif self.state == "entering":
            self.state = "paused"
        elif self.state == "paused":
            self.pause_timer += 1
            if self.pause_timer > 50:
                self.state = "exiting"
        elif self.state == "exiting":
            self.rect.x -= self.speed
            moving = True

        # Only animate wheels when moving
        if moving:
            self.frame_counter += 1
            if self.frame_counter >= self.frame_delay:
                self.frame_counter = 0
                self.current_frame = (self.current_frame + 1) % len(self.wheel_frames)

        return self.rect.right < 0

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        
        # Draw wheel animations if available
        if self.wheel_frames and self.wheel_positions:
            current_wheel = self.wheel_frames[self.current_frame]
            first_wheel = self.wheel_positions[0]
            for pos in self.wheel_positions:
                rel_x = pos[0] - first_wheel[0]
                rel_y = pos[1] - first_wheel[1]
                wheel_x = self.rect.x + rel_x
                wheel_y = self.rect.y + rel_y
                print(f"[{self.machine_name}] Wheel at: ({wheel_x}, {wheel_y})")
                surface.blit(current_wheel, (wheel_x, wheel_y))

def main():
    pygame.init()
    screen = pygame.display.set_mode((1920, 1080))
    pygame.display.set_caption("8-bit Machines")
    clock = pygame.time.Clock()

    # Load machine images (simplified)
    machine_files = [f for f in os.listdir(".") if f.endswith('.png')]
    
    current_machine = Machine(os.path.join(".", machine_files[0]), 1920, 1080)
    machine_index = 1

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False

        screen.fill((32, 33, 36))  # Dark gray background

        # Update current machine
        if current_machine:
            if current_machine.update():
                if machine_index < len(machine_files):
                    current_machine = Machine(os.path.join(".", 
                                           machine_files[machine_index]), 1920, 1080)
                    machine_index += 1
                else:
                    current_machine = None
            else:
                current_machine.draw(screen)  # Use new draw method

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
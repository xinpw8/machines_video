import pygame
import os
from pygame.locals import *
import math
import PIL.Image  # For loading GIF frames
import random

pygame.init()
FONT = pygame.font.SysFont(None, 28)     # Font for on-screen text
BIG_FONT = pygame.font.SysFont(None, 72)   # Large font for vehicle name

# Global toggle for random Y spawn mode:
random_y_mode = True

class Machine:
    def __init__(self, image_path, screen_width, screen_height, initial_y):
        # Load the machine image and set up its basic attributes
        self.image = pygame.image.load(image_path).convert_alpha()
        self.machine_name = os.path.splitext(os.path.basename(image_path))[0]
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Create the rect once and set the initial position using the provided initial_y.
        self.rect = self.image.get_rect()
        self.rect.x = screen_width  # Start offscreen on the right.
        self.rect.y = initial_y     # Use the passed initial_y value.

        # [GIF loading, wheel frame loading, etc... remain unchanged]
        self.wheel_frames = []
        try:
            wheel_gif_path = f"{self.machine_name}_wheel_animation.gif"
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

        self.wheel_positions = {
            'dumptruck':  [(162, 555), (330, 571), (533, 573), (660, 569), (783, 566)],
            'bulldozer':  [(120, 560)],
            'excavator':  [(200, 570), (450, 570)],
            'cementmixer':[(321, 900), (521, 900), (684, 900), (841, 900)],
            'cranetruck': [(105, 920), (330, 920), (480, 920), (630, 920)]
        }.get(self.machine_name, [])

        if self.machine_name == 'cementmixer' and self.wheel_frames:
            scaled_frames = []
            for frame in self.wheel_frames:
                w, h = frame.get_size()
                sw, sh = int(w * 1.2), int(h * 1.2)
                scaled_frames.append(pygame.transform.scale(frame, (sw, sh)))
            self.wheel_frames = scaled_frames

        # Animation parameters
        self.current_frame = 0
        self.frame_delay = 2
        self.frame_counter = 0

        # State, speed, and movement settings:
        self.state = "entering"
        self.pause_timer = 0
        self.speed = 15
        self.y_speed = 15  # Vertical movement speed

        # Runtime-editable parameters for wheel adjustments:
        self.wheel_offset_x = 0
        self.wheel_offset_y = 0
        self.wheel_scale = 1.0

        if self.machine_name == 'cementmixer':
            self.wheel_offset_x = 21
            self.wheel_offset_y = -25
        if self.machine_name == 'cranetruck':
            try:
                # Load the main crane wheels
                crane_wheel_gif = PIL.Image.open("crane_wheel.gif")
                crane_frames = []
                for frame_index in range(crane_wheel_gif.n_frames):
                    crane_wheel_gif.seek(frame_index)
                    frame = crane_wheel_gif.convert('RGBA')
                    pygame_surface = pygame.image.fromstring(
                        frame.tobytes(), frame.size, frame.mode
                    )
                    crane_frames.append(pygame_surface)
                self.wheel_frames = crane_frames
                self.wheel_positions = [(438, -110), (656, -110), (812, -110), (976, -110)]
            except Exception as e:
                print("Error loading crane_wheel.gif:", e)
                self.wheel_frames = []
                self.wheel_positions = []

            try:
                # Load the hook wheel separately
                self.hook_frames = []
                hook_gif = PIL.Image.open("wheel.gif")
                for frame_index in range(hook_gif.n_frames):
                    hook_gif.seek(frame_index)
                    frame = hook_gif.convert('RGBA')
                    pygame_surface = pygame.image.fromstring(
                        frame.tobytes(), frame.size, frame.mode
                    )
                    self.hook_frames.append(pygame_surface)
            except Exception as e:
                print("Error loading wheel.gif for hook:", e)
                self.hook_frames = []

            self.hook_position = (-800, -15)
            self.wheel_offset_x = 30
            self.wheel_offset_y = -87
            self.wheel_scale = 1.02

    def render_text_title(self, surface, machine_name, rect, font, screen_width):
        # Only render the title when random_y_mode is False.
        if not machine_name or random_y_mode:
            return
        # Adjust machine names for display
        display_name = {
            'cranetruck': 'Crane Truck',
            'cementmixer': 'Cement Mixer',
            'excavator':  'Excavator',
            'bulldozer':  'Bulldozer',
            'dumptruck':  'Dump Truck'
        }.get(machine_name, machine_name)
        
        if screen_width // 2 - 150 <= rect.centerx <= screen_width // 2 + 150:
            text_surface = font.render(display_name.upper(), True, (255, 255, 0))
            text_x = self.screen_width // 2 - text_surface.get_width() // 2
            text_y = self.screen_height // 6 - text_surface.get_height() // 2
            surface.blit(text_surface, (text_x, text_y))

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[K_LSHIFT] or keys[K_RSHIFT]:
            self.speed = 0

        # If random_y_mode is active, the machine should keep moving left continuously.
        if random_y_mode:
            self.rect.x -= self.speed * 5
        else:
            if self.state == "entering" and self.rect.centerx > 960:
                self.rect.x -= self.speed * 5
            elif self.state == "entering" and random_y_mode == False:
                self.state = "paused"
            elif self.state == "paused":
                self.pause_timer += 1
                if self.pause_timer > 50:
                    self.state = "exiting"
            elif self.state == "exiting":
                self.rect.x -= self.speed * 5

        # Handle vertical (and slight horizontal) manual movement:
        if keys[K_UP]:
            self.rect.y -= self.y_speed / 3
        if keys[K_DOWN]:
            self.rect.y += self.y_speed / 3
        if keys[K_LEFT]:
            self.rect.x -= self.y_speed * 3
        if keys[K_RIGHT]:
            self.rect.x += self.y_speed * 3

        # Update hook position for cranetruck if applicable
        if self.machine_name == 'cranetruck' and hasattr(self, 'hook_frames'):
            hook_base_x = self.rect.x - 15
            hook_base_y = self.rect.y + 15
            self.hook_position = (hook_base_x, hook_base_y)

        if self.wheel_frames:
            self.frame_counter += 1
            if self.frame_counter >= self.frame_delay:
                self.frame_counter = 0
                self.current_frame = (self.current_frame + 1) % len(self.wheel_frames)

        return self.rect.right < 0

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        self.render_text_title(surface, self.machine_name, self.rect, BIG_FONT, screen_width=self.screen_width)
        
        if self.machine_name == 'cranetruck' and hasattr(self, 'hook_frames') and self.hook_frames:
            current_hook_frame = self.hook_frames[self.current_frame]
            surface.blit(current_hook_frame, self.hook_position)

        if self.wheel_frames and self.wheel_positions:
            current_wheel = self.wheel_frames[self.current_frame]
            first_wheel = self.wheel_positions[0]
            for pos in self.wheel_positions:
                rel_x = (pos[0] - first_wheel[0]) + self.wheel_offset_x
                rel_y = (pos[1] - first_wheel[1]) + self.wheel_offset_y
                wheel_x = self.rect.x + int(rel_x * self.wheel_scale)
                wheel_y = self.rect.y + int(rel_y * self.wheel_scale)
                surface.blit(current_wheel, (wheel_x, wheel_y))

def main():
    global random_y_mode  # Ensure modifications affect the global variable
    screen_width, screen_height = 1920, 1080
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Random Y Spawn Vehicles")
    clock = pygame.time.Clock()

    machine_files = [f for f in os.listdir(".") if f.endswith('.png')]
    # These positions will now correctly be passed to each machine.
    machine_y_positions = {
        'dumptruck': 360,
        'bulldozer': 475,
        'excavator': 200, 
        'cementmixer': 240,
        'cranetruck': 100  # Changing cranetruck's value will now affect its spawn position.
    }
    
    toggled_machines = [None] * 9  # Storage for active machines
    selected_index = -1
    random_y_mode = False  # Initial mode

    running = True
    while running:
        screen.fill((32, 33, 36))
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False

                # Toggle random_y_mode when R is pressed.
                if event.key == K_r:
                    random_y_mode = not random_y_mode
                    print(f"Random Y Spawn Mode: {'ON' if random_y_mode else 'OFF'}")

                # Load a machine based on keys 1-9.
                if K_1 <= event.key <= K_9:
                    idx = event.key - K_1
                    if idx < len(machine_files):
                        machine_name = os.path.splitext(machine_files[idx])[0]
                        y_pos = machine_y_positions.get(machine_name, 100)
                        print(f"y_pos for {machine_name}: {y_pos}")
                        
                        if toggled_machines[idx] is None:
                            toggled_machines[idx] = Machine(
                                os.path.join(".", machine_files[idx]),
                                screen_width, screen_height,
                                y_pos
                            )
                            # If random_y_mode is active, you can randomize the y-position further if desired.
                            if random_y_mode:
                                if toggled_machines[idx].machine_name == "cranetruck":
                                    toggled_machines[idx].rect.y = random.randint(y_pos - 100, y_pos)
                                elif toggled_machines[idx].machine_name == "cementmixer":
                                    toggled_machines[idx].rect.y = random.randint(y_pos - 565, y_pos)
                                elif toggled_machines[idx].machine_name == "excavator":
                                    toggled_machines[idx].rect.y = random.randint(y_pos - 375, y_pos)
                                elif toggled_machines[idx].machine_name == "bulldozer":
                                    toggled_machines[idx].rect.y = random.randint(y_pos - 475, y_pos)
                                elif toggled_machines[idx].machine_name == "dumptruck":
                                    toggled_machines[idx].rect.y = random.randint(y_pos - 360, y_pos)
                                else:
                                    toggled_machines[idx].rect.y = random.randint(y_pos - 100, y_pos)
                                print(f"toggled_machines for {machine_name}: {toggled_machines[idx].rect.y}")

                            selected_index = idx
                        else:
                            toggled_machines[idx] = None
                            if selected_index == idx:
                                selected_index = -1
 
        # Update and draw machines.
        for i, m in enumerate(toggled_machines):
            if m is not None:
                done = m.update()
                if done:
                    toggled_machines[i] = None
                    if selected_index == i:
                        selected_index = -1
                else:
                    m.draw(screen)

        # [Overlay and instructions drawing code remain unchanged]

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()

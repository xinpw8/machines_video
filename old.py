import pygame
import os
from pygame.locals import *
import math
import PIL.Image  # For loading GIF frames
import random

pygame.init()
FONT = pygame.font.SysFont(None, 28)     # Font for on-screen text
BIG_FONT = pygame.font.SysFont(None, 72)   # Large font for vehicle name

# Global toggles:
random_y_mode = True     # Toggled by R key (keeps vehicles moving continuously)
race_mode_active = False # When M is held to select race vehicles
race_in_progress = False # True when a race is underway
finished_racers = []     # List to record finish order
race_podium_timer = 0    # Timer for podium freeze frame
RACE_PODIUM_DURATION = 300  # Duration of podium display in frames (~5 seconds at 60fps)

class Machine:
    def __init__(self, image_path, screen_width, screen_height, initial_y):
        self.image = pygame.image.load(image_path).convert_alpha()
        self.machine_name = os.path.splitext(os.path.basename(image_path))[0]
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # All vehicles start offscreen on the right.
        self.rect = self.image.get_rect()
        self.rect.x = screen_width  
        self.rect.y = initial_y     

        self.racing = False  # Flag: True if participating in a race

        # For dynamic speed variation during the race:
        self.speed_changes_remaining = 5  # Up to 5 changes per race
        self.speed_change_timer = 0       # Timer until next speed change

        # Load wheel frames if available.
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

        self.current_frame = 0
        self.frame_delay = 3
        self.frame_counter = 0

        self.state = "entering"
        self.pause_timer = 0
        self.speed = 50
        self.y_speed = 50

        self.wheel_offset_x = 0
        self.wheel_offset_y = 0
        self.wheel_scale = 1.0

        if self.machine_name == 'cementmixer':
            self.wheel_offset_x = 21
            self.wheel_offset_y = -25
        if self.machine_name == 'cranetruck':
            try:
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
        # Text rendering disabled (handled externally if needed)
        return

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[K_LSHIFT] or keys[K_RSHIFT]:
            self.speed = 0

        # Racing mode: vehicles move left (from right to left) and vary speed dynamically.
        if self.racing:
            if self.speed_change_timer <= 0:
                self.speed_change_timer = random.randint(60, 180)  # frames until next change
            else:
                self.speed_change_timer -= 1
            if self.speed_change_timer <= 0 and self.speed_changes_remaining > 0:
                self.speed = random.randint(5, 15)
                self.speed_changes_remaining -= 1
                self.speed_change_timer = random.randint(60, 180)
            self.rect.x -= self.speed  # move left
            self.rect.y += random.randint(-1, 1)  # slight vertical jitter
            if self.wheel_frames:
                self.frame_counter += 1
                if self.frame_counter >= self.frame_delay:
                    self.frame_counter = 0
                    self.current_frame = (self.current_frame + 1) % len(self.wheel_frames)
            return self.rect.right < 0

        # Normal (non-racing) update.
        if random_y_mode:
            self.rect.x -= self.speed
        else:
            if self.state == "entering" and self.rect.centerx > self.screen_width / 2:
                self.rect.x -= self.speed
            elif self.state == "entering":
                self.state = "paused"
            elif self.state == "paused":
                self.pause_timer += 1
                if self.pause_timer > 50:
                    self.state = "exiting"
            elif self.state == "exiting":
                self.rect.x -= self.speed

        if keys[K_UP]:
            self.rect.y -= self.y_speed / 3
        if keys[K_DOWN]:
            self.rect.y += self.y_speed / 3
        if keys[K_LEFT]:
            self.rect.x -= self.y_speed * 3
        if keys[K_RIGHT]:
            self.rect.x += self.y_speed * 3

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

def draw_podium(surface, finished_racers, screen_width, screen_height):
    # Define new podium positions and sizes so they appear higher on the screen.
    center_x = screen_width // 2
    # 1st podium: tallest podium, height 300, placed higher.
    first_rect = pygame.Rect(center_x, screen_height - 700, 200, 300)
    # 2nd podium: medium podium, height 200.
    second_rect = pygame.Rect(center_x - 300, screen_height - 600, 200, 200)
    # 3rd podium: shortest podium, height 150.
    third_rect = pygame.Rect(center_x + 300, screen_height - 550, 200, 150)
    podiums = [first_rect, second_rect, third_rect]
    labels = ["1st Place", "2nd Place", "3rd Place"]

    for i in range(min(3, len(finished_racers))):
        color = (200, 200, 200)  # Grey podium
        pygame.draw.rect(surface, color, podiums[i])
        pygame.draw.rect(surface, (0, 0, 0), podiums[i], 5)  # Border
        # Draw podium label:
        label_surface = BIG_FONT.render(labels[i], True, (255, 255, 0))
        label_rect = label_surface.get_rect()
        label_rect.centerx = podiums[i].centerx
        label_rect.top = podiums[i].top - label_rect.height #  - 10
        surface.blit(label_surface, label_rect)
        # Get the racer image, scale it down by 50%, then blit it.
        racer = finished_racers[i]
        img = racer.image
        scaled_img = pygame.transform.scale(img, (img.get_width() // 4, img.get_height() // 4))
        img_rect = scaled_img.get_rect()
        img_rect.centerx = podiums[i].centerx
        img_rect.bottom = podiums[i].top - 40  # position above the podium
        surface.blit(scaled_img, img_rect)

def main():
    global random_y_mode, race_mode_active, race_in_progress, finished_racers, race_podium_timer
    screen_width, screen_height = 2560, 1440
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
    pygame.display.set_caption("Random Y Spawn Vehicles")
    clock = pygame.time.Clock()

    machine_files = [f for f in os.listdir(".") if f.endswith('.png')]
    machine_y_positions = {
        'dumptruck': 360,
        'bulldozer': 475,
        'excavator': 200, 
        'cementmixer': 240,
        'cranetruck': 100
    }
    
    active_machines = []  # Currently active vehicles
    race_vehicles = []    # Vehicles selected for racing

    random_y_mode = False  # Initially off

    running = True
    while running:
        # If a podium freeze frame is active, display it and pause other updates.
        if race_podium_timer > 0:
            screen.fill((32, 33, 36))
            draw_podium(screen, finished_racers, screen_width, screen_height)
            pygame.display.flip()
            race_podium_timer -= 1
            if race_podium_timer <= 0:
                finished_racers.clear()
            clock.tick(60)
            continue

        screen.fill((32, 33, 36))
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                # Toggle random_y_mode to enforce continuous leftward movement.
                if event.key == K_r:
                    random_y_mode = not random_y_mode
                    print(f"Random Y Spawn Mode: {'ON' if random_y_mode else 'OFF'}")
                # Activate race mode when M is pressed.
                if event.key == K_m:
                    race_mode_active = True
                    print("Race mode activated. Press keys 1-9 to add vehicles to the race.")
                # In race mode, number keys add vehicles to the race.
                elif race_mode_active and K_1 <= event.key <= K_9:
                    idx = event.key - K_1
                    if idx < len(machine_files):
                        machine_name = os.path.splitext(machine_files[idx])[0]
                        y_pos = machine_y_positions.get(machine_name, screen_height // 2)
                        new_machine = Machine(os.path.join(".", machine_files[idx]), screen_width, screen_height, y_pos)
                        new_machine.racing = False  # Will be set to True when the race starts
                        race_vehicles.append(new_machine)
                        print(f"Added {machine_name} to race vehicles.")
                # Normal spawning if not in race mode.
                elif not race_mode_active and K_1 <= event.key <= K_9:
                    idx = event.key - K_1
                    if idx < len(machine_files):
                        machine_name = os.path.splitext(machine_files[idx])[0]
                        y_pos = machine_y_positions.get(machine_name, 100)
                        new_machine = Machine(os.path.join(".", machine_files[idx]), screen_width, screen_height, y_pos)
                        if random_y_mode:
                            if new_machine.machine_name == "cranetruck":
                                new_machine.rect.y = random.randint(y_pos - 300, y_pos + 100)
                            elif new_machine.machine_name == "cementmixer":
                                new_machine.rect.y = random.randint(y_pos - 565, y_pos + 465)
                            elif new_machine.machine_name == "excavator":
                                new_machine.rect.y = random.randint(y_pos - 375, y_pos + 375)
                            elif new_machine.machine_name == "bulldozer":
                                new_machine.rect.y = random.randint(y_pos - 575, y_pos + 375)
                            elif new_machine.machine_name == "dumptruck":
                                new_machine.rect.y = random.randint(y_pos - 560, y_pos + 360)
                            else:
                                new_machine.rect.y = random.randint(y_pos - 400, y_pos + 100)
                            print(f"New instance of {machine_name} spawned at y: {new_machine.rect.y}")
                        active_machines.append(new_machine)
            elif event.type == KEYUP:
                # When M is released, if race mode was active, start the race.
                if event.key == K_m and race_mode_active:
                    if race_vehicles:
                        start_x = screen_width - 200  # Vehicles line up near the right edge.
                        baseline_y = race_vehicles[0].rect.y  # Use the y of the first vehicle as baseline
                        spacing = 150
                        for i, vehicle in enumerate(race_vehicles):
                            vehicle.rect.x = start_x
                            vehicle.rect.y = baseline_y + int((i - len(race_vehicles)/2) * spacing) + random.randint(-20, 20)
                            vehicle.speed = random.randint(5, 15)
                            vehicle.speed_changes_remaining = 5
                            vehicle.speed_change_timer = random.randint(60, 180)
                            vehicle.racing = True
                        active_machines.extend(race_vehicles)
                        race_vehicles.clear()
                        race_mode_active = False
                        race_in_progress = True
                        print("Race started!")
                    else:
                        race_mode_active = False

        # Update and draw active vehicles.
        for m in active_machines[:]:
            if m.racing and m.update():
                if m not in finished_racers:
                    finished_racers.append(m)
                active_machines.remove(m)
            elif not m.racing and m.update():
                active_machines.remove(m)
            else:
                m.draw(screen)
        
        # If a race is in progress and no racing vehicles remain, trigger the podium.
        if race_in_progress:
            racing_vehicles = [m for m in active_machines if m.racing]
            if not racing_vehicles and len(finished_racers) > 0:
                race_in_progress = False
                race_podium_timer = RACE_PODIUM_DURATION
                print("Race finished! Displaying podium.")
        
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()

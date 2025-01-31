import pygame
import os
from pygame.locals import *
import math
import PIL.Image  # For loading GIF frames
import random

pygame.init()
FONT = pygame.font.SysFont(None, 28)  # Font for on-screen text
BIG_FONT = pygame.font.SysFont(None, 72)  # Large font for vehicle name


class Machine:
    def __init__(self, image_path, screen_width, screen_height, initial_y, random_y_mode=False):
        self.image = pygame.image.load(image_path).convert_alpha()
        self.machine_name = os.path.splitext(os.path.basename(image_path))[0]
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.rect = self.image.get_rect()
        self.rect.x = screen_width  # Start offscreen
        self.rect.y = initial_y  # <-- Set correct y position here!
        self.random_y_mode = False

        # ========== GIF LOADING (unchanged) ==========
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

        # ========== WHEEL POSITIONS (unchanged) ==========
        self.wheel_positions = {
            'dumptruck':  [(162, 555), (330, 571), (533, 573), (660, 569), (783, 566)],
            'bulldozer':  [(120, 560)],
            'excavator':  [(200, 570), (450, 570)],
            'cementmixer':[(321, 900), (521, 900), (684, 900), (841, 900)],
            'cranetruck': [(105, 920), (330, 920), (480, 920), (630, 920)]
        }.get(self.machine_name, [])

        # ========== SCALE CEMENT MIXER WHEELS (unchanged) ==========
        if self.machine_name == 'cementmixer' and self.wheel_frames:
            scaled_frames = []
            for frame in self.wheel_frames:
                w, h = frame.get_size()
                sw, sh = int(w * 1.2), int(h * 1.2)
                scaled_frames.append(pygame.transform.scale(frame, (sw, sh)))
            self.wheel_frames = scaled_frames

        # ========== GIF ANIMATION PARAMS (unchanged) ==========
        self.current_frame = 0
        self.frame_delay = 2
        self.frame_counter = 0

        # ========== MACHINE POSITION & STATE (unchanged) ==========
        self.rect = self.image.get_rect()
        self.rect.x = screen_width
        self.initial_y = initial_y
        self.rect.centery = screen_height / 2
        if self.machine_name == 'cranetruck':
            self.rect.bottom = screen_height #- 300
        self.state = "entering"
        self.pause_timer = 0
        self.speed = 15
        self.y_speed = 15  # Added y movement speed

        # ========== NEW: RUNTIME-EDITABLE PARAMS ==========
        self.wheel_offset_x = 0
        self.wheel_offset_y = 0
        self.wheel_scale = 1.0

        # If you want default offsets for cementmixer:
        if self.machine_name == 'cementmixer':
            self.wheel_offset_x = 21
            self.wheel_offset_y = -25
            self.wheel_scale = 1.0

        if self.machine_name == 'cranetruck':
            try:
                # Load main crane wheels
                crane_wheel_gif = PIL.Image.open("crane_wheel.gif")
                crane_frames = []
                for frame_index in range(crane_wheel_gif.n_frames):
                    crane_wheel_gif.seek(frame_index)
                    frame = crane_wheel_gif.convert('RGBA')
                    pygame_surface = pygame.image.fromstring(
                        frame.tobytes(), frame.size, frame.mode
                    )
                    crane_frames.append(pygame_surface)
                # Assign loaded frames to self.wheel_frames
                self.wheel_frames = crane_frames
                # Adjust wheel positions to fix alignment
                self.wheel_positions = [(438, -110), (656, -110), (812, -110), (976, -110)]
            except Exception as e:
                print("Error loading crane_wheel.gif:", e)
                self.wheel_frames = []
                self.wheel_positions = []

            # Load hook wheel separately
            self.hook_frames = []
            try:
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

            # single hook position
            self.hook_position = (-800, -15)

            self.wheel_offset_x = 30
            self.wheel_offset_y = -87
            self.wheel_scale = 1.02

    def render_text_title(self, surface, machine_name, rect, font, screen_width):
        """
        Renders the name of any vehicle dramatically when it reaches the center.
        """
        if not machine_name:
            return  # Ensure the machine name is valid
        
        if machine_name == 'cranetruck':
            machine_name = 'Crane Truck'
        elif machine_name == 'cementmixer':
            machine_name = 'Cement Mixer'
        elif machine_name == 'excavator':
            machine_name = 'Excavator'
        elif machine_name == 'bulldozer':
            machine_name = 'Bulldozer'
        elif machine_name == 'dumptruck':
            machine_name = 'Dump Truck'
        
        center_threshold = screen_width // 2 - 150 <= rect.centerx <= screen_width // 2 + 150
        if center_threshold:
    

            text_surface = font.render(machine_name.upper(), True, (255, 255, 0))  # Bright Yellow for dramatic effect
            text_x = self.screen_width // 2 - text_surface.get_width() // 2
            text_y = self.screen_height // 6 - text_surface.get_height() // 2
 
            surface.blit(text_surface, (text_x, text_y))



    def update(self):
        """
        Original logic: 'entering -> paused -> exiting'.
        Returns True if the machine is completely off-screen to the left
        (meaning we can remove it).
        """

        moving = False
        keys = pygame.key.get_pressed()
        if keys[K_LSHIFT] or keys[K_RSHIFT]:
            self.speed = 0
        if self.state == "entering" and self.rect.centerx > 960:
            self.rect.x -= self.speed * 5
            moving = True
        elif self.state == "entering":
            self.state = "paused"
        elif self.state == "paused":
            self.pause_timer += 1
            if self.pause_timer > 50:
                self.state = "exiting"
        elif self.state == "exiting":
            self.rect.x -= self.speed * 5
            moving = True
            
        # Handle vertical movement with arrow keys
        if keys[K_UP]:
            self.rect.y -= self.y_speed / 3
        if keys[K_DOWN]:
            self.rect.y += self.y_speed / 3 
        if keys[K_LEFT]:
            self.rect.x -= self.y_speed * 3
        if keys[K_RIGHT]:
            self.rect.x += self.y_speed * 3
            
        if self.machine_name == 'cranetruck':
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
        """
        Draws the machine, plus its wheel frames. Also prints wheel coords to console.
        Incorporates self.wheel_offset_{x,y} and self.wheel_scale in the wheel positioning.
        """
        surface.blit(self.image, self.rect)

        self.render_text_title(surface, self.machine_name, self.rect, BIG_FONT, screen_width=self.screen_width)
        
        if self.machine_name == 'cranetruck' and self.hook_frames:
            current_hook_frame = self.hook_frames[self.current_frame]
            surface.blit(current_hook_frame, self.hook_position)

        if self.wheel_frames and self.wheel_positions:
            current_wheel = self.wheel_frames[self.current_frame]

            # We always offset relative to the first wheel in the list
            first_wheel = self.wheel_positions[0]

            for pos in self.wheel_positions:
                # Basic approach:
                #    Δx = pos.x - first_wheel.x
                #    Δy = pos.y - first_wheel.y
                # Then add machine rect.x, rect.y, plus our offset & scale
                rel_x = (pos[0] - first_wheel[0]) + self.wheel_offset_x
                rel_y = (pos[1] - first_wheel[1]) + self.wheel_offset_y

                # Optionally apply scale
                wheel_x = self.rect.x + int(rel_x * self.wheel_scale)
                wheel_y = self.rect.y + int(rel_y * self.wheel_scale)

                # Blit wheel frames
                surface.blit(current_wheel, (wheel_x, wheel_y))



# def main():
#     screen_width = 1920
#     screen_height = 1080
#     screen = pygame.display.set_mode((screen_width, screen_height))
#     pygame.display.set_caption("8-bit Machines with Runtime Wheel Param Editing")
#     clock = pygame.time.Clock()

#     # Get machine files
#     machine_files = [f for f in os.listdir(".") if f.endswith('.png')]
#     machine_files.sort()  # consistent ordering

#     # Create machines with their specific Y positions
#     machines = []
#     for f in machine_files:
#         machine_name = os.path.splitext(os.path.basename(f))[0]
#         y_pos = machine_y_positions.get(machine_name, 100)  # Default 100 if not found
        
#         machine = Machine(os.path.join(".", f), screen_width, screen_height, y_pos)
#         machines.append(machine)
#         print(f'SET Y POSITION: {machine.machine_name} -> {machine.rect.y}')  # Debugging


#     toggled_machines = [None]*9  # each slot can hold one Machine or None
#     selected_index = -1

#     running = True
#     while running:
#         # ---------------------------------------------
#         # Event loop
#         # ---------------------------------------------
#         for event in pygame.event.get():
#             if event.type == QUIT:
#                 running = False
#             elif event.type == KEYDOWN:
#                 if event.key == K_ESCAPE:
#                     running = False

#                 # Press 1..9 to toggle that slot
#                 if K_1 <= event.key <= K_9:
#                     idx = event.key - K_1  # Get index 0..8
#                     if idx < len(machine_files):
#                         machine_name = os.path.splitext(os.path.basename(machine_files[idx]))[0]
#                         y_pos = machine_y_positions.get(machine_name, 100)  # Get correct y-pos
                        
#                         if toggled_machines[idx] is None:
                            
#                             toggled_machines[idx] = Machine(
#                                 os.path.join(".", machine_files[idx]),
#                                 screen_width, screen_height,
#                                 y_pos  # Use correct Y position
#                             )
#                             selected_index = idx
#                             toggled_machines[idx].random_y_mode = False

#                         else:
#                             # remove the machine
#                             toggled_machines[idx] = None
#                             if selected_index == idx:
#                                 selected_index = -1

#                 # Press Tab to cycle which machine is selected
#                 if event.key == K_TAB:
#                     active_indices = [
#                         i for i, m in enumerate(toggled_machines) if m is not None
#                     ]
#                     if not active_indices:
#                         selected_index = -1
#                     else:
#                         if selected_index not in active_indices:
#                             # pick the first
#                             selected_index = active_indices[0]
#                         else:
#                             # get the next in the cycle
#                             cur_pos = active_indices.index(selected_index)
#                             next_pos = (cur_pos + 1) % len(active_indices)
#                             selected_index = active_indices[next_pos]
                            
#                                     # Press TAB to toggle Random Y Mode
#                 if event.key == K_r:
#                     if 0 <= selected_index < len(toggled_machines):
#                         mach = toggled_machines[selected_index]
#                         if mach:
#                             mach.random_y_mode = not mach.random_y_mode  # Toggle mode for selected machine
#                             print(f"Random Y Mode for {mach.machine_name}: {'ON' if mach.random_y_mode else 'OFF'}")

#             # ---------------------------------------------
#         # Real-time param editing with arrow keys, [ & ]
#         # ---------------------------------------------
#         keys = pygame.key.get_pressed()
#         if 0 <= selected_index < len(toggled_machines):
#             mach = toggled_machines[selected_index]

#             print(f'current y pos machine {mach.machine_name}: {mach.rect.y}')
#             if not mach.random_y_mode:
#                 if mach.machine_name == "dumptruck":
#                     mach.rect.y = 360
#                 elif mach.machine_name == "bulldozer":
#                     mach.rect.y = 475
#                 elif mach.machine_name == "excavator":
#                     mach.rect.y = 200
#                 elif mach.machine_name == "cementmixer":
#                     mach.rect.y = 240
#                 elif mach.machine_name == "cranetruck":
#                     mach.rect.y = 100
#             else:
#                 mach.rect.y = random.randint(100, 900)

#         # ---------------------------------------------
#         # Clear screen
#         # ---------------------------------------------
#         screen.fill((32, 33, 36))





def main():
    screen_width, screen_height = 1920, 1080
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Random Y Spawn Vehicles")
    clock = pygame.time.Clock()

    machine_files = [f for f in os.listdir(".") if f.endswith('.png')]
    machine_y_positions = {'dumptruck': 360, 'bulldozer': 475, 'excavator': 200, 
                           'cementmixer': 240, 'cranetruck': 7}
    
    toggled_machines = [None] * 9  # Storage for active machines
    selected_index = -1
    random_y_mode = False  # Global toggle for random Y spawn

    running = True
    while running:
        screen.fill((32, 33, 36))

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False

                if event.key == K_r:  # Toggle random Y mode
                    random_y_mode = not random_y_mode
                    print(f"Random Y Spawn Mode: {'ON' if random_y_mode else 'OFF'}")

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
                                y_pos, random_y_mode
                            )
                            if toggled_machines[idx] is not None and random_y_mode:
                                toggled_machines[idx].rect.y = random.randint(y_pos - 1100, y_pos)
                                print(f"toggled_machines for {machine_name}: {toggled_machines[idx].rect.y}")

                            selected_index = idx
                        else:
                            toggled_machines[idx] = None
                            if selected_index == idx:
                                selected_index = -1
                        
 
        # ---------------------------------------------
        for i, m in enumerate(toggled_machines):
            if m is not None:
                done = m.update()
                if done:
                    toggled_machines[i] = None
                    if selected_index == i:
                        selected_index = -1
                else:
                    m.draw(screen)

        # ---------------------------------------------
        # Draw an overlay showing current param values
        # AND each wheel's final (x,y) for the selected machine
        # ---------------------------------------------
        overlay_y = 10
        if selected_index != -1:
            machine_obj = toggled_machines[selected_index]
            if machine_obj:
                txt_lines = [
                    f"Selected Machine: {machine_obj.machine_name}",
                    f"wheel_offset_x: {machine_obj.wheel_offset_x}",
                    f"wheel_offset_y: {machine_obj.wheel_offset_y}",
                    f"wheel_scale: {machine_obj.wheel_scale:.2f}",
                ]
                for line in txt_lines:
                    surf = FONT.render(line, True, (255,255,255))
                    screen.blit(surf, (10, overlay_y))
                    overlay_y += 30

                # Show final (x,y) for each wheel
                if machine_obj.wheel_positions and machine_obj.wheel_frames:
                    
                    first_wheel = machine_obj.wheel_positions[0]
                    for idx, pos in enumerate(machine_obj.wheel_positions):
                        rel_x = (pos[0] - first_wheel[0]) + machine_obj.wheel_offset_x
                        rel_y = (pos[1] - first_wheel[1]) + machine_obj.wheel_offset_y
                        wheel_x = machine_obj.rect.x + int(rel_x * machine_obj.wheel_scale)
                        wheel_y = machine_obj.rect.y + int(rel_y * machine_obj.wheel_scale)
                        wheel_line = f"Wheel {idx}: ({wheel_x}, {wheel_y})"
                        surf = FONT.render(wheel_line, True, (200, 200, 0))
                        screen.blit(surf, (10, overlay_y))
                        overlay_y += 25
        else:
            # handle out-of-range list index
            if 0 <= selected_index < len(toggled_machines):
                mach = toggled_machines[selected_index]
                # Show basic instructions if no machine is selected
                line = f"Load a machine: 1) {machine_files[0]}, 2) {machine_files[1]}, 3) {machine_files[2]}, 4) {machine_files[3]}, 5) {machine_files[4]}, 6) {machine_files[5]}, 7) {machine_files[6]}, 8) {machine_files[7]}, 9) {machine_files[8]}"
                surf = FONT.render(line, True, (255,255,255))
                screen.blit(surf, (10, overlay_y))

        # ---------------------------------------------
        # Flip
        # ---------------------------------------------
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()

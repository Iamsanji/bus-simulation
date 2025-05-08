import pygame
import random
import math
from collections import deque

# Initialize pygame
pygame.init()

# Set up display
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bus FCFS Scheduling Animation with Gantt Chart")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 80, 80)
GREEN = (80, 180, 80)
BLUE = (80, 120, 220)
YELLOW = (240, 200, 0)
ORANGE = (240, 140, 0)
PURPLE = (160, 80, 220)
CYAN = (0, 180, 200)
GRAY = (150, 150, 150)
LIGHT_BLUE = (180, 220, 250)
DARK_GREEN = (0, 120, 0)
BROWN = (160, 82, 45)
LIGHT_GRAY = (230, 230, 230)
DARK_GRAY = (80, 80, 80)
SKY_BLUE = (135, 206, 235)
GRASS_GREEN = (126, 200, 80)
ROAD_GRAY = (100, 100, 100)
BUS_YELLOW = (255, 215, 0)
PANEL_BG = (245, 245, 245)
PANEL_BORDER = (100, 100, 100)
HEADER_BG = (220, 225, 235)

# Fonts
try:
    font = pygame.font.SysFont("Arial", 16)
    small_font = pygame.font.SysFont("Arial", 14)
    title_font = pygame.font.SysFont("Arial", 20, bold=True)
    header_font = pygame.font.SysFont("Arial", 16, bold=True)
except:
    # Fallback to default font if Arial is not available
    font = pygame.font.Font(None, 24)
    small_font = pygame.font.Font(None, 20)
    title_font = pygame.font.Font(None, 28)
    header_font = pygame.font.Font(None, 24)

# Simulation parameters
FPS = 60
PASSENGER_GENERATION_RATE = 0.02  # Probability of a new passenger per frame
MAX_PASSENGERS = 20  # Maximum passengers waiting
MIN_RIDE_TIME = 5  # Minimum ride time (in seconds)
MAX_RIDE_TIME = 15  # Maximum ride time (in seconds)
SIMULATION_SPEED = 1  # Frames per simulation tick (higher = faster)
BUS_CAPACITY = 10  # Maximum passengers on the bus
BUS_SPEED = 100  # Pixels per second
BUS_STOP_TIME = 2  # Seconds to stop at each bus stop

# Bus stop positions (x coordinates)
BUS_STOPS = [150, 350, 550, 750, 950]
BUS_STOP_Y = HEIGHT - 250  # Y coordinate for all bus stops

# Passenger colors
PASSENGER_COLORS = [
    (220, 80, 80),  # Red
    (80, 180, 80),  # Green
    (80, 120, 220),  # Blue
    (240, 200, 0),  # Yellow
    (240, 140, 0),  # Orange
    (160, 80, 220),  # Purple
    (0, 180, 200),  # Cyan
    (180, 100, 140)  # Magenta
]


class Passenger:
    def __init__(self, passenger_id, arrival_time, ride_time, stop_index):
        self.id = passenger_id
        self.arrival_time = arrival_time  # When the passenger arrives
        self.ride_time = ride_time  # Total time needed on the bus
        self.remaining_time = ride_time  # Remaining time to complete journey
        self.start_time = -1  # When the passenger boards the bus
        self.completion_time = -1  # When the passenger completes journey
        self.wait_time = 0  # Time spent waiting at the bus stop
        self.turnaround_time = 0  # Total time from arrival to completion
        self.service_time = 0  # Time spent on the bus
        self.state = "waiting"  # waiting, onboard, completed
        self.color = random.choice(PASSENGER_COLORS)  # Random color for the passenger
        self.progress = 0  # Visual progress indicator (0-100%)
        self.stop_index = stop_index  # Which bus stop they're at
        self.destination_stop = min(len(BUS_STOPS) - 1,
                                    stop_index + max(1, int(ride_time / 5)))  # Destination stop

        # Visual representation
        self.size = 20
        self.x = BUS_STOPS[stop_index]
        self.y = BUS_STOP_Y - 30 - (self.size * 1.5)
        self.target_x = self.x
        self.target_y = self.y
        self.moving = False
        self.boarding_progress = 0  # For boarding animation

    def update(self, current_time, delta_time):
        if self.state == "waiting":
            # Update wait time while waiting
            self.wait_time = current_time - self.arrival_time

            # Move towards target position (for queueing animation)
            if self.moving:
                dx = self.target_x - self.x
                dy = self.target_y - self.y
                distance = math.sqrt(dx * dx + dy * dy)

                if distance > 1:
                    self.x += dx * 0.1
                    self.y += dy * 0.1
                else:
                    self.moving = False
                    self.x = self.target_x
                    self.y = self.target_y

        elif self.state == "onboard":
            # Update service time while on bus
            if self.start_time == -1:
                self.start_time = current_time
            self.service_time = current_time - self.start_time

            # Update remaining time
            self.remaining_time -= delta_time
            if self.remaining_time <= 0:
                self.remaining_time = 0
                self.state = "completed"
                self.completion_time = current_time
                self.turnaround_time = self.completion_time - self.arrival_time

            # Update progress percentage
            self.progress = 100 * (1 - self.remaining_time / self.ride_time)

        elif self.state == "completed":
            # Ensure statistics are properly calculated
            if self.completion_time == -1:
                self.completion_time = current_time
            self.turnaround_time = self.completion_time - self.arrival_time

    def draw(self, screen):
        if self.state == "waiting":
            # Draw waiting passenger
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)
            pygame.draw.circle(screen, BLACK, (int(self.x), int(self.y)), self.size, 2)

            # Draw passenger ID
            id_text = small_font.render(f"{self.id}", True, BLACK)
            screen.blit(id_text, (self.x - id_text.get_width() // 2, self.y - id_text.get_height() // 2))

        elif self.state == "onboard":
            # Passengers on the bus are drawn by the Bus class
            pass

        elif self.state == "completed":
            # Completed passengers are not drawn
            pass


class Bus:
    def __init__(self):
        self.x = 0
        self.y = BUS_STOP_Y - 50
        self.width = 120
        self.height = 60
        self.passengers = []
        self.current_stop = 0
        self.target_x = BUS_STOPS[0]
        self.state = "moving"  # moving, loading, unloading
        self.stop_timer = 0
        self.idle_time = 0
        self.busy_time = 0
        self.total_passengers_served = 0

        # For drawing passengers on the bus
        self.passenger_positions = []
        for i in range(BUS_CAPACITY):
            row = i // 5
            col = i % 5
            self.passenger_positions.append((
                20 + col * 20,
                15 + row * 20
            ))

    def update(self, delta_time, waiting_passengers):
        # Update bus state
        if self.state == "moving":
            # Move towards the current target
            dx = self.target_x - self.x
            distance = abs(dx)

            if distance > 5:
                # Move towards target
                direction = 1 if dx > 0 else -1
                self.x += direction * BUS_SPEED * delta_time
                self.busy_time += delta_time
            else:
                # Arrived at bus stop
                self.x = self.target_x
                self.state = "loading"
                self.stop_timer = BUS_STOP_TIME

        elif self.state == "loading":
            # At a bus stop, loading/unloading passengers
            self.stop_timer -= delta_time

            # Unload passengers who reached their destination
            for passenger in self.passengers[:]:
                if passenger.destination_stop == self.current_stop:
                    passenger.state = "completed"
                    self.passengers.remove(passenger)
                    self.total_passengers_served += 1

            # Load new passengers if there's room
            if len(self.passengers) < BUS_CAPACITY:
                # Find passengers waiting at this stop
                stop_passengers = [p for p in waiting_passengers if p.stop_index == self.current_stop
                                   and p.state == "waiting"]

                # Sort by arrival time (FCFS)
                stop_passengers.sort(key=lambda p: p.arrival_time)

                # Load as many as possible
                for passenger in stop_passengers:
                    if len(self.passengers) < BUS_CAPACITY:
                        passenger.state = "onboard"
                        passenger.start_time = -1  # Will be set in passenger.update()
                        self.passengers.append(passenger)
                    else:
                        break

            # Move to next stop when timer expires
            if self.stop_timer <= 0:
                self.current_stop = (self.current_stop + 1) % len(BUS_STOPS)
                self.target_x = BUS_STOPS[self.current_stop]
                self.state = "moving"

        # Update passenger positions on the bus
        for i, passenger in enumerate(self.passengers):
            if i < len(self.passenger_positions):
                passenger.bus_x, passenger.bus_y = self.passenger_positions[i]

    def draw(self, screen):
        # Draw bus body
        pygame.draw.rect(screen, BUS_YELLOW, (self.x - self.width // 2, self.y, self.width, self.height),
                         border_radius=10)
        pygame.draw.rect(screen, BLACK, (self.x - self.width // 2, self.y, self.width, self.height), 2,
                         border_radius=10)

        # Draw wheels
        wheel_radius = 10
        pygame.draw.circle(screen, BLACK, (int(self.x - self.width // 3), int(self.y + self.height)), wheel_radius)
        pygame.draw.circle(screen, BLACK, (int(self.x + self.width // 3), int(self.y + self.height)), wheel_radius)

        # Draw windows
        window_width = 15
        window_height = 20
        window_y = self.y + 10
        for i in range(4):
            window_x = self.x - self.width // 2 + 20 + i * 25
            pygame.draw.rect(screen, LIGHT_BLUE, (window_x, window_y, window_width, window_height))
            pygame.draw.rect(screen, BLACK, (window_x, window_y, window_width, window_height), 1)

        # Draw passengers on the bus
        for i, passenger in enumerate(self.passengers):
            if i < len(self.passenger_positions):
                px, py = self.passenger_positions[i]
                # Convert to screen coordinates
                px += self.x - self.width // 2
                py += self.y

                # Draw passenger
                pygame.draw.circle(screen, passenger.color, (int(px), int(py)), 8)
                pygame.draw.circle(screen, BLACK, (int(px), int(py)), 8, 1)

                # Draw passenger ID
                id_text = small_font.render(f"{passenger.id}", True, BLACK)
                screen.blit(id_text, (px - id_text.get_width() // 2, py - id_text.get_height() // 2))

        # Draw bus ID and status
        bus_text = font.render("BUS", True, BLACK)
        screen.blit(bus_text, (self.x - bus_text.get_width() // 2, self.y - 25))

        # Draw passenger count
        count_text = small_font.render(f"{len(self.passengers)}/{BUS_CAPACITY}", True, BLACK)
        screen.blit(count_text, (self.x - count_text.get_width() // 2, self.y + self.height + 15))

        # Draw state indicator
        state_text = small_font.render(self.state.upper(), True, BLACK)
        screen.blit(state_text, (self.x - state_text.get_width() // 2, self.y - 40))


class BusStopSign:
    def __init__(self, x, y, stop_number):
        self.x = x
        self.y = y
        self.stop_number = stop_number
        self.width = 20
        self.height = 60

    def draw(self, screen):
        # Draw pole
        pygame.draw.rect(screen, DARK_GRAY, (self.x - 2, self.y, 4, self.height))

        # Draw sign
        sign_width = 30
        sign_height = 30
        pygame.draw.rect(screen, BLUE, (self.x - sign_width // 2, self.y - sign_height, sign_width, sign_height))
        pygame.draw.rect(screen, BLACK, (self.x - sign_width // 2, self.y - sign_height, sign_width, sign_height), 2)

        # Draw bus symbol
        bus_text = small_font.render("BUS", True, WHITE)
        screen.blit(bus_text, (self.x - bus_text.get_width() // 2, self.y - sign_height + 5))

        # Draw stop number
        num_text = small_font.render(f"{self.stop_number}", True, WHITE)
        screen.blit(num_text, (self.x - num_text.get_width() // 2, self.y - sign_height // 2 + 5))


class GanttChart:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.timeline = []  # List of (passenger, start_time, end_time) tuples
        self.display_time = 30  # Show 30 seconds of timeline
        self.scroll_position = 0  # Current scroll position in seconds

    def update(self, current_passengers, current_time):
        # Update the timeline with the current passengers
        for passenger in current_passengers:
            # Check if we need to create a new timeline entry
            if not any(entry[0] == passenger for entry in self.timeline):
                # Create a new entry for this passenger
                self.timeline.append([passenger, current_time, current_time])
            else:
                # Update the end time of the current passenger
                for entry in self.timeline:
                    if entry[0] == passenger:
                        entry[2] = current_time
                        break

    def draw(self, screen, current_time):
        # Draw panel background
        pygame.draw.rect(screen, PANEL_BG, (self.x, self.y, self.width, self.height), border_radius=10)
        pygame.draw.rect(screen, PANEL_BORDER, (self.x, self.y, self.width, self.height), 2, border_radius=10)

        # Draw title
        title_text = title_font.render("Gantt Chart", True, BLACK)
        screen.blit(title_text, (self.x + (self.width - title_text.get_width()) // 2, self.y + 10))

        # Draw horizontal separator
        pygame.draw.line(screen, PANEL_BORDER,
                         (self.x + 5, self.y + 40),
                         (self.x + self.width - 5, self.y + 40),
                         1)

        # Calculate chart area
        chart_x = self.x + 50  # Leave space for labels
        chart_y = self.y + 60
        chart_width = self.width - 70
        chart_height = self.height - 100

        # Draw time axis
        pygame.draw.line(screen, BLACK, (chart_x, chart_y + chart_height),
                         (chart_x + chart_width, chart_y + chart_height), 2)

        # Draw chart background grid
        for i in range(self.display_time + 1):
            # Calculate x position for this time mark
            pos_x = chart_x + (i / self.display_time) * chart_width

            # Draw vertical grid line
            pygame.draw.line(screen, LIGHT_GRAY, (pos_x, chart_y), (pos_x, chart_y + chart_height), 1)

            # Draw time label
            time_label = small_font.render(f"{i + self.scroll_position:.0f}s", True, BLACK)
            screen.blit(time_label, (pos_x - time_label.get_width() // 2, chart_y + chart_height + 5))

        # Draw passenger blocks
        for passenger, start_time, end_time in self.timeline:
            # Skip if outside the current view
            if end_time < self.scroll_position or start_time > self.scroll_position + self.display_time:
                continue

            # Calculate position and width of this passenger block
            block_start = max(start_time, self.scroll_position)
            block_end = min(end_time, self.scroll_position + self.display_time)

            block_x = chart_x + ((block_start - self.scroll_position) / self.display_time) * chart_width
            block_width = ((block_end - block_start) / self.display_time) * chart_width

            # Draw the passenger block
            if block_width > 0:
                pygame.draw.rect(screen, passenger.color,
                                 (block_x, chart_y, block_width, chart_height), border_radius=5)
                pygame.draw.rect(screen, BLACK,
                                 (block_x, chart_y, block_width, chart_height), 1, border_radius=5)

                # Draw passenger ID if there's enough space
                if block_width > 30:
                    process_label = small_font.render(f"P{passenger.id}", True, BLACK)
                    screen.blit(process_label, (block_x + (block_width - process_label.get_width()) // 2,
                                                chart_y + (chart_height - process_label.get_height()) // 2))

        # Draw current time marker
        if current_time >= self.scroll_position and current_time <= self.scroll_position + self.display_time:
            marker_x = chart_x + ((current_time - self.scroll_position) / self.display_time) * chart_width
            pygame.draw.line(screen, RED, (marker_x, chart_y - 10), (marker_x, chart_y + chart_height + 10), 2)

        # Draw scroll buttons
        if self.scroll_position > 0:
            pygame.draw.polygon(screen, DARK_GRAY,
                                [(self.x + 20, self.y + self.height // 2),
                                 (self.x + 35, self.y + self.height // 2 - 10),
                                 (self.x + 35, self.y + self.height // 2 + 10)])

        pygame.draw.polygon(screen, DARK_GRAY,
                            [(self.x + self.width - 20, self.y + self.height // 2),
                             (self.x + self.width - 35, self.y + self.height // 2 - 10),
                             (self.x + self.width - 35, self.y + self.height // 2 + 10)])


class StatsTable:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.border_color = PANEL_BORDER
        self.bg_color = PANEL_BG
        self.header_color = HEADER_BG
        self.row_height = 25
        self.title_height = 30
        self.scroll_position = 0
        self.scroll_offset = 0
        self.max_visible_rows = 0

    def draw(self, screen, completed_passengers, current_time):
        # Draw table background with rounded corners
        pygame.draw.rect(screen, self.bg_color,
                         (self.x, self.y, self.width, self.height),
                         border_radius=10)
        pygame.draw.rect(screen, self.border_color,
                         (self.x, self.y, self.width, self.height),
                         2, border_radius=10)

        # Draw table title with improved styling
        title_text = title_font.render("Passenger Statistics", True, BLACK)
        title_width = title_text.get_width()

        # Draw title background
        pygame.draw.rect(screen, HEADER_BG,
                         (self.x + 1, self.y + 1, self.width - 2, self.title_height),
                         border_radius=10, border_top_left_radius=10, border_top_right_radius=10)

        # Draw title text
        screen.blit(title_text, (self.x + (self.width - title_width) // 2, self.y + 10))

        # Draw horizontal separator below title
        pygame.draw.line(screen, PANEL_BORDER,
                         (self.x + 5, self.y + self.title_height),
                         (self.x + self.width - 5, self.y + self.title_height),
                         1)

        # Draw table headers
        header_y = self.y + self.title_height + 5
        headers = ["ID", "Arrival", "Ride", "Start", "Completion", "Wait", "Turnaround"]

        # Calculate column widths based on table width
        col_widths = [
            int(self.width * 0.10),  # ID
            int(self.width * 0.15),  # Arrival
            int(self.width * 0.15),  # Ride
            int(self.width * 0.15),  # Start
            int(self.width * 0.15),  # Completion
            int(self.width * 0.15),  # Wait
            int(self.width * 0.15)  # Turnaround
        ]

        # Draw header background
        pygame.draw.rect(screen, self.header_color,
                         (self.x + 1, header_y, self.width - 2, 25),
                         border_radius=0)

        # Draw header text and separators
        x_pos = self.x + 10
        for i, header in enumerate(headers):
            header_text = header_font.render(header, True, BLACK)
            screen.blit(header_text, (x_pos, header_y + 5))

            # Draw vertical separator
            if i < len(headers) - 1:
                pygame.draw.line(screen, LIGHT_GRAY,
                                 (x_pos + col_widths[i] - 5, header_y),
                                 (x_pos + col_widths[i] - 5, self.y + self.height - 5),
                                 1)
            x_pos += col_widths[i]

        # Draw horizontal separator below headers
        pygame.draw.line(screen, DARK_GRAY,
                         (self.x, header_y + 25),
                         (self.x + self.width, header_y + 25),
                         1)

        # Draw process data
        row_y = header_y + 30

        # Calculate visible rows
        self.max_visible_rows = int((self.height - row_y + self.y - 10) // self.row_height)
        self.max_visible_rows = max(1, self.max_visible_rows)

        # Calculate maximum scroll offset
        max_scroll = max(0, len(completed_passengers) - self.max_visible_rows)
        self.scroll_offset = min(self.scroll_offset, max_scroll)

        # Get the slice of passengers to display based on scroll position
        start_idx = max(0, len(completed_passengers) - self.max_visible_rows - self.scroll_offset)
        end_idx = len(completed_passengers) - self.scroll_offset
        passengers_to_show = completed_passengers[start_idx:end_idx] if len(completed_passengers) > 0 else []

        for i, passenger in enumerate(passengers_to_show):
            if row_y + self.row_height > self.y + self.height - 5:
                break

            # Alternate row colors for better readability
            if i % 2 == 0:
                pygame.draw.rect(screen, (230, 235, 240),
                                 (self.x + 1, row_y, self.width - 2, self.row_height))

            # Draw row data
            col_x = self.x + 10

            # Passenger ID
            pid_text = small_font.render(f"P{passenger.id}", True, BLACK)
            screen.blit(pid_text, (col_x, row_y + 5))
            col_x += col_widths[0]

            # Arrival Time
            arrival_text = small_font.render(f"{passenger.arrival_time:.1f}s", True, BLACK)
            screen.blit(arrival_text, (col_x, row_y + 5))
            col_x += col_widths[1]

            # Ride Time
            ride_text = small_font.render(f"{passenger.ride_time:.1f}s", True, BLACK)
            screen.blit(ride_text, (col_x, row_y + 5))
            col_x += col_widths[2]

            # Start Time
            start_time = passenger.start_time if passenger.start_time != -1 else "N/A"
            start_text = small_font.render(f"{start_time:.1f}s" if start_time != "N/A" else start_time, True, BLACK)
            screen.blit(start_text, (col_x, row_y + 5))
            col_x += col_widths[3]

            # Completion Time
            completion_time = passenger.completion_time if passenger.completion_time != -1 else "N/A"
            completion_text = small_font.render(
                f"{completion_time:.1f}s" if completion_time != "N/A" else completion_time, True, BLACK)
            screen.blit(completion_text, (col_x, row_y + 5))
            col_x += col_widths[4]

            # Wait Time
            wait_text = small_font.render(f"{passenger.wait_time:.1f}s", True, BLACK)
            screen.blit(wait_text, (col_x, row_y + 5))
            col_x += col_widths[5]

            # Turnaround Time
            turnaround_time = passenger.turnaround_time
            turnaround_text = small_font.render(f"{turnaround_time:.1f}s", True, BLACK)
            screen.blit(turnaround_text, (col_x, row_y + 5))

            # Update for next row
            row_y += self.row_height

            # Draw row separator
            pygame.draw.line(screen, LIGHT_GRAY,
                             (self.x + 5, row_y),
                             (self.x + self.width - 5, row_y),
                             1)

        # Draw scroll indicators if needed
        if len(completed_passengers) > self.max_visible_rows:
            # Draw up arrow if not at top
            if self.scroll_offset < len(completed_passengers) - self.max_visible_rows:
                pygame.draw.polygon(screen, DARK_GRAY,
                                    [(self.x + self.width - 20, self.y + 50),
                                     (self.x + self.width - 30, self.y + 65),
                                     (self.x + self.width - 10, self.y + 65)])

            # Draw down arrow if not at bottom
            if self.scroll_offset > 0:
                pygame.draw.polygon(screen, DARK_GRAY,
                                    [(self.x + self.width - 20, self.y + self.height - 20),
                                     (self.x + self.width - 30, self.y + self.height - 35),
                                     (self.x + self.width - 10, self.y + self.height - 35)])


class AverageStatsPanel:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def draw(self, screen, waiting_passengers, onboard_passengers, completed_passengers, current_time, bus_utilization):
        # Draw panel background
        pygame.draw.rect(screen, PANEL_BG, (self.x, self.y, self.width, self.height), border_radius=10)
        pygame.draw.rect(screen, PANEL_BORDER, (self.x, self.y, self.width, self.height), 2, border_radius=10)

        # Draw title
        title_text = title_font.render("Average Statistics", True, BLACK)
        screen.blit(title_text, (self.x + (self.width - title_text.get_width()) // 2, self.y + 10))

        # Draw horizontal separator
        pygame.draw.line(screen, PANEL_BORDER,
                         (self.x + 5, self.y + 40),
                         (self.x + self.width - 5, self.y + 40),
                         1)

        # Calculate averages
        if completed_passengers:
            avg_wait_time = sum(p.wait_time for p in completed_passengers) / len(completed_passengers)
            avg_turnaround = sum(p.turnaround_time for p in completed_passengers) / len(completed_passengers)
            avg_response = sum(max(0, p.start_time - p.arrival_time) for p in completed_passengers) / len(
                completed_passengers)
            avg_ride = sum(p.ride_time for p in completed_passengers) / len(completed_passengers)
            throughput = len(completed_passengers) / max(1, current_time)  # Passengers per second
        else:
            avg_wait_time = 0
            avg_turnaround = 0
            avg_response = 0
            avg_ride = 0
            throughput = 0

        # Calculate total unique passengers by ID
        all_passengers = waiting_passengers + onboard_passengers + completed_passengers
        unique_ids = set()
        for p in all_passengers:
            unique_ids.add(p.id)

        # Draw statistics
        stats = [
            f"Total Passengers: {len(unique_ids)}",
            f"Waiting: {len([p for p in waiting_passengers if p.state == 'waiting'])}",
            f"On Bus: {len(onboard_passengers)}",
            f"Completed: {len(completed_passengers)}",
            f"Average Wait Time: {avg_wait_time:.2f}s",
            f"Average Response Time: {avg_response:.2f}s",
            f"Average Ride Time: {avg_ride:.2f}s",
            f"Average Turnaround Time: {avg_turnaround:.2f}s",
            f"Throughput: {throughput:.2f} pass/s",
            f"Bus Utilization: {bus_utilization:.1f}%"
        ]

        for i, stat in enumerate(stats):
            stat_text = font.render(stat, True, BLACK)
            screen.blit(stat_text, (self.x + 20, self.y + 60 + i * 25))


class BusSimulation:
    def __init__(self):
        self.reset()

    def reset(self):
        self.bus = Bus()
        self.waiting_passengers = []
        self.completed_passengers = []
        self.passenger_counter = 1
        self.time = 0  # Simulation time in seconds
        self.frames = 0
        self.paused = False
        self.auto_generate = True

        # Create bus stops
        self.bus_stops = []
        for i, x in enumerate(BUS_STOPS):
            self.bus_stops.append(BusStopSign(x, BUS_STOP_Y - 60, i + 1))

        # Create stats panel - moved to top left
        self.stats_panel = AverageStatsPanel(20, 20, 280, 300)

        # Create Gantt chart - moved to top right
        self.gantt_chart = GanttChart(320, 20, WIDTH - 340, 150)

        # Create stats table - moved below Gantt chart
        self.stats_table = StatsTable(320, 190, WIDTH - 340, 200)

    def generate_random_passenger(self):
        """Generate a random passenger with sensible parameters"""
        ride_time = random.uniform(MIN_RIDE_TIME, MAX_RIDE_TIME)
        stop_index = random.randint(0, len(BUS_STOPS) - 1)
        passenger = Passenger(self.passenger_counter, self.time, ride_time, stop_index)
        self.passenger_counter += 1
        return passenger

    def handle_events(self):
        """Process pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    self.reset()
                elif event.key == pygame.K_a:
                    self.auto_generate = not self.auto_generate
                elif event.key == pygame.K_n:
                    # Manually add a new passenger
                    new_passenger = self.generate_random_passenger()
                    self.waiting_passengers.append(new_passenger)
                    self.arrange_waiting_passengers()
                elif event.key == pygame.K_RIGHT:
                    # Scroll Gantt chart forward
                    self.gantt_chart.scroll_position += 5
                elif event.key == pygame.K_LEFT:
                    # Scroll Gantt chart backward
                    self.gantt_chart.scroll_position = max(0, self.gantt_chart.scroll_position - 5)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Check if clicked on Gantt chart scroll buttons
                if event.button == 1:  # Left click
                    if (self.gantt_chart.x + 20 <= event.pos[0] <= self.gantt_chart.x + 35 and
                            self.gantt_chart.y + self.gantt_chart.height // 2 - 10 <= event.pos[
                                1] <= self.gantt_chart.y + self.gantt_chart.height // 2 + 10):
                        # Left scroll button
                        self.gantt_chart.scroll_position = max(0, self.gantt_chart.scroll_position - 5)
                    elif (self.gantt_chart.x + self.gantt_chart.width - 35 <= event.pos[
                        0] <= self.gantt_chart.x + self.gantt_chart.width - 20 and
                          self.gantt_chart.y + self.gantt_chart.height // 2 - 10 <= event.pos[
                              1] <= self.gantt_chart.y + self.gantt_chart.height // 2 + 10):
                        # Right scroll button
                        self.gantt_chart.scroll_position += 5

                # Handle mouse wheel scrolling for stats table
                elif event.button == 4:  # Scroll up
                    if (self.stats_table.x <= event.pos[0] <= self.stats_table.x + self.stats_table.width and
                            self.stats_table.y <= event.pos[1] <= self.stats_table.y + self.stats_table.height):
                        self.stats_table.scroll_offset = min(
                            len(self.completed_passengers) - self.stats_table.max_visible_rows,
                            self.stats_table.scroll_offset + 1
                        )
                        self.stats_table.scroll_offset = max(0, self.stats_table.scroll_offset)
                elif event.button == 5:  # Scroll down
                    if (self.stats_table.x <= event.pos[0] <= self.stats_table.x + self.stats_table.width and
                            self.stats_table.y <= event.pos[1] <= self.stats_table.y + self.stats_table.height):
                        self.stats_table.scroll_offset = max(0, self.stats_table.scroll_offset - 1)

        return True

    def update(self):
        """Update simulation state"""
        if self.paused:
            return

        # Update frame counter
        self.frames += 1

        # Only update simulation state every SIMULATION_SPEED frames
        if self.frames % SIMULATION_SPEED != 0:
            return

        # Update simulation time
        time_delta = 1 / FPS
        self.time += time_delta

        # Update bus
        self.bus.update(time_delta, self.waiting_passengers)

        # Update all passengers
        for passenger in self.waiting_passengers:
            passenger.update(self.time, time_delta)

        for passenger in self.bus.passengers:
            passenger.update(self.time, time_delta)

        # Move completed passengers to the completed list
        for passenger in self.bus.passengers[:]:
            if passenger.state == "completed":
                self.completed_passengers.append(passenger)
                self.bus.passengers.remove(passenger)

        # Update Gantt chart
        self.gantt_chart.update(self.bus.passengers, self.time)

        # Potentially generate new passenger
        if self.auto_generate and len(self.waiting_passengers) < MAX_PASSENGERS:
            if random.random() < PASSENGER_GENERATION_RATE:
                new_passenger = self.generate_random_passenger()
                self.waiting_passengers.append(new_passenger)

                # Arrange waiting passengers at each stop
                self.arrange_waiting_passengers()

    def arrange_waiting_passengers(self):
        """Arrange waiting passengers in a queue at each bus stop"""
        # Group passengers by stop
        passengers_by_stop = {}
        for stop_idx in range(len(BUS_STOPS)):
            passengers_by_stop[stop_idx] = []

        for passenger in self.waiting_passengers:
            if passenger.state == "waiting":
                passengers_by_stop[passenger.stop_index].append(passenger)

        # Sort passengers at each stop by arrival time (FCFS)
        for stop_idx, passengers in passengers_by_stop.items():
            passengers.sort(key=lambda p: p.arrival_time)

            # Arrange passengers in a queue
            stop_x = BUS_STOPS[stop_idx]
            for i, passenger in enumerate(passengers):
                row = i // 5
                col = i % 5
                passenger.target_x = stop_x - 40 + col * 20
                passenger.target_y = BUS_STOP_Y - 30 - row * 25
                passenger.moving = True

    def draw(self, screen):
        """Draw the simulation state to the screen"""
        # Draw background
        screen.fill(SKY_BLUE)

        # Draw grass
        pygame.draw.rect(screen, GRASS_GREEN, (0, BUS_STOP_Y + 20, WIDTH, HEIGHT - BUS_STOP_Y - 20))

        # Draw road
        pygame.draw.rect(screen, ROAD_GRAY, (0, BUS_STOP_Y, WIDTH, 20))

        # Draw road markings
        for i in range(0, WIDTH, 40):
            pygame.draw.rect(screen, YELLOW, (i, BUS_STOP_Y + 10 - 2, 20, 4))

        # Draw bus stops
        for bus_stop in self.bus_stops:
            bus_stop.draw(screen)

        # Draw waiting passengers
        for passenger in self.waiting_passengers:
            passenger.draw(screen)

        # Draw bus
        self.bus.draw(screen)

        # Calculate bus utilization
        total_time = max(1, self.time)
        bus_utilization = (self.bus.busy_time / total_time) * 100

        # Draw stats panel
        self.stats_panel.draw(screen, self.waiting_passengers, self.bus.passengers,
                              self.completed_passengers, self.time, bus_utilization)

        # Draw Gantt chart
        self.gantt_chart.draw(screen, self.time)

        # Draw stats table
        self.stats_table.draw(screen, self.completed_passengers, self.time)

        # Draw simulation time and controls info in a compact panel at the bottom
        info_panel_height = 60
        pygame.draw.rect(screen, PANEL_BG, (0, HEIGHT - info_panel_height, WIDTH, info_panel_height))
        pygame.draw.line(screen, PANEL_BORDER, (0, HEIGHT - info_panel_height), (WIDTH, HEIGHT - info_panel_height), 2)

        # Draw simulation time
        time_text = title_font.render(f"Simulation Time: {self.time:.1f}s", True, BLACK)
        screen.blit(time_text, (20, HEIGHT - info_panel_height + 10))

        # Draw auto-generate status
        auto_gen_text = font.render(f"Auto-generate: {'ON' if self.auto_generate else 'OFF'} (Press A to toggle)",
                                    True, BLACK)
        screen.blit(auto_gen_text, (20, HEIGHT - info_panel_height + 35))

        # Draw controls hint
        controls_text = font.render("Controls: SPACE = Pause, R = Reset, N = New Passenger, LEFT/RIGHT = Scroll Chart",
                                    True, BLACK)
        screen.blit(controls_text, (WIDTH // 2, HEIGHT - info_panel_height + 20))

        # Draw simulation status (paused or running)
        if self.paused:
            pause_text = title_font.render("PAUSED", True, RED)
            screen.blit(pause_text, (WIDTH - pause_text.get_width() - 20, HEIGHT - info_panel_height + 20))

        # Update display
        pygame.display.flip()

    def run(self):
        """Main simulation loop"""
        running = True

        while running:
            # Process events
            running = self.handle_events()

            # Update simulation state
            self.update()

            # Draw current state
            self.draw(screen)

            # Maintain frame rate
            pygame.time.Clock().tick(FPS)


# Create and run the simulation
def main():
    # Initialize simulation
    simulation = BusSimulation()

    # Run simulation
    simulation.run()

    # Clean up
    pygame.quit()


# Only run the main function if this script is executed directly
if __name__ == "__main__":
    main()

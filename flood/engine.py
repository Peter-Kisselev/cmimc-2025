from typing import List, Tuple, Type
from bots.bot import Bot
from scipy.interpolate import RegularGridInterpolator
import numpy as np

class FloodResult:
    def __init__(self, num_alive: int, difficulty: int, seed: int):
        self.num_alive = num_alive
        self.difficulty = difficulty
        self.seed = seed

    def print_result(self) -> None:
        difficulty_strings = ["Easy", "Medium", "Hard"]
        difficulty_string = difficulty_strings[self.difficulty]
        print(f"Number of Bots Alive on Difficulty {difficulty_string}, Seed {self.seed}: {self.num_alive}")

class FloodSimulator:
    @staticmethod
    def _generate_cubic(coarse_size: int, fine_size: int) -> np.ndarray:
        pad = 3
        padded_size = coarse_size + pad

        coarse_grid = np.random.rand(padded_size, padded_size)
        coarse_grid[coarse_size:coarse_size+pad, :] = coarse_grid[0:pad, :]
        coarse_grid[:, coarse_size:coarse_size+pad] = coarse_grid[:, 0:pad]

        coord_coarse = np.linspace(
            -1.0 / coarse_size,
            1.0 + 1.0 / coarse_size,
            padded_size
        )

        coord_fine = np.linspace(0.0, 1.0, fine_size, endpoint=False)
        grid_x, grid_y = np.meshgrid(coord_fine, coord_fine)
        sample_pts = np.column_stack((grid_x.ravel(), grid_y.ravel()))

        interpolator = RegularGridInterpolator(
            (coord_coarse, coord_coarse),
            coarse_grid,
            method='cubic'
        )
        fine_grid = interpolator(sample_pts).reshape(fine_size, fine_size)

        min_val, max_val = fine_grid.min(), fine_grid.max()
        normalized = (fine_grid - min_val) / (max_val - min_val)

        return normalized

    @staticmethod
    def _generate_easy(grid_size: int) -> np.ndarray:
        base_noise = FloodSimulator._generate_cubic(16, grid_size) - 0.1
        terrain = np.copy(base_noise)
        terrain[base_noise < 0.] *= 5000.
        terrain[base_noise > 0.] *= 200.
        terrain += 500
        return terrain + FloodSimulator._generate_cubic(64, grid_size) * 50.

    @staticmethod
    def _generate_medium(grid_size: int) -> np.ndarray:
        num_blobs = 8

        blob_heights = np.sqrt(np.random.rand(num_blobs, num_blobs)) * 700.

        repeat_factor = grid_size // num_blobs
        upsampled_blobs = np.repeat(blob_heights, repeat_factor, 0)
        upsampled_blobs = np.repeat(upsampled_blobs, repeat_factor, 1)

        mid_noise = FloodSimulator._generate_cubic(64, grid_size) * 200.

        terrain = upsampled_blobs + mid_noise
        return terrain

    @staticmethod
    def _generate_hard(grid_size: int) -> np.ndarray:
        base_noise = FloodSimulator._generate_cubic(16, grid_size) - 0.15

        terrain = base_noise.copy()
        terrain[base_noise < 0.] *= 5000.
        terrain[base_noise > 0.] *= 200.
        terrain += 750

        detail_noise = FloodSimulator._generate_cubic(64, grid_size)
        terrain += detail_noise * 50.

        weights = 68. * np.random.rand(8) + 30.
        offsets = (weights / weights.sum() * grid_size).cumsum().astype(int)
        np.random.shuffle(offsets)
        y0 = np.random.randint(0, grid_size)

        for ridge_index, offset in enumerate(offsets, start=1):
            center_x = np.random.randint(0, grid_size)
            center_y = y0 + offset

            cap_height = ridge_index * 100. - 50.

            for dy in range(-1, 1 + 1):
                y = (center_y + dy) % grid_size
                xs = (np.arange(center_x - 200, center_x + 200 + 1) % grid_size)
                terrain[xs, y] = np.minimum(cap_height, terrain[xs, y])

        return terrain

    def initialize(self, bot: Type[Bot], difficulty: int, seed: int, grid_size: int = 512, view_radius: int = 8, message_len: int = 32, num_bots: int = 64) -> None:
        self.grid_size = grid_size
        self.view_radius = view_radius
        self.message_len = message_len
        self.num_bots = num_bots

        np.random.seed(seed)
        self.flood_height = 0.

        self.terrain = None
        if difficulty == 0:
            self.terrain = self._generate_easy(grid_size)
        elif difficulty == 1:
            self.terrain = self._generate_medium(grid_size)
        elif difficulty == 2:
            self.terrain = self._generate_hard(grid_size)
        else:
            raise ValueError(f"Invalid difficulty {difficulty}.")
        self.terrain_padded = np.pad(self.terrain, view_radius, mode="wrap")

        self.max_height = np.max(self.terrain)

        self.num_alive = num_bots
        self.is_alive = [True] * num_bots

        self.bots = [bot(i, difficulty) for i in range(num_bots)]
        self.positions = [(np.random.randint(0, grid_size), np.random.randint(0, grid_size)) for _ in range(num_bots)]
        self.messages = [0] * num_bots

    def step(self) -> bool:
        nxt_positions = [None for _ in range(self.num_bots)]
        nxt_messages = [0 for _ in range(self.num_bots)]
        for i in range(self.num_bots):
            if self.is_alive[i]:
                x, y = self.positions[i]

                height = self.terrain_padded[x:x+2*self.view_radius+1, y:y+2*self.view_radius+1]
                neighbors = []

                for j in range(self.num_bots):
                    if self.is_alive[j]:
                        w, z = self.positions[j]
                        dx, dy = w - x, z - y

                        half = self.grid_size // 2

                        if dx > half:
                            dx -= self.grid_size
                        elif dx < -half:
                            dx += self.grid_size

                        if dy > half:
                            dy -= self.grid_size
                        elif dy < -half:
                            dy += self.grid_size

                        if abs(dx) <= self.view_radius and abs(dy) <= self.view_radius:
                            neighbors.append((dx, dy, self.messages[j]))

                dx, dy, new_message = self.bots[i].step(height, neighbors)

                if abs(dx) > 1:
                    raise ValueError(f"Step {dx} too large.")
                if abs(dy) > 1:
                    raise ValueError(f"Step {dy} too large.")
                if new_message < 0 or new_message >= (1 << self.message_len):
                    raise ValueError(f"Message {new_message} does not abide to constraints.")

                nxt_positions[i] = ((x + dx) % self.grid_size, (y + dy) % self.grid_size)
                nxt_messages[i] = new_message

        self.flood_height += 1.0
        if self.flood_height > self.max_height:
            self.flood_height = self.max_height

        for i in range(self.num_bots):
            if self.is_alive[i]:
                nx, ny = nxt_positions[i]
                if self.terrain[nx, ny] < self.flood_height:
                    self.is_alive[i] = False
                    self.num_alive -= 1
                else:
                    self.positions[i] = nxt_positions[i]
                    self.messages[i] = nxt_messages[i]

        if self.flood_height >= self.max_height or self.num_alive <= 0:
            return True
        return False

class FloodEngine:
    def grade(self, bot: Type[Bot], difficulty: int, seed: int, grid_size: int = 512, view_radius: int = 8, message_len: int = 32, num_bots: int = 64) -> FloodResult:
        simulator = FloodSimulator()
        simulator.initialize(bot, difficulty, seed, grid_size, view_radius, message_len, num_bots)

        stop = False
        while not stop:
            stop = simulator.step()
        num_alive = simulator.num_alive

        return FloodResult(num_alive, difficulty, seed)

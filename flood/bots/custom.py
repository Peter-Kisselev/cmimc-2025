from bots.bot import Bot
from typing import List, Tuple
import random
import numpy as np


VIEW = 8
GRID_SIZE = 512

# Simple bot that walks towards peaks, doesn't communicate other than saying its id
class customBot(Bot):
    def __init__(self, index: int, difficulty: int):
        self.index = index
        self.difficulty = difficulty

        self.map = np.zeros((GRID_SIZE, GRID_SIZE))

        # pick one direction based on index
        moves = [[-1,-1],[-1,0],[-1,1],[0,-1],[0,1],[1,-1],[1,0],[1,1]]
        self.movex, self.movey = moves[index & 0x7]

    def getTruePos(pos):
        newPos = pos
        pos
        return

    def step(self, height: np.ndarray, neighbors: List[Tuple[int, int, int]]) -> Tuple[int, int, int]:
        sign = lambda x: -1 if x < 0 else (0 if x == 0 else 1)

        # Index of highest point in field of view
        ind = np.unravel_index(np.argmax(height, axis=None), height.shape)

        # move towards higher points
        if height[ind] > height[VIEW,VIEW]:
            movex = sign(ind[0] - VIEW)
            movey = sign(ind[1] - VIEW)

        # stay if higher than adjacent points (note argmax default to 0,0)
        elif ind[0] == VIEW and ind[1] == VIEW:
            movex = 0
            movey = 0

        else:
            movex = self.movex
            movey = self.movey

        m = self.index

        return (movex, movey, m)

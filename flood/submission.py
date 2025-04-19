from typing import List, Tuple
from bots.bot import Bot
import random
import numpy as np

view_radius = 8

class SubmissionBot(Bot):
    DEBUG = False
    
    ### PASTE BELOW THIS LINE TO AVOID DEBUG ERRORS ###

    def __init__(self, index: int, difficulty: int):
        self.index = index
        self.difficulty = difficulty

        # pick one direction based on index
        moves = [[-1,-1],[-1,0],[-1,1],[0,-1],[0,1],[1,-1],[1,0],[1,1]]
        self.movex, self.movey = moves[index & 0x7]

    def step(self, height: np.ndarray, neighbors: List[Tuple[int, int, int]]) -> Tuple[int, int, int]:
        sign = lambda x: -1 if x < 0 else (0 if x == 0 else 1)

        # Index of highest point in field of view
        ind = np.unravel_index(np.argmax(height, axis=None), height.shape)

        # move towards higher points
        if height[ind] > height[view_radius,view_radius]: 
            movex = sign(ind[0] - view_radius)
            movey = sign(ind[1] - view_radius)

        # stay if higher than adjacent points (note argmax default to 0,0)
        elif ind[0] == view_radius and ind[1] == view_radius:
            movex = 0
            movey = 0

        else:
            movex = self.movex
            movey = self.movey

        m = self.index

        return (movex, movey, m)

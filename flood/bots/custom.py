from bots.bot import Bot
from typing import List, Tuple
import random
import numpy as np

# Simple bot that walks towards peaks, doesn't communicate other than saying its id
class customBot(Bot):
    DEBUG = True

    VIEW = 8
    GRID_SIZE = 512

    UNSEEN = 1 if DEBUG else 10000

    def fullprint(self, arr):
        with np.printoptions(threshold=np.inf):
            print(arr)

    # View mapped area
    def saveCache(self, arr):
        # Copy to avoid modifying original
        newArr = arr.copy()

        # Define quadrants
        Q1 = arr[0:256, 0:256]
        Q2 = arr[0:256, 256:512]
        Q3 = arr[256:512, 0:256]
        Q4 = arr[256:512, 256:512]

        # Step 1: Q1 <-> Q4
        newArr[0:256, 0:256] = Q4  # Q1 becomes Q4
        newArr[256:512, 256:512] = Q1  # Q4 becomes Q2

        # Step 2: Q2  <-> Q3
        newArr[256:512, 0:256] = Q2  # Q3 becomes Q2
        newArr[0:256, 256:512] = Q3  # Q2 becomes Q3
        np.savetxt("/flood/cache.txt", arr, delimiter=",", fmt="%3d")
        np.savetxt("flood/cacheResown.txt", newArr, delimiter=",", fmt="%3d")

    def __init__(self, index: int, difficulty: int):

        self.index = index
        self.difficulty = difficulty

        self.cache = np.full((self.GRID_SIZE, self.GRID_SIZE), self.UNSEEN)
        self.pos = np.array([0, 0])

        # pick one direction based on index
        moves = [[-1,-1],[-1,0],[-1,1],[0,-1],[0,1],[1,-1],[1,0],[1,1]]
        self.movex, self.movey = moves[index & 0x7]

    def getTruePos(self, pos) -> np.ndarray[int, int]:
        newPos = []
        for p in pos:
            if p < 0:
                newPos.append(self.GRID_SIZE + p)
            elif p >= self.GRID_SIZE:
                newPos.append(p - self.GRID_SIZE)
            else:
                newPos.append(p)
        return np.array(newPos)

    def updateCache(self, heights):
        for i in range(len(heights)):
            for j in range(len(heights[0])):
                curPos = self.getTruePos([j - self.VIEW + self.pos[0], i - self.VIEW + self.pos[1]])
                if self.index == 1:
                    print(curPos)
                self.cache[curPos[1]][curPos[0]] = heights[i][j]
        if self.DEBUG and self.index == 1:
            print(self.pos)
            self.saveCache(self.cache)
            # self.fullprint(self.cache)

    def step(self, height: np.ndarray, neighbors: List[Tuple[int, int, int]]) -> Tuple[int, int, int]:
        sign = lambda x: -1 if x < 0 else (0 if x == 0 else 1)
        self.updateCache(height)

        # Index of highest point in field of view
        ind = np.unravel_index(np.argmax(height, axis=None), height.shape)

        # move towards higher points
        if height[ind] > height[self.VIEW, self.VIEW]:
            movex = sign(ind[0] - self.VIEW)
            movey = sign(ind[1] - self.VIEW)

        # stay if higher than adjacent points (note argmax default to 0,0)
        elif ind[0] == self.VIEW and ind[1] == self.VIEW:
            movex = 0
            movey = 0

        else:
            movex = self.movex
            movey = self.movey

        self.pos[0] += movex
        self.pos[1] += movey
        self.pos = self.getTruePos(self.pos)

        m = self.index

        return (movex, movey, m)

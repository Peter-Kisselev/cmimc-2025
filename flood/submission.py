from typing import List, Tuple
from bots.bot import Bot
import random
import numpy as np

view_radius = 8

class SubmissionBot(Bot):
    DEBUG = False

    ### PASTE BELOW THIS LINE TO AVOID DEBUG ERRORS ###

    # Constants
    VIEW = 8
    VIEW_FULL = 17
    GRID_SIZE = 512
    DEBUG_INDEX = 5
    UNSEEN = 1 if DEBUG else -10000

    # Parameters (tweak by hand) but constant at runtime
    EXPLORE = 300
    ESCAPE_MAX = 30
    HIST_LEN = 3
    MIN_GRAD = 0.5
    MOMENTUM_MAX = 2

    def rTF(self) -> bool:
        return random.choice([True, False])

    # print only on debug
    def cPrint(self, val=""):
        if self.DEBUG:
            print(val)

    # print big array
    def fullprint(self, arr):
        if self.DEBUG:
            with np.printoptions(threshold=np.inf, linewidth=np.inf):
                self.cPrint(arr)

    # View mapped area
    def saveCache(self, arr):
        if self.DEBUG:
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
            np.savetxt("flood/data/cache.txt", arr, delimiter=",", fmt="%3d")
            np.savetxt("flood/data/cacheResown.txt", newArr, delimiter=",", fmt="%3d")

    # initialize class
    def __init__(self, index: int, difficulty: int):

        self.index = index
        self.difficulty = difficulty
        self.cache = np.full((self.GRID_SIZE, self.GRID_SIZE), self.UNSEEN, dtype=float)
        self.pos = np.array([0, 0])
        self.bestPos = [[0, 0], self.UNSEEN]
        self.TURN = 0
        self.ESCAPE = 0
        self.posHist = [[0,0],[0,0]]
        self.momentum = 0

        # pick one direction based on index
        moves = [[-1,-1],[-1,0],[-1,1],[0,-1],[0,1],[1,-1],[1,0],[1,1]]
        self.movey, self.movex = moves[index % 8]

    # wraparound
    def getTruePos(self, pos) -> np.ndarray[int, int]:
        return pos%self.GRID_SIZE

    # Relative position of points on torus grid given an "origin"
    def torusRelPos(self, origin, pos):
        dx = ((pos[1] - origin[1] + self.GRID_SIZE//2) % self.GRID_SIZE) - self.GRID_SIZE//2
        dy = ((pos[0] - origin[0] + self.GRID_SIZE//2) % self.GRID_SIZE) - self.GRID_SIZE//2
        return np.array([dy, dx])

    # Pack binary message
    def packMsg(self, bestPos) -> int:
        wa = 9
        wb = 9
        wc = 10
        a = bestPos[0][0]
        b = bestPos[0][1]
        c = bestPos[1]
        c = int(c) # approximate to fit in msg

        aS = np.binary_repr(a, wa)
        bS = np.binary_repr(b, wb)
        cS = format(c, f'0{wc}b')

        payload = aS + bS + cS
        return int(payload.zfill(32), 2)

    # Convert signed fields via two's‑complement
    def decodeSigned(self, bits: str) -> int:
        val = int(bits, 2)
        if bits[0] == '1':
            val += -(1 << len(bits))
        return val

    # Unpack binary message
    def unpackMsg(self, msg: int) -> tuple[int, int, int]:
        bits = bin(msg)[2:].zfill(32)
        wa = 9
        wb = 9
        wc = 10
        a_str = bits[0:wa]
        b_str = bits[wa:wa+wb]
        c_str = bits[-wc:]

        a = self.decodeSigned(a_str)
        b = self.decodeSigned(b_str)
        c = int(c_str, 2)
        return [a, b, c]

    # Avoid hitting known values, get only new positions (n^2 -> 2n complexity)
    def slidingWindow(self, pos, dx, dy):
        half = self.VIEW
        x0_new = pos[1] - half  # cache origin x
        y0_new = pos[0] - half  # cache origin y
        bands = []

        if dy != 0:
            if dy > 0:
                y_edge = y0_new + self.VIEW_FULL - 1  # Bottom edge of new view
            else:
                y_edge = y0_new  # Top edge of new view
            x_vals = np.arange(x0_new, x0_new + self.VIEW_FULL)
            local_y = y_edge - y0_new
            local_x = x_vals - x0_new
            row = np.stack((np.full(self.VIEW_FULL, y_edge), x_vals, np.full(self.VIEW_FULL, local_y), local_x), axis=1)
            bands.append(row)

        if dx != 0:
            if dx > 0:
                x_edge = x0_new + self.VIEW_FULL - 1  # Right edge of new view
            else:
                x_edge = x0_new  # Left edge of new view
            y_vals = np.arange(y0_new, y0_new + self.VIEW_FULL)
            local_x = x_edge - x0_new
            local_y = y_vals - y0_new
            col = np.stack((y_vals, np.full(self.VIEW_FULL, x_edge), local_y, np.full(self.VIEW_FULL, local_x)), axis=1)
            bands.append(col)

        if not bands:
            return np.empty((0, 4), dtype=int)
        # Stack as [cache_y, cache_x, local_y, local_x]
        all_cells = np.vstack(bands)
        return all_cells # allow duplicated corner when moving diagonally, performance cost is small

    # Update known values with new things and update best position
    def updateCache(self, heights):
        for val in self.slidingWindow(self.pos, self.movex, self.movey):
            cache_pos = val[:2]
            local_y = val[2]
            local_x = val[3]

            # if (0 <= local_y < self.VIEW_FULL) and (0 <= local_x < self.VIEW_FULL):
            h = heights[local_y][local_x]
            curPos = self.getTruePos(cache_pos)
            self.cache[curPos[0]][curPos[1]] = h
            if h > self.bestPos[1]:
                self.bestPos = [curPos.copy(), h]

    # Use neighbor info
    def readNbrs(self, nbrs):
        for nbr in nbrs:
            rPos = [nbr[1], nbr[0]]
            msg = self.unpackMsg(nbr[2])
            bH = msg.pop(2)
            # bP = [self.pos[0] + rPos[0] + msg[0], self.pos[1] + rPos[1] + msg[1]]
            bP = np.add(self.pos, np.add(rPos, msg))
            newP = self.getTruePos(bP)

            if self.cache[newP[0]][newP[1]] == self.UNSEEN:
                self.cache[newP[0]][newP[1]] = bH
                if bH > self.bestPos[1]:
                    self.bestPos = [newP.copy(), bH]

    # Compute gradient based on 3x3 grid centered on current position (for continuous section)
    def contGrad(self, heights):
        center = len(heights) // 2
        gx = (heights[center, center + 1] - heights[center, center - 1]) * 0.5
        gy = (heights[center + 1, center] - heights[center - 1, center]) * 0.5
        return np.array([gy, gx])

    # perform a step
    def step(self, height: np.ndarray, neighbors: List[Tuple[int, int, int]]) -> Tuple[int, int, int]:
        height = height.transpose()
        sign = lambda x: -1 if x < 0 else (0 if x == 0 else 1)

        self.updateCache(height)
        self.readNbrs(neighbors)

        if self.TURN > self.EXPLORE:
            if self.bestPos[1] > self.cache[self.pos[0]][self.pos[1]]:
                dy, dx = self.torusRelPos(self.pos, self.bestPos[0])

                movex = sign(dx)
                movey = sign(dy)
            elif self.bestPos[1] == self.cache[self.pos[0]][self.pos[1]]:
                grad = self.contGrad(height)
                if sum(grad**2) > self.MIN_GRAD*0.5:
                    movey = sign(grad[0])
                    movex = sign(grad[1])
                else:
                    movex = 0
                    movey = 0
            else:
                movex = self.movex
                movey = self.movey
        else:
            if self.momentum == 0:
                self.posHist.append(self.pos.copy())
                if len(self.posHist) > self.HIST_LEN:
                    self.posHist.pop(0)
                self.cPrint(self.posHist)
                self.cPrint(self.pos)

                grad = self.contGrad(height)
                if (sum(grad**2) > self.MIN_GRAD) and (any(self.pos[i] != self.posHist[0][i] for i in range(len(self.pos)))):
                    movey = sign(round(grad[0]))
                    movex = sign(round(grad[1]))
                    self.momentum = self.MOMENTUM_MAX
                else:
                    self.momentum = self.ESCAPE_MAX
                    # movex = int(self.rTF())*2-1
                    # movey = int(self.rTF())*2-1
                    movey = -sign(grad[0])
                    movex = -sign(grad[1])
            else:
                movex = self.movex
                movey = self.movey
                self.momentum += -1

        self.pos[1] += movex
        self.pos[0] += movey

        self.movex = movex
        self.movey = movey

        self.pos = self.getTruePos(self.pos)

        # bestPos
        relPos = [self.torusRelPos(self.pos, self.bestPos[0]), self.bestPos[1]]
        m = self.packMsg(relPos)

        # Increment turn counter
        self.TURN += 1
        return (movex, movey, m)
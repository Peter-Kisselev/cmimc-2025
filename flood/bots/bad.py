from bots.bot import Bot
from typing import List, Tuple
import random
import numpy as np
import math

# Simple bot that walks towards peaks, doesn't communicate other than saying its id
class customBot7(Bot):
    DEBUG = True

    ### COPY BELOW THIS LINE TO AVOID DEBUG ERRORS ###

    # Constants
    VIEW = 8
    VIEW_FULL = 17
    GRID_SIZE = 512
    DEBUG_INDEX = 5
    UNSEEN = 1 if DEBUG else -10000

    # Parameters (tweak by hand) but constant at runtime
    GRAD_SMOOTH = 2
    ESCAPE_MAX = 20
    HIST_LEN = 3
    MIN_GRAD = 5
    MOMENTUM_MAX = 3

    # Manhattan distance
    def mDist(self, p1, p2) -> int:
        return sum(abs(p1 - p2))

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

        self.id = index
        self.difficulty = difficulty
        self.cache = np.full((self.GRID_SIZE, self.GRID_SIZE), self.UNSEEN, dtype=float)
        self.pos = np.array([0, 0])
        self.bestPos = [[0, 0], self.UNSEEN]
        self.TURN = 0
        self.ESCAPE = 0
        self.posHist = [[0,0],[0,0]]
        self.momentum = 0

        self.sideChance = 10
        self.newChance = 0

        if difficulty == 0:
            self.EXPLORE = 350
        elif difficulty == 1:
            self.EXPLORE = 250
        elif difficulty == 2:
            self.EXPLORE = 350

        # pick one direction based on index
        moves = [[-1,-1],[-1,0],[-1,1],[0,-1],[0,1],[1,-1],[1,0],[1,1]]
        self.dy, self.dx = moves[index % 8]

        self.directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),          (0, 1),
            (1, -1),  (1, 0), (1, 1)
        ]

        self.noUp = False

        self.slideCache = {}

        self.gaps = []

    # wraparound
    def getTruePos(self, pos) -> np.ndarray[int, int]:
        return pos%self.GRID_SIZE

    # Relative position of points on torus grid given an "origin"
    def torusRelPos(self, origin, pos):
        dx = ((pos[1] - origin[1] + self.GRID_SIZE//2) % self.GRID_SIZE) - self.GRID_SIZE//2
        dy = ((pos[0] - origin[0] + self.GRID_SIZE//2) % self.GRID_SIZE) - self.GRID_SIZE//2
        return np.array([dy, dx])

    # Toroidal distance
    def torDist(self, origin, p):
        return self.mDist(origin, self.torusRelPos(origin, p))

    # Decode signed binary: if sign bit is 1, subtract 2^len(bits)
    def decodeSigned(self, bits: str) -> int:
        val = int(bits, 2)
        if bits[0] == '1':
            val -= (1 << len(bits))
        return val

    # Pack binary message
    def packMsg(self, bestPos) -> int:
        # widths: 10 bits signed a, 10 bits signed b, 10 bits unsigned c
        wa = 10
        wb = 10
        wc = 10
        a = bestPos[0][0]
        b = bestPos[0][1]
        c = int(bestPos[1])  # ensure integer (lose only tiny amount of precision)

        a_raw = a & ((1 << wa) - 1)
        b_raw = b & ((1 << wb) - 1)
        c_raw = c & ((1 << wc) - 1)

        payload = (a_raw << (wb + wc)) | (b_raw << wc) | c_raw
        return payload

    # Unpack binary message
    def unpackMsg(self, msg: int) -> tuple[int, int, int]:
        wa = 10
        wb = 10
        wc = 10
        offSet = 32-wa-wb-wc
        bits = bin(msg)[2:].zfill(32)

        a_str = bits[offSet:offSet+wa]
        b_str = bits[offSet+wa:offSet+wa+wb]
        c_str = bits[offSet+wa+wb:]

        a = self.decodeSigned(a_str)
        b = self.decodeSigned(b_str)
        c = int(c_str, 2)
        return [a, b, c]

    # Use neighbor info
    def readNbrs(self, nbrs):
        for nbr in nbrs:
            rPos = [nbr[1], nbr[0]]
            if sum(rPos) == 0: continue #check if self
            msg = self.unpackMsg(nbr[2])
            bH = msg.pop(2)
            bP = np.add(np.add(self.pos, rPos), msg)
            newP = self.getTruePos(bP)

            if self.cache[newP[0]][newP[1]] == self.UNSEEN:
                self.cache[newP[0]][newP[1]] = bH
                if bH >= self.bestPos[1]:
                    self.bestPos = [newP.copy(), bH]

    # Avoid hitting known values, get only new positions (n^2 -> 2n complexity)
    def slidingWindow(self, pos, dx, dy):
        key = (int(pos[0]), int(pos[1]), dx, dy)
        if key in self.slideCache:
            return self.slideCache[key]

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

        self.slideCache[key] = all_cells
        return all_cells # allow duplicated corner when moving diagonally, performance cost is small

    # Update known values with new things and update best position
    def updateCache(self, heights):
        for val in self.slidingWindow(self.pos, self.dx, self.dy):
            cache_pos = val[:2]
            local_y = val[2]
            local_x = val[3]

            # if (0 <= local_y < self.VIEW_FULL) and (0 <= local_x < self.VIEW_FULL):
            h = heights[local_y][local_x]
            curPos = self.getTruePos(cache_pos)
            self.cache[curPos[0]][curPos[1]] = h
            if h > self.bestPos[1]:
                self.bestPos = [curPos.copy(), h]

    # SLOW FIRST UPDATE of caching
    def updateCacheSLOW(self, heights):
        for i in range(len(heights)):
            for j in range(len(heights[0])):
                # curPos = self.getTruePos([i - self.VIEW + self.pos[0], j - self.VIEW + self.pos[1]])
                curPos = self.getTruePos(np.add(self.pos-self.VIEW,[i,j]))
                h = heights[i][j]
                self.cache[curPos[0]][curPos[1]] = h
                if h > self.bestPos[1]:
                    self.bestPos = [curPos.copy(), h]

    # Compute gradient based on 3x3 grid centered on current position (for continuous section)
    def contGrad(self, heights):
        center = len(heights) // 2
        gxTot = 0
        gyTot = 0
        for i in range(self.GRAD_SMOOTH):
            gxTot += (heights[center, center + i] - heights[center, center - i]) / 2
            gyTot += (heights[center + i, center] - heights[center - i, center]) / 2
        return np.array([gyTot/self.GRAD_SMOOTH, gxTot/self.GRAD_SMOOTH])

    # Detect moving into water and turn (pos is assumed to be after dy and dx appied)
    def avoidWater(self, pos):
        safe = []
        level = self.TURN + 1
        for dy, dx in self.directions:
        # for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            newPos = self.getTruePos(np.add(pos,[dy,dx]))
            if self.cache[newPos[0], newPos[1]] > level:
                safe.append((dy, dx))
        return safe

    # Go towards most unchecked
    def mostUnchecked(self, pos):
        maxCount = 0
        bestDir = (0, 0)

        for dx, dy in self.directions:
        # for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            newPos = np.add(pos, [dy, dx])
            counter = 0

            for val in self.slidingWindow(newPos, self.dx, self.dy):
                cache_pos = val[:2]
                curPos = self.getTruePos(cache_pos)
                p = self.cache[curPos[0]][curPos[1]]
                if p == self.UNSEEN:
                    counter += 1
            if counter > maxCount:
                maxCount = counter
                bestDir = (dy, dx)
        return bestDir

    # perform a step
    def step(self, height: np.ndarray, neighbors: List[Tuple[int, int, int]]) -> Tuple[int, int, int]:
        height = height.transpose()
        sign = lambda x: -1 if x < 0 else (0 if x == 0 else 1)

        if self.TURN <= 4:
            self.updateCacheSLOW(height)
        else:
            self.updateCache(height)

        self.readNbrs(neighbors)

        if self.difficulty == 0:
            if self.bestPos[1] > 700:
                self.sideChance = self.newChance
        elif self.difficulty == 1:
            if self.bestPos[1] > 800:
                self.sideChance = self.newChance
        else:
            if self.bestPos[1] > 950:
                self.sideChance = self.newChance

        # if self.TURN >= self.EXPLORE-50:
        #     self.EXPLORE += -1*max(self.torDist(self.pos, self.bestPos[0])-20, 0)

        if self.momentum == 0:
            if self.TURN > self.EXPLORE:
                self.momentum = 0
                if self.bestPos[1] > self.cache[self.pos[0]][self.pos[1]]:
                    dely, delx = self.torusRelPos(self.pos, self.bestPos[0])
                    dx = sign(delx)
                    dy = sign(dely)
                elif self.bestPos[1] == self.cache[self.pos[0]][self.pos[1]]:
                    # grad = self.contGrad(height)
                    # if sum(grad**2) > 200*self.MIN_GRAD:
                    #     dy = sign(grad[0])
                    #     dx = sign(grad[1])
                    # else:
                        dx = 0
                        dy = 0
                        self.dx = 0
                        self.dy = 0
                else:
                    dx = self.dx
                    dy = self.dy
            else:
                self.posHist.append(self.pos.copy())
                if len(self.posHist) > self.HIST_LEN:
                    self.posHist.pop(0)

                grad = self.contGrad(height)
                if (sum(grad**2) > self.MIN_GRAD) and (any(self.pos[i] != self.posHist[0][i] for i in range(len(self.pos)))):
                    dy = sign(round(grad[0]))
                    dx = sign(round(grad[1]))
                    self.momentum = self.MOMENTUM_MAX
                else:
                    dy, dx = self.mostUnchecked(self.pos)
                    self.momentum = self.ESCAPE_MAX//2
                    if dy + dx == 0:
                        dx = 1
                        dy = 1
                        self.momentum = self.ESCAPE_MAX//2
                    # dy = -sign(grad[0])
                    # dx = -sign(grad[1])
        else:
            dx = self.dx
            dy = self.dy

            rand = random.randint(0,self.sideChance)
            if rand == 0:
                dx = -dx
                self.noUp = True
            # elif rand == 1:
            #     dy = -dy
            #     self.noUp = True

            self.momentum += -1

        # If moving into water, simply turn around
        available = self.avoidWater(self.pos)
        if dy + dx != 0 and not((dy, dx) in available):
            if available:
                newDir = random.choice(available)
            else:
                newDir = (0, 0)
            dx = newDir[1]
            dy = newDir[0]
            self.dx = dx
            self.dy = dy
            self.momentum = 30 if self.TURN <= self.EXPLORE else 20

        self.pos[1] += dx
        self.pos[0] += dy
        if not self.noUp:
            self.dx = dx
            self.dy = dy
        self.noUp = False

        # if self.bestPos[1] == 953:

        self.pos = self.getTruePos(self.pos)

        relPos = [self.torusRelPos(self.pos, self.bestPos[0]), self.bestPos[1]]
        m = self.packMsg(relPos)

        # Increment turn counter
        self.TURN += 1
        return (dx, dy, m)
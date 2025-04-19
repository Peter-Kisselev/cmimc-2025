from bots.bot import Bot
from typing import List, Tuple
import random
import numpy as np

# Simple bot that walks towards peaks, doesn't communicate other than saying its id
class customBot(Bot):
    DEBUG = True

    ### COPY BELOW THIS LINE TO AVOID DEBUG ERRORS ###

    VIEW = 8
    GRID_SIZE = 512
    DEBUG_INDEX = 5

    UNSEEN = 1 if DEBUG else -10000

    EXPLORE = 10

    def rTF(self) -> bool:
        return random.choice([True, False])

    # print only on debug
    def cPrint(self, val=""):
        if self.DEBUG:
            print(val)

    # print big array
    def fullprint(self, arr):
        if self.DEBUG:
            with np.printoptions(threshold=np.inf):
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

        self.cache = np.full((self.GRID_SIZE, self.GRID_SIZE), self.UNSEEN)
        self.pos = np.array([0, 0])

        self.bestPos = [[0, 0], 0]

        self.TURN = 0

        # pick one direction based on index
        moves = [[-1,-1],[-1,0],[-1,1],[0,-1],[0,1],[1,-1],[1,0],[1,1]]
        self.movex, self.movey = moves[index & 0x7]

    # wraparound
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

    # Relative position of points on torus grid given an "origin"
    def torusRelPos(self, origin, pos):
        dx = ((pos[0] - origin[0] + self.GRID_SIZE//2) % self.GRID_SIZE) - self.GRID_SIZE//2
        dy = ((pos[1] - origin[1] + self.GRID_SIZE//2) % self.GRID_SIZE) - self.GRID_SIZE//2
        return [dx, dy]

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
        return a, b, c

    # update "map"
    def updateCache(self, heights):
        for i in range(len(heights)):
            for j in range(len(heights[0])):
                curPos = self.getTruePos([j - self.VIEW + self.pos[0], i - self.VIEW + self.pos[1]])
                self.cache[curPos[1]][curPos[0]] = heights[i][j]
        if self.DEBUG and self.index == self.DEBUG_INDEX:
            # self.cPrint(self.pos)
            self.saveCache(self.cache)

    # Use neighbor info
    def readNbrs(self, nbrs):
        for nbr in nbrs:
            rPos = [nbr[0], nbr[1]]
            msg = self.unpackMsg(nbr[2])

            bP = [self.pos[0] + rPos[0] + msg[0], self.pos[1] + rPos[1] + msg[1]]
            bH = msg[2]
            newP = self.getTruePos(bP)
            # self.cache[newP[1]][newP[0]] = bH

    # perform a step
    def step(self, height: np.ndarray, neighbors: List[Tuple[int, int, int]]) -> Tuple[int, int, int]:
        sign = lambda x: -1 if x < 0 else (0 if x == 0 else 1)

        if self.index == self.DEBUG_INDEX:
            self.cPrint("test")

        self.updateCache(height)
        self.readNbrs(neighbors)

        # Index of highest point in field of view
        bP = tuple([*np.unravel_index(np.argmax(self.cache), self.cache.shape)][::-1])
        if self.cache[bP[1]][bP[0]] > self.bestPos[1]:
            self.bestPos = [bP, self.cache[bP[1]][bP[0]]]
        bP = self.bestPos[0]

        if self.TURN > self.EXPLORE:
            if self.index == self.DEBUG_INDEX:
                rP = self.torusRelPos(self.pos, bP)
                self.cPrint()
                self.cPrint(self.index)
                self.cPrint([int(num) for num in self.pos])
                self.cPrint([int(num) for num in self.bestPos[0]])
                self.cPrint(self.cache[self.pos[1]][self.pos[0]])
                self.cPrint(self.cache[bP[1]][bP[0]])
                self.cPrint(self.bestPos[1])
                self.cPrint(self.cache[np.unravel_index(np.argmax(self.cache), self.cache.shape)])
                self.cPrint([int(num) for num in rP])

            # move towards higher points
            if self.cache[bP[1]][bP[0]] > self.cache[self.pos[1]][self.pos[0]]:
                rP = self.torusRelPos(self.pos, bP)

                movex = sign(rP[0])
                movey = sign(rP[1])
            elif self.cache[bP[1]][bP[0]] == self.cache[self.pos[1]][self.pos[0]]:
                movex = 0
                movey = 0
            else:
                movex = self.movex
                movey = self.movey
        else:
            random.choice([True, False])
            # movex = self.movex
            # movey = self.movey
            movex = int(self.rTF())*2-1
            movey = int(self.rTF())*2-1

        self.pos[0] += movex
        self.pos[1] += movey
        self.pos = self.getTruePos(self.pos)

        # bestPos
        relPos = [self.torusRelPos(self.pos, self.bestPos[0]), self.bestPos[1]]
        m = self.packMsg(relPos)

        # Increment turn counter
        self.TURN += 1
        return (movex, movey, m)

from bots.bot import Bot
from typing import List, Tuple, Optional
import random
import numpy as np
# import math
from heapq import heappush, heappop


# Simple bot that walks towards peaks, doesn't communicate other than saying its id
class testBot(Bot):
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
    EXPLORE = 370
    ESCAPE_MAX = 32
    HIST_LEN = 3
    MIN_GRAD = 0.5
    MOMENTUM_MAX = 3

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
        self.dy, self.dx = moves[index % 8]

    # wraparound
    def getTruePos(self, pos) -> np.ndarray[int, int]:
        return pos%self.GRID_SIZE

    # Relative position of points on torus grid given an "origin"
    def torusRelPos(self, origin, pos):
        dx = ((pos[1] - origin[1] + self.GRID_SIZE//2) % self.GRID_SIZE) - self.GRID_SIZE//2
        dy = ((pos[0] - origin[0] + self.GRID_SIZE//2) % self.GRID_SIZE) - self.GRID_SIZE//2
        return np.array([dy, dx])

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
        level = self.TURN + 1
        return self.cache[pos[0]][pos[1]] <= level

    """Bidirectional A* pathfinding with flood awareness"""
    def _bidirectional_astar(self, start: Tuple[int, int], target: Tuple[int, int], height: np.ndarray, current_flood: int) -> Optional[Tuple[int, int]]:
        def heuristic(x1: int, y1: int, x2: int, y2: int) -> int:
            return abs(x1 - x2) + abs(y1 - y2)

        sx, sy = start
        tx, ty = target
        grid_size = height.shape[0]

        # Forward search (from start)
        forward_open = []
        heappush(forward_open, (0, sx, sy, 0))
        forward_costs = {(sx, sy, 0): 0}
        forward_path = {}

        # Backward search (from target)
        backward_open = []
        heappush(backward_open, (0, tx, ty, 0))
        backward_costs = {(tx, ty, 0): 0}
        backward_path = {}

        best_cost = np.inf
        meeting_point = None

        while forward_open and backward_open:
            # Expand forward search
            f_cost, fx, fy, f_steps = heappop(forward_open)
            if (fx, fy, f_steps) in backward_costs:
                total_cost = f_cost + backward_costs[(fx, fy, f_steps)]
                if total_cost < best_cost:
                    best_cost = total_cost
                    meeting_point = (fx, fy, f_steps)

            # Expand backward search
            b_cost, bx, by, b_steps = heappop(backward_open)
            if (bx, by, b_steps) in forward_costs:
                total_cost = b_cost + forward_costs[(bx, by, b_steps)]
                if total_cost < best_cost:
                    best_cost = total_cost
                    meeting_point = (bx, by, b_steps)

            # Forward neighbors
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1), (-1,-1), (-1,1), (1,-1), (1,1)]:
                nfx = (fx + dx) % grid_size
                nfy = (fy + dy) % grid_size
                n_steps = f_steps + 1
                if height[nfy, nfx] <= current_flood + n_steps:
                    continue
                new_cost = forward_costs.get((fx, fy, f_steps), np.inf) + 1
                if new_cost < forward_costs.get((nfx, nfy, n_steps), np.inf):
                    forward_costs[(nfx, nfy, n_steps)] = new_cost
                    priority = new_cost + heuristic(nfx, nfy, tx, ty)
                    heappush(forward_open, (priority, nfx, nfy, n_steps))
                    forward_path[(nfx, nfy, n_steps)] = (fx, fy, f_steps)

            # Backward neighbors
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1), (-1,-1), (-1,1), (1,-1), (1,1)]:
                nbx = (bx + dx) % grid_size
                nby = (by + dy) % grid_size
                n_steps = b_steps + 1
                if height[nby, nbx] <= current_flood + n_steps:
                    continue
                new_cost = backward_costs.get((bx, by, b_steps), np.inf) + 1
                if new_cost < backward_costs.get((nbx, nby, n_steps), np.inf):
                    backward_costs[(nbx, nby, n_steps)] = new_cost
                    priority = new_cost + heuristic(nbx, nby, sx, sy)
                    heappush(backward_open, (priority, nbx, nby, n_steps))
                    backward_path[(nbx, nby, n_steps)] = (bx, by, b_steps)

        # Reconstruct path if found
        if meeting_point:
            path = []
            # Build forward path
            current = meeting_point
            while current in forward_path:
                current = forward_path[current]
                path.append(current)
            path.reverse()
            
            # Build backward path
            current = meeting_point
            while current in backward_path:
                current = backward_path[current]
                path.append(current)
            
            # Extract first move
            if len(path) > 1:
                first_move = path[1]  # path[0] is start position
                return (first_move[0] - sx, first_move[1] - sy)
        
        return None

    # perform a step
    def step(self, height: np.ndarray, neighbors: List[Tuple[int, int, int]]) -> Tuple[int, int, int]:
        height = height.transpose()
        sign = lambda x: -1 if x < 0 else (0 if x == 0 else 1)

        if self.TURN <= 4:
            self.updateCacheSLOW(height)
        else:
            self.updateCache(height)

        self.readNbrs(neighbors)

        if self.momentum == 0:
            if self.TURN > self.EXPLORE:
                if self.bestPos[1] > self.cache[self.pos[0]][self.pos[1]]:
                    dely, delx = self.torusRelPos(self.pos, self.bestPos[0])
                    dx = sign(delx)
                    dy = sign(dely)
                elif self.bestPos[1] == self.cache[self.pos[0]][self.pos[1]]:
                    grad = self.contGrad(height)
                    if sum(grad**2) > 2*self.MIN_GRAD:
                        dy = sign(grad[0])
                        dx = sign(grad[1])
                    else:
                        dx = 0
                        dy = 0
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
                    self.momentum = self.ESCAPE_MAX
                    dy = -sign(grad[0])
                    dx = -sign(grad[1])
        else:
            dx = self.dx
            dy = self.dy
            self.momentum += -1

        self.pos[1] += dx
        self.pos[0] += dy
        self.dx = dx
        self.dy = dy

        self.pos = self.getTruePos(self.pos)

        # if self.index == 10:
        #     self.saveCache(self.cache)
        #     print(self.cache[tuple(self.pos)])

        # If moving into water, simply turn around
        if self.avoidWater(self.pos):
            dx = -dx
            dy = -dy
            self.dx = dx
            self.dy = dy
            self.momentum = 20 if self.TURN <= self.EXPLORE else 3
            self.pos[1] += 2*dx
            self.pos[0] += 2*dy
            self.pos = self.getTruePos(self.pos)

        relPos = [self.torusRelPos(self.pos, self.bestPos[0]), self.bestPos[1]]
        m = self.packMsg(relPos)

        # Increment turn counter
        self.TURN += 1
        return (dx, dy, m)
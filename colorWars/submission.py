from typing import List, Tuple
from players.player import Player
import random
import json
import logging

logging.basicConfig(
    filename='debug.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)

# Don't change the name of this class when you submit!
class SubmissionPlayer(Player):
    def __init__(self, player_index: int, grid_size: int, num_players: int):
        self.player_index = player_index
        self.grid_size = grid_size
        self.num_players = num_players

    def play(self, board: List[List[int]], history: List[List[Tuple[int, int]]]) -> Tuple[int, int]:
        n = self.grid_size

        roots = []
        bfs = []
        distance = {}
        vis = set()
        for i in range(self.grid_size):
            roots.append((-1, i))
            roots.append((self.grid_size, i))
            roots.append((i, -1))
            roots.append((i, self.grid_size))

        for y in range(self.grid_size):
            for x in range(self.grid_size):
                if (board[y][x] != 0):
                    roots.append((y,x))

        for p in roots:
            bfs.append(p)
            vis.add(p)
            distance[p] = 0

        bfs_ptr = 0
        distance_points = {}
        max_dist = 0
        while (bfs_ptr < len(bfs)):
            top = bfs[bfs_ptr]
            bfs_ptr+=1
            for di in [-1, 0, 1]:
                for dj in [-1, 0, 1]:
                    if (di == dj == 0): continue
                    if (0 <= top[0]+di < n) and (0 <= top[1]+dj < n) and board[top[0]+di][top[1]+dj] == 0 and ((top[0]+di, top[1]+dj) not in vis):
                        bfs.append((top[0]+di, top[1]+dj))
                        distance[bfs[-1]] = distance[top]+1
                        vis.add(bfs[-1])

                        if distance[bfs[-1]] in distance_points:
                            distance_points[distance[bfs[-1]]].append(bfs[-1])
                        else:
                            distance_points[distance[bfs[-1]]]= [bfs[-1]]

                        max_dist = max(max_dist, distance[bfs[-1]])

        # if (len(distance_points) == 1):
        return random.choice(distance_points[max_dist])
        # else:
        #     return random.choice(distance_points[max_dist]+distance_points[max_dist-1])
from typing import List, Tuple
from players.player import Player
import copy
import random
import pygame
from pygame.locals import *

pygame.init()


class HumanPlayer(Player):
    def __init__(self, player_index: int, grid_size: int, num_players: int):
        self.player_index = player_index
        self.grid_size = grid_size
        self.num_players = num_players
        self.size = 640 // grid_size  # Screen size//Grid size
        self.screen = pygame.display.set_mode((grid_size * self.size, grid_size * self.size))

    def play(self, board: List[List[int]], history: List[List[Tuple[int, int]]]) -> Tuple[int, int]:
        self.screen.fill((255, 127, 0))
        for x in range(self.grid_size):
            for y in range(self.grid_size): pygame.draw.rect(self.screen,
                                                             (0, 255, 0) if board[x][y] == 2 ** self.player_index else (
                                                             127, 127, 127) if bin(board[x][y]).count("1") > 1 else (
                                                             int(min(255.0, 255*1/4*board[x][y])), min(255, int(255*2/5*board[x][y])), min(255, int(255*5/7*board[x][y]))) if board[x][y] != 0 else (0, 0, 0),
                                                             (x * self.size, y * self.size, 10, 10))
        pygame.display.update()
        while True:
            for event in pygame.event.get():
                if event.type == MOUSEBUTTONUP: return (event.pos[0] // self.size, event.pos[1] // self.size)
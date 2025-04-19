from players.player import Player
from typing import List
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
    def __init__(self, player_index: int):
        self.player_index = player_index
        self.remaining_cards = set(range(1, 16))
        mapping = {-5:10, -4:8, -3:6, -2:4, -1: 2, 1:1, 2:3, 3:5, 4:7, 5:9, 6:11, 7:12, 8:13, 9:14, 10:15}
        self.oto = mapping
    def play(self, score_card: int, player_history: List[List[int]]) -> int:
        ret = self.oto[score_card]
        self.remaining_cards.remove(ret)
        return ret


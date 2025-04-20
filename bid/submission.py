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
        self.INF = int(1e9)
        self.my_cards = set(range(1, 16))
        self.opponent_cards = [set(range(1, 16)) for i in range(4)]
        self.previous_auctions = []
        self.remaining_auctions = set(range(1,11))|set(range(-5,0))
        self.scores = [0]*4

    def play(self, score_card: int, player_history: List[List[int]]) -> int:
        self.update_vars(player_history)
        # BEGIN

        all_cards = [*self.opponent_cards[0], *self.opponent_cards[1], *self.opponent_cards[2], *self.opponent_cards[3]]
        mn = (5, -1)
        for i in self.my_cards:
            mn = min(mn, (all_cards.count(i), i))

        ret = mn[1]
        # END
        self.previous_auctions.append(score_card)
        self.my_cards.remove(ret)
        return ret

    def update_vars(self, player_history):
        if not player_history[0]: return
        bids = [0]*16
        for i in range(4):
            self.opponent_cards[i].remove(player_history[i][-1])
            bids[player_history[i][-1]]+=1
        winning_bid = -1
        if self.previous_auctions[-1] > 0:
            for i in range(16):
                if bids[i] == 1:
                    winning_bid = i
        else:
            for i in range(15, 0, -1):
                if bids[i] == 1:
                    winning_bid = i

        if winning_bid > 0:
            for i in range(4):
                if player_history[i][-1] == winning_bid:
                    self.scores[i]+=self.previous_auctions[-1]
from players.player import Player
from typing import List
import random

class MiddleScorePlayer(Player):
    def __init__(self, player_index: int):
        self.player_index = player_index
        self.my_cards = set(range(1, 16))
        self.opponent_cards = [set(range(1, 16)) for i in range(4)]
        self.previous_auctions = []
        self.remaining_auctions = set(range(1,11))|set(range(-5,0))
        self.scores = [0]*4
        middle = [-5, -4, 4, 5, 6, 3, 7]
        cards = [15, 14, 13, 12, 11, 10, 9]
        for card in cards:
            self.my_cards.remove(card)
        random.shuffle(cards)
        self.oto = {middle[i]:cards[i] for i in range(7)}
    def play(self, score_card: int, player_history: List[List[int]]) -> int:
        self.update_vars(player_history)
        # print(self.scores)
        # CODE BEGINS
        ret = None # This is the choice
        if (score_card in self.oto):
            ret = self.oto[score_card]
        else:
            ret = random.choice(list(self.my_cards))
            self.my_cards.remove(ret)

        # CODE ENDS
        self.previous_auctions.append(score_card)
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

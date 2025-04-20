from players.player import Player
from typing import List
import random

class TestPlayer(Player):
    def __init__(self, player_index: int):
        self.player_index = player_index
        self.INF = int(1e9)
        self.my_cards = set(range(1, 16))
        self.opponent_cards = [set(range(1, 16)) for i in range(4)]
        self.previous_auctions = []
        self.remaining_auctions = set(range(1,11))|set(range(-5,0))
        self.scores = [0]*4
        self.assigned_cards = {}

    def play(self, score_card: int, player_history: List[List[int]]) -> int:
        self.update_vars(player_history)
        # BEGIN

        ret = None
        if (score_card in self.assigned_cards):
            ret = self.assigned_cards[score_card]
        else:
            ret = self.choose_card(score_card);

        # END
        self.previous_auctions.append(score_card)
        self.my_cards.remove(ret)
        return ret

    def choose_card(self, score_card:int) -> int:
        ALL_CARDS = [*self.opponent_cards[0], *self.opponent_cards[1], *self.opponent_cards[2], *self.opponent_cards[3]]
        if score_card < 0:
            my_sorted_cards = sorted(list(self.my_cards))
            return random.choice(my_sorted_cards[len(my_sorted_cards)//3:max(1, 2*len(my_sorted_cards)//3)])
        elif score_card < 4:
            return min(self.my_cards)
        elif score_card < 8:
            my_sorted_cards = sorted(list(self.my_cards))
            return random.choice(my_sorted_cards[len(my_sorted_cards)//3:max(1, 2*len(my_sorted_cards)//3)])
        else:
            if (max(ALL_CARDS) >= max(self.my_cards)):
                return min(self.my_cards)
            else:
                return max(self.my_cards)

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
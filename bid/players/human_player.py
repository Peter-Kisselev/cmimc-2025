from players.player import Player
from typing import List
import random

class HumanInputPlayer(Player):
    def __init__(self, player_index: int):
        self.player_index = player_index
        self.my_cards = set(range(1, 16))
        self.opponent_cards = [set(range(1, 16)) for i in range(4)]
        self.previous_auctions = []
        self.remaining_auctions = set(range(1,11))|set(range(-5,0))
        self.scores = [0]*4
    def play(self, score_card: int, player_history: List[List[int]]) -> int:
        self.update_vars(player_history)
        # CODE BEGINS
        print(" ".join(str(player_history[i][-1]) for i in range(4)))
        print(f"score_card: {score_card}")
        print("----")
        print("\n".join(map(str, self.opponent_cards)))
        ret = int(input())
        # CODE ENDS
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

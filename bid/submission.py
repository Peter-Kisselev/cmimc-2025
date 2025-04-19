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
        if (len(self.remaining_auctions) > 3):
            ret = None # This is the choice
            if (score_card in self.oto):
                ret = self.oto[score_card]
            else:
                ret = random.choice(list(self.my_cards))
                self.my_cards.remove(ret)
        else:
            new_list = list(self.remaining_auctions)[:]
            new_list.remove(score_card)
            player_cards_remaining = [list({*range(1,16)}-set(player_history[i])) for i in range(4)]
            score, ret = self.terminal_tree([score_card]+new_list, 0, player_cards_remaining, True)

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


    def terminal_tree(self, rem_aucs:List[int], curr_score:int, remaining_player_cards: List[List[int]], is_first:bool) -> (int, int):
        score_distribution = {}
        if not rem_aucs:
            return curr_score, -1
        for idx, card in enumerate(rem_aucs):
            if is_first and idx > 0: break
            for p1 in remaining_player_cards[0]:
                for p2 in remaining_player_cards[1]:
                    for p3 in remaining_player_cards[2]:
                        for p4 in remaining_player_cards[3]:
                            moves = [p1,p2,p3,p4]
                            new_score = curr_score
                            if (max(moves) == moves[self.player_index] and moves.count(max(moves)) == 1):
                                new_score+=card
                            new_player_cards = [[mv for mv in remaining_player_cards[p] if mv != moves[p]] for p in range(4)]
                            ret, mv = self.terminal_tree(rem_aucs[:idx] + rem_aucs[idx + 1:], new_score, new_player_cards, False)
                            if moves[self.player_index] in score_distribution:
                                score_distribution[moves[self.player_index]].append(ret)
                            else:
                                score_distribution[moves[self.player_index]] = [ret]
        best_pair = (-self.INF, -1)
        for k in score_distribution:
            expected_score = sum(score_distribution[k])/len(score_distribution[k])
            if (u:=(expected_score, k)) > best_pair:
                best_pair = u
        return best_pair
from players.player import Player
from typing import List
import random

class TerminalTreeSearch(Player):
    def __init__(self, player_index: int):
        self.player_index = player_index
        self.my_cards = set(range(1, 16))
        self.opponent_cards = [set(range(1, 16)) for i in range(4)]
        self.previous_auctions = []
        self.remaining_auctions = set(range(1,11))|set(range(-5,0))
        self.scores = [0]*4

        top_cards = [12,13,14,15]
        middle_cards = [10,11]

        random.shuffle(top_cards)
        random.shuffle(middle_cards)

        self.oto = {-5:9, -4:7, -3:5, -2:4, -1: 2, 1:1, 2:3, 3:6, 4:8, 5:middle_cards[0], 6:middle_cards[1], 7:top_cards[0], 8:top_cards[1], 9:top_cards[2], 10:top_cards[3]}
    def play(self, score_card: int, player_history: List[List[int]]) -> int:
        self.update_vars(player_history)
        # print(self.scores)
        # CODE BEGINS
        if (len(self.remaining_auctions) > 3):
            ret = self.oto[score_card]
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
                            for mv in sorted(moves, reverse=True):
                                if (moves.count(mv) == 1 and moves[self.player_index] == mv):
                                    new_score+=card
                                    break
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
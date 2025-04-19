from players.player import Player
from typing import List
import random

class TerminalTreeSearch(Player):
    def __init__(self, player_index: int):
        mapping = {-5:10, -4:8, -3:6, -2:4, -1: 2, 1:1, 2:3, 3:5, 4:7, 5:9, 6:11, 7:12, 8:13, 9:14, 10:15}

        self.player_index = player_index
        self.remaining_cards = set(range(1, 16))
        self.remaining_auctions = {*range(-5, 11)}
        self.remaining_auctions.remove(0)
        self.oto = mapping
        self.INF = int(1e9)
    def play(self, score_card: int, player_history: List[List[int]]) -> int:
        if (len(self.remaining_auctions) > 3):
            # ret = random.choice(list(self.remaining_cards))
            ret = self.oto[score_card]
        else:
            # print("Entered Tree Search")
            new_list = list(self.remaining_auctions)[:]
            new_list.remove(score_card)
            player_cards_remaining = [list({*range(1,16)}-set(player_history[i])) for i in range(4)]
            score, ret = self.terminal_tree([score_card]+new_list, 0, player_cards_remaining, True)

        self.remaining_cards.remove(ret)
        self.remaining_auctions.remove(score_card)
        return ret

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
from players.player import Player
from typing import List
import random

class TrainedPlayer(Player):
    def __init__(self, player_index: int, weights=None):
        if weights is None:
            weights = [3, -4, 2, 4, -3, 3]
        self.player_index = player_index
        self.INF = int(1e9)
        self.my_cards = set(range(1, 16))
        self.opponent_cards = [set(range(1, 16)) for i in range(4)]
        self.previous_auctions = []
        self.remaining_auctions = set(range(1,11))|set(range(-5,0))
        self.scores = [0]*4

        self.LG_MY_SCORE = weights[0]
        self.LG_MY_STRONG = weights[1]
        self.LG_MY_WEAK = weights[2]
        self.LG_OPP_STRONG = weights[3]
        self.LG_OPP_WEAK = weights[4]
        self.LG_HEAVY_AUC = weights[5]

    def play(self, score_card: int, player_history: List[List[int]]) -> int:
        self.update_vars(player_history)
        self.remaining_auctions.remove(score_card)
        # BEGIN

        card_stats = {}

        for p0 in self.opponent_cards[0]:
            for p1 in self.opponent_cards[1]:
                for p2 in self.opponent_cards[2]:
                    for p3 in self.opponent_cards[3]:
                        bids = [p0,p1,p2,p3]
                        my_score = 0
                        for bid in sorted(bids, reverse=True):
                            if bids.count(bid) == 1 and bids[self.player_index] == bid:
                                my_score = score_card
                        new_cards = [{auc for auc in self.opponent_cards[i] if auc != bids[i]} for i in range(4)]
                        res = self.evaluate_position(new_cards, my_score)

                        if bids[self.player_index] not in card_stats:
                            card_stats[bids[self.player_index]] = [res, 1]
                        else:
                            card_stats[bids[self.player_index]][0] += res
                            card_stats[bids[self.player_index]][1] += 1
        for card in card_stats:
            card_stats[card][0] /= card_stats[card][1]
        best_choice = [-self.INF, -1]
        for card in card_stats:
            if (card_stats[card][0] > best_choice[0]):
                best_choice = [card_stats[card][0], card]

        ret = max(min(self.my_cards), best_choice[1])
        # END
        self.previous_auctions.append(score_card)
        self.my_cards.remove(ret)
        return ret

    def evaluate_position(self, player_cards: List[set[int]], player_score:int):
        all_cards = [*player_cards[0], *player_cards[1], *player_cards[2], *player_cards[3]]
        if not all_cards:
            return self.LG_MY_SCORE*player_score*5

        opponent_strong = 0
        opponent_weak = 0

        my_strong = 0
        my_weak = 0

        for card in all_cards:
            if (card >= 10):
                opponent_strong+=1
            elif (card <= 5):
                opponent_weak+=1

        for card in player_cards[self.player_index]:
            if card >= 10:
                my_strong+=1
            elif card <= 5:
                my_weak+=1

        opponent_weak-=my_weak
        opponent_strong-=my_strong

        opponent_strong /= len(all_cards)-len(player_cards[self.player_index])
        opponent_weak /= len(all_cards)-len(player_cards[self.player_index])

        my_strong/= len(player_cards[self.player_index])
        my_weak/= len(player_cards[self.player_index])

        heavy_auctions_remaining = len([auc for auc in self.remaining_auctions if auc in [-5,-4, 10,9,8,7,6]])
        heavy_auctions_remaining /= len(self.remaining_auctions)

        late_game = (len(self.remaining_auctions) < 8)+1
        return (late_game*heavy_auctions_remaining*self.LG_HEAVY_AUC+late_game*player_score*self.LG_MY_SCORE+my_strong*self.LG_MY_STRONG+my_weak*self.LG_MY_WEAK
                +opponent_weak*self.LG_OPP_WEAK + opponent_strong*self.LG_OPP_STRONG)




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

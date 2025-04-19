from config import *
from engine import BidEngine

if __name__ == "__main__":
    for i in range(num_games):
        grading_result = BidEngine.grade(player_classes, 1)
        grading_result.print_result()
        t = input()

from players.random import RandomPlayer
from players.greedy import GreedyPlayer
from players.middle_score_player import MiddleScorePlayer
from players.human_player import HumanInputPlayer
from players.shit_greedy import BadGreedyPlayer
from players.random_and_min_greedy import MinGreedyPlayer
from players.terminal_tree_search import TerminalTreeSearch

# List of players in the game, of form (player_name, player_class)
player_classes = [("Bad Greedy Player #1", BadGreedyPlayer), ("TTS Player #1", TerminalTreeSearch), ("Min Random Player #1", MinGreedyPlayer), ("Random Player #1", RandomPlayer)]

# Number of games to run
num_games = int(1e3)

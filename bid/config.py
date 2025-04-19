from players.random import RandomPlayer
from players.greedy import GreedyPlayer
from players.middle_score_player import MiddleScorePlayer
from players.shit_greedy import BadGreedyPlayer
from players.random_and_min_greedy import MinGreedyPlayer
from players.terminal_tree_search import TerminalTreeSearch

# List of players in the game, of form (player_name, player_class)
player_classes = [("Middle Score Player #1", MiddleScorePlayer), ("TTS Player #1", TerminalTreeSearch), ("Min Random Player #1", MinGreedyPlayer), ("Greedy Player #1", GreedyPlayer)]

# Number of games to run
num_games = int(1e3)

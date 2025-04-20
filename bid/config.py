from players.random import RandomPlayer
from players.greedy import GreedyPlayer
from players.middle_score_player import MiddleScorePlayer
from players.past_players_player import PastPlayer
from players.human_player import HumanInputPlayer
from players.shit_greedy import BadGreedyPlayer
from players.random_and_min_greedy import MinGreedyPlayer
from players.terminal_tree_search import TerminalTreeSearch
from players.terrible_player import TerriblePlayer
from players.testing_strategies import TestPlayer

# List of players in the game, of form (player_name, player_class)
player_classes = [("TTS #1", TerminalTreeSearch), ("Past Player #1", PastPlayer), ("Test Player #1", TestPlayer), ("TTS Player #2", TerminalTreeSearch)]

# Number of games to run
num_games = int(10)

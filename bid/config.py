from players.random import RandomPlayer
from players.greedy import GreedyPlayer
from players.shit_greedy import BadGreedyPlayer
from players.terminal_tree_search import TerminalTreeSearch

# List of players in the game, of form (player_name, player_class)
player_classes = [("Random Player #1", RandomPlayer), ("TTS Player #1", TerminalTreeSearch), ("Random Player #2", RandomPlayer), ("Greedy Player #1", GreedyPlayer)]

# Number of games to run
num_games = int(1e4)

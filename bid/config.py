from players.random import RandomPlayer
from players.greedy import GreedyPlayer
from players.shit_greedy import BadGreedyPlayer

# List of players in the game, of form (player_name, player_class)
player_classes = [("Random Player #1", RandomPlayer), ("Random Player #2", RandomPlayer), ("Bad Greedy #1", BadGreedyPlayer), ("Greedy Player #1", GreedyPlayer)]

# Number of games to run
num_games = int(1e5)

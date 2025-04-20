from players.random import RandomPlayer
from players.stupid import StupidPlayer
from players.human import HumanPlayer
from players.anti_clumping import AntiClumpingPlayer
# List of players in the game, of form (player_name, player_class)
player_classes = [("Random Player #1", RandomPlayer), ("Anti Clump Player", AntiClumpingPlayer), ("Random Player #2", RandomPlayer), ("Human Player #1", HumanPlayer)]

# Size of grid
grid_size = 256

# Number of games to run
num_games = 1

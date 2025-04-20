from ast import Sub
from bots.basic import BasicBot
from bots.custom import customBot
from bots.custom2 import customBot2
from bots.custom3 import customBot3
from bots.custom4 import customBot4
from submission import SubmissionBot

# bot = customBot
# bot = customBot2 # Second iteration
bot = customBot3 # Third iteration
bot = customBot4 # Third iteration
# bot = SubmissionBot # Test submission

difficulty = 0  # 0 is easy, 1 is medium, 2 is hard
seed = 1  # Random seed

# Format message for visualization
def format_message(x: int) -> str:
    return str(x)

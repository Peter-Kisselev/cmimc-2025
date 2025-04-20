from ast import Sub
from bots.basic import BasicBot
from bots.custom2 import customBot2
from bots.custom3 import customBot3
from bots.custom4 import customBot4
from bots.custom5 import customBot5
from bots.test import testBot
from submission import SubmissionBot

# bot = customBot2 # Second iteration
# bot = customBot3 # Third iteration
# bot = customBot4 # Fourth iteration
# bot = customBot5 # Fourth iteration

bot = testBot # Very conceptual


# bot = SubmissionBot # Test submission

difficulty = 0  # 0 is easy, 1 is medium, 2 is hard
seed = 2  # Random seed

# Format message for visualization
def format_message(x: int) -> str:
    return str(x)

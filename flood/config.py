from ast import Sub
from bots.basic import BasicBot
from bots.custom import customBot
from submission import SubmissionBot

# bot = BasicBot  # Bot to test
bot = customBot
# bot = SubmissionBot # Test submission
difficulty = 0  # 0 is easy, 1 is medium, 2 is hard
seed = 1  # Random seed

# Format message for visualization
def format_message(x: int) -> str:
    return str(x)

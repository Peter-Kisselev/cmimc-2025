from bots.basic import BasicBot
from bots.custom import customBot

# bot = BasicBot  # Bot to test
bot = customBot
difficulty = 1  # 0 is easy, 1 is medium, 2 is hard
seed = 1  # Random seed

# Format message for visualization
def format_message(x: int) -> str:
    return str(x)

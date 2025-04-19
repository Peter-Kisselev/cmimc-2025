# Flood Survival Starter Code

## Directory Structure

```
flood_survival/
├── config.py                 # Configure bot, difficulty, seed, and grid size
├── engine.py                 # Core simulation engine
├── cli.py                    # CLI for running simulations
├── submission.py             # Template for your submission bot
├── visualizer.py             # Pygame-based simulation visualizer
├── bots/
│   ├── bot.py                # Abstract bot class (base implementation)
│── └── basic.py              # Example bot implementation
├── requirements.txt          # Python dependencies
```

## Installation

1. Create a virtual environment (optional but recommended):
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Local Testing

### Step 1: Implement Your Bot
- Create a new bot by subclassing the `Bot` abstract class located in `bots/bot.py`.
- Implement your bot's strategy in the `step()` method, handling inputs:
  - `height`: Local grid elevations.
  - `neighbors`: Positions and messages of nearby bots.
- Check `bots/basic.py` for a working example.

### Step 2: Configure the Simulation
- Open `config.py` and set:
  - Your bot class (e.g., `from bots.basic import BasicBot`).
  - Difficulty (`difficulty`: `0`=Easy, `1`=Medium, `2`=Hard).
  - Random seed (`seed`) for consistent simulations.

### Step 3: Run Your Simulation
Run via CLI:

```bash
python cli.py run
```

This will execute your configured bot and print results directly to the terminal.

Visualize via CLI:
```bash
python cli.py visualize
```
This will display a step-by-step animation of your bot navigating the flood simulation. Each bot displays their message as a number above its icon. You can customize the display via `format_message` in `config.py`.

## Submission Preparation

### Prepare Your Submission
- Implement your bot logic in `submission.py` within the `SubmissionBot` class.
- **Important Submission Rules:**
  - Do not change the class name (`SubmissionBot`).
  - Do not modify provided execution code.
  - Do not use `print()` statements.

### Submit Your Bot
- Submit **only** the completed `submission.py` file to the contest submission platform.


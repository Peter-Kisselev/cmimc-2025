import click
import config
from engine import FloodEngine, FloodSimulator
from visualizer import FloodVisualizer

@click.group()
def cli():
    pass

@cli.command()
def run():
    engine = FloodEngine()
    result = engine.grade(
        config.bot,
        config.difficulty,
        config.seed
    )
    result.print_result()

@cli.command()
def visualize():
    simulator = FloodSimulator()
    simulator.initialize(
        config.bot,
        config.difficulty,
        config.seed,
    )
    visualizer = FloodVisualizer(simulator)
    visualizer.run()

if __name__ == '__main__':
    cli()

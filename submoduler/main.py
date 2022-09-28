import click
import os
import auth

from loguru import logger
from git import Git
from yaml import load, Loader

from submoduler import Submoduler


@click.command
@click.option('--config_path',
              help="Path to the configuration file. This supports relative path, e.g.: ../submoduler.yaml.",
              default="/opt/submoduler.yaml")
def launch(config_path):
    config_path = os.path.abspath(config_path)

    logger.info("Starting submoduler")
    try:
        with open(config_path, "r") as config_stream:
            config_data = load(config_stream, Loader=Loader)

        Submoduler(config_data)

    except FileNotFoundError:
        logger.error(f"Specified config file not found at: {config_path}.")
        return


if __name__ == '__main__':
    launch()

import click
import os

from loguru import logger
from yaml import load, Loader

from submoduler import Submoduler


@click.command
@click.option('--config_path',
              help="Path to the configuration file. This supports relative path, e.g.: ../submoduler-example-config.yaml.",
              default="/opt/submoduler.yaml")
@click.option('--user',
              help="Username.",
              default=os.environ.get("USER"))
@click.option('--email',
              help="User Email.",
              default=os.environ.get("EMAIL", ""))
@click.option('--pat',
              help="User Email.",
              default=os.environ.get("PAT"))
def launch(config_path, user, email, pat):
    config_path = os.path.abspath(config_path)

    logger.info("Starting submoduler")
    try:
        with open(config_path, "r") as config_stream:
            config_data = load(config_stream, Loader=Loader)

        Submoduler(config_data, user, pat, email)

    except FileNotFoundError as error:
        logger.error(error)
        logger.error(f"Specified config file not found at: {config_path}.")
        return


if __name__ == '__main__':
    launch()

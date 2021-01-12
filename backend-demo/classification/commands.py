import click

from classification.train import train
from classification.update import update


@click.group()
def classification():
    pass


classification.add_command(train)
classification.add_command(update)

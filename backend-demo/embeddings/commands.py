import click

from embeddings.embed import embed
from embeddings.index import index
from embeddings.retrieve import retrieve


@click.group()
def embeddings():
    pass


embeddings.add_command(embed)
embeddings.add_command(index)
embeddings.add_command(retrieve)

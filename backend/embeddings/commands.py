import click

from embeddings.embed import embed
from embeddings.index import index
from embeddings.retrieve import retrieve


@click.group()
def embeddings():
    pass


@embeddings.command('embed', help='Embed comments in DB')
@click.argument('source-id', required=True, type=int)
@click.option('--embed-all', is_flag=True, help='(Re-)embed all data')
@click.option('--batch-size', default=8, help='Batch size for tensor operations')
def cli_embed(source_id: int, embed_all: bool, batch_size: int):
    embed(source_id=source_id, embed_all=embed_all, batch_size=batch_size)


@embeddings.command('index', help='Index comment embeddings')
@click.argument('source-id', required=True, type=int)
def cli_index(source_id: int):
    index(source_id=source_id)


@embeddings.command('retrieve')
@click.argument('source-id', required=True, type=int)
@click.argument('comment-id', required=True, type=int)
@click.option('--n', default=10, help='Number of nearest neighbors')
def cli_retrieve(source_id: int, comment_id: int, n: int):
    retrieve(source_id=source_id, comment_id=comment_id, n=n)

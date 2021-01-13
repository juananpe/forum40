import click

from serve import serve
from classification.commands import classification
from embeddings.commands import embeddings


@click.group()
def cli():
    pass


@cli.command('serve', help='Start the server')
def cli_serve():
    serve()


cli.add_command(classification)
cli.add_command(embeddings)


if __name__ == '__main__':
    cli()

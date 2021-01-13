import click

from serve import serve
from classification.commands import classification
from embeddings.commands import embeddings


@click.group()
def cli():
    pass


@cli.command('serve', help='Start the server')
@click.option('--port', default=5050, help='The port on which to run')
@click.option('--debug', is_flag=True, help='Run in debug mode with live reloading and additional logs')
def cli_serve(port: int, debug: bool):
    serve(port=port, debug=debug)


cli.add_command(classification)
cli.add_command(embeddings)


if __name__ == '__main__':
    cli()

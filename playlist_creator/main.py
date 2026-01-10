"""Main CLI entry point for YouTube Playlist Creator."""
import click

from playlist_creator import __version__
from playlist_creator.commands.search import search_command
from playlist_creator.commands.create import create_command
from playlist_creator.commands.sync import sync_command
from playlist_creator.core.auth import get_authenticated_service
from playlist_creator.core.utils import Icons


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    """YouTube Playlist Creator - Cria playlists a partir de arquivos Markdown."""
    pass


@cli.command("auth")
def auth_command() -> None:
    """Autenticar com sua conta do YouTube."""
    click.echo(f"{Icons.LOCK} Iniciando autenticacao...")
    try:
        get_authenticated_service()
        click.echo(f"{Icons.SUCCESS} Autenticacao concluida!")
    except Exception as e:
        click.echo(f"{Icons.ERROR} Falha na autenticacao: {e}", err=True)
        raise SystemExit(1)


# Register commands
cli.add_command(search_command, "search")
cli.add_command(create_command, "create")
cli.add_command(sync_command, "sync")


if __name__ == "__main__":
    cli()

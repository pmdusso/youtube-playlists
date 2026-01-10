"""Search command implementation."""
import logging
from pathlib import Path

import click

from playlist_creator.core.auth import get_authenticated_service
from playlist_creator.core.cache import CacheManager
from playlist_creator.core.exceptions import QuotaExceededError, PlaylistCreatorError
from playlist_creator.core.logger import setup_logging
from playlist_creator.core.parser import parse_markdown
from playlist_creator.core.utils import Icons, format_track_status
from playlist_creator.core.youtube_client import YouTubeClient
from playlist_creator.models import CacheStatus


@click.command("search")
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option("--force", is_flag=True, help="Re-search songs already in cache")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def search_command(file: Path, force: bool, verbose: bool) -> None:
    """Search YouTube for songs in a Markdown playlist file."""
    logger = setup_logging(verbose=verbose)

    try:
        # Parse markdown
        click.echo(f"{Icons.FOLDER} Lendo: {file}")
        playlist = parse_markdown(file)
        click.echo(f"{Icons.PLAYLIST} Playlist: \"{playlist.name}\"")

        # Initialize cache
        cache = CacheManager()
        cache.ensure_initialized()

        # Count cached vs new
        cached_count = sum(1 for t in playlist.tracks if cache.has(t.query) and not force)
        new_count = len(playlist.tracks) - cached_count

        click.echo(f"{Icons.SEARCH} {len(playlist.tracks)} musicas no arquivo, {cached_count} ja no cache")
        click.echo()

        if new_count == 0 and not force:
            click.echo(f"{Icons.SUCCESS} Todas as musicas ja estao no cache. Use --force para re-buscar.")
            return

        # Get authenticated service
        service = get_authenticated_service()
        youtube = YouTubeClient(service)

        # Search each track
        found = 0
        not_found = 0
        skipped = 0

        for i, track in enumerate(playlist.tracks, 1):
            if cache.has(track.query) and not force:
                if verbose:
                    click.echo(format_track_status(
                        i, len(playlist.tracks),
                        track.title, track.artist,
                        Icons.SKIP, "Ja no cache"
                    ))
                skipped += 1
                continue

            click.echo(f"[{i}/{len(playlist.tracks)}] {track.title} - {track.artist}")
            click.echo(f"       {Icons.SEARCH} Buscando...")

            try:
                result = youtube.search(track.title, track.artist)
                cache.save(result)

                if result.status == CacheStatus.FOUND:
                    found += 1
                    match = result.matches[0]
                    click.echo(f"       {Icons.SUCCESS} Encontrado: \"{match.title}\" ({match.duration}) [{match.channel}]")

                    if verbose and len(result.matches) > 1:
                        for j, alt in enumerate(result.matches[1:], 2):
                            click.echo(f"         Alt {j}: \"{alt.title}\" ({alt.duration}) [{alt.channel}]")
                else:
                    not_found += 1
                    click.echo(f"       {Icons.WARNING} Nao encontrado")

            except QuotaExceededError as e:
                click.echo(f"\n{Icons.ERROR} {e}")
                click.echo(f"   Progresso salvo. Retome mais tarde.")
                raise SystemExit(1)

            click.echo()

        # Summary
        click.echo("-" * 40)
        click.echo(f"{Icons.SUCCESS} Busca completa")
        click.echo(f"   {found} encontradas (novas)")
        click.echo(f"   {skipped} do cache (puladas)")
        click.echo(f"   {not_found} nao encontradas")
        click.echo()
        click.echo(f"{Icons.CACHED} Cache salvo")

    except PlaylistCreatorError as e:
        click.echo(f"{Icons.ERROR} {e}", err=True)
        raise SystemExit(1)

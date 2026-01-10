"""Create command implementation."""
import logging
from pathlib import Path
from typing import Optional

import click

from config import DEFAULT_PRIVACY
from playlist_creator.core.auth import get_authenticated_service
from playlist_creator.core.cache import CacheManager
from playlist_creator.core.exceptions import (
    QuotaExceededError,
    VideoUnavailableError,
    PlaylistCreatorError,
)
from playlist_creator.core.logger import setup_logging
from playlist_creator.core.parser import parse_markdown
from playlist_creator.core.utils import Icons
from playlist_creator.core.youtube_client import YouTubeClient
from playlist_creator.models import CacheStatus


@click.command("create")
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option("--name", help="Custom playlist name (overrides title from file)")
@click.option("--dry-run", is_flag=True, help="Show what would be done without creating")
@click.option("--skip-missing", is_flag=True, help="Skip missing songs without confirmation")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def create_command(
    file: Path,
    name: Optional[str],
    dry_run: bool,
    skip_missing: bool,
    verbose: bool
) -> None:
    """Create a YouTube playlist from a Markdown file."""
    logger = setup_logging(verbose=verbose)

    try:
        # Parse markdown
        click.echo(f"{Icons.FOLDER} Lendo: {file}")
        playlist = parse_markdown(file)
        playlist_name = name or playlist.name
        click.echo(f"{Icons.PLAYLIST} Playlist: \"{playlist_name}\"")

        # Load cache
        cache = CacheManager()
        cache.ensure_initialized()

        # Check cache status for all tracks
        tracks_ready = []
        tracks_missing = []
        tracks_not_found = []

        for track in playlist.tracks:
            entry = cache.get(track.query)
            if entry is None:
                tracks_missing.append(track)
            elif entry.status == CacheStatus.NOT_FOUND:
                tracks_not_found.append(track)
            else:
                video_id = cache.get_selected_video_id(track.query)
                if video_id:
                    tracks_ready.append((track, video_id, entry))
                else:
                    tracks_missing.append(track)

        # Report status
        click.echo()
        click.echo(f"   {len(tracks_ready)} musicas prontas")
        click.echo(f"   {len(tracks_not_found)} nao encontradas (serao puladas)")
        click.echo(f"   {len(tracks_missing)} sem cache")

        # Abort if missing cache
        if tracks_missing:
            click.echo()
            click.echo(f"{Icons.ERROR} {len(tracks_missing)} musicas nao estao no cache.")
            click.echo(f"   Execute primeiro: python main.py search {file}")
            for track in tracks_missing[:5]:
                click.echo(f"   - {track.title} - {track.artist}")
            if len(tracks_missing) > 5:
                click.echo(f"   ... e mais {len(tracks_missing) - 5}")
            raise SystemExit(1)

        # Confirm if many not found
        if tracks_not_found and not skip_missing:
            pct = len(tracks_not_found) / len(playlist.tracks) * 100
            click.echo()
            click.echo(f"{Icons.WARNING} {len(tracks_not_found)} de {len(playlist.tracks)} musicas nao encontradas ({pct:.0f}%)")
            if not dry_run:
                if not click.confirm("   Continuar criando playlist?"):
                    raise SystemExit(0)

        # Dry run
        if dry_run:
            click.echo()
            click.echo("-" * 40)
            click.echo("[DRY-RUN] O que seria feito:")
            click.echo(f"   - Criar playlist \"{playlist_name}\" (privada)")
            click.echo(f"   - Adicionar {len(tracks_ready)} musicas:")
            for track, video_id, _ in tracks_ready:
                click.echo(f"     [{track.position}] {track.title} - {track.artist}")
            if tracks_not_found:
                click.echo(f"   - Pular {len(tracks_not_found)} nao encontradas")
            return

        # Create playlist
        click.echo()
        click.echo(f"{Icons.SEARCH} Criando playlist...")

        service = get_authenticated_service()
        youtube = YouTubeClient(service)

        playlist_id = youtube.create_playlist(playlist_name, privacy=DEFAULT_PRIVACY)
        click.echo(f"{Icons.SUCCESS} Playlist criada: https://youtube.com/playlist?list={playlist_id}")

        # Add videos
        click.echo()
        added = 0
        failed = 0

        for i, (track, video_id, entry) in enumerate(tracks_ready, 1):
            click.echo(f"[{i}/{len(tracks_ready)}] {track.title} - {track.artist}")

            try:
                youtube.add_video_to_playlist(playlist_id, video_id)
                click.echo(f"       {Icons.SUCCESS} Adicionado")
                added += 1
            except VideoUnavailableError:
                click.echo(f"       {Icons.WARNING} Video indisponivel - pulando")
                failed += 1
            except QuotaExceededError as e:
                click.echo(f"\n{Icons.ERROR} {e}")
                click.echo(f"   Playlist criada: https://youtube.com/playlist?list={playlist_id}")
                click.echo(f"   {added} musicas adicionadas antes do erro.")
                raise SystemExit(1)

        # Summary
        click.echo()
        click.echo("-" * 40)
        click.echo(f"{Icons.SUCCESS} Playlist criada: https://youtube.com/playlist?list={playlist_id}")
        click.echo(f"   {added}/{len(playlist.tracks)} musicas adicionadas")
        if tracks_not_found:
            click.echo(f"   {len(tracks_not_found)} nao encontradas (puladas)")
        if failed:
            click.echo(f"   {failed} indisponiveis (puladas)")

    except PlaylistCreatorError as e:
        click.echo(f"{Icons.ERROR} {e}", err=True)
        raise SystemExit(1)

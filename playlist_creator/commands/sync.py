"""Sync command implementation."""
import logging
import re
from pathlib import Path
from typing import Optional

import click

from playlist_creator.core.auth import get_authenticated_service
from playlist_creator.core.cache import CacheManager
from playlist_creator.core.exceptions import (
    QuotaExceededError,
    VideoUnavailableError,
    PlaylistNotFoundError,
    PlaylistCreatorError,
)
from playlist_creator.core.logger import setup_logging
from playlist_creator.core.parser import parse_markdown
from playlist_creator.core.utils import Icons
from playlist_creator.core.youtube_client import YouTubeClient
from playlist_creator.models import CacheStatus


def extract_playlist_id(url_or_id: str) -> str:
    """Extract playlist ID from URL or return as-is if already an ID."""
    # Match playlist ID in URL
    match = re.search(r"[?&]list=([^&]+)", url_or_id)
    if match:
        return match.group(1)
    # Assume it's already an ID
    return url_or_id


@click.command("sync")
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option("--playlist-url", help="YouTube playlist URL")
@click.option("--playlist-id", help="YouTube playlist ID")
@click.option("--remove-unknown", is_flag=True, help="Remove songs not in Markdown file")
@click.option("--dry-run", is_flag=True, help="Show what would be done without modifying")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def sync_command(
    file: Path,
    playlist_url: Optional[str],
    playlist_id: Optional[str],
    remove_unknown: bool,
    dry_run: bool,
    verbose: bool
) -> None:
    """Synchronize a YouTube playlist with a Markdown file."""
    logger = setup_logging(verbose=verbose)

    # Validate playlist identifier
    if not playlist_url and not playlist_id:
        click.echo(f"{Icons.ERROR} Especifique --playlist-url ou --playlist-id", err=True)
        raise SystemExit(1)

    pl_id = playlist_id or extract_playlist_id(playlist_url)

    try:
        # Parse markdown
        click.echo(f"{Icons.FOLDER} Lendo: {file}")
        playlist = parse_markdown(file)
        click.echo(f"{Icons.PLAYLIST} Arquivo: \"{playlist.name}\" ({len(playlist.tracks)} musicas)")

        # Load cache
        cache = CacheManager()
        cache.ensure_initialized()

        # Build desired state from markdown + cache
        desired: list[tuple] = []  # (position, track, video_id)
        missing_cache = []
        not_found = []

        for track in playlist.tracks:
            video_id = cache.get_selected_video_id(track.query)
            if video_id:
                desired.append((track.position, track, video_id))
            else:
                entry = cache.get(track.query)
                if entry and entry.status == CacheStatus.NOT_FOUND:
                    not_found.append(track)
                else:
                    missing_cache.append(track)

        if missing_cache:
            click.echo(f"\n{Icons.ERROR} {len(missing_cache)} musicas nao estao no cache.")
            click.echo(f"   Execute primeiro: python main.py search {file}")
            raise SystemExit(1)

        # Sort by position
        desired.sort(key=lambda x: x[0])
        desired_video_ids = [vid for _, _, vid in desired]

        # Get current YouTube state
        click.echo(f"{Icons.SEARCH} Carregando playlist do YouTube...")

        service = get_authenticated_service()
        youtube = YouTubeClient(service)

        try:
            current_items = youtube.get_playlist_items(pl_id)
        except PlaylistNotFoundError:
            click.echo(f"{Icons.ERROR} Playlist nao encontrada: {pl_id}")
            raise SystemExit(1)

        click.echo(f"{Icons.PLAYLIST} YouTube: {len(current_items)} musicas")

        # Build current state map
        current_by_video_id = {item["video_id"]: item for item in current_items}
        current_video_ids = [item["video_id"] for item in current_items]

        # Calculate changes
        to_add = []  # (position, track, video_id)
        to_remove = []  # (item_id, video_id)
        unknown = []  # In YouTube but not in desired

        # Find what to add
        for pos, track, vid in desired:
            if vid not in current_by_video_id:
                to_add.append((pos, track, vid))

        # Find what to remove or mark as unknown
        desired_set = set(desired_video_ids)
        for item in current_items:
            if item["video_id"] not in desired_set:
                if remove_unknown:
                    to_remove.append((item["item_id"], item["video_id"]))
                else:
                    unknown.append(item)

        # Report
        click.echo()
        click.echo("Alteracoes necessarias:")

        if to_add:
            click.echo(f"\n  ADICIONAR ({len(to_add)}):")
            for pos, track, vid in to_add:
                click.echo(f"    + {track.title} - {track.artist} (posicao {pos})")

        if to_remove:
            click.echo(f"\n  REMOVER ({len(to_remove)}):")
            for item_id, vid in to_remove:
                click.echo(f"    - video_id: {vid}")

        if unknown and not remove_unknown:
            click.echo(f"\n  {Icons.WARNING} NAO MAPEADAS ({len(unknown)}) - mantidas no final:")
            for item in unknown:
                click.echo(f"    - video_id: {item['video_id']}")
            click.echo(f"\n  Use --remove-unknown para remove-las")

        if not_found:
            click.echo(f"\n  {Icons.WARNING} NAO ENCONTRADAS ({len(not_found)}) - serao ignoradas:")
            for track in not_found:
                click.echo(f"    - {track.title} - {track.artist}")

        if not to_add and not to_remove:
            click.echo(f"\n{Icons.SUCCESS} Playlist ja esta sincronizada!")
            return

        # Dry run stops here
        if dry_run:
            click.echo("\n[DRY-RUN] Nenhuma alteracao feita.")
            return

        # Execute changes: Add -> Remove
        click.echo()

        # Add new videos
        if to_add:
            click.echo(f"{Icons.SEARCH} Adicionando {len(to_add)} musicas...")
            for pos, track, vid in to_add:
                try:
                    youtube.add_video_to_playlist(pl_id, vid)
                    click.echo(f"  {Icons.SUCCESS} {track.title} - {track.artist}")
                except VideoUnavailableError:
                    click.echo(f"  {Icons.WARNING} {track.title} - video indisponivel")
                except QuotaExceededError as e:
                    click.echo(f"\n{Icons.ERROR} {e}")
                    raise SystemExit(1)

        # Remove videos
        if to_remove:
            click.echo(f"{Icons.SEARCH} Removendo {len(to_remove)} musicas...")
            for item_id, vid in to_remove:
                try:
                    youtube.remove_playlist_item(item_id)
                    click.echo(f"  {Icons.SUCCESS} Removido: {vid}")
                except QuotaExceededError as e:
                    click.echo(f"\n{Icons.ERROR} {e}")
                    raise SystemExit(1)

        # Summary
        click.echo()
        click.echo("-" * 40)
        click.echo(f"{Icons.SUCCESS} Sincronizacao completa!")
        click.echo(f"   https://youtube.com/playlist?list={pl_id}")

    except PlaylistCreatorError as e:
        click.echo(f"{Icons.ERROR} {e}", err=True)
        raise SystemExit(1)

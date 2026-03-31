#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "typer>=0.24.1",
#     "yt-dlp>=2026.3.17",
# ]
# ///

from __future__ import annotations

import concurrent.futures
import pathlib
import re
import shutil
import subprocess

import typer

MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\((https?://[^)\s]+)\)")
app = typer.Typer(
    add_completion=False, help="Batch download court videos from URL file."
)


def extract_url_from_line(line: str) -> str | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None

    match = MARKDOWN_LINK_RE.search(stripped)
    if match:
        return match.group(1)

    if stripped.startswith(("http://", "https://")):
        return stripped

    return None


def load_urls(url_file: pathlib.Path) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()

    for line in url_file.read_text(encoding="utf-8").splitlines():
        url = extract_url_from_line(line)
        if url is None or url in seen:
            continue
        seen.add(url)
        urls.append(url)

    return urls


def download_one(
    url: str, output_dir: pathlib.Path, *, audio_only: bool = False
) -> None:
    command = ["yt-dlp"]
    if audio_only:
        command.extend(
            [
                "-f",
                "bestaudio",
                "-o",
                f"{output_dir}/%(title)s.%(ext)s",
                url,
            ]
        )
    else:
        command.extend(
            [
                "-f",
                "bestvideo*+bestaudio/best",
                "--merge-output-format",
                "mp4",
                "--embed-metadata",
                "-o",
                f"{output_dir}/%(title)s.%(ext)s",
                url,
            ]
        )

    subprocess.run(command, check=True)


def run(url_file: str, output_dir: str, workers: int, *, audio_only: bool) -> int:
    if workers <= 0:
        typer.secho(
            f"Error: workers must be a positive integer. Got: {workers}",
            fg="red",
            err=True,
        )
        return 1

    if shutil.which("yt-dlp") is None:
        typer.secho(
            "Error: yt-dlp is not installed or not in PATH.", fg="red", err=True
        )
        return 1

    url_file_path = pathlib.Path(url_file)
    if not url_file_path.is_file():
        typer.secho(f"Error: URL file not found: {url_file_path}", fg="red", err=True)
        return 1

    output_dir_path = pathlib.Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    urls = load_urls(url_file_path)
    if not urls:
        typer.echo(f"No URLs found in: {url_file_path}")
        return 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(download_one, url, output_dir_path, audio_only=audio_only)
            for url in urls
        ]
        for future in concurrent.futures.as_completed(futures):
            future.result()

    typer.echo(f"Done. Videos saved to: {output_dir_path}")
    return 0


@app.command()
def main(
    url_file: str = typer.Option(
        "docs/court_video_urls.md", "--url-file", help="Input file containing video URLs."
    ),
    output_dir: str = typer.Option(
        "data/videos", "--output-dir", help="Directory to store downloaded files."
    ),
    workers: int = typer.Option(1, "--workers", help="Number of parallel download workers."),
    audio_only: bool = typer.Option(
        False, "--audio-only", help="Download audio only in original source format."
    ),
) -> None:
    raise typer.Exit(code=run(url_file, output_dir, workers, audio_only=audio_only))


if __name__ == "__main__":
    app()

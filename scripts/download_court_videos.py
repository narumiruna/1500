#!/usr/bin/env python3

from __future__ import annotations

import argparse
import concurrent.futures
import pathlib
import re
import shutil
import subprocess
import sys

MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\((https?://[^)\s]+)\)")


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


def download_one(url: str, output_dir: pathlib.Path) -> None:
    subprocess.run(
        [
            "yt-dlp",
            "-f",
            "wv*+wa/w",
            "--merge-output-format",
            "mp4",
            "--embed-metadata",
            "-o",
            f"{output_dir}/%(title)s.%(ext)s",
            url,
        ],
        check=True,
    )


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Batch download court videos from URL file."
    )
    parser.add_argument("url_file", nargs="?", default="docs/court_video_urls.md")
    parser.add_argument("output_dir", nargs="?", default="data/videos")
    parser.add_argument("workers", nargs="?", default="4")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        workers = int(args.workers)
    except ValueError:
        print(
            f"Error: workers must be a positive integer. Got: {args.workers}",
            file=sys.stderr,
        )
        return 1
    if workers <= 0:
        print(
            f"Error: workers must be a positive integer. Got: {workers}",
            file=sys.stderr,
        )
        return 1

    if shutil.which("yt-dlp") is None:
        print("Error: yt-dlp is not installed or not in PATH.", file=sys.stderr)
        return 1

    url_file = pathlib.Path(args.url_file)
    if not url_file.is_file():
        print(f"Error: URL file not found: {url_file}", file=sys.stderr)
        return 1

    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    urls = load_urls(url_file)
    if not urls:
        print(f"No URLs found in: {url_file}")
        return 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(download_one, url, output_dir) for url in urls]
        for future in concurrent.futures.as_completed(futures):
            future.result()

    print(f"Done. Videos saved to: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

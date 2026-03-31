#!/usr/bin/env bash

set -euo pipefail

URL_FILE="${1:-docs/court_video_urls.md}"
OUTPUT_DIR="${2:-court-videos}"

if ! command -v yt-dlp >/dev/null 2>&1; then
  echo "Error: yt-dlp is not installed or not in PATH." >&2
  exit 1
fi

if [[ ! -f "$URL_FILE" ]]; then
  echo "Error: URL file not found: $URL_FILE" >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

yt-dlp \
  --batch-file "$URL_FILE" \
  -f "bv*+ba/b" \
  --merge-output-format mp4 \
  --embed-metadata \
  -o "$OUTPUT_DIR/%(title)s.%(ext)s"

echo "Done. Videos saved to: $OUTPUT_DIR"

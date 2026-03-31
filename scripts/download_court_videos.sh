#!/usr/bin/env bash

set -euo pipefail

URL_FILE="${1:-docs/court_video_urls.md}"
OUTPUT_DIR="${2:-court-videos}"
WORKERS="${3:-4}"

if ! [[ "$WORKERS" =~ ^[1-9][0-9]*$ ]]; then
  echo "Error: workers must be a positive integer. Got: $WORKERS" >&2
  exit 1
fi

if ! command -v yt-dlp >/dev/null 2>&1; then
  echo "Error: yt-dlp is not installed or not in PATH." >&2
  exit 1
fi

if [[ ! -f "$URL_FILE" ]]; then
  echo "Error: URL file not found: $URL_FILE" >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

urls=()
while IFS= read -r line || [[ -n "$line" ]]; do
  line="${line%%#*}"
  [[ -z "${line//[[:space:]]/}" ]] && continue
  urls+=("$line")
done < "$URL_FILE"

if [[ ${#urls[@]} -eq 0 ]]; then
  echo "No URLs found in: $URL_FILE"
  exit 0
fi

download_one() {
  local url="$1"
  yt-dlp \
    -f "wv*+wa/w" \
    --merge-output-format mp4 \
    --embed-metadata \
    -o "$OUTPUT_DIR/%(title)s.%(ext)s" \
    "$url"
}

export OUTPUT_DIR
export -f download_one

printf '%s\0' "${urls[@]}" | xargs -0 -n 1 -P "$WORKERS" bash -c 'download_one "$1"' _

echo "Done. Videos saved to: $OUTPUT_DIR"

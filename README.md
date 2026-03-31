# 1500

## Download Court Videos

Use the wrapper script:

```bash
scripts/download_court_videos.sh [URL_FILE] [OUTPUT_DIR] [WORKERS]
```

Defaults:

- `URL_FILE`: `docs/court_video_urls.md`
- `OUTPUT_DIR`: `data/videos`
- `WORKERS`: `1`

The URL file supports both:

- Markdown links, such as `- [title](https://www.youtube.com/watch?v=...)`
- Plain URLs, such as `https://www.youtube.com/watch?v=...`

### Download Highest-Quality Video

```bash
scripts/download_court_videos.sh
```

This uses `yt-dlp` format: `bestvideo*+bestaudio/best`.

### Download Audio Only (MP3)

Run the Python entrypoint with `--audio-only`:

```bash
uv run python scripts/download_court_videos.py --audio-only [URL_FILE] [OUTPUT_DIR] [WORKERS]
```

Example:

```bash
uv run python scripts/download_court_videos.py --audio-only docs/court_video_urls.md data/audio 1
```

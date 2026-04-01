# 1500

## Download Court Videos

Use the Python script:

```bash
uv run --script scripts/download_court_videos.py [OPTIONS]
```

Defaults:

- `--url-file`: `docs/court_video_urls.md`
- `--output-dir`: `data/videos`
- `--workers`: `1`

The URL file supports both:

- Markdown links, such as `- [title](https://www.youtube.com/watch?v=...)`
- Plain URLs, such as `https://www.youtube.com/watch?v=...`

### Download Highest-Quality Video

```bash
uv run --script scripts/download_court_videos.py
```

This uses `yt-dlp` format: `bestvideo*+bestaudio/best`.

### Download Audio Only (Original Format)

Run the Python entrypoint with `--audio-only`:

```bash
uv run --script scripts/download_court_videos.py --audio-only [OPTIONS]
```

This uses `yt-dlp` format: `bestaudio` (no transcoding).

Example:

```bash
uv run --script scripts/download_court_videos.py --audio-only --url-file docs/court_video_urls.md --output-dir data/audio --workers 1
```

## Transcribe Court Videos

Use the Python script:

```bash
uv run --script scripts/transcribe_court_videos.py [OPTIONS]
```

Defaults:

- `--input-dir`: `data/videos`
- `--output-dir`: `docs/transcripts`
- `--model`: `large-v3`

Output transcript filenames are normalized to avoid special characters:

- Replace special characters (including `/`, `⧸`, and spaces) with `_`
- Collapse repeated `_`
- Trim leading/trailing `_` and `.`

## Check Oral Argument Page Consistency

Use this script to verify that each oral-argument detail page:

- Uses the unified date line format
- Uses the unified video link format (`庭審錄影` + `rel="noopener noreferrer"`)
- Contains a matching transcript link

```bash
uv run --script scripts/check_oral_arguments_consistency.py
```

Optional:

```bash
uv run --script scripts/check_oral_arguments_consistency.py --oral-arguments-dir oral-arguments
```

# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "openai-whisper>=20250625",
#     "torch>=2.11.0",
#     "typer>=0.24.1",
# ]
# ///
from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated

import torch
import typer
import whisper

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".webm", ".mov", ".avi", ".m4v"}

app = typer.Typer(add_completion=False, help="Transcribe all videos to text files.")


def find_video_files(input_dir: Path) -> list[Path]:
    files = [
        path
        for path in sorted(input_dir.iterdir())
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
    ]
    return files


def sanitize_transcript_basename(raw_name: str) -> str:
    sanitized = re.sub(r"[^\w.-]+", "_", raw_name, flags=re.UNICODE)
    sanitized = re.sub(r"_+", "_", sanitized).strip("_.")
    return sanitized or "untitled"


@app.command()
def main(
    input_dir: Annotated[
        Path,
        typer.Option("--input-dir", help="Directory that contains video files."),
    ] = Path("data/videos"),
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", help="Directory to save transcripts."),
    ] = Path("docs/transcripts"),
    model_name: Annotated[
        str,
        typer.Option("--model", help="Whisper model name, e.g. large-v3/small/medium."),
    ] = "large-v3",
    language: Annotated[
        str | None,
        typer.Option(
            "--language",
            help="Language code like en/zh. Leave empty for auto-detection.",
        ),
    ] = None,
) -> None:
    if not input_dir.exists() or not input_dir.is_dir():
        typer.secho(
            f"Error: Input directory not found: {input_dir}", fg="red", err=True
        )
        raise typer.Exit(code=1)

    video_files = find_video_files(input_dir)
    if not video_files:
        typer.secho(f"No video files found in {input_dir}", fg="yellow")
        raise typer.Exit(code=0)

    model_output_dir = output_dir / model_name.replace("/", "-")
    model_output_dir.mkdir(parents=True, exist_ok=True)

    typer.echo(f"Loading Whisper model: {model_name}")
    model = whisper.load_model(model_name)

    use_fp16 = torch.cuda.is_available()
    failed: list[Path] = []

    for index, video_path in enumerate(video_files, start=1):
        typer.echo(f"[{index}/{len(video_files)}] Transcribing {video_path.name}")
        try:
            result = model.transcribe(
                str(video_path),
                language=language,
                fp16=use_fp16,
                verbose=False,
            )
            text = (result.get("text") or "").strip()
            transcript_name = sanitize_transcript_basename(video_path.stem)
            transcript_path = model_output_dir / f"{transcript_name}.txt"
            transcript_path.write_text(text + "\n", encoding="utf-8")
        except Exception as exc:
            failed.append(video_path)
            typer.secho(f"  Failed: {exc}", fg="red")

    if failed:
        typer.secho("\nCompleted with errors. Failed files:", fg="yellow")
        for path in failed:
            typer.echo(f"- {path}")
        raise typer.Exit(code=2)

    typer.secho(f"\nDone. Transcripts saved to: {model_output_dir}", fg="green")


if __name__ == "__main__":
    app()

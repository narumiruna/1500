#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "typer>=0.24.1",
# ]
# ///

from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated

import typer

DATE_LINE_RE = re.compile(r"📅\s*日期：\d{3} 年 \d{1,2} 月 \d{1,2} 日（[上下]午）")
VIDEO_LINE_RE = re.compile(
    r'🎥\s*<a href="https://www\.youtube\.com/watch\?v=[A-Za-z0-9_-]+" '
    r'target="_blank" rel="noopener noreferrer">庭審錄影</a>'
)

app = typer.Typer(add_completion=False, help="Check oral-arguments page consistency.")


def list_target_files(orals_dir: Path) -> list[Path]:
    return sorted(path for path in orals_dir.glob("114-*.html") if path.is_file())


def expected_transcript_relpath(filename: str) -> str | None:
    match = re.match(r"(\d{3})-(\d{2})-(\d{2})-(am|pm)\.html$", filename)
    if not match:
        return None

    roc, month, day, ap = match.groups()
    period = "上午" if ap == "am" else "下午"
    transcript_name = (
        f"113年度金訴字第51號言詞辯論_{roc}_{month}_{day}{period}法庭錄影.txt"
    )
    return f"../docs/transcripts/large-v3/{transcript_name}"


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    content = path.read_text(encoding="utf-8")

    if not DATE_LINE_RE.search(content):
        issues.append("日期格式不符合統一規則")

    if not VIDEO_LINE_RE.search(content):
        issues.append("錄影連結文案或 rel 屬性不符合統一規則")

    expected_transcript = expected_transcript_relpath(path.name)
    if expected_transcript is None:
        issues.append("檔名不符合預期規則，無法推導逐字稿路徑")
    elif expected_transcript not in content:
        issues.append(f"缺少逐字稿連結：{expected_transcript}")

    return issues


@app.command()
def main(
    oral_arguments_dir: Annotated[
        Path,
        typer.Option(
            "--oral-arguments-dir",
            help="Directory containing oral argument HTML files.",
        ),
    ] = Path("oral-arguments"),
) -> None:
    if not oral_arguments_dir.is_dir():
        typer.secho(
            f"Error: directory not found: {oral_arguments_dir}", fg="red", err=True
        )
        raise typer.Exit(code=1)

    files = list_target_files(oral_arguments_dir)
    if not files:
        typer.secho("No target files found (pattern: 114-*.html)", fg="yellow")
        raise typer.Exit(code=0)

    total_issues = 0
    for path in files:
        issues = check_file(path)
        if not issues:
            continue

        total_issues += len(issues)
        typer.secho(f"[FAIL] {path}", fg="red")
        for issue in issues:
            typer.echo(f"  - {issue}")

    if total_issues:
        typer.secho(f"\nFound {total_issues} issue(s).", fg="red")
        raise typer.Exit(code=2)

    typer.secho(f"OK: {len(files)} files passed consistency checks.", fg="green")


if __name__ == "__main__":
    app()

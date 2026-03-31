# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "markdownify>=1.2.2",
#     "typer>=0.24.1",
# ]
# ///
from __future__ import annotations

import shutil
import ssl
import subprocess
from pathlib import Path
from typing import Annotated
from urllib.request import Request, urlopen

import typer
from markdownify import markdownify as md

DEFAULT_URL = "https://tpd.judicial.gov.tw/tw/cp-2850-2834163-856cd-151.html"
DEFAULT_OUTPUT = Path("docs/case_113_jinsu_51_press_release.md")

app = typer.Typer(
    add_completion=False, help="Download a web page and convert it to Markdown."
)


def fetch_html(url: str, timeout: float, insecure: bool = False) -> str:
    try:
        return fetch_html_with_urllib(url=url, timeout=timeout, insecure=insecure)
    except Exception:
        return fetch_html_with_curl(url=url, timeout=timeout, insecure=insecure)


def fetch_html_with_urllib(url: str, timeout: float, insecure: bool = False) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; markdownify-script/1.0)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    context = None
    if insecure:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    with urlopen(request, timeout=timeout, context=context) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def fetch_html_with_curl(url: str, timeout: float, insecure: bool = False) -> str:
    curl_path = shutil.which("curl")
    if curl_path is None:
        raise RuntimeError("curl is not available in PATH")

    cmd = [
        curl_path,
        "--silent",
        "--show-error",
        "--location",
        "--http1.1",
        "--tlsv1.2",
        "--retry",
        "3",
        "--retry-all-errors",
        "--max-time",
        str(timeout),
        "--user-agent",
        "Mozilla/5.0 (compatible; markdownify-script/1.0)",
        "--header",
        "Accept: text/html,application/xhtml+xml",
    ]
    if insecure:
        cmd.append("--insecure")
    cmd.append(url)

    completed = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"curl failed ({completed.returncode}): {stderr}")
    return completed.stdout.decode("utf-8", errors="replace")


def convert_html_to_markdown(html: str) -> str:
    return md(html, heading_style="ATX", strip=["script", "style"]).strip() + "\n"


@app.command()
def main(
    url: Annotated[
        str,
        typer.Option("--url", help="Target web page URL."),
    ] = DEFAULT_URL,
    output: Annotated[
        Path,
        typer.Option("--output", help="Output Markdown file path."),
    ] = DEFAULT_OUTPUT,
    timeout: Annotated[
        float,
        typer.Option("--timeout", min=1.0, help="HTTP timeout in seconds."),
    ] = 30.0,
    insecure: Annotated[
        bool,
        typer.Option(
            "--insecure",
            help="Disable TLS certificate verification (use only when necessary).",
        ),
    ] = False,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        html = fetch_html(url=url, timeout=timeout, insecure=insecure)
    except Exception as exc:
        typer.secho(f"Failed to download URL: {url}\nReason: {exc}", fg="red", err=True)
        raise typer.Exit(code=1)

    markdown = convert_html_to_markdown(html)
    output.write_text(markdown, encoding="utf-8")
    typer.secho(f"Saved Markdown to: {output}", fg="green")


if __name__ == "__main__":
    app()

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import typer
from markdownify import markdownify as md
from playwright.async_api import async_playwright

DEFAULT_URL = "https://tpd.judicial.gov.tw/tw/cp-2850-2834163-856cd-151.html"
DEFAULT_OUTPUT = Path("docs/case_113_jinsu_51_press_release.md")

app = typer.Typer(
    add_completion=False,
    help="Download a web page with Playwright and convert it to Markdown.",
)


def convert_html_to_markdown(html: str) -> str:
    return md(html, heading_style="ATX", strip=["script", "style"]).strip() + "\n"


async def fetch_html_with_playwright(
    url: str,
    timeout: float,
    insecure: bool = False,
) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(ignore_https_errors=insecure)
        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=int(timeout * 1000))
        html = await page.content()
        await context.close()
        await browser.close()
        return html


def build_jina_reader_url(url: str) -> str:
    return f"https://r.jina.ai/http://{url.removeprefix('https://').removeprefix('http://')}"


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
    ] = 45.0,
    insecure: Annotated[
        bool,
        typer.Option(
            "--insecure",
            help="Disable TLS certificate verification in browser context.",
        ),
    ] = False,
    use_jina_reader: Annotated[
        bool,
        typer.Option(
            "--use-jina-reader",
            help="Fetch via r.jina.ai reader proxy if direct connection is blocked.",
        ),
    ] = False,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    target_url = build_jina_reader_url(url) if use_jina_reader else url

    try:
        html = asyncio.run(
            fetch_html_with_playwright(
                url=target_url, timeout=timeout, insecure=insecure
            )
        )
    except Exception as exc:
        typer.secho(
            f"Failed to download URL: {target_url}\nReason: {exc}",
            fg="red",
            err=True,
        )
        raise typer.Exit(code=1)

    markdown = convert_html_to_markdown(html)
    output.write_text(markdown, encoding="utf-8")
    typer.secho(f"Saved Markdown to: {output}", fg="green")


if __name__ == "__main__":
    app()

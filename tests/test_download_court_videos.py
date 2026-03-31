from __future__ import annotations

import importlib.util
import pathlib
import tempfile
import unittest
from unittest import mock


def _load_module():
    module_path = pathlib.Path("scripts/download_court_videos.py")
    spec = importlib.util.spec_from_file_location("download_court_videos", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DownloadCourtVideosTests(unittest.TestCase):
    def test_parse_args_default_workers_is_one(self):
        mod = _load_module()
        args = mod.parse_args([])
        self.assertEqual(args.workers, "1")
        self.assertFalse(args.audio_only)

    def test_parse_args_audio_only_flag(self):
        mod = _load_module()
        args = mod.parse_args(["--audio-only"])
        self.assertTrue(args.audio_only)

    def test_extract_url_from_line_supports_markdown_and_plain_url(self):
        mod = _load_module()

        self.assertEqual(
            mod.extract_url_from_line("- [title](https://www.youtube.com/watch?v=abc)"),
            "https://www.youtube.com/watch?v=abc",
        )
        self.assertEqual(
            mod.extract_url_from_line("https://www.youtube.com/watch?v=def"),
            "https://www.youtube.com/watch?v=def",
        )
        self.assertIsNone(mod.extract_url_from_line("# comment"))
        self.assertIsNone(mod.extract_url_from_line("not a url"))

    def test_load_urls_ignores_noise_and_deduplicates(self):
        mod = _load_module()
        content = "\n".join(
            [
                "- [A](https://www.youtube.com/watch?v=abc)",
                "https://www.youtube.com/watch?v=def",
                "- [A duplicate](https://www.youtube.com/watch?v=abc)",
                "# comment",
                "random text",
                "",
            ]
        )

        with tempfile.TemporaryDirectory() as td:
            url_file = pathlib.Path(td) / "court_video_urls.md"
            url_file.write_text(content, encoding="utf-8")

            urls = mod.load_urls(url_file)

        self.assertEqual(
            urls,
            [
                "https://www.youtube.com/watch?v=abc",
                "https://www.youtube.com/watch?v=def",
            ],
        )

    def test_main_downloads_all_urls(self):
        mod = _load_module()
        content = "\n".join(
            [
                "- [A](https://www.youtube.com/watch?v=abc)",
                "https://www.youtube.com/watch?v=def",
            ]
        )

        with tempfile.TemporaryDirectory() as td:
            tmpdir = pathlib.Path(td)
            url_file = tmpdir / "court_video_urls.md"
            out_dir = tmpdir / "videos"
            url_file.write_text(content, encoding="utf-8")

            with (
                mock.patch.object(mod.shutil, "which", return_value="/usr/bin/yt-dlp"),
                mock.patch.object(mod, "download_one") as download_one,
            ):
                code = mod.main([str(url_file), str(out_dir), "2"])

        self.assertEqual(code, 0)
        self.assertEqual(download_one.call_count, 2)

    def test_download_one_uses_highest_quality_format(self):
        mod = _load_module()

        with tempfile.TemporaryDirectory() as td:
            out_dir = pathlib.Path(td)
            with mock.patch.object(mod.subprocess, "run") as run:
                mod.download_one("https://www.youtube.com/watch?v=abc", out_dir)

        command = run.call_args[0][0]
        self.assertIn("-f", command)
        format_value = command[command.index("-f") + 1]
        self.assertEqual(format_value, "bestvideo*+bestaudio/best")

    def test_download_one_audio_only_uses_mp3_extract(self):
        mod = _load_module()

        with tempfile.TemporaryDirectory() as td:
            out_dir = pathlib.Path(td)
            with mock.patch.object(mod.subprocess, "run") as run:
                mod.download_one(
                    "https://www.youtube.com/watch?v=abc", out_dir, audio_only=True
                )

        command = run.call_args[0][0]
        self.assertIn("-x", command)
        self.assertIn("--audio-format", command)
        self.assertEqual(
            command[command.index("--audio-format") + 1],
            "mp3",
        )


if __name__ == "__main__":
    unittest.main()

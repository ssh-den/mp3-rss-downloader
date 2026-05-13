import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import mp3_rss_downloader as downloader


def build_feed(items: list[str]) -> bytes:
    return f"<rss><channel>{''.join(items)}</channel></rss>".encode("utf-8")


class FakeProgressBar:
    def __init__(self, total, unit, desc):
        self.total = total
        self.unit = unit
        self.desc = desc
        self.updated = 0
        self.closed = False

    def update(self, amount):
        self.updated += amount

    def close(self):
        self.closed = True


class ParseRssTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.download_path = Path(self.temp_dir.name)
        self.download_path_patch = patch.object(downloader, "DOWNLOAD_PATH", self.download_path)
        self.limit_patch = patch.object(downloader, "EPISODE_DOWNLOAD_LIMIT", None)
        self.download_path_patch.start()
        self.limit_patch.start()

    def tearDown(self):
        self.limit_patch.stop()
        self.download_path_patch.stop()
        self.temp_dir.cleanup()

    def test_parse_rss_sorts_by_pubdate_and_skips_invalid_items(self):
        rss = build_feed(
            [
                '<item><title>Older Episode</title><pubDate>Mon, 01 Jan 2024 10:00:00 GMT</pubDate><enclosure url="https://example.com/old.mp3" /></item>',
                '<item><title>Newest Episode</title><pubDate>Mon, 01 Jan 2025 10:00:00 GMT</pubDate><enclosure url="https://example.com/new.mp3" /></item>',
                '<item><title>Missing Enclosure</title></item>',
                '<item><pubDate>Mon, 01 Jan 2026 10:00:00 GMT</pubDate><enclosure url="https://example.com/no-title.mp3" /></item>',
            ]
        )

        tasks, skipped_items = downloader.parse_rss(rss)

        self.assertEqual([task.title for task in tasks], ["Newest Episode", "Older Episode"])
        self.assertEqual(skipped_items, 2)
        self.assertEqual(tasks[0].filename, self.download_path / "Newest Episode.mp3")

    def test_parse_rss_keeps_only_newest_items_when_limit_is_set(self):
        rss = build_feed(
            [
                '<item><title>Episode 1</title><pubDate>Mon, 01 Jan 2023 10:00:00 GMT</pubDate><enclosure url="https://example.com/1.mp3" /></item>',
                '<item><title>Episode 2</title><pubDate>Mon, 01 Jan 2024 10:00:00 GMT</pubDate><enclosure url="https://example.com/2.mp3" /></item>',
                '<item><title>Episode 3</title><pubDate>Mon, 01 Jan 2025 10:00:00 GMT</pubDate><enclosure url="https://example.com/3.mp3" /></item>',
            ]
        )

        with patch.object(downloader, "EPISODE_DOWNLOAD_LIMIT", 2):
            tasks, skipped_items = downloader.parse_rss(rss)

        self.assertEqual([task.title for task in tasks], ["Episode 3", "Episode 2"])
        self.assertEqual(skipped_items, 0)

    def test_parse_rss_falls_back_to_feed_order_when_pubdate_is_missing(self):
        rss = build_feed(
            [
                '<item><title>First In Feed</title><enclosure url="https://example.com/1.mp3" /></item>',
                '<item><title>Second In Feed</title><enclosure url="https://example.com/2.mp3" /></item>',
                '<item><title>Third In Feed</title><enclosure url="https://example.com/3.mp3" /></item>',
            ]
        )

        with patch.object(downloader, "EPISODE_DOWNLOAD_LIMIT", 2):
            tasks, skipped_items = downloader.parse_rss(rss)

        self.assertEqual([task.title for task in tasks], ["First In Feed", "Second In Feed"])
        self.assertEqual(skipped_items, 0)

    def test_parse_rss_assigns_unique_filenames_after_sanitizing_titles(self):
        rss = build_feed(
            [
                '<item><title>Same/Title</title><pubDate>Mon, 01 Jan 2025 10:00:00 GMT</pubDate><enclosure url="https://example.com/1.mp3" /></item>',
                '<item><title>Same:Title</title><pubDate>Mon, 01 Jan 2024 10:00:00 GMT</pubDate><enclosure url="https://example.com/2.mp3" /></item>',
                '<item><title>Same_Title-2</title><pubDate>Mon, 01 Jan 2023 10:00:00 GMT</pubDate><enclosure url="https://example.com/3.mp3" /></item>',
                '<item><title>Same/Title</title><pubDate>Mon, 01 Jan 2022 10:00:00 GMT</pubDate><enclosure url="https://example.com/4.mp3" /></item>',
            ]
        )

        tasks, skipped_items = downloader.parse_rss(rss)

        self.assertEqual(skipped_items, 0)
        self.assertEqual(
            [task.filename.name for task in tasks],
            ["Same_Title.mp3", "Same_Title-2.mp3", "Same_Title-2-2.mp3", "Same_Title-3.mp3"],
        )


class DownloadFilesTests(unittest.TestCase):
    def test_download_files_updates_progress_for_downloaded_skipped_and_failed_items(self):
        tasks = [
            downloader.EpisodeTask("Downloaded", "https://example.com/1.mp3", Path("downloaded.mp3"), (1, 3.0)),
            downloader.EpisodeTask("Skipped", "https://example.com/2.mp3", Path("skipped.mp3"), (1, 2.0)),
            downloader.EpisodeTask("Failed", "https://example.com/3.mp3", Path("failed.mp3"), (1, 1.0)),
        ]

        statuses = {
            "Downloaded": ("downloaded", "downloaded.mp3"),
            "Skipped": ("skipped", "skipped.mp3"),
            "Failed": ("failed", "Failed: boom"),
        }
        progress = FakeProgressBar(total=0, unit="", desc="")

        def fake_download_file(task):
            return statuses[task.title]

        def fake_tqdm(total, unit, desc):
            progress.total = total
            progress.unit = unit
            progress.desc = desc
            return progress

        with patch.object(downloader, "download_file", side_effect=fake_download_file):
            with patch.object(downloader, "tqdm", side_effect=fake_tqdm):
                downloaded, skipped, failures = downloader.download_files(tasks)

        self.assertEqual(downloaded, 1)
        self.assertEqual(skipped, 1)
        self.assertEqual(failures, ["Failed: boom"])
        self.assertEqual(progress.total, 3)
        self.assertEqual(progress.updated, 3)
        self.assertTrue(progress.closed)


class MainTests(unittest.TestCase):
    def test_main_prints_config_error_without_traceback_when_rss_url_is_placeholder(self):
        with patch.object(downloader, "parse_args"):
            with patch.object(downloader, "RSS_URL", "your_rss_feed_url_here"):
                with patch.object(downloader, "fetch_rss_content") as fetch_rss_content:
                    with patch("builtins.print") as print_mock:
                        exit_code = downloader.main()

        self.assertEqual(exit_code, 1)
        fetch_rss_content.assert_not_called()
        print_mock.assert_called_once_with("Error: Set RSS_URL in src/config.py before running the script.")

    def test_main_reports_invalid_items_without_starting_downloads(self):
        rss = build_feed(
            [
                '<item><title>Missing Enclosure</title></item>',
                '<item><enclosure url="https://example.com/no-title.mp3" /></item>',
            ]
        )

        with patch.object(downloader, "parse_args"):
            with patch.object(downloader, "RSS_URL", "https://example.com/feed.xml"):
                with patch.object(downloader, "setup_download_folder"):
                    with patch.object(downloader, "fetch_rss_content", return_value=rss):
                        with patch.object(downloader, "download_files") as download_files:
                            with patch("builtins.print") as print_mock:
                                exit_code = downloader.main()

        self.assertEqual(exit_code, 0)
        download_files.assert_not_called()
        self.assertEqual(
            [call.args[0] for call in print_mock.call_args_list],
            [
                "Skipped 2 RSS item(s) without a usable title or enclosure URL.",
                "No valid RSS episodes matched your settings.",
            ],
        )


if __name__ == "__main__":
    unittest.main()

"""Download MP3 episodes from an RSS feed."""

from __future__ import annotations

import argparse
import heapq
import re
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from io import BytesIO
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET

import requests
from requests import RequestException
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import (
    DOWNLOAD_FOLDER,
    EPISODE_DOWNLOAD_LIMIT,
    MAX_WORKERS,
    REQUEST_TIMEOUT_SECONDS,
    RSS_URL,
    RSS_URL_ARRAY,
    USE_ARRAY,
)

VERSION = "0.2.0"
REPO_ROOT = Path(__file__).resolve().parents[1]
DOWNLOAD_PATH = REPO_ROOT / DOWNLOAD_FOLDER
INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*]')

@dataclass(frozen=True)
class EpisodeTask:
    """A single file that should be downloaded."""

    title: str
    url: str
    filename: Path
    sort_key: tuple[int, float]

def parse_args() -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser(description="Download MP3 episodes from an RSS feed.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    return parser.parse_args()


def validate_config() -> None:
    """Fail early when the editable config still contains placeholder values."""
    if not RSS_URL or RSS_URL == "your_rss_feed_url_here":
        raise ValueError("Set RSS_URL in src/config.py before running the script.")

    if EPISODE_DOWNLOAD_LIMIT is not None and EPISODE_DOWNLOAD_LIMIT <= 0:
        raise ValueError("EPISODE_DOWNLOAD_LIMIT must be greater than 0 or None.")

    if MAX_WORKERS <= 0:
        raise ValueError("MAX_WORKERS must be greater than 0.")

    if REQUEST_TIMEOUT_SECONDS <= 0:
        raise ValueError("REQUEST_TIMEOUT_SECONDS must be greater than 0.")


def setup_download_folder() -> None:
    """Create the download folder if it does not already exist."""
    DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)


def strip_namespace(tag: str) -> str:
    """Normalize XML tags like {namespace}item to plain item."""
    return tag.split("}", 1)[-1]


def find_child(item: ET.Element, child_name: str) -> ET.Element | None:
    """Find a direct child element without caring about XML namespaces."""
    for child in item:
        if strip_namespace(child.tag) == child_name:
            return child
    return None


def parse_pub_date(value: str | None) -> datetime | None:
    """Parse pubDate when the feed provides one.

    We prefer pubDate for sorting because feed order is not always reliable.
    """
    if not value:
        return None

    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def sanitize_filename(title: str) -> str:
    """Turn an episode title into a filesystem-friendly MP3 filename."""
    collapsed_whitespace = " ".join(title.split())
    safe_title = INVALID_FILENAME_CHARS.sub("_", collapsed_whitespace).strip(" .")
    return safe_title or "untitled-episode"


def build_episode_task(item: ET.Element, source_index: int) -> EpisodeTask | None:
    """Create a download task from an RSS item or skip it when required fields are missing."""
    title_element = find_child(item, "title")
    enclosure_element = find_child(item, "enclosure")
    pub_date_element = find_child(item, "pubDate")

    title = title_element.text.strip() if title_element is not None and title_element.text else ""
    enclosure_url = enclosure_element.get("url", "").strip() if enclosure_element is not None else ""

    if not title or not enclosure_url:
          return None

    published_at = parse_pub_date(pub_date_element.text if pub_date_element is not None else None)

    # Dated items are sorted by actual publication time. Undated items keep feed order as a fallback.
    if published_at is not None:
        sort_key = (1, published_at.timestamp())
    else:
        sort_key = (0, -float(source_index))

    filename = DOWNLOAD_PATH / f"{sanitize_filename(title)}.mp3"
    return EpisodeTask(title=title, url=enclosure_url, filename=filename, sort_key=sort_key)


def assign_unique_filenames(tasks: Iterable[EpisodeTask]) -> list[EpisodeTask]:
    """Avoid filename clashes after RSS titles are sanitized."""
    renamed_tasks: list[EpisodeTask] = []
    used_filenames: set[str] = set()

    for task in tasks:
        stem = task.filename.stem
        suffix = task.filename.suffix
        counter = 1
        filename = task.filename

        while filename.name in used_filenames:
            counter += 1
            filename = task.filename.with_name(f"{stem}-{counter}{suffix}")

        used_filenames.add(filename.name)
        renamed_tasks.append(replace(task, filename=filename))

    return renamed_tasks


def keep_top_episodes(tasks: list[tuple[tuple[int, float], int, EpisodeTask]], task: EpisodeTask, source_index: int) -> None:
    """Keep only the newest N episodes in memory when a download limit is configured."""
    entry = (task.sort_key, source_index, task)

    if EPISODE_DOWNLOAD_LIMIT is None:
        tasks.append(entry)
        return

    if len(tasks) < EPISODE_DOWNLOAD_LIMIT:
        heapq.heappush(tasks, entry)
        return

    heapq.heappushpop(tasks, entry)


def parse_rss(rss_content: bytes) -> tuple[list[EpisodeTask], int]:
    """Parse the RSS XML and return the selected download tasks.

    When EPISODE_DOWNLOAD_LIMIT is set, we keep only the newest matching
    items instead of building a full task list and slicing it afterwards.
    """
    selected_tasks: list[tuple[tuple[int, float], int, EpisodeTask]] = []
    skipped_items = 0

    for source_index, (_, item) in enumerate(ET.iterparse(BytesIO(rss_content), events=("end",)), start=1):
        if strip_namespace(item.tag) != "item":
            continue

        task = build_episode_task(item, source_index)
        if task is None:
            skipped_items += 1
        else:
            keep_top_episodes(selected_tasks, task, source_index)

            item.clear()

    ordered_tasks = [entry[2] for entry in selected_tasks]
    ordered_tasks.sort(key=lambda task: task.sort_key, reverse=True)
    return assign_unique_filenames(ordered_tasks), skipped_items


def fetch_rss_content(rss_url: str) -> bytes:
    """Fetch the RSS feed and raise a useful error when the request fails."""
    response = requests.get(rss_url, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.content


def stream_to_file(url: str, destination: Path) -> None:
    """Download a URL into a temporary file and move it into place when complete."""
    temp_destination = destination.with_suffix(f"{destination.suffix}.part")

    with requests.get(url, stream=True, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        response.raise_for_status()
        with temp_destination.open("wb") as file_handle:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file_handle.write(chunk)

    temp_destination.replace(destination)


def download_file(task: EpisodeTask) -> tuple[str, str]:
    """Download one episode and return a small status summary."""
    if task.filename.exists():
        return "skipped", task.filename.name

    try:
        stream_to_file(task.url, task.filename)
    except (OSError, RequestException) as exc:
        partial_file = task.filename.with_suffix(f"{task.filename.suffix}.part")
        if partial_file.exists():
            partial_file.unlink()
        return "failed", f"{task.title}: {exc}"

    return "downloaded", task.filename.name


def download_files(download_tasks: Iterable[EpisodeTask]) -> tuple[int, int, list[str]]:
    """Download the selected episodes with a progress bar that always reaches 100%."""
    tasks = list(download_tasks)
    downloaded = 0
    skipped = 0
    failures: list[str] = []

    progress_bar = tqdm(total=len(tasks), unit="file", desc="Downloading")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(download_file, task) for task in tasks]

        for future in as_completed(futures):
            try:
                status, details = future.result()
            except Exception as exc:  # pragma: no cover - last-resort worker guard
                status, details = "failed", f"Unexpected worker error: {exc}"

            if status == "downloaded":
                downloaded += 1
            elif status == "skipped":
                skipped += 1
            else:
                failures.append(details)

            progress_bar.update(1)

    progress_bar.close()
    return downloaded, skipped, failures


def print_summary(downloaded: int, skipped: int, failures: list[str], skipped_items: int) -> None:
    """Print the run summary."""
    if skipped_items:
        print(f"Skipped {skipped_items} RSS item(s) without a usable title or enclosure URL.")

    print(f"Downloaded: {downloaded}")
    print(f"Already present: {skipped}")

    if failures:
        print(f"Failed: {len(failures)}")
        for failure in failures:
            print(f"  - {failure}")
    else:
        print("Failed: 0")


def main() -> int:
    """Run the downloader."""
    global RSS_URL

    parse_args()

    try:
        validate_config()
        setup_download_folder()
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1

    total_downloaded = 0
    total_skipped = 0
    total_failures: list[str] = []
    total_skipped_items = 0

    if USE_ARRAY == True:
        for rss_url in RSS_URL_ARRAY:
    
            try:
                validate_config()
                setup_download_folder()

                rss_content = fetch_rss_content(rss_url)

                download_tasks, skipped_items = parse_rss(rss_content)

            except (ET.ParseError, RequestException, ValueError) as exc:
                print(f"Error: {exc}")
                continue

            if not download_tasks:
                print(f"No episodes found for {rss_url}")
                continue

            downloaded, skipped, failures = download_files(download_tasks)

            total_downloaded += downloaded
            total_skipped += skipped
            total_failures.extend(failures)
            total_skipped_items += skipped_items
            
        print_summary(
            total_downloaded,
            total_skipped,
            total_failures,
            total_skipped_items,
        )
    else:
        try:
            validate_config()
            setup_download_folder()

            rss_content = fetch_rss_content(rss_url)

            download_tasks, skipped_items = parse_rss(rss_content)

        except (ET.ParseError, RequestException, ValueError) as exc:
            print(f"Error: {exc}")
            continue

        if not download_tasks:
            print(f"No episodes found for {rss_url}")
            continue

        downloaded, skipped, failures = download_files(download_tasks)

        total_downloaded += downloaded
        total_skipped += skipped
        total_failures.extend(failures)
        total_skipped_items += skipped_items
            
        print_summary(
            total_downloaded,
            total_skipped,
            total_failures,
            total_skipped_items,
            
    print("\nDownload complete!")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

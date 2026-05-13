# Criteria for successful downloading

This document describes the downloader's logic and the RSS structure it expects.

## Configuration

User-editable settings live in [`src/config.py`](../src/config.py):

1. `RSS_URL` points to the RSS feed.
2. `DOWNLOAD_FOLDER` sets the output directory relative to the repository root.
3. `MAX_WORKERS` controls how many files may download in parallel.
4. `EPISODE_DOWNLOAD_LIMIT` limits how many episodes are selected.
5. `REQUEST_TIMEOUT_SECONDS` sets the timeout for RSS and MP3 requests.

## RSS item requirements

Each `<item>` is evaluated independently.

1. `title` is used to build the output filename.
2. `enclosure url="..."` is used as the download URL.
3. `pubDate` is optional, but it improves episode ordering.

If `title` is missing or empty, the item is skipped.
If `enclosure` is missing or its `url` attribute is empty, the item is skipped.

## Episode selection

The downloader parses RSS items incrementally.

1. Each valid item becomes a download task.
2. If `EPISODE_DOWNLOAD_LIMIT` is `None`, all valid items are kept.
3. If a numeric limit is set, only the newest matching items are kept in memory.

This keeps memory usage predictable even when the feed contains many items.

## Episode ordering

Episode order is based on `pubDate` when available.

1. Items with a valid `pubDate` are sorted from newest to oldest.
2. Items without a valid `pubDate` fall back to feed order.
3. When a download limit is set, the limit is applied after this selection logic, not by taking the first raw XML items.

## Filenames

The script converts episode titles into safe filenames.

1. Extra whitespace is collapsed.
2. Characters that are invalid in common filesystems are replaced with underscores.
3. The `.mp3` extension is appended to the sanitized title.

## Download behavior

Each selected item is processed as follows:

1. If the target file already exists, it is skipped.
2. Otherwise, the file is downloaded to a temporary `.part` file first.
3. After a successful download, the temporary file is renamed to the final `.mp3` filename.
4. If a download fails, the temporary partial file is removed.

## Progress and summary

The progress bar tracks every selected task.

1. Downloaded files advance the bar.
2. Already existing files also advance the bar.
3. Failed downloads advance the bar and are listed in the final summary.

At the end of the run, the script prints counts for downloaded files, skipped existing files, failed downloads, and skipped invalid RSS items.

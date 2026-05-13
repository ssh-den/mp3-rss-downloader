# Changelog

Project changes are listed here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.2.0] - 2026-05-12

### Added
- Added `src/config.py` for RSS URL and downloader settings.
- Added script versioning with a `--version` flag.
- Added this changelog in Keep a Changelog format.

### Changed
- Moved the downloader script into `src/`.
- Moved Markdown support documentation into `docs/`.
- Renamed `MAX_EPISODES_TO_DOWNLOAD` to `EPISODE_DOWNLOAD_LIMIT` for clearer configuration naming.
- Updated episode selection to keep only the newest matching items in memory when a limit is configured.
- Updated README instructions and links to reflect the new structure.

### Fixed
- Fixed episode limiting so the script no longer builds a full download task list before trimming it.
- Fixed episode ordering by preferring `pubDate` instead of trusting raw RSS item order.
- Fixed progress reporting so skipped existing files still advance the progress bar.
- Fixed RSS parsing to skip items that are missing a usable `title` or `enclosure` URL.

# mp3-rss-downloader

Simple RSS-to-MP3 downloader with a small config file, concurrent downloads, and a progress bar.

Current version: `0.2.0`

## Features

* Edit feed URL and limits in [`src/config.py`](./src/config.py).
* The downloader prefers RSS `pubDate` when deciding which episodes are the newest.
* If a limit is configured, the script keeps only the selected episodes in memory instead of building a full list and slicing it afterwards.
* Existing files are skipped, and the progress bar still finishes correctly.
* RSS items missing `title` or `enclosure` are skipped cleanly instead of crashing the run.

## Usage

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ssh-den/mp3-rss-downloader.git
   ```
   Or download the script file directly.

2. **Create a virtual environment (recommended)**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install requests tqdm
   ```

   If you prefer not to activate the environment, you can use `.venv/bin/pip` and `.venv/bin/python` directly.

4. **Set your feed and limits**:
   - Open [`src/config.py`](./src/config.py).
   - Replace `your_rss_feed_url_here` with the RSS feed URL you want to use.
   - Optionally adjust `DOWNLOAD_FOLDER`, `MAX_WORKERS`, `EPISODE_DOWNLOAD_LIMIT`, and `REQUEST_TIMEOUT_SECONDS`.

5. **Run the script**:
   ```bash
   python src/mp3_rss_downloader.py
   ```

6. **Check the version**:
   ```bash
   python src/mp3_rss_downloader.py --version
   ```

7. **Downloaded files**:
   MP3 files are saved in the folder defined by `DOWNLOAD_FOLDER`, relative to the repository root.

## Project structure

* [`src/mp3_rss_downloader.py`](./src/mp3_rss_downloader.py) — main downloader script
* [`src/config.py`](./src/config.py) — editable settings
* [`docs/Criteria_for_Successful_Downloading.md`](./docs/Criteria_for_Successful_Downloading.md) — script behavior and feed expectations
* [`CHANGELOG.md`](./CHANGELOG.md) — project history in Keep a Changelog format

## Notes on RSS ordering

The script sorts episodes by `pubDate` when that field is available. If a feed does not provide `pubDate`, the script falls back to the original RSS item order.

## License

This project is licensed under the MIT License. See [`LICENSE`](./LICENSE) for details.

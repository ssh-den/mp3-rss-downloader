# mp3-rss-downloader

This simple Python script is designed to download MP3 files from a specific RSS feed. It parses the given RSS feed, extracts MP3 links along with their titles, and downloads them into a specified directory. The script ensures that each MP3 file is downloaded by only one worker, skipping the download if the file already exists locally. It utilizes concurrent programming with ThreadPoolExecutor for efficient downloading and includes progress bar to track the download progress.

## Features

* Parses an RSS feed to extract MP3 links and titles.
* Downloads MP3 files concurrently, ensuring each link is processed by only one worker.
* Skips downloading if the file already exists locally.
* Utilizes progress bars to indicate download progress for each file.
* Easy to use and configurable.

## Usage

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ssh-den/mp3-rss-downloader.git
   ```
   Or download the script file directly.

2. **Install Dependencies**:
   ```bash
   pip install requests tqdm
   ```

4. **Set RSS Feed URL**:
   - Open the script and replace 'your_rss_feed_url_here' with the URL of your RSS feed.
   - Adjust other settings such as the download folder location or the maximum number of concurrent downloads if needed.

5. **Run the Script**:
   ```bash
   python mp3_rss_downloader.py.py
   ```

6. **Downloaded Files**:
   MP3 files will be saved in the 'mp3' directory within the script's location.

## Criteria for successfull downloading

   [Criteria for successful downloading](./Criteria_for_Successful_Downloading.md) — Guidelines for customizing and adapting the script to download MP3 files from RSS feeds.

## License:

This project is licensed under the MIT License. See the LICENSE file for details.

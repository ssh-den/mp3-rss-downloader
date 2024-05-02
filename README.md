# mp3-rss-downloader
Downloading mp3 from rss feeds

# Description

This Python script is designed to download MP3 files from an RSS feed. It parses the given RSS feed, extracts MP3 links along with their titles, and downloads them into a specified directory. The script ensures that each MP3 file is downloaded by only one worker, skipping the download if the file already exists locally. It utilizes concurrent programming with ThreadPoolExecutor for efficient downloading and includes progress bars to track the download progress.

# Features

* Parses an RSS feed to extract MP3 links and titles.
* Downloads MP3 files concurrently, ensuring each link is processed by only one worker.
* Skips downloading if the file already exists locally.
* Utilizes progress bars to indicate download progress for each file.
* Easy to use and configurable.

# Usage

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/repository.git
   ```
   Or download the script file directly.

2. **Install Dependencies**:
   - Make sure you have the following dependencies installed:
     - `requests`
     - `tqdm`
     
   ```bash
   pip install requests tqdm
   ```

4. **Set RSS Feed URL**:
   - Open the script and replace 'your_rss_feed_url_here' with the URL of your RSS feed.
   - Adjust other settings such as the download folder location or the maximum number of concurrent downloads if needed.

5. **Run the Script**:
   ```bash
   python script.py
   ```

6. **Downloaded Files**:
   MP3 files will be saved in the 'mp3' directory within the script's location.

# Contributing:

Contributions are welcome! If you find any issues or have suggestions for improvements, feel free to open an issue or submit a pull request.

# License:

This project is licensed under the MIT License. See the LICENSE file for details.

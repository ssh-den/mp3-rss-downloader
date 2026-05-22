"""Editable settings for the RSS downloader.

Change these values to point the script at your feed and tune downloads.
"""

#Use the array instead of a single url
USE_ARRAY = True

# RSS feed with podcast/audio episodes.
RSS_URL = "insert rss url here"

# List of RSS feeds with podcast/audio episodes.
RSS_URL_ARRAY = ["insert a lsit of rss urls, seperated by a comma"]

# Download target relative to the repository root.
DOWNLOAD_FOLDER = 'mp3'

# Number of concurrent downloads.
MAX_WORKERS = 5

# Limit how many newest episodes to download.
# Use None to download every valid episode from the feed.
EPISODE_DOWNLOAD_LIMIT = 5

# Network timeout in seconds for RSS and MP3 requests.
REQUEST_TIMEOUT_SECONDS = 30
"""Editable settings for the RSS downloader.

Change these values to point the script at your feed and tune downloads.
"""

# RSS feed with podcast/audio episodes.
RSS_URL = "your_rss_feed_url_here"

# Download target relative to the repository root.
DOWNLOAD_FOLDER = "mp3"

# Number of concurrent downloads.
MAX_WORKERS = 5

# Limit how many newest episodes to download.
# Use None to download every valid episode from the feed.
EPISODE_DOWNLOAD_LIMIT = None

# Network timeout in seconds for RSS and MP3 requests.
REQUEST_TIMEOUT_SECONDS = 30

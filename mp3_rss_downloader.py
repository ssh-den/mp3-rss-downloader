import os
import requests
import xml.etree.ElementTree as ET
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

# Variables
RSS_URL = 'your_rss_feed_url_here' # URL of the RSS feed containing MP3 files
DOWNLOAD_FOLDER = 'mp3' # Folder where the MP3 files will be downloaded
MAX_WORKERS = 5 # Maximum number of concurrent workers for downloading

# Functions
def setup_download_folder():
    # Create the download folder if it doesn't exist
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)

def parse_rss(rss_content):
    # Parse the RSS content and extract MP3 links along with titles
    root = ET.fromstring(rss_content)
    # Extracting MP3 links and corresponding filenames for downloading
    download_tasks = [(
        item.find('enclosure').attrib['url'],
        os.path.join(DOWNLOAD_FOLDER, f"{item.find('title').text.strip()}.mp3")
    ) for item in root.findall('.//item')]
    return download_tasks

def fetch_rss_content():
    # Fetch the content of the RSS feed and handle HTTP errors
    response = requests.get(RSS_URL)
    if response.status_code == 200:
        return response.content
    else:
        # Print error message and exit if unable to fetch the RSS feed
        print(f"Failed to fetch RSS feed, status code: {response.status_code}")
        exit(1)

def download_file(args, progress_bar):
    # Download the file from the given URL if it doesn't exist locally
    url, filename = args
    # Skip download if the file already exists
    if os.path.exists(filename):
        return
    # Download the file with progress tracking using tqdm
    response = requests.get(url, stream=True)
    with open(filename, 'wb') as f:
        for data in response.iter_content(1024):
            f.write(data)
    # Update the progress bar after successful download
    progress_bar.update(1)

def download_files(download_tasks):
    # Download the files using ThreadPoolExecutor with a progress bar
    progress_bar = tqdm(total=len(download_tasks), unit='files', desc="Downloading")
    # Use executor.map to execute download_file in parallel with max workers
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        _ = list(executor.map(lambda args: download_file(args, progress_bar), download_tasks))
    # Close the progress bar upon completion
    progress_bar.close()

# Main function
def main():
    # Main function to orchestrate the download process
    setup_download_folder()
    # Fetch the RSS feed content
    rss_content = fetch_rss_content()
    # Parse the RSS content to extract download tasks
    download_tasks = parse_rss(rss_content)
    # Download the files using concurrent workers
    download_files(download_tasks)
    print("\nDownload complete!")

if __name__ == "__main__":
    main()

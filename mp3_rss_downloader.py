import os
import requests
import xml.etree.ElementTree as ET
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

RSS_URL = 'your_rss_feed_url_here'
DOWNLOAD_FOLDER = 'mp3'
MAX_WORKERS = 5

def setup_download_folder():
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)

def parse_rss(rss_content):
    root = ET.fromstring(rss_content)
    download_tasks = [(
        item.find('enclosure').attrib['url'],
        os.path.join(DOWNLOAD_FOLDER, f"{item.find('title').text.strip()}.mp3")
    ) for item in root.findall('.//item')]
    return download_tasks

def fetch_rss_content():
    response = requests.get(RSS_URL)
    if response.status_code == 200:
        return response.content
    else:
        print(f"Failed to fetch RSS feed, status code: {response.status_code}")
        exit(1)

def download_file(args, progress_bar):
    url, filename = args
    if os.path.exists(filename):
        return
    response = requests.get(url, stream=True)
    with open(filename, 'wb') as f:
        for data in response.iter_content(1024):
            f.write(data)
    progress_bar.update(1)

def download_files(download_tasks):
    progress_bar = tqdm(total=len(download_tasks), unit='files', desc="Downloading")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        _ = list(executor.map(lambda args: download_file(args, progress_bar), download_tasks))
    progress_bar.close()

def main():
    setup_download_folder()
    rss_content = fetch_rss_content()
    download_tasks = parse_rss(rss_content)
    download_files(download_tasks)
    print("\nDownload complete!")

if __name__ == "__main__":
    main()

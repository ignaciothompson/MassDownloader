import os
import re
import requests
import threading
import webview
from tkinter import filedialog, Tk
from tkinter import DoubleVar  # Add this import if not present
from tkinter import Frame, Label, Entry, Button, Text  # Add these imports if not present
from tkinter import ttk  # Add this import if not present

def extract_season_episode(url):
    """
    Extracts the season and episode information from the URL using regex.
    Expected pattern: SxxExx (e.g., S05E01)
    """
    match = re.search(r'S(\d{2})E(\d{2})', url, re.IGNORECASE)
    if match:
        season = match.group(1)
        episode = match.group(2)
        return f'S{season}E{episode}'
    else:
        return None

def sanitize_title(title):
    """
    Sanitizes the title by replacing spaces and invalid characters with dots.
    """
    return re.sub(r'[^\w\.]', '.', title)

def download_file(url, save_path, task_id, file_index):
    try:
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024  # 1KB
        wrote = 0

        with open(save_path, 'wb') as file:
            for data in response.iter_content(block_size):
                size = file.write(data)
                wrote += size
                if total_size > 0:
                    progress_percentage = (wrote / total_size) * 100
                else:
                    progress_percentage = 100
                # Send progress update to frontend
                webview.windows[0].evaluate_js(f"updateProgress({task_id}, {file_index}, {progress_percentage})")
        print(f"Download completed for {url}")
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")
        # Send error message to frontend
        webview.windows[0].evaluate_js(f"displayError('Failed to download {url}: {str(e)}')")

def start_all_downloads(task_frames, window):
    print("Starting all downloads...")  # Debugging information
    for frame in task_frames:
        path = frame['path_entry']
        urls = frame['urls']  # Updated to handle individual URLs
        task_id = frame['taskId']

        print(f"Task ID: {task_id}, Path: {path}, URLs: {urls}")  # Debugging information

        if not os.path.isdir(path):
            webview.windows[0].evaluate_js("displayError('Please select a valid download path.')")
            continue
        if not urls:
            webview.windows[0].evaluate_js("displayError('Please add at least one URL.')")
            continue

        for file_index, url_entry in enumerate(urls, start=1):
            url = url_entry['url']
            if url.strip() == '':
                continue
            # Extract filename components
            season_episode = extract_season_episode(url)
            original_filename = os.path.basename(url)
            file_extension = os.path.splitext(original_filename)[1]  # Includes the dot, e.g., '.mkv'

            if season_episode:
                # Extract title by removing the season/episode part and extension
                title_part = original_filename.split(season_episode)[0]
                title = sanitize_title(title_part)
                custom_filename = f"Its.Always.Sunny.In.Philadelphia.{season_episode}{file_extension}"
            else:
                # Fallback to original filename if pattern not found
                custom_filename = original_filename

            save_path = os.path.join(path, custom_filename)

            print(f"Starting download for {url} as {custom_filename}...")  # Debugging information
            webview.windows[0].evaluate_js(f"addProgressBar({task_id}, {file_index}, '{custom_filename}')")
            thread = threading.Thread(target=download_file, args=(url, save_path, task_id, file_index))
            thread.start()
            print(f"Thread started for {url}")  # Debugging information

def browse_directory():
    root = Tk()
    root.withdraw()  # Hide the root window
    directory = filedialog.askdirectory()
    root.destroy()
    return directory

class Api:
    def __init__(self):
        pass  # Removed window parameter

    def browse_directory(self):
        print("browse_directory called")  # Debugging information
        directory = browse_directory()
        print(f"Directory selected: {directory}")  # Debugging information
        return directory

    def start_all_downloads(self, task_frames):
        print("start_all_downloads called")  # Debugging information
        start_all_downloads(task_frames, webview.windows[0])  # Use global window reference

def main():
    print("Initializing Pywebview...")  # Debugging information
    # Initialize Pywebview
    api = Api()  # Initialize Api without window parameter
    window = webview.create_window(
        "Multi-Download Manager",
        "../assets/index.html",
        width=1000,
        height=800,
        js_api=api  # Register Api with js_api parameter
    )
    # Removed: window.js_api = api

    print("Pywebview started.")  # Debugging information

    # Start Pywebview on the main thread
    webview.start()

if __name__ == "__main__":
    main()
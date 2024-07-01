from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import random
import time
import tempfile
import json
import logging
import multiprocessing
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor, as_completed
import yt_dlp
import zipfile

app = Flask(__name__, static_folder='static')
CORS(app)

logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/download_reels', methods=['POST'])
def download_reels():
    data = request.json
    urls = data['urls']

    output_directory = tempfile.mkdtemp()
    NUM_CORES = multiprocessing.cpu_count()
    MAX_WORKERS = max(1, NUM_CORES - 2)

    def update_progress_bar(future):
        pass  # Placeholder for progress update logic if needed

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(download_reel, url, idx, output_directory): url for idx, url in enumerate(urls)}
        for future in as_completed(futures):
            future.add_done_callback(update_progress_bar)

    zip_filename = os.path.join(output_directory, 'reels.zip')
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for root, dirs, files in os.walk(output_directory):
            for file in files:
                if file != 'reels.zip':
                    zipf.write(os.path.join(root, file), file)

    return send_file(zip_filename, as_attachment=True, attachment_filename='reels.zip')

def download_reel(url, idx, output_directory):
    ydl_opts = {
        'outtmpl': os.path.join(output_directory, f'reel_{idx + 1}.%(ext)s'),
        'format': 'best',
        'quiet': True,
        'no_warnings': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
            logging.info(f"Reel {idx + 1} downloaded: {url}")
        except Exception as e:
            logging.error(f"Reel {idx + 1} not downloaded: {str(e)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

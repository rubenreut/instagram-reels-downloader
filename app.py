from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import logging
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
import yt_dlp

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
    output_directory = 'reels'
    os.makedirs(output_directory, exist_ok=True)

    NUM_CORES = multiprocessing.cpu_count()
    MAX_WORKERS = max(1, NUM_CORES - 2)

    results = []

    def update_progress_bar(future):
        pass  # Placeholder for progress update logic if needed

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(download_reel, url, idx, output_directory): url for idx, url in enumerate(urls)}
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
                update_progress_bar(future)
            except Exception as e:
                logging.error(f"Error in downloading: {str(e)}")

    return jsonify({"status": "success", "results": results})

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
            return {"url": url, "status": "success"}
        except Exception as e:
            logging.error(f"Reel {idx + 1} not downloaded: {str(e)}")
            return {"url": url, "status": "failed", "error": str(e)}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

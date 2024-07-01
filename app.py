from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import yt_dlp

app = Flask(__name__, static_folder='static')
CORS(app, resources={r"/*": {"origins": "*"}})

# Specify the paths to your SSL certificate and private key
ssl_cert = os.path.join(os.path.dirname(__file__), 'ssl', 'cert.pem')
ssl_key = os.path.join(os.path.dirname(__file__), 'ssl', 'key.pem')

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/download_reels', methods=['POST'])
def download_reels():
    data = request.json
    urls = data.get('urls', [])
    output_directory = 'reels'
    os.makedirs(output_directory, exist_ok=True)

    results = []

    for idx, url in enumerate(urls):
        result = download_reel(url, idx, output_directory)
        results.append(result)

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
            return {"url": url, "status": "success"}
        except Exception as e:
            return {"url": url, "status": "failed", "error": str(e)}

if __name__ == '__main__':
    ssl_cert = './cert.pem'
    ssl_key = './key.pem'
    app.run(host='0.0.0.0', port=8080, debug=True, ssl_context=(ssl_cert, ssl_key))


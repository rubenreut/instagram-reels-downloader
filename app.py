from flask import Flask, request, jsonify, send_from_directory
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
from concurrent.futures import ThreadPoolExecutor, as_completed
import yt_dlp

app = Flask(__name__, static_folder='static')
CORS(app)

logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/collect_links', methods=['POST'])
def collect_links():
    data = request.json
    username = data['username']
    password = data['password']
    headless = data.get('headless', True)

    temp_user_data_dir = tempfile.mkdtemp()
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-plugins-discovery")
    chrome_options.add_argument(f"--user-data-dir={temp_user_data_dir}")

    if headless:
        chrome_options.add_argument("--headless")

    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:79.0) Gecko/20100101 Firefox/79.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'
    ]
    chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")

    driver_path = '/opt/homebrew/bin/chromedriver'  # Adjust the path to your chromedriver
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(random.uniform(2, 5))

        driver.find_element(By.NAME, "username").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(random.uniform(5, 10))

        driver.get(f"https://www.instagram.com/{username}/saved/")
        time.sleep(random.uniform(5, 10))

        reel_links = collect_saved_reels_links(driver)

        return jsonify({"status": "success", "links": reel_links})

    except Exception as e:
        logging.error(f"Error collecting reel links: {e}")
        return jsonify({"status": "error", "message": str(e)})

    finally:
        driver.quit()

def collect_saved_reels_links(driver):
    reel_links = set()
    scroll_pause_time = random.uniform(1, 3)
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        links = driver.find_elements(By.TAG_NAME, 'a')
        for link in links:
            href = link.get_attribute('href')
            if href and '/p/' in href:
                reel_links.add(href)
                logging.info(f"Added reel link: {href}")
        logging.info(f"Collected {len(reel_links)} links so far.")

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    return list(reel_links)

@app.route('/download_reels', methods=['POST'])
def download_reels():
    data = request.json
    urls = data['urls']
    output_directory = 'reels'
    os.makedirs(output_directory, exist_ok=True)

    NUM_CORES = multiprocessing.cpu_count()
    MAX_WORKERS = max(1, NUM_CORES - 2)

    def update_progress_bar(future):
        pass  # Placeholder for progress update logic if needed

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(download_reel, url, idx, output_directory): url for idx, url in enumerate(urls)}
        for future in as_completed(futures):
            future.add_done_callback(update_progress_bar)

    return jsonify({"status": "success"})

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

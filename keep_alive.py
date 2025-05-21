import time
import threading
import requests
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def self_ping():
    while True:
        try:
            requests.get("https://d9106bfc-15f4-47c3-9123-f002f49768f0-00-34luxqspzmv08.sisko.replit.dev/")
        except Exception as e:
            print(f"Self-ping error: {e}")
        time.sleep(60)  # Пинг каждые 60 секунд

def keep_alive():
    t = Thread(target=run)
    t.start()
    ping_thread = threading.Thread(target=self_ping)
    ping_thread.daemon = True
    ping_thread.start()

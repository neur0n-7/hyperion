from flask import Flask
from threading import Thread
import os
import time
import requests

app = Flask('')

@app.route('/')
def home():
    return "Hyperion is online."

def run():
  app.run(host='0.0.0.0',port=os.environ.get('PORT', 8080))

def self_ping():
    while True:
        try:
            response = requests.get("https://hyperion-z4wx.onrender.com/")
        except requests.exceptions.RequestException as e:
            print("Ping failed:", e)
        time.sleep(5)
def start_self_ping():
    s = Thread(target=self_ping)
    s.start()
def keep_alive():
    t = Thread(target=run)
    t.start()

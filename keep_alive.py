from flask import Flask, render_template
from threading import Thread
import os
import time
import requests

app = Flask('')

@app.route('/')
def home():
    return render_template('index.html', invite_link=os.environ["INVITE_LINK"])

def run():
  app.run(host='0.0.0.0',port=os.environ.get('PORT', 8080))

def self_ping():
    while True:
        try:
            response = requests.get(os.environ["SERVICE_URL"])
        except requests.exceptions.RequestException as e:
            print("ERROR: Ping failed:", e)
        time.sleep(10)

def start_self_ping():
    s = Thread(target=self_ping)
    s.start()

def keep_alive():
    t = Thread(target=run)
    t.start()

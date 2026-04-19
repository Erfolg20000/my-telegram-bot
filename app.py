import os
import threading
import time
import requests
from flask import Flask

TELEGRAM_TOKEN = "8693513457:AAEDsr2PG_ruPAhWTQo_WoNPuNvAWfGZeYk"
OPENROUTER_KEY = "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"

app = Flask(__name__)

def ask_ai(text):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
    data = {"model": "openrouter/free", "messages": [{"role": "user", "content": text}]}
    try:
        response = requests.post(url, json=data, headers=headers)
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Ошибка API: {e}"

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

def run_bot():
    print("Бот запущен и слушает сообщения...")
    offset = 0
    while True:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        try:
            updates = requests.get(url, params={"offset": offset, "timeout": 30}).json()
            for update in updates.get("result", []):
                offset = update["update_id"] + 1
                if "message" in update and "text" in update["message"]:
                    chat_id = update["message"]["chat"]["id"]
                    user_text = update["message"]["text"]
                    print(f"Получено: {user_text}")
                    reply = ask_ai(user_text)
                    send_message(chat_id, reply)
        except Exception as e:
            print(f"Ошибка бота: {e}")
        time.sleep(1)

@app.route('/')
def index():
    return "Бот работает!", 200

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

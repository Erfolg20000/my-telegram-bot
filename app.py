import os
import threading
import time
import requests
from flask import Flask

TELEGRAM_TOKEN = "8693513457:AAEDsr2PG_ruPAhWTQo_WoNPuNvAWfGZeYk"
OPENROUTER_KEY = "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"

app = Flask(__name__)

# Список бесплатных моделей для автоматического перебора
MODELS = [
    "openrouter/free",
    "google/gemini-2.0-flash-exp:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "microsoft/phi-3.5-mini-128k-instruct:free",
    "qwen/qwen-2.5-7b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "moonshotai/kimi-k2.5:free",
]

def ask_ai(text):
    for model in MODELS:
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "model": model,
                "messages": [{"role": "user", "content": text}]
            }
            response = requests.post(url, json=data, headers=headers, timeout=30)
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Модель {model} не ответила: {e}")
            continue
    
    return "❌ Все модели временно недоступны. Попробуй через минуту."

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text})
    except Exception as e:
        print(f"Ошибка отправки: {e}")

def run_bot():
    print("🚀 Бот запущен. Автоматический выбор модели...")
    print(f"📋 Всего моделей: {len(MODELS)}")
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
                    print(f"📩 Получено: {user_text}")
                    reply = ask_ai(user_text)
                    print(f"🤖 Ответ: {reply[:100]}...")
                    send_message(chat_id, reply)
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
        time.sleep(1)

@app.route('/')
def index():
    return "Бот работает! Автоматический выбор модели", 200

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

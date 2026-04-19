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
    
    # Критически важно: OpenRouter требует эти заголовки, иначе будет ошибка [citation:5]
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://my-telegram-bot.onrender.com", 
        "X-Title": "Telegram AI Bot"
    }
    
    data = {
        "model": "openrouter/free",
        "messages": [{"role": "user", "content": text}]
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        
        # === НАЧАЛО ДИАГНОСТИКИ ===
        # Если сервер вернул не 200, покажем точную причину [citation:7][citation:10]
        if response.status_code != 200:
            error_detail = response.json()
            err_msg = error_detail.get('error', {}).get('message', 'Неизвестная ошибка')
            return f"❌ Ошибка API ({response.status_code}): {err_msg}"
        
        # Парсим результат
        result = response.json()
        
        # Если поле choices отсутствует или пустое — сообщаем об этом [citation:4]
        if "choices" not in result or not result["choices"]:
            return f"⚠️ Сервер OpenAI вернул пустой ответ. Попробуй написать ещё раз."
            
        # Всё хорошо, возвращаем ответ
        return result["choices"][0]["message"]["content"]
        # === КОНЕЦ ДИАГНОСТИКИ ===
        
    except requests.exceptions.RequestException as e:
        return f"🌐 Нет связи с API: {e}"
    except Exception as e:
        return f"💥 Внутренняя ошибка: {e}"

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text})
    except Exception as e:
        print(f"Ошибка отправки: {e}")

def run_bot():
    print("🚀 Бот запущен и слушает сообщения...")
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
            print(f"⚠️ Ошибка в цикле бота: {e}")
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

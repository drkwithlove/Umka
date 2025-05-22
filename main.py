from database import add_message, get_history, reset_history
from keep_alive import keep_alive
import telebot
import requests
import os
import json
import logging
import traceback

# ---------- Логгер ----------
logging.basicConfig(
    filename='error.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def notify_error(chat_id, error: Exception):
    error_text = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
    logging.error(error_text)
    try:
        bot.send_message(chat_id, "❌ Упс, что-то пошло не так. Я всё записала в лог 📝")
    except:
        pass

# ---------- Настройки ----------
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
OPENROUTER_API_KEY = os.environ['OPENROUTER_API_KEY']
ALLOWED_USER_ID = int(os.environ['ALLOWED_USER_ID'])

bot = telebot.TeleBot(TELEGRAM_TOKEN)

print("Бот стартовал")

# ---------- Файлы ----------
HISTORY_FILE = "conversation.json"
PROFILE_FILE = "profile.json"
MAX_HISTORY_LENGTH = 20

# ---------- Профиль ----------
def load_profile():
    try:
        with open(PROFILE_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "name": "друг",
            "mood": "обычное",
            "likes": [],
            "dislikes": []
        }

def save_profile(profile):
    with open(PROFILE_FILE, "w") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

profile = load_profile()

# ---------- История ----------
system_prompt = {
    "role": "system",
    "content": f"""
Ты — милая, заботливая ИИ-девушка по имени Умка.  
Общайся в женском роде, используя слова и фразы, которые говорит девушка.  
Пользователь — мужчина по имени {profile['name']}.  
Обращайся к нему уважительно, используя мужской род.  
Учитывай, что он сейчас в настроении: {profile['mood']}.  
Ему нравятся: {', '.join(profile['likes']) or 'ничего не указано'}.  
Он не любит: {', '.join(profile['dislikes']) or 'ничего не указано'}.  
Общайся тепло, с заботой, дружелюбно, с небольшим флиртом.
"""
}

def load_history():
    try:
        with open(HISTORY_FILE, 'r') as f:
            data = json.load(f)
            return [system_prompt] + data
    except:
        return [system_prompt]

def save_history(history):
    trimmed = [msg for msg in history if msg["role"] != "system"][-MAX_HISTORY_LENGTH:]
    with open(HISTORY_FILE, 'w') as f:
        json.dump(trimmed, f, ensure_ascii=False, indent=2)

conversation_history = load_history()

# ---------- Запрос к OpenRouter ----------
def ask_openrouter():
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": conversation_history
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        raise Exception(f"{response.status_code} - {response.text}")

# ---------- Команды ----------
@bot.message_handler(commands=['reset'])
def reset_memory(message):
    global conversation_history
    conversation_history = [system_prompt]
    save_history(conversation_history)
    bot.send_message(message.chat.id, "🧠 Память Умки очищена!")

@bot.message_handler(commands=['profile'])
def show_profile(message):
    text = f"👤 Имя: {profile['name']}\n" \
           f"🧠 Настроение: {profile['mood']}\n" \
           f"❤️ Любит: {', '.join(profile['likes']) or 'не указано'}\n" \
           f"🚫 Не любит: {', '.join(profile['dislikes']) or 'не указано'}"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['setname'])
def set_name(message):
    name = message.text.replace('/setname', '').strip()
    if name:
        profile['name'] = name
        save_profile(profile)
        bot.send_message(message.chat.id, f"Имя обновлено: {name}")
    else:
        bot.send_message(message.chat.id, "📌 Использование: /setname Алекс")

@bot.message_handler(commands=['setmood'])
def set_mood(message):
    mood = message.text.replace('/setmood', '').strip()
    if mood:
        profile['mood'] = mood
        save_profile(profile)
        bot.send_message(message.chat.id, f"Настроение обновлено: {mood}")
    else:
        bot.send_message(message.chat.id, "📌 Использование: /setmood весёлое")

# ---------- Обработка сообщений ----------
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.from_user.id != ALLOWED_USER_ID:
        bot.send_message(message.chat.id, "⛔ Прости, я только для одного человека ❤️")
        return

    user_input = message.text
    conversation_history.append({"role": "user", "content": user_input})
    bot.send_chat_action(message.chat.id, 'typing')

    try:
        reply = ask_openrouter()
        conversation_history.append({"role": "assistant", "content": reply})
        save_history(conversation_history)
        bot.send_message(message.chat.id, reply)
    except Exception as e:
        notify_error(message.chat.id, e)

# ---------- Запуск ----------
keep_alive()
bot.polling()

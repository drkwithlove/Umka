from database import add_message, get_history
from keep_alive import keep_alive
import telebot
import requests
import os
import json
import logging
import traceback
from gtts import gTTS

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
print("Бот запущен")

# ---------- Профиль ----------
PROFILE_FILE = "profile.json"
def load_profile():
    try:
        with open(PROFILE_FILE, "r") as f:
            return json.load(f)
    except:
        return {"name": "друг", "mood": "обычное", "likes": [], "dislikes": []}

def save_profile(profile):
    with open(PROFILE_FILE, "w") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

profile = load_profile()

# ---------- Prompt ----------
def get_system_prompt():
    return {
        "role": "system",
        "content": f"""
Ты — милая, заботливая ИИ-девушка по имени Умка.  
Общайся в женском роде. Пользователь — мужчина по имени {profile['name']}.  
Он сейчас в настроении: {profile['mood']}.  
Ему нравятся: {', '.join(profile['likes']) or 'ничего не указано'}.  
Он не любит: {', '.join(profile['dislikes']) or 'ничего не указано'}.
Общайся тепло, с заботой, дружелюбно, с лёгким флиртом.
"""
    }

# ---------- Запрос к OpenRouter ----------
def ask_openrouter(messages):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": messages
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        raise Exception(f"{response.status_code} - {response.text}")

# ---------- Команды ----------
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

# ---------- Сообщения ----------
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.from_user.id != ALLOWED_USER_ID:
        bot.send_message(message.chat.id, "⛔ Прости, я только для одного человека ❤️")
        return

    user_input = message.text
    bot.send_chat_action(message.chat.id, 'typing')
    add_message("user", user_input)

    try:
        history = [get_system_prompt()] + get_history()
        reply = ask_openrouter(history)
        add_message("assistant", reply)

        # Отправка текста
        bot.send_message(message.chat.id, reply)

        # Отправка голосом
        tts = gTTS(reply, lang="ru")
        tts.save("umka_voice.ogg")
        with open("umka_voice.ogg", "rb") as audio:
            bot.send_voice(message.chat.id, audio)

    except Exception as e:
        notify_error(message.chat.id, e)

# ---------- Запуск ----------
keep_alive()
bot.polling()

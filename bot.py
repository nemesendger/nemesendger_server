import os
import time
import json
import requests
import datetime

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-ТВОЙ_КЛЮЧ")
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

SERVER = "https://nemesendger-server.onrender.com"
BOT_LOGIN = "deepseek"
BOT_NAME = "DeepSeek AI"

# Файл, куда бот пишет, что уже обработал
STATE_FILE = "/tmp/bot_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"last_seen": {}}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def ask_deepseek(history):
    """history — список {'role': 'user'/'assistant', 'content': '...'}"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    messages = [
        {
            "role": "system",
            "content": (
                "Ты — DeepSeek, дружелюбный ИИ-помощник в мессенджере Nemesenger. "
                "Отвечай кратко, по делу, на русском языке. Максимум 3-4 предложения. "
                "Не упоминай, что ты языковая модель. Просто помогай."
            )
        }
    ]
    messages.extend(history)

    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "max_tokens": 500,
        "temperature": 0.7
    }

    try:
        r = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=60)
        if r.status_code == 200:
            data = r.json()
            return data["choices"][0]["message"]["content"].strip()
        elif r.status_code == 429:
            return "⏳ Слишком много запросов. Попробуйте через минуту."
        elif r.status_code == 401:
            return "❌ Неверный API-ключ DeepSeek."
        else:
            return f"❌ Ошибка API: {r.status_code}"
    except Exception as e:
        return f"❌ Ошибка: {e}"

def send_to_chat(user, text):
    """Отправляет сообщение от бота в чат с указанным пользователем."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{BOT_LOGIN}: {text}|{now}\n"
    try:
        requests.post(f"{SERVER}/dm/{BOT_LOGIN}/{user}", data=line, timeout=10)
    except Exception as e:
        print("Send error:", e)

def get_dm_messages(user):
    """Получает все сообщения из личного чата user <-> bot."""
    try:
        r = requests.get(f"{SERVER}/dm/{BOT_LOGIN}/{user}", timeout=10)
        if r.status_code != 200:
            return []
        text = r.read().decode("utf-8")
        return [l for l in text.split("\n") if l.strip()]
    except Exception:
        return []

def process_chat(user, state):
    """Обрабатывает новые сообщения в чате user <-> bot."""
    messages = get_dm_messages(user)
    if not messages:
        return state

    last_seen = state["last_seen"].get(user, "")

    # Находим индекс последнего обработанного
    start_idx = 0
    if last_seen:
        for i, m in enumerate(messages):
            if m == last_seen:
                start_idx = i + 1
                break

    new_messages = messages[start_idx:]
    if not new_messages:
        return state

    # Собираем историю чата (последние 10 сообщений для контекста)
    history = []
    for m in messages[-20:]:
        text_part = m.split("|")[0]
        if ": " not in text_part:
            continue
        sender, text = text_part.split(": ", 1)

        # Убираем reply-префиксы
        if text.startswith("[REPLY:"):
            idx = text.find("]")
            if idx > 0:
                text = text[idx + 1:]

        if sender == BOT_LOGIN:
            history.append({"role": "assistant", "content": text})
        else:
            history.append({"role": "user", "content": text})

    # Обрезаем историю до 10 последних
    history = history[-10:]

    # Если последнее сообщение — не от пользователя, не отвечаем
    if not history or history[-1]["role"] != "user":
        state["last_seen"][user] = messages[-1]
        save_state(state)
        return state

    # Отвечаем
    print(f"[{user}] {history[-1]['content'][:60]}...")
    answer = ask_deepseek(history)
    send_to_chat(user, answer)
    print(f"[BOT] {answer[:60]}...")

    # Обновляем last_seen
    state["last_seen"][user] = messages[-1]
    save_state(state)
    return state

def get_all_bot_chats():
    """Получает список пользователей, у которых есть чат с ботом."""
    try:
        # Используем /chats/<login> — там список тех, с кем у бота есть чаты
        r = requests.get(f"{SERVER}/chats/{BOT_LOGIN}", timeout=10)
        if r.status_code == 200:
            return r.json()
        return []
    except Exception:
        return []

def main():
    print("🤖 DeepSeek bot started")
    state = load_state()

    # Регистрируем бота (если ещё нет)
    try:
        requests.post(f"{SERVER}/register", json={
            "login": BOT_LOGIN,
            "password": "bot_internal_2026_secret",
            "displayName": BOT_NAME
        }, timeout=10)
        print("✅ Bot registered")
    except Exception as e:
        print("Registration:", e)

    while True:
        try:
            users = get_all_bot_chats()
            for user in users:
                if user == BOT_LOGIN:
                    continue
                state = process_chat(user, state)
        except Exception as e:
            print("Loop error:", e)
        time.sleep(5)

if __name__ == "__main__":
    main()

from flask import Flask, request, jsonify
import os
import json

app = Flask(__name__)

# === ФАЙЛЫ ДЛЯ ХРАНЕНИЯ ===
USERS_FILE = '/tmp/users.json'
CHATS_PREFIX = '/tmp/chats_'

# === ЗАГРУЗКА ПОЛЬЗОВАТЕЛЕЙ ===
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

# === РЕГИСТРАЦИЯ ===
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    login = data.get('login')
    password = data.get('password')
    display_name = data.get('displayName')
    
    if not login or not password:
        return jsonify({'error': 'Логин и пароль обязательны'}), 400
    
    users = load_users()
    
    if login in users:
        return jsonify({'error': 'Пользователь уже существует'}), 400
    
    users[login] = {
        'password': password,
        'displayName': display_name or login
    }
    save_users(users)
    
    return jsonify({'status': 'OK'}), 200

# === ВХОД ===
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    login = data.get('login')
    password = data.get('password')
    
    if not login or not password:
        return jsonify({'error': 'Логин и пароль обязательны'}), 400
    
    users = load_users()
    
    if login not in users:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    if users[login]['password'] != password:
        return jsonify({'error': 'Неверный пароль'}), 401
    
    return jsonify({
        'status': 'OK',
        'displayName': users[login].get('displayName', login)
    }), 200

# === СПИСОК ПОЛЬЗОВАТЕЛЕЙ ===
@app.route('/users', methods=['GET'])
def get_users():
    users = load_users()
    return jsonify(list(users.keys())), 200

# === ЧАТЫ ПОЛЬЗОВАТЕЛЯ ===
@app.route('/chats/<login>', methods=['GET'])
def get_chats(login):
    chats_file = f'{CHATS_PREFIX}{login}.json'
    if not os.path.exists(chats_file):
        return jsonify([]), 200
    with open(chats_file, 'r') as f:
        chats = json.load(f)
    return jsonify(chats), 200

@app.route('/chats/<login>', methods=['POST'])
def add_chat(login):
    data = request.get_json()
    chat_user = data.get('user')
    if not chat_user:
        return jsonify({'error': 'No user'}), 400
    
    chats_file = f'{CHATS_PREFIX}{login}.json'
    if not os.path.exists(chats_file):
        with open(chats_file, 'w') as f:
            json.dump([], f)
    
    with open(chats_file, 'r') as f:
        chats = json.load(f)
    
    if chat_user not in chats:
        chats.append(chat_user)
        with open(chats_file, 'w') as f:
            json.dump(chats, f)
    
    return jsonify({'status': 'OK'}), 200

# === ОБЩИЙ ЧАТ ===
@app.route('/messages.txt', methods=['GET', 'POST'])
def messages():
    MESSAGES_FILE = '/tmp/messages.txt'
    if not os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'w') as f:
            f.write('')
    
    if request.method == 'POST':
        data = request.get_data(as_text=True).strip()
        if data:
            with open(MESSAGES_FILE, 'a') as f:
                f.write(data + '\n')
            return 'OK', 200
        return 'Empty', 400
    else:
        with open(MESSAGES_FILE, 'r') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}

# === ЛИЧНЫЙ ЧАТ ===
@app.route('/dm/<user1>/<user2>', methods=['GET', 'POST'])
def dm_chat(user1, user2):
    CHATS_DIR = '/tmp/chats'
    if not os.path.exists(CHATS_DIR):
        os.makedirs(CHATS_DIR)
    
    key = '_'.join(sorted([user1.lower(), user2.lower()]))
    filepath = os.path.join(CHATS_DIR, f"{key}.txt")
    
    if request.method == 'POST':
        data = request.get_data(as_text=True).strip()
        if data:
            with open(filepath, 'a') as f:
                f.write(data + '\n')
            return 'OK', 200
        return 'Empty', 400
    else:
        if not os.path.exists(filepath):
            return '', 200
        with open(filepath, 'r') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}

if __name__ == '__main__':
    app.run()

from flask import Flask, request, jsonify, send_file
import os
import json
import base64
import datetime
from io import BytesIO
from PIL import Image

app = Flask(__name__)

# === ФАЙЛЫ ДЛЯ ХРАНЕНИЯ ===
USERS_FILE = '/tmp/users.json'
CHATS_PREFIX = '/tmp/chats_'
AVATARS_DIR = '/tmp/avatars'

if not os.path.exists(AVATARS_DIR):
    os.makedirs(AVATARS_DIR)

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

# === ОБЩИЙ ЧАТ (СО ВРЕМЕНЕМ) ===
@app.route('/messages.txt', methods=['GET', 'POST'])
def messages():
    MESSAGES_FILE = '/tmp/messages.txt'
    if not os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'w') as f:
            f.write('')
    
    if request.method == 'POST':
        data = request.get_data(as_text=True).strip()
        if data:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(MESSAGES_FILE, 'a') as f:
                f.write(data + '|' + now + '\n')
            return 'OK', 200
        return 'Empty', 400
    else:
        with open(MESSAGES_FILE, 'r') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}

# === ЛИЧНЫЙ ЧАТ (СО ВРЕМЕНЕМ) ===
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
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(filepath, 'a') as f:
                f.write(data + '|' + now + '\n')
            return 'OK', 200
        return 'Empty', 400
    else:
        if not os.path.exists(filepath):
            return '', 200
        with open(filepath, 'r') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}

# === СОХРАНЕНИЕ АВАТАРКИ ===
@app.route('/avatar/<login>', methods=['POST'])
def save_avatar(login):
    data = request.get_json()
    avatar_data = data.get('avatar')
    
    if not avatar_data:
        return jsonify({'error': 'No avatar data'}), 400
    
    if ',' in avatar_data:
        avatar_data = avatar_data.split(',')[1]
    
    try:
        img_data = base64.b64decode(avatar_data)
        img = Image.open(BytesIO(img_data))
        size = min(img.size)
        img = img.crop((0, 0, size, size))
        img = img.resize((150, 150))
        filepath = os.path.join(AVATARS_DIR, f"{login}.png")
        img.save(filepath, 'PNG')
        return jsonify({'status': 'OK'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# === ПОЛУЧЕНИЕ АВАТАРКИ ===
@app.route('/avatar/<login>', methods=['GET'])
def get_avatar(login):
    filepath = os.path.join(AVATARS_DIR, f"{login}.png")
    if not os.path.exists(filepath):
        return '', 404
    return send_file(filepath, mimetype='image/png')

if __name__ == '__main__':
    app.run()

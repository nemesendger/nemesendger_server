from flask import Flask, request, jsonify, send_file
import os
import json
import base64
import datetime

app = Flask(__name__)

# === ПАРОЛЬ АДМИНА ===
ADMIN_PASSWORD = "1230908070605gg"

# === ФАЙЛЫ ДЛЯ ХРАНЕНИЯ ===
USERS_FILE = '/tmp/users.json'
BANNED_FILE = '/tmp/banned.json'
CHATS_PREFIX = '/tmp/chats_'
AVATARS_DIR = '/tmp/avatars'
VOICE_DIR = '/tmp/voice'
PHOTOS_DIR = '/tmp/photos'
VIDEO_DIR = '/tmp/video'

if not os.path.exists(AVATARS_DIR):
    os.makedirs(AVATARS_DIR)
if not os.path.exists(VOICE_DIR):
    os.makedirs(VOICE_DIR)
if not os.path.exists(PHOTOS_DIR):
    os.makedirs(PHOTOS_DIR)
if not os.path.exists(VIDEO_DIR):
    os.makedirs(VIDEO_DIR)

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

def load_banned():
    if not os.path.exists(BANNED_FILE):
        return []
    with open(BANNED_FILE, 'r') as f:
        return json.load(f)

def save_banned(banned):
    with open(BANNED_FILE, 'w') as f:
        json.dump(banned, f)

# === РЕГИСТРАЦИЯ ===
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    login = data.get('login')
    password = data.get('password')
    display_name = data.get('displayName')
    
    if not login or not password:
        return jsonify({'error': 'Логин и пароль обязательны'}), 400
    
    if len(login) > 20:
        return jsonify({'error': 'Логин не более 20 символов'}), 400
    
    if display_name and len(display_name) > 20:
        return jsonify({'error': 'Имя не более 20 символов'}), 400
    
    # === ПРОВЕРКА БАНА ===
    banned = load_banned()
    if login in banned:
        return jsonify({'error': 'Этот логин заблокирован администратором'}), 403
    
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
    
    # === ПРОВЕРКА БАНА ===
    banned = load_banned()
    if login in banned:
        return jsonify({'error': 'Ваш аккаунт заблокирован администратором'}), 403
    
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
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(MESSAGES_FILE, 'a') as f:
                f.write(data + '|' + now + '\n')
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

# === АВАТАРКИ ===
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
        filepath = os.path.join(AVATARS_DIR, f"{login}.png")
        with open(filepath, 'wb') as f:
            f.write(img_data)
        return jsonify({'status': 'OK'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/avatar/<login>', methods=['GET'])
def get_avatar(login):
    filepath = os.path.join(AVATARS_DIR, f"{login}.png")
    if not os.path.exists(filepath):
        return '', 404
    return send_file(filepath, mimetype='image/png')

# === ГОЛОСОВЫЕ ===
@app.route('/voice/<filename>', methods=['GET'])
def get_voice(filename):
    filepath = os.path.join(VOICE_DIR, filename)
    if not os.path.exists(filepath):
        return '', 404
    return send_file(filepath, mimetype='audio/amr')

@app.route('/voice', methods=['POST'])
def upload_voice():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file'}), 400
    
    file = request.files['audio']
    filename = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    filepath = os.path.join(VOICE_DIR, filename)
    file.save(filepath)
    
    return jsonify({
        'status': 'OK',
        'url': f'https://nemesendger-server.onrender.com/voice/{filename}'
    }), 200

# === ФОТО ===
@app.route('/photo/<filename>', methods=['GET'])
def get_photo(filename):
    filepath = os.path.join(PHOTOS_DIR, filename)
    if not os.path.exists(filepath):
        return '', 404
    return send_file(filepath)

@app.route('/photo', methods=['POST'])
def upload_photo():
    if 'photo' not in request.files:
        return jsonify({'error': 'No photo'}), 400
    
    file = request.files['photo']
    filename = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    filepath = os.path.join(PHOTOS_DIR, filename)
    file.save(filepath)
    
    return jsonify({
        'status': 'OK',
        'url': f'https://nemesendger-server.onrender.com/photo/{filename}'
    }), 200

# === ВИДЕО ===
@app.route('/video/<filename>', methods=['GET'])
def get_video(filename):
    filepath = os.path.join(VIDEO_DIR, filename)
    if not os.path.exists(filepath):
        return '', 404
    return send_file(filepath, mimetype='video/mp4')

@app.route('/video', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video'}), 400
    
    file = request.files['video']
    filename = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    filepath = os.path.join(VIDEO_DIR, filename)
    file.save(filepath)
    
    return jsonify({
        'status': 'OK',
        'url': f'https://nemesendger-server.onrender.com/video/{filename}'
    }), 200

# === УДАЛЕНИЕ АККАУНТА (самим пользователем) ===
@app.route('/delete_user', methods=['POST'])
def delete_user():
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
    
    del users[login]
    save_users(users)
    
    try:
        avatar_path = os.path.join(AVATARS_DIR, f"{login}.png")
        if os.path.exists(avatar_path):
            os.remove(avatar_path)
        
        chats_file = f'{CHATS_PREFIX}{login}.json'
        if os.path.exists(chats_file):
            os.remove(chats_file)
    except:
        pass
    
    return jsonify({'status': 'OK'}), 200

# ============================================================
# === АДМИНКА ================================================
# ============================================================

@app.route('/admin/users', methods=['GET'])
def admin_users():
    pwd = request.args.get('pwd', '')
    if pwd != ADMIN_PASSWORD:
        return jsonify({'error': 'Unauthorized'}), 401
    
    users = load_users()
    result = []
    for login, data in users.items():
        result.append({
            'login': login,
            'displayName': data.get('displayName', login)
        })
    return jsonify(result), 200

@app.route('/admin/banned', methods=['GET'])
def admin_banned():
    pwd = request.args.get('pwd', '')
    if pwd != ADMIN_PASSWORD:
        return jsonify({'error': 'Unauthorized'}), 401
    
    return jsonify(load_banned()), 200

@app.route('/admin/delete_user', methods=['POST'])
def admin_delete_user():
    data = request.get_json()
    if data.get('pwd', '') != ADMIN_PASSWORD:
        return jsonify({'error': 'Unauthorized'}), 401
    
    login = data.get('login')
    users = load_users()
    
    if login in users:
        del users[login]
        save_users(users)
        
        try:
            avatar_path = os.path.join(AVATARS_DIR, f"{login}.png")
            if os.path.exists(avatar_path):
                os.remove(avatar_path)
            
            chats_file = f'{CHATS_PREFIX}{login}.json'
            if os.path.exists(chats_file):
                os.remove(chats_file)
        except:
            pass
    
    return jsonify({'status': 'OK'}), 200

@app.route('/admin/ban_user', methods=['POST'])
def admin_ban_user():
    data = request.get_json()
    if data.get('pwd', '') != ADMIN_PASSWORD:
        return jsonify({'error': 'Unauthorized'}), 401
    
    login = data.get('login')
    if not login:
        return jsonify({'error': 'No login'}), 400
    
    # Добавляем в бан-лист (если ещё нет)
    banned = load_banned()
    if login not in banned:
        banned.append(login)
        save_banned(banned)
    
    # Удаляем пользователя из users
    users = load_users()
    if login in users:
        del users[login]
        save_users(users)
        
        try:
            avatar_path = os.path.join(AVATARS_DIR, f"{login}.png")
            if os.path.exists(avatar_path):
                os.remove(avatar_path)
            
            chats_file = f'{CHATS_PREFIX}{login}.json'
            if os.path.exists(chats_file):
                os.remove(chats_file)
        except:
            pass
    
    return jsonify({'status': 'OK'}), 200

@app.route('/admin/unban_user', methods=['POST'])
def admin_unban_user():
    data = request.get_json()
    if data.get('pwd', '') != ADMIN_PASSWORD:
        return jsonify({'error': 'Unauthorized'}), 401
    
    login = data.get('login')
    if not login:
        return jsonify({'error': 'No login'}), 400
    
    banned = load_banned()
    if login in banned:
        banned.remove(login)
        save_banned(banned)
    
    return jsonify({'status': 'OK'}), 200

@app.route('/admin/clear_global', methods=['POST'])
def admin_clear_global():
    data = request.get_json()
    if data.get('pwd', '') != ADMIN_PASSWORD:
        return jsonify({'error': 'Unauthorized'}), 401
    
    MESSAGES_FILE = '/tmp/messages.txt'
    with open(MESSAGES_FILE, 'w') as f:
        f.write('')
    
    return jsonify({'status': 'OK'}), 200

if __name__ == '__main__':
    app.run()

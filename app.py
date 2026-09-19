from flask import Flask, request, jsonify, send_file
import os
import json
import base64
import datetime

app = Flask(__name__)

MSK = datetime.timezone(datetime.timedelta(hours=3))

def now_msk():
    return datetime.datetime.now(MSK).strftime("%Y-%m-%d %H:%M:%S")

ADMIN_PASSWORD = "1230908070605gg"
OWNER_LOGIN = "nemesendger_official"

USERS_FILE = '/tmp/users.json'
BANNED_FILE = '/tmp/banned.json'
ADMINS_FILE = '/tmp/admins.json'
CHATS_PREFIX = '/tmp/chats_'
AVATARS_DIR = '/tmp/avatars'
VOICE_DIR = '/tmp/voice'
PHOTOS_DIR = '/tmp/photos'
VIDEO_DIR = '/tmp/video'
READ_DIR = '/tmp/read'
ONLINE_DIR = '/tmp/online'
TYPING_DIR = '/tmp/typing'
REACTIONS_DIR = '/tmp/reactions'
SUPPORT_DIR = '/tmp/support'

for d in [AVATARS_DIR, VOICE_DIR, PHOTOS_DIR, VIDEO_DIR, READ_DIR, ONLINE_DIR, TYPING_DIR, REACTIONS_DIR, SUPPORT_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

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

def load_admins():
    if not os.path.exists(ADMINS_FILE):
        return []
    with open(ADMINS_FILE, 'r') as f:
        return json.load(f)

def save_admins(admins):
    with open(ADMINS_FILE, 'w') as f:
        json.dump(admins, f)

def add_to_chat_list(owner, other):
    if not owner or not other or owner == other:
        return
    chats_file = f'{CHATS_PREFIX}{owner}.json'
    if not os.path.exists(chats_file):
        with open(chats_file, 'w') as f:
            json.dump([], f)
    with open(chats_file, 'r') as f:
        chats = json.load(f)
    if other not in chats:
        chats.append(other)
        with open(chats_file, 'w') as f:
            json.dump(chats, f)

# ==================== АККАУНТ ПОДДЕРЖКИ ====================
def ensure_support_account():
    users = load_users()
    if OWNER_LOGIN not in users:
        users[OWNER_LOGIN] = {
            'password': ADMIN_PASSWORD,
            'displayName': 'Техподдержка'
        }
        save_users(users)

ensure_support_account()

# ==================== РЕАКЦИИ ====================
def reactions_file(chat_id):
    safe = chat_id.replace('/', '_').replace('\\', '_')
    return os.path.join(REACTIONS_DIR, f'{safe}.json')

def load_reactions(chat_id):
    path = reactions_file(chat_id)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_reactions(chat_id, data):
    path = reactions_file(chat_id)
    with open(path, 'w') as f:
        json.dump(data, f)

# ==================== РЕГИСТРАЦИЯ ====================
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
    if login in load_banned():
        return jsonify({'error': 'Этот логин заблокирован'}), 403

    users = load_users()
    if login in users:
        return jsonify({'error': 'Пользователь уже существует'}), 400

    users[login] = {'password': password, 'displayName': display_name or login}
    save_users(users)
    return jsonify({'status': 'OK'}), 200

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    login = data.get('login')
    password = data.get('password')

    if not login or not password:
        return jsonify({'error': 'Логин и пароль обязательны'}), 400
    if login in load_banned():
        return jsonify({'error': 'Аккаунт заблокирован'}), 403

    users = load_users()
    if login not in users:
        return jsonify({'error': 'Пользователь не найден'}), 404
    if users[login]['password'] != password:
        return jsonify({'error': 'Неверный пароль'}), 401

    return jsonify({
        'status': 'OK',
        'displayName': users[login].get('displayName', login)
    }), 200

@app.route('/users', methods=['GET'])
def get_users():
    return jsonify(list(load_users().keys())), 200

@app.route('/admins', methods=['GET'])
def get_admins():
    return jsonify(load_admins()), 200

@app.route('/admin/add_admin', methods=['POST'])
def admin_add_admin():
    data = request.get_json()
    if data.get('pwd', '') != ADMIN_PASSWORD:
        return jsonify({'error': 'Unauthorized'}), 401
    login = data.get('login')
    if not login:
        return jsonify({'error': 'No login'}), 400
    if login == OWNER_LOGIN:
        return jsonify({'error': 'Владелец уже владелец'}), 400
    admins = load_admins()
    if login not in admins:
        admins.append(login)
        save_admins(admins)
    return jsonify({'status': 'OK'}), 200

@app.route('/admin/remove_admin', methods=['POST'])
def admin_remove_admin():
    data = request.get_json()
    if data.get('pwd', '') != ADMIN_PASSWORD:
        return jsonify({'error': 'Unauthorized'}), 401
    login = data.get('login')
    admins = load_admins()
    if login in admins:
        admins.remove(login)
        save_admins(admins)
    return jsonify({'status': 'OK'}), 200

@app.route('/chats/<login>', methods=['GET'])
def get_chats(login):
    chats_file = f'{CHATS_PREFIX}{login}.json'
    if not os.path.exists(chats_file):
        return jsonify([]), 200
    with open(chats_file, 'r') as f:
        return jsonify(json.load(f)), 200

@app.route('/chats/<login>', methods=['POST'])
def add_chat(login):
    data = request.get_json()
    chat_user = data.get('user')
    if not chat_user:
        return jsonify({'error': 'No user'}), 400
    add_to_chat_list(login, chat_user)
    return jsonify({'status': 'OK'}), 200

@app.route('/unread/<login>', methods=['GET'])
def get_unread(login):
    chats_file = f'{CHATS_PREFIX}{login}.json'
    if not os.path.exists(chats_file):
        return jsonify({}), 200
    with open(chats_file, 'r') as f:
        chats = json.load(f)
    result = {}
    CHATS_DIR = '/tmp/chats'
    for recipient in chats:
        if recipient == login:
            continue
        key = '_'.join(sorted([login.lower(), recipient.lower()]))
        chat_file = os.path.join(CHATS_DIR, f"{key}.txt")
        if not os.path.exists(chat_file):
            result[recipient] = 0
            continue
        read_file = os.path.join(READ_DIR, f"{key}_{login}.txt")
        read_time = ""
        if os.path.exists(read_file):
            with open(read_file, 'r') as rf:
                read_time = rf.read().strip()
        count = 0
        try:
            with open(chat_file, 'r') as cf:
                for line in cf:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split('|')
                    if len(parts) < 2:
                        continue
                    msg_part = parts[0]
                    msg_time = parts[1]
                    if ': ' not in msg_part:
                        continue
                    sender = msg_part.split(': ', 1)[0]
                    if sender == login:
                        continue
                    if not read_time or msg_time > read_time:
                        count += 1
        except:
            count = 0
        result[recipient] = count
    return jsonify(result), 200

@app.route('/messages.txt', methods=['GET', 'POST'])
def messages():
    MESSAGES_FILE = '/tmp/messages.txt'
    if not os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'w') as f:
            f.write('')
    if request.method == 'POST':
        data = request.get_data(as_text=True).strip()
        if data:
            now = now_msk()
            with open(MESSAGES_FILE, 'a') as f:
                f.write(data + '|' + now + '\n')
            return 'OK', 200
        return 'Empty', 400
    else:
        with open(MESSAGES_FILE, 'r') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}

# ==================== ЛИЧНЫЕ СООБЩЕНИЯ + ПОДДЕРЖКА ====================
@app.route('/dm/<user1>/<user2>', methods=['GET', 'POST'])
def dm_chat(user1, user2):
    u1 = user1.lower()
    u2 = user2.lower()
    owner = OWNER_LOGIN.lower()

    # === ПОДДЕРЖКА ===
    if u1 == owner or u2 == owner:
        user = u2 if u1 == owner else u1
        filepath = os.path.join(SUPPORT_DIR, f'{user}.txt')

        if request.method == 'POST':
            data = request.get_data(as_text=True).strip()
            if data:
                now = now_msk()
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

    # === ОБЫЧНЫЙ ЧАТ ===
    CHATS_DIR = '/tmp/chats'
    if not os.path.exists(CHATS_DIR):
        os.makedirs(CHATS_DIR)
    key = '_'.join(sorted([u1, u2]))
    filepath = os.path.join(CHATS_DIR, f"{key}.txt")
    if request.method == 'POST':
        data = request.get_data(as_text=True).strip()
        if data:
            now = now_msk()
            with open(filepath, 'a') as f:
                f.write(data + '|' + now + '\n')
            add_to_chat_list(user1, user2)
            add_to_chat_list(user2, user1)
            return 'OK', 200
        return 'Empty', 400
    else:
        if not os.path.exists(filepath):
            return '', 200
        with open(filepath, 'r') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}

# ==================== СПИСОК ЖАЛОБ ====================
@app.route('/support_list', methods=['GET'])
def support_list():
    if not os.path.exists(SUPPORT_DIR):
        return jsonify([]), 200
    users = []
    for fname in os.listdir(SUPPORT_DIR):
        if fname.endswith('.txt'):
            users.append(fname[:-4])
    return jsonify(users), 200

# ==================== ПОДДЕРЖКА: НЕПРОЧИТАННЫЕ ====================
@app.route('/support_unread/<client>/<viewer>', methods=['GET'])
def support_unread_one(client, viewer):
    client = client.lower()
    viewer = viewer.lower()
    filepath = os.path.join(SUPPORT_DIR, f'{client}.txt')
    if not os.path.exists(filepath):
        return jsonify({'count': 0}), 200

    read_file = os.path.join(READ_DIR, f"support_{client}_{viewer}.txt")
    read_time = ""
    if os.path.exists(read_file):
        with open(read_file, 'r') as f:
            read_time = f.read().strip()

    count = 0
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split('|')
                if len(parts) < 2:
                    continue
                msg_part = parts[0]
                msg_time = parts[1]
                if ': ' not in msg_part:
                    continue
                sender = msg_part.split(': ', 1)[0]
                if sender.lower() == viewer:
                    continue
                if not read_time or msg_time > read_time:
                    count += 1
    except:
        count = 0

    return jsonify({'count': count}), 200

@app.route('/support_unread_all/<viewer>', methods=['GET'])
def support_unread_all(viewer):
    viewer = viewer.lower()
    result = {}
    if not os.path.exists(SUPPORT_DIR):
        return jsonify(result), 200

    for fname in os.listdir(SUPPORT_DIR):
        if not fname.endswith('.txt'):
            continue
        client = fname[:-4]
        filepath = os.path.join(SUPPORT_DIR, fname)

        read_file = os.path.join(READ_DIR, f"support_{client}_{viewer}.txt")
        read_time = ""
        if os.path.exists(read_file):
            with open(read_file, 'r') as f:
                read_time = f.read().strip()

        count = 0
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split('|')
                    if len(parts) < 2:
                        continue
                    msg_part = parts[0]
                    msg_time = parts[1]
                    if ': ' not in msg_part:
                        continue
                    sender = msg_part.split(': ', 1)[0]
                    if sender.lower() == viewer:
                        continue
                    if not read_time or msg_time > read_time:
                        count += 1
        except:
            count = 0

        result[client] = count

    return jsonify(result), 200

# ==================== ADMIN CHAT ====================
@app.route('/admin_chat.txt', methods=['GET', 'POST'])
def admin_chat():
    FILE = '/tmp/admin_chat.txt'
    if not os.path.exists(FILE):
        with open(FILE, 'w') as f:
            f.write('')
    if request.method == 'POST':
        data = request.get_data(as_text=True).strip()
        if data:
            now = now_msk()
            with open(FILE, 'a') as f:
                f.write(data + '|' + now + '\n')
            return 'OK', 200
        return 'Empty', 400
    else:
        with open(FILE, 'r') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}

# ==================== УДАЛЕНИЕ ====================
@app.route('/delete_message', methods=['POST'])
def delete_message():
    data = request.get_json()
    chat_type = data.get('chat_type')
    me = data.get('me')
    recipient = data.get('recipient')
    line = data.get('line')
    if not chat_type or not line:
        return jsonify({'error': 'Missing params'}), 400
    if chat_type == 'global':
        filepath = '/tmp/messages.txt'
    elif chat_type == 'admin':
        filepath = '/tmp/admin_chat.txt'
    elif chat_type == 'support':
        if not recipient:
            return jsonify({'error': 'Missing user'}), 400
        filepath = os.path.join(SUPPORT_DIR, f"{recipient.lower()}.txt")
    elif chat_type == 'dm':
        if not me or not recipient:
            return jsonify({'error': 'Missing users'}), 400
        key = '_'.join(sorted([me.lower(), recipient.lower()]))
        filepath = f'/tmp/chats/{key}.txt'
    else:
        return jsonify({'error': 'Bad chat_type'}), 400
    if not os.path.exists(filepath):
        return jsonify({'status': 'OK'}), 200
    with open(filepath, 'r') as f:
        lines = f.readlines()
    new_lines = [l for l in lines if l.rstrip('\n') != line]
    with open(filepath, 'w') as f:
        f.writelines(new_lines)
    return jsonify({'status': 'OK'}), 200

# ==================== READ / ONLINE / TYPING ====================
@app.route('/read/<chat_id>/<user>', methods=['GET', 'POST'])
def read_status(chat_id, user):
    filepath = os.path.join(READ_DIR, f"{chat_id}_{user}.txt")
    if request.method == 'POST':
        with open(filepath, 'w') as f:
            f.write(now_msk())
        return 'OK', 200
    else:
        if not os.path.exists(filepath):
            return '', 200
        with open(filepath, 'r') as f:
            return f.read(), 200

@app.route('/online/<user>', methods=['GET', 'POST'])
def online_status(user):
    filepath = os.path.join(ONLINE_DIR, f"{user}.txt")
    if request.method == 'POST':
        with open(filepath, 'w') as f:
            f.write(now_msk())
        return 'OK', 200
    else:
        if not os.path.exists(filepath):
            return '', 200
        with open(filepath, 'r') as f:
            return f.read(), 200

@app.route('/typing/<chat_id>/<user>', methods=['GET', 'POST'])
def typing_status(chat_id, user):
    filepath = os.path.join(TYPING_DIR, f"{chat_id}_{user}.txt")
    if request.method == 'POST':
        with open(filepath, 'w') as f:
            f.write(now_msk())
        return 'OK', 200
    else:
        if not os.path.exists(filepath):
            return '', 200
        with open(filepath, 'r') as f:
            return f.read(), 200

# ==================== РЕАКЦИИ ====================
@app.route('/reaction', methods=['POST'])
def reaction_toggle():
    data = request.get_json() or {}
    chat_id = data.get('chat_id', '')
    msg_id = data.get('msg_id', '')
    emoji = data.get('emoji', '')
    user = (data.get('user') or '').lower()
    if not chat_id or not msg_id or not emoji or not user:
        return jsonify({'error': 'missing fields'}), 400
    reactions = load_reactions(chat_id)
    msg = reactions.setdefault(msg_id, {})
    users = msg.setdefault(emoji, [])
    if user in users:
        users.remove(user)
    else:
        users.append(user)
    if not users:
        del msg[emoji]
    if not msg:
        del reactions[msg_id]
    save_reactions(chat_id, reactions)
    return jsonify({'status': 'OK'}), 200

@app.route('/reactions/<chat_id>', methods=['GET'])
def reactions_get(chat_id):
    return jsonify(load_reactions(chat_id)), 200

# ==================== ФАЙЛЫ ====================
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
    filename = f"{datetime.datetime.now(MSK).strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    filepath = os.path.join(VOICE_DIR, filename)
    file.save(filepath)
    return jsonify({'status': 'OK',
                    'url': f'https://nemesendger-server.onrender.com/voice/{filename}'}), 200

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
    filename = f"{datetime.datetime.now(MSK).strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    filepath = os.path.join(PHOTOS_DIR, filename)
    file.save(filepath)
    return jsonify({'status': 'OK',
                    'url': f'https://nemesendger-server.onrender.com/photo/{filename}'}), 200

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
    filename = f"{datetime.datetime.now(MSK).strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    filepath = os.path.join(VIDEO_DIR, filename)
    file.save(filepath)
    return jsonify({'status': 'OK',
                    'url': f'https://nemesendger-server.onrender.com/video/{filename}'}), 200

# ==================== АДМИН ====================
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

@app.route('/admin/users', methods=['GET'])
def admin_users():
    pwd = request.args.get('pwd', '')
    if pwd != ADMIN_PASSWORD:
        return jsonify({'error': 'Unauthorized'}), 401
    users = load_users()
    result = []
    for login, data in users.items():
        result.append({'login': login, 'displayName': data.get('displayName', login)})
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
    banned = load_banned()
    if login not in banned:
        banned.append(login)
        save_banned(banned)
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
    with open('/tmp/messages.txt', 'w') as f:
        f.write('')
    return jsonify({'status': 'OK'}), 200

if __name__ == '__main__':
    app.run()

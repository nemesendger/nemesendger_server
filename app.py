# app.py
# Полный сервер для мессенджера Nemesendger

import os
import json
from datetime import datetime, timezone, timedelta
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Часовой пояс сервера (Москва = UTC+3)
LOCAL_TZ = timezone(timedelta(hours=3))

# =========================================================
# ПАПКИ И ФАЙЛЫ
# =========================================================
DATA_DIR = 'data'
UPLOAD_DIR = 'uploads'
DM_DIR = os.path.join(DATA_DIR, 'dm')

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DM_DIR, exist_ok=True)

USERS_FILE = os.path.join(DATA_DIR, 'users.json')
CHATS_FILE = os.path.join(DATA_DIR, 'chats.json')
ONLINE_FILE = os.path.join(DATA_DIR, 'online.json')
TYPING_FILE = os.path.join(DATA_DIR, 'typing.json')
READ_FILE = os.path.join(DATA_DIR, 'read.json')
UNREAD_FILE = os.path.join(DATA_DIR, 'unread.json')
ADMINS_FILE = os.path.join(DATA_DIR, 'admins.json')
REACTIONS_FILE = os.path.join(DATA_DIR, 'reactions.json')
AVATARS_FILE = os.path.join(DATA_DIR, 'avatars.json')

GLOBAL_MESSAGES_FILE = os.path.join(DATA_DIR, 'messages.txt')

OWNER_LOGIN = 'nemesendger_official'
ADMIN_PASSWORD = '1230908070605gg'


# =========================================================
# ХЕЛПЕРЫ
# =========================================================
def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return default
    return default


def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def now_str():
    return datetime.now(LOCAL_TZ).strftime('%Y-%m-%d %H:%M:%S')


def dm_path(u1, u2):
    a, b = sorted([u1.lower(), u2.lower()])
    return os.path.join(DM_DIR, a + '_' + b + '.txt')


def read_file(path):
    if not os.path.exists(path):
        return ''
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def append_file(path, text):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(text)


def full_url(path):
    """Возвращает абсолютный URL для файла на сервере."""
    return request.host_url.rstrip('/') + path


# =========================================================
# ГЛАВНАЯ
# =========================================================
@app.route('/', methods=['GET'])
def index():
    return 'Nemesendger server is running 🚀'


# =========================================================
# РЕГИСТРАЦИЯ / ЛОГИН
# =========================================================
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    login = (data.get('login') or '').strip().lower()
    password = data.get('password') or ''
    display = data.get('displayName') or login

    if not login or not password:
        return jsonify({'ok': False, 'error': 'empty fields'}), 400

    users = load_json(USERS_FILE, {})

    if login in users:
        if users[login].get('password') == password:
            return jsonify({'ok': True, 'restored': True})
        return jsonify({'ok': False, 'error': 'wrong password'}), 403

    users[login] = {
        'password': password,
        'displayName': display,
        'createdAt': now_str()
    }
    save_json(USERS_FILE, users)
    return jsonify({'ok': True})


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    login = (data.get('login') or '').strip().lower()
    password = data.get('password') or ''

    users = load_json(USERS_FILE, {})
    u = users.get(login)

    if not u:
        return jsonify({'ok': False, 'error': 'not found'}), 404
    if u.get('password') != password:
        return jsonify({'ok': False, 'error': 'wrong password'}), 403

    return jsonify({
        'ok': True,
        'login': login,
        'displayName': u.get('displayName', login)
    })


@app.route('/users', methods=['GET'])
def users_list():
    users = load_json(USERS_FILE, {})
    return jsonify(list(users.keys()))


@app.route('/user/<login>', methods=['GET'])
def user_info(login):
    users = load_json(USERS_FILE, {})
    u = users.get(login.lower())
    if not u:
        return jsonify({'ok': False}), 404
    return jsonify({
        'login': login.lower(),
        'displayName': u.get('displayName', login)
    })


@app.route('/user/update', methods=['POST'])
def user_update():
    data = request.get_json(silent=True) or {}
    login = (data.get('login') or '').strip().lower()
    newName = data.get('displayName')

    users = load_json(USERS_FILE, {})
    if login not in users:
        return jsonify({'ok': False}), 404

    if newName:
        users[login]['displayName'] = newName
        save_json(USERS_FILE, users)
    return jsonify({'ok': True})


# =========================================================
# АДМИНЫ
# =========================================================
@app.route('/admins', methods=['GET'])
def admins_list():
    admins = load_json(ADMINS_FILE, [])
    if OWNER_LOGIN not in admins:
        admins.append(OWNER_LOGIN)
        save_json(ADMINS_FILE, admins)
    return jsonify(admins)


@app.route('/admin/add', methods=['POST'])
def admin_add():
    data = request.get_json(silent=True) or {}
    if data.get('password') != ADMIN_PASSWORD:
        return jsonify({'ok': False, 'error': 'wrong password'}), 403

    login = (data.get('login') or '').strip().lower()
    if not login:
        return jsonify({'ok': False}), 400

    admins = load_json(ADMINS_FILE, [])
    if login not in admins:
        admins.append(login)
        save_json(ADMINS_FILE, admins)
    return jsonify({'ok': True})


@app.route('/admin/remove', methods=['POST'])
def admin_remove():
    data = request.get_json(silent=True) or {}
    if data.get('password') != ADMIN_PASSWORD:
        return jsonify({'ok': False}), 403

    login = (data.get('login') or '').strip().lower()
    admins = load_json(ADMINS_FILE, [])
    if login in admins:
        admins.remove(login)
        save_json(ADMINS_FILE, admins)
    return jsonify({'ok': True})


@app.route('/admin/ban', methods=['POST'])
def admin_ban():
    data = request.get_json(silent=True) or {}
    if data.get('password') != ADMIN_PASSWORD:
        return jsonify({'ok': False}), 403

    login = (data.get('login') or '').strip().lower()
    users = load_json(USERS_FILE, {})
    if login in users:
        del users[login]
        save_json(USERS_FILE, users)
    return jsonify({'ok': True})


# =========================================================
# СПИСОК ЧАТОВ
# =========================================================
@app.route('/chats/<login>', methods=['GET'])
def chats_get(login):
    chats = load_json(CHATS_FILE, {})
    return jsonify(chats.get(login.lower(), []))


@app.route('/chats/<login>', methods=['POST'])
def chats_add(login):
    data = request.get_json(silent=True) or {}
    other = (data.get('user') or '').strip().lower()
    if not other:
        return jsonify({'ok': False}), 400

    chats = load_json(CHATS_FILE, {})
    me = login.lower()

    me_list = set(chats.get(me, []))
    me_list.add(other)
    chats[me] = list(me_list)

    other_list = set(chats.get(other, []))
    other_list.add(me)
    chats[other] = list(other_list)

    save_json(CHATS_FILE, chats)
    return jsonify({'ok': True})


@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    data = request.get_json(silent=True) or {}
    me = (data.get('me') or '').lower()
    other = (data.get('other') or '').lower()
    if not me or not other:
        return jsonify({'ok': False}), 400

    path = dm_path(me, other)
    if os.path.exists(path):
        open(path, 'w', encoding='utf-8').close()

    unread = load_json(UNREAD_FILE, {})
    unread.setdefault(me, {})[other] = 0
    unread.setdefault(other, {})[me] = 0
    save_json(UNREAD_FILE, unread)
    return jsonify({'ok': True})


@app.route('/delete_chat', methods=['POST'])
def delete_chat():
    data = request.get_json(silent=True) or {}
    me = (data.get('me') or '').lower()
    other = (data.get('other') or '').lower()
    if not me or not other:
        return jsonify({'ok': False}), 400

    path = dm_path(me, other)
    if os.path.exists(path):
        os.remove(path)

    chats = load_json(CHATS_FILE, {})
    lst = set(chats.get(me, []))
    lst.discard(other)
    chats[me] = list(lst)

    lst2 = set(chats.get(other, []))
    lst2.discard(me)
    chats[other] = list(lst2)
    save_json(CHATS_FILE, chats)

    unread = load_json(UNREAD_FILE, {})
    unread.setdefault(me, {})[other] = 0
    unread.setdefault(other, {})[me] = 0
    save_json(UNREAD_FILE, unread)
    return jsonify({'ok': True})


# =========================================================
# ОБЩИЙ ЧАТ
# =========================================================
@app.route('/messages.txt', methods=['GET'])
def messages_get():
    return read_file(GLOBAL_MESSAGES_FILE)


@app.route('/messages.txt', methods=['POST'])
def messages_post():
    text = request.get_data(as_text=True)
    if not text:
        return jsonify({'ok': False}), 400

    line = text.strip()
    if line:
        append_file(GLOBAL_MESSAGES_FILE, line + '|' + now_str() + '\n')

        if ':' in line:
            sender = line.split(':', 1)[0].strip().lower()
            unread = load_json(UNREAD_FILE, {})
            users = load_json(USERS_FILE, {})
            for u in users.keys():
                if u != sender:
                    unread.setdefault(u, {})
                    unread[u]['global'] = unread[u].get('global', 0) + 1
            save_json(UNREAD_FILE, unread)

    return jsonify({'ok': True})


# =========================================================
# ЛИЧНЫЕ СООБЩЕНИЯ
# =========================================================
@app.route('/dm/<u1>/<u2>', methods=['GET'])
def dm_get(u1, u2):
    return read_file(dm_path(u1, u2))


@app.route('/dm/<u1>/<u2>', methods=['POST'])
def dm_post(u1, u2):
    text = request.get_data(as_text=True)
    if not text:
        return jsonify({'ok': False}), 400

    line = text.strip()
    if line:
        append_file(dm_path(u1, u2), line + '|' + now_str() + '\n')

        if ':' in line:
            sender = line.split(':', 1)[0].strip().lower()
            if sender == u1.lower():
                recipient = u2.lower()
            elif sender == u2.lower():
                recipient = u1.lower()
            else:
                recipient = u2.lower()

            unread = load_json(UNREAD_FILE, {})
            unread.setdefault(recipient, {})
            unread[recipient][sender] = unread[recipient].get(sender, 0) + 1
            save_json(UNREAD_FILE, unread)

            chats = load_json(CHATS_FILE, {})
            lst = set(chats.get(recipient, []))
            lst.add(sender)
            chats[recipient] = list(lst)

            lst2 = set(chats.get(sender, []))
            lst2.add(recipient)
            chats[sender] = list(lst2)
            save_json(CHATS_FILE, chats)

    return jsonify({'ok': True})


# =========================================================
# НЕПРОЧИТАННЫЕ
# =========================================================
@app.route('/unread/<login>', methods=['GET'])
def unread_get(login):
    unread = load_json(UNREAD_FILE, {})
    return jsonify(unread.get(login.lower(), {}))


@app.route('/unread/reset', methods=['POST'])
def unread_reset():
    data = request.get_json(silent=True) or {}
    me = (data.get('me') or '').lower()
    other = (data.get('other') or '').lower()
    if not me or not other:
        return jsonify({'ok': False}), 400

    unread = load_json(UNREAD_FILE, {})
    unread.setdefault(me, {})[other] = 0
    save_json(UNREAD_FILE, unread)
    return jsonify({'ok': True})


# =========================================================
# ТИПИНГ
# =========================================================
@app.route('/typing/<chat_id>/<user>', methods=['POST'])
def typing_post(chat_id, user):
    typing = load_json(TYPING_FILE, {})
    typing.setdefault(chat_id, {})[user.lower()] = now_str()
    save_json(TYPING_FILE, typing)
    return jsonify({'ok': True})


@app.route('/typing/<chat_id>/<user>', methods=['GET'])
def typing_get(chat_id, user):
    typing = load_json(TYPING_FILE, {})
    return typing.get(chat_id, {}).get(user.lower(), '')


# =========================================================
# ОНЛАЙН
# =========================================================
@app.route('/online/<user>', methods=['GET'])
def online_get(user):
    online = load_json(ONLINE_FILE, {})
    return online.get(user.lower(), '')


@app.route('/online/<user>', methods=['POST'])
def online_post(user):
    online = load_json(ONLINE_FILE, {})
    online[user.lower()] = now_str()
    save_json(ONLINE_FILE, online)
    return jsonify({'ok': True})


# =========================================================
# ПРОЧИТАНО
# =========================================================
@app.route('/read/<chat_id>/<user>', methods=['POST'])
def read_post(chat_id, user):
    read = load_json(READ_FILE, {})
    read.setdefault(chat_id, {})[user.lower()] = now_str()
    save_json(READ_FILE, read)

    if '_' in chat_id:
        a, b = chat_id.split('_', 1)
        other = b if user.lower() == a else a
        unread = load_json(UNREAD_FILE, {})
        unread.setdefault(user.lower(), {})[other] = 0
        save_json(UNREAD_FILE, unread)

    return jsonify({'ok': True})


@app.route('/read/<chat_id>/<user>', methods=['GET'])
def read_get(chat_id, user):
    read = load_json(READ_FILE, {})
    return read.get(chat_id, {}).get(user.lower(), '')


# =========================================================
# УДАЛЕНИЕ СООБЩЕНИЙ
# =========================================================
@app.route('/delete_message', methods=['POST'])
def delete_message():
    data = request.get_json(silent=True) or {}
    chat_type = data.get('chat_type', 'global')
    me = (data.get('me') or '').lower()
    recipient = (data.get('recipient') or '').lower()
    line = data.get('line') or ''

    if not line:
        return jsonify({'ok': False}), 400

    if chat_type == 'global':
        path = GLOBAL_MESSAGES_FILE
    else:
        path = dm_path(me, recipient)

    if os.path.exists(path):
        content = read_file(path)
        new_lines = [ln for ln in content.split('\n') if ln != line]
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))

    return jsonify({'ok': True})


# =========================================================
# РЕАКЦИИ
# =========================================================
@app.route('/reaction', methods=['POST'])
def reaction_toggle():
    data = request.get_json(silent=True) or {}
    chat_id = data.get('chat_id') or ''
    msg_id = data.get('msg_id') or ''
    emoji = data.get('emoji') or ''
    user = (data.get('user') or '').lower()

    if not chat_id or not msg_id or not emoji or not user:
        return jsonify({'ok': False, 'error': 'missing fields'}), 400

    reactions = load_json(REACTIONS_FILE, {})
    chat = reactions.setdefault(chat_id, {})
    msg = chat.setdefault(msg_id, {})
    users = msg.setdefault(emoji, [])

    if user in users:
        users.remove(user)
    else:
        users.append(user)

    if not users:
        del msg[emoji]
    if not msg:
        del chat[msg_id]
    if not chat:
        del reactions[chat_id]

    save_json(REACTIONS_FILE, reactions)
    return jsonify({'ok': True})


@app.route('/reactions/<chat_id>', methods=['GET'])
def reactions_get(chat_id):
    reactions = load_json(REACTIONS_FILE, {})
    return jsonify(reactions.get(chat_id, {}))


# =========================================================
# ЗАГРУЗКА ФАЙЛОВ
# =========================================================
@app.route('/photo', methods=['POST'])
def upload_photo():
    if 'photo' not in request.files:
        return jsonify({'ok': False}), 400

    f = request.files['photo']
    name = 'photo_' + str(int(datetime.now(LOCAL_TZ).timestamp())) + '_' + secure_filename(f.filename)
    f.save(os.path.join(UPLOAD_DIR, name))
    return jsonify({'url': full_url('/uploads/' + name)})


@app.route('/video', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'ok': False}), 400

    f = request.files['video']
    name = 'video_' + str(int(datetime.now(LOCAL_TZ).timestamp())) + '_' + secure_filename(f.filename)
    f.save(os.path.join(UPLOAD_DIR, name))
    return jsonify({'url': full_url('/uploads/' + name)})


@app.route('/voice', methods=['POST'])
def upload_voice():
    if 'audio' not in request.files:
        return jsonify({'ok': False}), 400

    f = request.files['audio']
    name = 'voice_' + str(int(datetime.now(LOCAL_TZ).timestamp())) + '_' + secure_filename(f.filename)
    f.save(os.path.join(UPLOAD_DIR, name))
    return jsonify({'url': full_url('/uploads/' + name)})


@app.route('/uploads/<path:filename>', methods=['GET'])
def serve_upload(filename):
    return send_from_directory(UPLOAD_DIR, filename)


# =========================================================
# АВАТАРКИ
# =========================================================
@app.route('/avatar/<login>', methods=['GET'])
def avatar_get(login):
    avatars = load_json(AVATARS_FILE, {})
    url = avatars.get(login.lower())
    if not url:
        return ('', 404)
    return jsonify({'url': url})


@app.route('/avatar/<login>', methods=['POST'])
def avatar_upload(login):
    if 'avatar' not in request.files:
        return jsonify({'ok': False}), 400

    f = request.files['avatar']
    name = 'avatar_' + login.lower() + '_' + str(int(datetime.now(LOCAL_TZ).timestamp())) + '_' + secure_filename(f.filename)
    f.save(os.path.join(UPLOAD_DIR, name))

    avatars = load_json(AVATARS_FILE, {})
    avatars[login.lower()] = full_url('/uploads/' + name)
    save_json(AVATARS_FILE, avatars)

    return jsonify({'url': full_url('/uploads/' + name)})


# =========================================================
# ЗАПУСК
# =========================================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

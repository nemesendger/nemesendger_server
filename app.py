from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# === ХРАНИЛИЩА ===
global_messages = []
users = []
dm_messages = {}

@app.route('/')
def index():
    return 'Nemesenger server works!'

# === ОБЩИЙ ЧАТ ===
@app.route('/messages.txt', methods=['GET', 'POST'])
def messages():
    if request.method == 'POST':
        data = request.get_data(as_text=True).strip()
        if data:
            global_messages.append(data)
            return 'OK', 200
        return 'Empty', 400
    else:
        return '\n'.join(global_messages), 200, {'Content-Type': 'text/plain; charset=utf-8'}

# === ЛИЧНЫЙ ЧАТ ===
@app.route('/dm/<user1>/<user2>', methods=['GET', 'POST'])
def dm_chat(user1, user2):
    key = '_'.join(sorted([user1.lower(), user2.lower()]))
    if key not in dm_messages:
        dm_messages[key] = []
    
    if request.method == 'POST':
        data = request.get_data(as_text=True).strip()
        if data:
            dm_messages[key].append(data)
            return 'OK', 200
        return 'Empty', 400
    else:
        return '\n'.join(dm_messages[key]), 200, {'Content-Type': 'text/plain; charset=utf-8'}

# === ПОЛЬЗОВАТЕЛИ ===
@app.route('/users', methods=['GET'])
def get_users():
    return jsonify(users), 200

@app.route('/register_user', methods=['POST'])
def register_user():
    data = request.get_data(as_text=True).strip()
    if data in users:
        return 'exists', 400
    users.append(data)
    return 'OK', 200

from flask import Flask, request
import os

app = Flask(__name__)

MESSAGES_FILE = '/tmp/messages.txt'

if not os.path.exists(MESSAGES_FILE):
    with open(MESSAGES_FILE, 'w') as f:
        f.write('')

@app.route('/')
def index():
    return 'Nemesenger server works!'

@app.route('/messages.txt', methods=['GET', 'POST'])
def messages():
    if request.method == 'POST':
        data = request.get_data(as_text=True)
        with open(MESSAGES_FILE, 'a') as f:
            f.write(data)
        return 'OK', 200
    else:
        try:
            with open(MESSAGES_FILE, 'r') as f:
                content = f.read()
            return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}
        except:
            return '', 200

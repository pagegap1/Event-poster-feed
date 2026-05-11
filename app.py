import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB limit
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

DB_PATH = os.path.join(os.path.dirname(__file__), 'events.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_filename TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET'])
def index():
    with get_db() as conn:
        events = conn.execute(
            'SELECT * FROM events ORDER BY created_at DESC'
        ).fetchall()
    return render_template('index.html', events=events)


@app.route('/post', methods=['POST'])
def post_event():
    description = request.form.get('description', '').strip()
    file = request.files.get('poster')

    if not file or file.filename == '':
        return redirect(url_for('index'))
    if not allowed_file(file.filename):
        return redirect(url_for('index'))
    if not description:
        return redirect(url_for('index'))

    filename = secure_filename(file.filename)
    # Make filename unique using a counter
    base, ext = os.path.splitext(filename)
    counter = 1
    dest = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    while os.path.exists(dest):
        filename = f"{base}_{counter}{ext}"
        dest = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        counter += 1

    file.save(dest)

    with get_db() as conn:
        conn.execute(
            'INSERT INTO events (image_filename, description) VALUES (?, ?)',
            (filename, description)
        )

    return redirect(url_for('index'))


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

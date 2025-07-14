from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
from flask import send_from_directory
from flask import Response
import csv
from io import StringIO
import os
import sqlite3
from datetime import datetime

# Setup paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

# Init app
app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Debug print
print("Templates path exists:", os.path.exists(TEMPLATE_DIR))

# Ensure uploads folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 🔧 Initialize the SQLite database
def init_db():
    conn = sqlite3.connect('contact.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            filename TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# 🌐 Routes

@app.route('/')
def home():
    return render_template('project3.html')

@app.route('/thankyou')
def thankyou():
    return render_template('thankyou.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')
    file = request.files.get('file')

    filename = None
    if file and file.filename:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect('contact.db')
    c = conn.cursor()
    c.execute("INSERT INTO contacts (name, email, message, filename, timestamp) VALUES (?, ?, ?, ?, ?)",
              (name, email, message, filename, timestamp))
    conn.commit()
    conn.close()

    return render_template('thankyou.html')

@app.route('/download_csv', methods=['GET'])
def download_csv():
    # Connect to DB and get all rows
    conn = sqlite3.connect('contact.db')
    c = conn.cursor()
    c.execute("SELECT * FROM contacts")
    data = c.fetchall()
    conn.close()

    # Set up CSV in memory
    si = StringIO()
    writer = csv.writer(si)

    # Write headers
    writer.writerow(["ID", "Name", "Email", "Message", "Filename", "Timestamp"])


    # Write data rows
    for row in data:
        writer.writerow(row)

    # Create response
    output = si.getvalue()
    response = Response(output, mimetype='text/csv')
    response.headers["Content-Disposition"] = "attachment; filename=contact_submissions.csv"
    return response

@app.route('/all_submissions', methods=['GET'])
def get_all():
    try:
        conn = sqlite3.connect('contact.db')
        c = conn.cursor()
        c.execute("SELECT * FROM contacts")
        data = c.fetchall()
        conn.close()

        results = []
        for row in data:
            results.append({
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "message": row[3],
                "filename": row[4],
                "timestamp": row[5]
            })

        return jsonify(results)  # ✅ INSIDE the get_all() function
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500


@app.route('/uploads/<uploads>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
# ✅ Run the app
if __name__ == '__main__':
    app.run(debug=True)

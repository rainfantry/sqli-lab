"""
Medical Practice SQLi Lab
Deliberately vulnerable Flask app for learning SQL injection.
4 progressive levels. 2 hidden flags.
DO NOT deploy in production. Ever.
"""

import sqlite3
import os
from flask import Flask, request, g, redirect, url_for

app = Flask(__name__)
app.secret_key = 'machine-spirit-wills-it'
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'medical.db')


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    # Users table
    db.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )''')
    # Patient table
    db.execute('''CREATE TABLE IF NOT EXISTS patient (
        patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        date_of_birth TEXT,
        gender TEXT,
        mobile_phone TEXT
    )''')
    # Practitioner table
    db.execute('''CREATE TABLE IF NOT EXISTS practitioner (
        practitioner_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        practitioner_type TEXT NOT NULL
    )''')
    # Appointment table
    db.execute('''CREATE TABLE IF NOT EXISTS appointment (
        appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        practitioner_id INTEGER,
        appointment_date TEXT,
        appointment_time TEXT,
        notes TEXT
    )''')
    # Secrets table (the flags)
    db.execute('''CREATE TABLE IF NOT EXISTS secrets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flag TEXT NOT NULL,
        description TEXT
    )''')

    # Seed data only if tables are empty
    if db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        db.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'administrator')")
        db.execute("INSERT INTO users (username, password, role) VALUES ('drsmith', 'password1', 'practitioner')")
        db.execute("INSERT INTO users (username, password, role) VALUES ('nurse_jones', 'nursepw', 'practitioner')")
        db.execute("INSERT INTO users (username, password, role) VALUES ('reception', 'front_desk', 'staff')")

    if db.execute("SELECT COUNT(*) FROM patient").fetchone()[0] == 0:
        db.execute("INSERT INTO patient (first_name, last_name, date_of_birth, gender, mobile_phone) VALUES ('John', 'Smith', '1985-03-15', 'Male', '0412345678')")
        db.execute("INSERT INTO patient (first_name, last_name, date_of_birth, gender, mobile_phone) VALUES ('Sarah', 'Connor', '1990-07-22', 'Female', '0423456789')")
        db.execute("INSERT INTO patient (first_name, last_name, date_of_birth, gender, mobile_phone) VALUES ('James', 'Wilson', '1978-11-30', 'Male', '0434567890')")
        db.execute("INSERT INTO patient (first_name, last_name, date_of_birth, gender, mobile_phone) VALUES ('Emily', 'Chen', '2001-01-14', 'Female', '0445678901')")
        db.execute("INSERT INTO patient (first_name, last_name, date_of_birth, gender, mobile_phone) VALUES ('Robert', 'Brown', '1965-09-08', 'Male', '0456789012')")

    if db.execute("SELECT COUNT(*) FROM practitioner").fetchone()[0] == 0:
        db.execute("INSERT INTO practitioner (first_name, last_name, practitioner_type) VALUES ('David', 'Smith', 'GP')")
        db.execute("INSERT INTO practitioner (first_name, last_name, practitioner_type) VALUES ('Maria', 'Garcia', 'Nurse')")
        db.execute("INSERT INTO practitioner (first_name, last_name, practitioner_type) VALUES ('Alan', 'Turing', 'Physiotherapist')")

    if db.execute("SELECT COUNT(*) FROM appointment").fetchone()[0] == 0:
        db.execute("INSERT INTO appointment (patient_id, practitioner_id, appointment_date, appointment_time, notes) VALUES (1, 1, '2026-02-15', '09:00', 'General checkup')")
        db.execute("INSERT INTO appointment (patient_id, practitioner_id, appointment_date, appointment_time, notes) VALUES (2, 1, '2026-02-15', '10:30', 'Follow-up blood work')")
        db.execute("INSERT INTO appointment (patient_id, practitioner_id, appointment_date, appointment_time, notes) VALUES (3, 2, '2026-02-16', '14:00', 'Wound dressing change')")
        db.execute("INSERT INTO appointment (patient_id, practitioner_id, appointment_date, appointment_time, notes) VALUES (4, 3, '2026-02-17', '11:00', 'Knee rehabilitation session')")
        db.execute("INSERT INTO appointment (patient_id, practitioner_id, appointment_date, appointment_time, notes) VALUES (1, 1, '2026-03-01', '09:00', 'Results review - CONFIDENTIAL')")

    if db.execute("SELECT COUNT(*) FROM secrets").fetchone()[0] == 0:
        db.execute("INSERT INTO secrets (flag, description) VALUES ('FLAG{sql_injection_is_not_a_feature}', 'Flag 1: Found via UNION extraction')")
        db.execute("INSERT INTO secrets (flag, description) VALUES ('FLAG{blind_as_a_bat_but_still_sees}', 'Flag 2: Found via blind boolean inference')")

    db.commit()


# ──────────────────────────────────────────────
# HTML LAYOUT
# ──────────────────────────────────────────────

LAYOUT = '''
<!DOCTYPE html>
<html>
<head>
<title>Medical Practice Portal</title>
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
        background: #0a0a0a; color: #c0c0c0; font-family: 'Courier New', monospace;
        font-size: 14px; line-height: 1.6; padding: 20px;
    }
    .container { max-width: 900px; margin: 0 auto; }
    h1 { color: #ff4444; margin-bottom: 5px; font-size: 20px; }
    h2 { color: #ff6666; margin: 20px 0 10px; font-size: 16px; }
    .subtitle { color: #666; font-size: 12px; margin-bottom: 20px; }
    a { color: #ff4444; text-decoration: none; }
    a:hover { color: #ff6666; text-decoration: underline; }
    nav { margin: 20px 0; padding: 10px 0; border-top: 1px solid #333; border-bottom: 1px solid #333; }
    nav a { margin-right: 20px; }
    .level-box {
        background: #111; border: 1px solid #333; padding: 20px; margin: 15px 0;
        border-left: 3px solid #ff4444;
    }
    input[type="text"], input[type="password"] {
        background: #1a1a1a; border: 1px solid #444; color: #c0c0c0;
        padding: 8px 12px; font-family: 'Courier New', monospace; font-size: 14px;
        width: 300px;
    }
    input[type="text"]:focus, input[type="password"]:focus { border-color: #ff4444; outline: none; }
    button {
        background: #ff4444; color: #0a0a0a; border: none; padding: 8px 20px;
        font-family: 'Courier New', monospace; font-size: 14px; cursor: pointer;
        font-weight: bold;
    }
    button:hover { background: #ff6666; }
    .query-box {
        background: #1a1a1a; border: 1px solid #333; padding: 12px; margin: 10px 0;
        font-size: 13px; color: #888; word-wrap: break-word; white-space: pre-wrap;
    }
    .query-label { color: #ff4444; font-weight: bold; }
    .result { color: #44ff44; margin: 5px 0; }
    .error { color: #ff4444; margin: 5px 0; }
    .hint { color: #666; font-size: 12px; margin-top: 10px; font-style: italic; }
    table { border-collapse: collapse; margin: 10px 0; width: 100%; }
    th { background: #1a1a1a; color: #ff4444; text-align: left; padding: 8px; border: 1px solid #333; }
    td { padding: 8px; border: 1px solid #333; }
    .tag { display: inline-block; background: #1a1a1a; border: 1px solid #ff4444;
           color: #ff4444; padding: 2px 8px; font-size: 11px; margin-right: 5px; }
</style>
</head>
<body>
<div class="container">
    <h1>MEDICAL PRACTICE PORTAL</h1>
    <div class="subtitle">[ Definitely Secure Healthcare System v1.0 ]</div>
    <nav>
        <a href="/">INDEX</a>
        <a href="/login">LEVEL 1: LOGIN</a>
        <a href="/search">LEVEL 2: SEARCH</a>
        <a href="/union">LEVEL 3: UNION</a>
        <a href="/blind">LEVEL 4: BLIND</a>
        <a href="/theory">THEORY</a>
    </nav>
    CONTENT_PLACEHOLDER
</div>
</body>
</html>
'''


def render(content):
    return LAYOUT.replace('CONTENT_PLACEHOLDER', content)


# ──────────────────────────────────────────────
# INDEX
# ──────────────────────────────────────────────

@app.route('/')
def index():
    return render('''
    <h2>SQL INJECTION TRAINING LAB</h2>
    <div class="level-box">
        <p>This application is <strong>deliberately vulnerable</strong>.</p>
        <p>Every input field concatenates user input directly into SQL queries.</p>
        <p>Your mission: exploit each level and find the <strong>2 hidden flags</strong>.</p>
    </div>
    <h2>LEVELS</h2>
    <div class="level-box">
        <span class="tag">LEVEL 1</span> <a href="/login">Login Bypass</a>
        <span class="hint"> — Authentication bypass via tautology injection</span>
    </div>
    <div class="level-box">
        <span class="tag">LEVEL 2</span> <a href="/search">Data Extraction</a>
        <span class="hint"> — Break out of LIKE clause with UNION SELECT</span>
    </div>
    <div class="level-box">
        <span class="tag">LEVEL 3</span> <a href="/union">UNION Attack</a>
        <span class="hint"> — Column enumeration and full table extraction</span>
    </div>
    <div class="level-box">
        <span class="tag">LEVEL 4</span> <a href="/blind">Blind SQLi</a>
        <span class="hint"> — Boolean-based inference, one character at a time</span>
    </div>
    <div class="level-box">
        <span class="tag">REFERENCE</span> <a href="/theory">Theory &amp; Defence</a>
        <span class="hint"> — How it works, why it works, how to stop it</span>
    </div>
    ''')


# ──────────────────────────────────────────────
# LEVEL 1: LOGIN BYPASS
# ──────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    result = ''
    query_display = ''

    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        query_display = f'<div class="query-box"><span class="query-label">EXECUTED QUERY:</span>\n{query}</div>'

        try:
            db = get_db()
            rows = db.execute(query).fetchall()
            if rows:
                result = '<div class="result">ACCESS GRANTED</div>'
                result += '<table><tr><th>ID</th><th>Username</th><th>Password</th><th>Role</th></tr>'
                for row in rows:
                    result += f'<tr><td>{row["id"]}</td><td>{row["username"]}</td><td>{row["password"]}</td><td>{row["role"]}</td></tr>'
                result += '</table>'
            else:
                result = '<div class="error">ACCESS DENIED: Invalid credentials</div>'
        except Exception as e:
            result = f'<div class="error">SQL ERROR: {e}</div>'

    return render(f'''
    <h2>LEVEL 1: LOGIN BYPASS</h2>
    <div class="level-box">
        <p>Bypass the login form without knowing valid credentials.</p>
        <p><strong>Vulnerability:</strong> String concatenation in WHERE clause.</p>
        <form method="POST">
            <p><label>Username:</label><br><input type="text" name="username" autocomplete="off"></p>
            <p><label>Password:</label><br><input type="text" name="password" autocomplete="off"></p>
            <p><button type="submit">LOGIN</button></p>
        </form>
        {query_display}
        {result}
        <div class="hint">Hint: What happens if you close the quote early and add your own logic?</div>
    </div>
    ''')


# ──────────────────────────────────────────────
# LEVEL 2: DATA EXTRACTION (SEARCH)
# ──────────────────────────────────────────────

@app.route('/search', methods=['GET', 'POST'])
def search():
    result = ''
    query_display = ''

    if request.method == 'POST':
        name = request.form.get('name', '')

        query = f"SELECT * FROM patient WHERE first_name LIKE '%{name}%' OR last_name LIKE '%{name}%'"
        query_display = f'<div class="query-box"><span class="query-label">EXECUTED QUERY:</span>\n{query}</div>'

        try:
            db = get_db()
            rows = db.execute(query).fetchall()
            if rows:
                result = '<table><tr><th>ID</th><th>First Name</th><th>Last Name</th><th>DOB</th><th>Gender</th><th>Phone</th></tr>'
                for row in rows:
                    result += f'<tr><td>{row["patient_id"]}</td><td>{row["first_name"]}</td><td>{row["last_name"]}</td><td>{row["date_of_birth"]}</td><td>{row["gender"]}</td><td>{row["mobile_phone"]}</td></tr>'
                result += '</table>'
            else:
                result = '<div class="error">No patients found.</div>'
        except Exception as e:
            result = f'<div class="error">SQL ERROR: {e}</div>'

    return render(f'''
    <h2>LEVEL 2: DATA EXTRACTION</h2>
    <div class="level-box">
        <p>Search for patients by name. Then extract data from other tables.</p>
        <p><strong>Vulnerability:</strong> Direct interpolation in LIKE clause.</p>
        <form method="POST">
            <p><label>Patient Name:</label><br><input type="text" name="name" autocomplete="off"></p>
            <p><button type="submit">SEARCH</button></p>
        </form>
        {query_display}
        {result}
        <div class="hint">Hint: Can you close the LIKE clause and UNION SELECT from another table?</div>
    </div>
    ''')


# ──────────────────────────────────────────────
# LEVEL 3: UNION ATTACK
# ──────────────────────────────────────────────

@app.route('/union', methods=['GET', 'POST'])
def union():
    result = ''
    query_display = ''

    if request.method == 'POST':
        patient_id = request.form.get('patient_id', '')

        query = f"SELECT appointment_id, appointment_date, appointment_time, notes FROM appointment WHERE patient_id = {patient_id}"
        query_display = f'<div class="query-box"><span class="query-label">EXECUTED QUERY:</span>\n{query}</div>'

        try:
            db = get_db()
            rows = db.execute(query).fetchall()
            if rows:
                result = '<table><tr><th>Appt ID</th><th>Date</th><th>Time</th><th>Notes</th></tr>'
                for row in rows:
                    result += f'<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td></tr>'
                result += '</table>'
            else:
                result = '<div class="error">No appointments found for this patient.</div>'
        except Exception as e:
            result = f'<div class="error">SQL ERROR: {e}</div>'

    return render(f'''
    <h2>LEVEL 3: UNION ATTACK</h2>
    <div class="level-box">
        <p>Look up appointments by patient ID. Then enumerate the entire database.</p>
        <p><strong>Vulnerability:</strong> No type checking on integer input.</p>
        <form method="POST">
            <p><label>Patient ID:</label><br><input type="text" name="patient_id" autocomplete="off"></p>
            <p><button type="submit">LOOKUP</button></p>
        </form>
        {query_display}
        {result}
        <div class="hint">Hint: Use ORDER BY to find column count, then UNION SELECT from sqlite_master.</div>
    </div>
    ''')


# ──────────────────────────────────────────────
# LEVEL 4: BLIND SQLi
# ──────────────────────────────────────────────

@app.route('/blind', methods=['GET', 'POST'])
def blind():
    result = ''
    query_display = ''

    if request.method == 'POST':
        patient_id = request.form.get('patient_id', '')

        query = f"SELECT first_name FROM patient WHERE patient_id = {patient_id}"
        query_display = f'<div class="query-box"><span class="query-label">EXECUTED QUERY:</span>\n{query}</div>'

        try:
            db = get_db()
            rows = db.execute(query).fetchall()
            if rows:
                result = '<div class="result">Patient exists.</div>'
            else:
                result = '<div class="error">Patient not found.</div>'
        except Exception as e:
            result = f'<div class="error">SQL ERROR: {e}</div>'

    return render(f'''
    <h2>LEVEL 4: BLIND SQLi</h2>
    <div class="level-box">
        <p>Check if a patient exists by ID. No data is returned — only yes or no.</p>
        <p><strong>Vulnerability:</strong> Boolean-based blind injection.</p>
        <form method="POST">
            <p><label>Patient ID:</label><br><input type="text" name="patient_id" autocomplete="off"></p>
            <p><button type="submit">CHECK</button></p>
        </form>
        {query_display}
        {result}
        <div class="hint">Hint: 1 AND (SELECT substr(flag,1,1) FROM secrets WHERE id=1)='F' — what does the response tell you?</div>
    </div>
    ''')


# ──────────────────────────────────────────────
# THEORY PAGE
# ──────────────────────────────────────────────

@app.route('/theory')
def theory():
    return render('''
    <h2>SQL INJECTION THEORY</h2>

    <div class="level-box">
        <h2>What is SQL Injection?</h2>
        <p>SQL injection occurs when user input is concatenated directly into a SQL query
        string instead of being passed as a parameter. The database cannot distinguish
        between the developer's intended SQL and the attacker's injected SQL.</p>
    </div>

    <div class="level-box">
        <h2>Types of SQLi</h2>
        <table>
            <tr><th>Type</th><th>Description</th><th>Level</th></tr>
            <tr><td>Tautology / Auth Bypass</td><td>Inject OR 1=1 to make WHERE always true</td><td>1</td></tr>
            <tr><td>UNION-based</td><td>Append UNION SELECT to extract from other tables</td><td>2, 3</td></tr>
            <tr><td>Error-based</td><td>Force SQL errors that leak schema info</td><td>Any</td></tr>
            <tr><td>Blind (Boolean)</td><td>Infer data from yes/no responses</td><td>4</td></tr>
            <tr><td>Blind (Time)</td><td>Infer data from response delay (not in this lab)</td><td>-</td></tr>
        </table>
    </div>

    <div class="level-box">
        <h2>UNION SELECT Technique</h2>
        <p><strong>Step 1:</strong> Find column count with ORDER BY</p>
        <div class="query-box">1 ORDER BY 1 --    (works)
1 ORDER BY 2 --    (works)
1 ORDER BY 3 --    (works)
1 ORDER BY 4 --    (works)
1 ORDER BY 5 --    (error = only 4 columns)</div>

        <p><strong>Step 2:</strong> Enumerate tables from sqlite_master</p>
        <div class="query-box">0 UNION SELECT 1, name, 3, 4 FROM sqlite_master WHERE type='table' --</div>

        <p><strong>Step 3:</strong> Enumerate columns</p>
        <div class="query-box">0 UNION SELECT 1, sql, 3, 4 FROM sqlite_master WHERE name='secrets' --</div>

        <p><strong>Step 4:</strong> Extract data</p>
        <div class="query-box">0 UNION SELECT 1, flag, description, 4 FROM secrets --</div>
    </div>

    <div class="level-box">
        <h2>Blind SQLi Technique</h2>
        <p>When no data is returned, extract one character at a time:</p>
        <div class="query-box">1 AND (SELECT substr(flag,1,1) FROM secrets WHERE id=1)='F'
-- If "Patient exists" -> first char is F
-- If "Patient not found" -> first char is NOT F
-- Repeat for each position: substr(flag,2,1), substr(flag,3,1), ...</div>
    </div>

    <div class="level-box">
        <h2>The Fix: Parameterised Queries</h2>
        <p>Every vulnerability in this lab is solved by parameterised queries:</p>
        <div class="query-box"><span style="color:#ff4444;">VULNERABLE:</span>
cursor.execute(f"SELECT * FROM users WHERE name = '{name}'")<br>
<span style="color:#44ff44;">SECURE:</span>
cursor.execute("SELECT * FROM users WHERE name = ?", (name,))</div>
        <p>The <code>?</code> placeholder tells the database to treat input as <strong>data</strong>, never as <strong>code</strong>.</p>
    </div>
    ''')


# ──────────────────────────────────────────────
# INIT AND RUN
# ──────────────────────────────────────────────

with app.app_context():
    init_db()

if __name__ == '__main__':
    print("[*] Medical Practice SQLi Lab starting...")
    print("[*] http://localhost:8888")
    print("[*] 4 levels. 2 flags. No sanitisation.")
    app.run(host='0.0.0.0', port=8888, debug=True)

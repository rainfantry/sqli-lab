# Medical Practice SQLi Lab

A deliberately vulnerable Flask web application for learning SQL injection techniques. Built as a hands-on training tool with 4 progressive levels of difficulty.

**DO NOT deploy this in production. Ever.**

## How It Works

The app simulates a medical practice portal backed by a SQLite database. Every input field is intentionally vulnerable — no parameterised queries, no input sanitisation, no escaping. User input is concatenated directly into SQL strings, which is exactly how real-world SQLi vulnerabilities occur.

### Tech Stack

- **Python 3 / Flask** — lightweight web framework
- **SQLite** — embedded database (no server needed)
- **Jinja2 `render_template_string`** — inline HTML templates

### Database Schema

The app creates 5 tables on first run:

| Table | Columns | Purpose |
|-------|---------|---------|
| `users` | id, username, password, role | Login credentials (plaintext passwords) |
| `patient` | patient_id, first_name, last_name, date_of_birth, gender, mobile_phone | Patient records |
| `practitioner` | practitioner_id, first_name, last_name, practitioner_type | Doctors and specialists |
| `appointment` | appointment_id, patient_id, practitioner_id, appointment_date, appointment_time, notes | Scheduled appointments |
| `secrets` | id, flag, description | Hidden flags to find via injection |

## The 4 Levels

### Level 1: Login Bypass (`/login`)

**Vulnerability:** String concatenation in authentication query.

```python
query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
```

The attacker closes the quote early and injects their own SQL logic. Input like `' OR 1=1 --` makes the WHERE clause always true, bypassing authentication entirely.

### Level 2: Data Extraction (`/search`)

**Vulnerability:** Direct string interpolation in a LIKE search.

```python
query = f"SELECT * FROM patient WHERE first_name LIKE '%{name}%' OR last_name LIKE '%{name}%'"
```

Because the search term is injected raw into the query, an attacker can break out of the LIKE clause and append a UNION SELECT to read from any table in the database — including `users` and `secrets`.

### Level 3: UNION Attack (`/union`)

**Vulnerability:** No type checking on integer input.

```python
query = f"SELECT appointment_id, appointment_date, appointment_time, notes FROM appointment WHERE patient_id = {patient_id}"
```

The patient_id field expects an integer but accepts anything. An attacker uses ORDER BY to determine column count, then UNION SELECT to enumerate tables via `sqlite_master` and extract data from any table.

### Level 4: Blind SQLi (`/blind`)

**Vulnerability:** Boolean-based blind injection.

```python
query = f"SELECT first_name FROM patient WHERE patient_id = {patient_id}"
```

The app only returns "Patient exists" or "Patient not found" — no data is displayed. The attacker injects boolean conditions (e.g., `1 AND (SELECT substr(flag,1,1) FROM secrets WHERE id=1) = 'F'`) and infers data one character at a time based on the yes/no response.

## Source Code Structure

The entire app is a single file (`app.py`):

- **Lines 14-86** — Database setup: `get_db()`, `init_db()` with all table creation and seed data
- **Lines 88-131** — HTML layout template with CSS (dark theme, monospace)
- **Lines 163-210** — Level 1: Login bypass route
- **Lines 214-257** — Level 2: Patient search data extraction route
- **Lines 261-305** — Level 3: UNION attack route
- **Lines 309-355** — Level 4: Blind SQLi route
- **Lines 359-440** — Theory page with SQLi types, UNION technique walkthrough, and defence strategies
- **Lines 443-452** — Index route and app entry point

Each level shows the executed SQL query back to the user and includes hints on how to exploit it.

## How to Run

```bash
pip install flask
python app.py
```

The app runs on `http://0.0.0.0:8888`.

## The Fix

Every vulnerability in this lab is solved by **parameterised queries**:

```python
# Vulnerable:
cursor.execute(f"SELECT * FROM users WHERE name = '{name}'")

# Secure:
cursor.execute("SELECT * FROM users WHERE name = ?", (name,))
```

The `?` placeholder tells the database to treat the input as data, never as SQL code.

## Objective

Find the 2 flags hidden in the `secrets` table using the techniques taught at each level.

#!/usr/bin/env python3
"""
JobPortal System - Flask Backend
Candidate Registration & Employer Dashboard
"""

import sqlite3
import json
import os
import hashlib
import secrets
from datetime import datetime, date
from functools import wraps
from flask import Flask, request, jsonify, session, send_from_directory, render_template_string

app = Flask(__name__, static_folder='static')
# Stable secret key derived from a fixed seed so sessions survive restarts.
# Override with a real SECRET_KEY env var in production.
_raw_key = os.environ.get('SECRET_KEY', 'jobportal-dev-key-change-in-production')
app.secret_key = hashlib.sha256(_raw_key.encode()).hexdigest()

DB_PATH = os.path.join(os.path.dirname(__file__), 'jobportal.db')

# ─────────────────────────────────────────────
# Database Setup
# ─────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _migrate(conn):
    """Add new columns to existing databases without data loss."""
    new_cols = [
        ("medical_date",    "TEXT DEFAULT ''"),
        ("reference_type",  "TEXT DEFAULT 'Implants'"),
        ("reference_detail","TEXT DEFAULT ''"),
        ("doj",             "TEXT DEFAULT ''"),
        ("employee_id",     "TEXT DEFAULT ''"),
        ("oms_id",          "TEXT DEFAULT ''"),
        ("aadhaar_seeding", "TEXT DEFAULT 'Pending'"),
        ("bank_name",       "TEXT DEFAULT ''"),
        ("ap_code",         "TEXT DEFAULT ''"),
        ("ap_mail_id",      "TEXT DEFAULT ''"),
    ]
    for col, defn in new_cols:
        try:
            conn.execute(f"ALTER TABLE candidates ADD COLUMN {col} {defn}")
        except Exception:
            pass  # column already exists

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        father_name TEXT NOT NULL,
        mobile TEXT NOT NULL,
        aadhaar TEXT NOT NULL,
        pan TEXT NOT NULL,
        dob TEXT NOT NULL,
        age INTEGER,
        gender TEXT,
        marital_status TEXT,
        candidate_type TEXT,
        education_track TEXT,
        degree TEXT,
        puc_branch TEXT,
        iti_trade TEXT,
        sslc_per REAL,
        puc_per REAL,
        iti_per REAL,
        grad_per REAL,
        religion TEXT,
        category TEXT,
        location TEXT,
        district TEXT,
        interview_date TEXT,
        criteria_met TEXT DEFAULT 'NO',
        interview_status TEXT DEFAULT 'Pending',
        medical_status TEXT DEFAULT 'Pending',
        submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
        medical_date TEXT DEFAULT '',
        reference_type TEXT DEFAULT 'Implants',
        reference_detail TEXT DEFAULT '',
        doj TEXT DEFAULT '',
        employee_id TEXT DEFAULT '',
        oms_id TEXT DEFAULT '',
        aadhaar_seeding TEXT DEFAULT 'Pending',
        bank_name TEXT DEFAULT '',
        ap_code TEXT DEFAULT '',
        ap_mail_id TEXT DEFAULT ''
    )''')

    _migrate(conn)

    c.execute('''CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )''')

    # Create default admin: admin / admin123
    pwd_hash = hashlib.sha256('admin123'.encode()).hexdigest()
    c.execute('INSERT OR IGNORE INTO admins (username, password_hash) VALUES (?, ?)',
              ('admin', pwd_hash))

    # Seed sample data
    c.execute('SELECT COUNT(*) FROM candidates')
    if c.fetchone()[0] == 0:
        samples = [
            ('Ramesh Kumar', 'Anand Kumar', '9876543210', '123456789012', 'ABCDE1234F',
             '2005-06-15', 20, 'Male', 'Unmarried', 'Fresher', 'ITI+PUC', 'None',
             'Science', 'Fitter', 78.5, 68.2, 82.0, 0, 'Hindu', '2A',
             'Maddur', 'Mandya', '2026-05-20', 'YES', 'Pending', 'Pending'),
            ('Savitri Patil', 'Basavaraj Patil', '9123456789', '987654321098', 'XYZK9876P',
             '2001-02-10', 25, 'Female', 'Unmarried', 'Outside Apprenticeship Completed', 'PUC', 'BA',
             'Arts', 'N/A', 48.0, 55.0, 0, 62.1, 'Hindu', 'General',
             'Hubli', 'Dharwad', '2026-05-22', 'NO', 'Pending', 'Pending'),
            ('Mahesh Gowda', 'Srinivas Gowda', '9845123456', '456789012345', 'MNOPQ5678R',
             '2004-11-20', 21, 'Male', 'Unmarried', 'Fresher', 'ITI', 'None',
             'N/A', 'Electrician', 72.3, 0, 79.5, 0, 'Hindu', '2B',
             'Mysuru', 'Mysuru', '2026-05-20', 'YES', 'Selected', 'Medical Fit'),
            ('Priya Sharma', 'Mohan Sharma', '9988776655', '321098765432', 'PQRST9012U',
             '2003-03-15', 22, 'Female', 'Unmarried', 'Fresher', 'PUC', 'B.Sc',
             'Science', 'N/A', 85.0, 78.5, 0, 71.2, 'Hindu', 'General',
             'Bengaluru', 'Bengaluru Urban', '2026-05-25', 'YES', 'Pending', 'Pending'),
            ('Arjun Naik', 'Ramu Naik', '9765432109', '654321098765', 'UVWXY3456Z',
             '2006-07-08', 19, 'Male', 'Unmarried', 'Fresher', 'ITI+PUC', 'None',
             'Commerce', 'Welder', 65.0, 60.0, 71.0, 0, 'Muslim', 'OBC',
             'Belgaum', 'Belagavi', '2026-05-22', 'YES', 'Pending', 'Pending'),
        ]
        c.executemany('''INSERT INTO candidates 
            (name, father_name, mobile, aadhaar, pan, dob, age, gender, marital_status,
             candidate_type, education_track, degree, puc_branch, iti_trade,
             sslc_per, puc_per, iti_per, grad_per, religion, category,
             location, district, interview_date, criteria_met, interview_status, medical_status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', samples)

    conn.commit()
    conn.close()

# Run at import time so Gunicorn (and direct runs) both initialise the DB.
init_db()

# ─────────────────────────────────────────────
# Auth Helper
# ─────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

def calculate_age(dob_str):
    try:
        birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
        today = date.today()
        age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        return age
    except:
        return 0

def check_eligibility(age, sslc, puc, iti, track, degree, grad):
    age_valid = 18 <= age <= 23
    if 'PUC' in track and 'ITI' in track:
        acad_valid = sslc >= 50 and puc >= 50 and iti >= 50
    elif 'PUC' in track:
        acad_valid = sslc >= 50 and puc >= 50
    elif 'ITI' in track:
        acad_valid = sslc >= 50 and iti >= 50
    else:
        acad_valid = sslc >= 50

    if degree and degree != 'None' and grad < 50:
        acad_valid = False

    return 'YES' if (age_valid and acad_valid) else 'NO'

# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    return send_from_directory(ROOT_DIR, 'index.html')

@app.route('/admin')
def admin_page():
    return send_from_directory(ROOT_DIR, 'admin.html')

# ── Auth ──────────────────────────────────────

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()

    conn = get_db()
    admin = conn.execute('SELECT * FROM admins WHERE username = ? AND password_hash = ?',
                          (username, pwd_hash)).fetchone()
    conn.close()

    if admin:
        session['admin_logged_in'] = True
        session['admin_username'] = username
        return jsonify({'success': True, 'username': username})
    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/auth/check', methods=['GET'])
def check_auth():
    return jsonify({'authenticated': session.get('admin_logged_in', False)})

# ── Candidate Submission ──────────────────────

@app.route('/api/candidates', methods=['POST'])
def submit_candidate():
    data = request.get_json()

    required = ['name', 'fatherName', 'mobile', 'aadhaar', 'pan', 'dob',
                'gender', 'maritalStatus', 'candidateType', 'educationTrack',
                'sslcPer', 'religion', 'category', 'location', 'district', 'interviewDate']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'Missing required field: {field}'}), 400

    age = calculate_age(data['dob'])
    track = data['educationTrack']
    sslc = float(data.get('sslcPer', 0))
    puc = float(data.get('pucPer', 0))
    iti = float(data.get('itiPer', 0))
    grad = float(data.get('gradPer', 0))
    degree = data.get('degree', 'None')

    criteria = check_eligibility(age, sslc, puc, iti, track, degree, grad)

    conn = get_db()
    conn.execute('''INSERT INTO candidates 
        (name, father_name, mobile, aadhaar, pan, dob, age, gender, marital_status,
         candidate_type, education_track, degree, puc_branch, iti_trade,
         sslc_per, puc_per, iti_per, grad_per, religion, category,
         location, district, interview_date, criteria_met)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (data['name'], data['fatherName'], data['mobile'], data['aadhaar'],
         data['pan'].upper(), data['dob'], age, data['gender'], data['maritalStatus'],
         data['candidateType'], track, degree,
         data.get('pucBranch', 'N/A'), data.get('itiTrade', 'N/A'),
         sslc, puc, iti, grad, data['religion'], data['category'],
         data['location'], data['district'], data['interviewDate'], criteria))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'criteriaMet': criteria, 'age': age})

# ── Admin: Candidates CRUD ────────────────────

@app.route('/api/admin/candidates', methods=['GET'])
@login_required
def get_candidates():
    conn = get_db()
    search = request.args.get('search', '')
    filter_date = request.args.get('date', '')
    filter_status = request.args.get('status', '')
    filter_criteria = request.args.get('criteria', '')
    sort_by = request.args.get('sort', 'submitted_at')
    sort_dir = request.args.get('dir', 'desc')

    allowed_sorts = ['name', 'submitted_at', 'interview_date', 'age', 'sslc_per', 'criteria_met', 'dob', 'education_track']
    if sort_by not in allowed_sorts:
        sort_by = 'submitted_at'
    if sort_dir not in ['asc', 'desc']:
        sort_dir = 'desc'

    query = 'SELECT * FROM candidates WHERE 1=1'
    params = []

    if search:
        query += ' AND (name LIKE ? OR mobile LIKE ? OR pan LIKE ? OR district LIKE ?)'
        s = f'%{search}%'
        params += [s, s, s, s]
    if filter_date:
        query += ' AND interview_date = ?'
        params.append(filter_date)
    if filter_status:
        query += ' AND interview_status = ?'
        params.append(filter_status)
    if filter_criteria:
        query += ' AND criteria_met = ?'
        params.append(filter_criteria)

    query += f' ORDER BY {sort_by} {sort_dir}'

    rows = conn.execute(query, params).fetchall()
    conn.close()

    candidates = []
    for row in rows:
        c = dict(row)
        c['aadhaar'] = '[Redacted]'  # Security: never expose Aadhaar
        candidates.append(c)

    return jsonify(candidates)

@app.route('/api/admin/candidates/<int:cid>', methods=['PATCH'])
@login_required
def update_candidate(cid):
    data = request.get_json()
    allowed_fields = [
        'interview_status', 'medical_status', 'interview_date',
        'medical_date', 'reference_type', 'reference_detail',
        'doj', 'employee_id', 'oms_id', 'aadhaar_seeding',
        'bank_name', 'ap_code', 'ap_mail_id'
    ]
    
    updates = {k: v for k, v in data.items() if k in allowed_fields}
    if not updates:
        return jsonify({'error': 'No valid fields to update'}), 400

    set_clause = ', '.join([f'{k} = ?' for k in updates])
    values = list(updates.values()) + [cid]

    conn = get_db()
    conn.execute(f'UPDATE candidates SET {set_clause} WHERE id = ?', values)
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/admin/candidates/<int:cid>', methods=['DELETE'])
@login_required
def delete_candidate(cid):
    conn = get_db()
    conn.execute('DELETE FROM candidates WHERE id = ?', (cid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ── Admin: Stats ──────────────────────────────

@app.route('/api/admin/stats', methods=['GET'])
@login_required
def get_stats():
    conn = get_db()
    c = conn.cursor()

    total = c.execute('SELECT COUNT(*) FROM candidates').fetchone()[0]
    eligible = c.execute("SELECT COUNT(*) FROM candidates WHERE criteria_met='YES'").fetchone()[0]
    selected = c.execute("SELECT COUNT(*) FROM candidates WHERE interview_status='Selected'").fetchone()[0]
    rejected = c.execute("SELECT COUNT(*) FROM candidates WHERE interview_status='Rejected'").fetchone()[0]
    pending = c.execute("SELECT COUNT(*) FROM candidates WHERE interview_status='Pending'").fetchone()[0]
    med_fit = c.execute("SELECT COUNT(*) FROM candidates WHERE medical_status='Medical Fit'").fetchone()[0]
    med_unfit = c.execute("SELECT COUNT(*) FROM candidates WHERE medical_status='Medical Unfit'").fetchone()[0]
    male = c.execute("SELECT COUNT(*) FROM candidates WHERE gender='Male'").fetchone()[0]
    female = c.execute("SELECT COUNT(*) FROM candidates WHERE gender='Female'").fetchone()[0]
    fresher = c.execute("SELECT COUNT(*) FROM candidates WHERE candidate_type='Fresher'").fetchone()[0]
    today_count = c.execute(
        "SELECT COUNT(*) FROM candidates WHERE date(submitted_at) = date('now')"
    ).fetchone()[0]

    by_district = c.execute(
        "SELECT district, COUNT(*) as cnt FROM candidates GROUP BY district ORDER BY cnt DESC LIMIT 8"
    ).fetchall()
    by_track = c.execute(
        "SELECT education_track, COUNT(*) as cnt FROM candidates GROUP BY education_track"
    ).fetchall()
    by_category = c.execute(
        "SELECT category, COUNT(*) as cnt FROM candidates GROUP BY category ORDER BY cnt DESC"
    ).fetchall()
    by_trade = c.execute(
        "SELECT iti_trade, COUNT(*) as cnt FROM candidates WHERE iti_trade != 'N/A' GROUP BY iti_trade ORDER BY cnt DESC LIMIT 6"
    ).fetchall()
    by_date = c.execute(
        "SELECT interview_date, COUNT(*) as cnt FROM candidates GROUP BY interview_date ORDER BY interview_date"
    ).fetchall()
    recent = c.execute(
        "SELECT id, name, mobile, criteria_met, interview_status, submitted_at FROM candidates ORDER BY submitted_at DESC LIMIT 5"
    ).fetchall()

    conn.close()

    return jsonify({
        'total': total,
        'eligible': eligible,
        'ineligible': total - eligible,
        'selected': selected,
        'rejected': rejected,
        'pending': pending,
        'medFit': med_fit,
        'medUnfit': med_unfit,
        'male': male,
        'female': female,
        'fresher': fresher,
        'todayCount': today_count,
        'byDistrict': [dict(r) for r in by_district],
        'byTrack': [dict(r) for r in by_track],
        'byCategory': [dict(r) for r in by_category],
        'byTrade': [dict(r) for r in by_trade],
        'byDate': [dict(r) for r in by_date],
        'recent': [dict(r) for r in recent]
    })

# ── Export ────────────────────────────────────

@app.route('/api/admin/export', methods=['GET'])
@login_required
def export_candidates():
    import csv
    import io

    conn = get_db()
    filter_date = request.args.get('date', '')
    
    query = 'SELECT * FROM candidates'
    params = []
    if filter_date:
        query += ' WHERE interview_date = ?'
        params.append(filter_date)
    query += ' ORDER BY submitted_at DESC'

    rows = conn.execute(query, params).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    headers = ['ID', 'Name', 'Father Name', 'Mobile', 'PAN', 'DOB', 'Age',
               'Gender', 'Marital Status', 'Candidate Type', 'Education Track',
               'Degree', 'PUC Branch', 'ITI Trade', 'SSLC%', 'PUC%', 'ITI%',
               'Graduation%', 'Religion', 'Category', 'Location', 'District',
               'Interview Date', 'Criteria Met', 'Interview Status', 'Medical Status',
               'Medical Date', 'Reference Channel', 'Reference Detail',
               'Date of Joining', 'Employee ID', 'OMS ID', 'Aadhaar Seeding',
               'Bank Name', 'AP Code', 'AP Mail ID',
               'Submitted At', 'Aadhaar']
    writer.writerow(headers)

    for row in rows:
        r = dict(row)
        writer.writerow([
            r['id'], r['name'], r['father_name'], r['mobile'], r['pan'],
            r['dob'], r['age'], r['gender'], r['marital_status'], r['candidate_type'],
            r['education_track'], r['degree'], r['puc_branch'], r['iti_trade'],
            r['sslc_per'], r['puc_per'], r['iti_per'], r['grad_per'],
            r['religion'], r['category'], r['location'], r['district'],
            r['interview_date'], r['criteria_met'], r['interview_status'],
            r['medical_status'],
            r.get('medical_date', ''), r.get('reference_type', 'Implants'),
            r.get('reference_detail', ''), r.get('doj', ''),
            r.get('employee_id', ''), r.get('oms_id', ''),
            r.get('aadhaar_seeding', 'Pending'), r.get('bank_name', ''),
            r.get('ap_code', ''), r.get('ap_mail_id', ''),
            r['submitted_at'], '[Redacted]'
        ])

    from flask import Response
    filename = f'recruitment_{filter_date or "all"}.csv'
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

# ─────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    print(f"✅ JobPortal System running on http://localhost:{port}")
    print("   Public Form:   http://localhost:{port}/")
    print("   Admin Panel:   http://localhost:{port}/admin")
    print("   Credentials:   admin / admin123")
    app.run(host='0.0.0.0', port=port, debug=debug)

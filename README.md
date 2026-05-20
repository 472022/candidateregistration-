# JobPortal System
### Candidate Registration & Employer Dashboard

A production-ready recruitment management platform with a public candidate form and a secure admin dashboard — built with Python Flask, SQLite, and vanilla HTML/CSS/JS.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ (Flask will auto-install)

### Run the Server
```bash
cd jobportal-flask
python start.py
```
Or directly:
```bash
python app.py
```

The server starts at **http://localhost:5000**

---

## 🌐 URLs

| URL | Description |
|-----|-------------|
| `http://localhost:5000/` | Public candidate registration form |
| `http://localhost:5000/admin` | Admin login & dashboard |

---

## 🔐 Admin Credentials

| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `admin123` |

> Change the password by modifying the `init_db()` function in `app.py` before first run, or update the `admins` table directly in SQLite.

---

## 📁 Project Structure

```
jobportal-flask/
├── app.py               # Flask backend — all routes, DB, auth
├── start.py             # Convenience startup script
├── jobportal.db         # SQLite database (auto-created on first run)
├── static/
│   ├── index.html       # Public candidate registration form
│   └── admin.html       # Admin login + full management dashboard
└── README.md
```

---

## ✅ Features

### Public Candidate Form
- Multi-step form (4 sections) with step-by-step progress indicator
- Bilingual UI: English + Kannada labels throughout
- Dynamic education fields (ITI / PUC / ITI+PUC with conditional inputs)
- Live client-side validation with inline error messages
- Auto-calculates candidate age from DOB
- Auto-evaluates eligibility criteria (age 18–23, all academics ≥ 50%)
- Aadhaar securely stored but always redacted in admin views
- Success screen with eligibility result after submission
- Fully mobile responsive

### Admin Dashboard
- **Secure login** with session-based authentication
- **Dashboard page**: 4 KPI stat cards + 4 charts (interview status, education track, district breakdown, category distribution) + recent submissions table
- **Candidates page**: Full data table with search, filter by date/status/criteria, column sorting, inline status updates (interview + medical), delete records, pagination (15/page)
- **Analytics page**: Gender split, medical fitness, eligibility ratio, submission timeline, ITI trade distribution
- **CSV export** (all records or filtered by date)
- Responsive sidebar navigation

### Backend / Database
- SQLite database — zero-config, single file
- REST API with JSON responses
- Session-based admin authentication (SHA-256 password hashing)
- Aadhaar always redacted in all API responses
- Auto-seeded with 5 sample candidates on first run
- All CRUD operations for candidate management

---

## 🔧 API Reference

### Public
| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/candidates` | Submit new candidate application |

### Admin (requires login)
| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/auth/login` | Admin login |
| POST | `/api/auth/logout` | Admin logout |
| GET | `/api/auth/check` | Check auth status |
| GET | `/api/admin/candidates` | List all candidates (supports search/filter/sort params) |
| PATCH | `/api/admin/candidates/:id` | Update interview_status or medical_status |
| DELETE | `/api/admin/candidates/:id` | Delete a candidate record |
| GET | `/api/admin/stats` | Get dashboard statistics and chart data |
| GET | `/api/admin/export` | Download CSV of all/filtered candidates |

---

## ⚙️ Eligibility Criteria (Auto-evaluated on submission)

A candidate is marked **Eligible (YES)** if:
- Age is between **18 and 23** years (calculated from DOB)
- **SSLC ≥ 50%**
- **PUC ≥ 50%** (if PUC track selected)
- **ITI ≥ 50%** (if ITI track selected)
- **Graduation ≥ 50%** (if a degree is selected)

Otherwise marked **Ineligible (NO)**.

---

## 🔒 Security Notes
- Aadhaar numbers are **always redacted** (`[Redacted]`) in all API responses and admin views — they are stored in DB but never exposed
- Admin routes require an active session
- Passwords stored as SHA-256 hash
- For production: switch to bcrypt, use HTTPS, set a strong `SECRET_KEY` in `app.py`

---

## 📦 Dependencies

Only **Flask** is required:
```bash
pip install flask
```

SQLite is included in Python's standard library — no additional database setup needed.

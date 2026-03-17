# SSELabTrack

A full-featured lab inventory and resource management system built with Django. SSELabTrack helps lab administrators and members track equipment, manage borrowing and reservations, monitor consumable stock, coordinate projects, and log incidents — all from a single web interface.

---

## Features

1. **Equipment Inventory** — Add, edit, and search equipment items with serial numbers, categories, locations, condition ratings, and lifecycle history.
2. **Borrowing Management** — Check equipment in and out, track active loans, enforce due dates, and view full borrowing history per item or user.
3. **Reservations** — Reserve equipment for a future time slot; conflict detection prevents double-booking.
4. **Lab Kits** — Bundle multiple equipment pieces into a named kit that can be borrowed as a single unit.
5. **Projects** — Organize work into projects, assign lead and member roles, and link equipment usage to a project.
6. **Consumables Tracking** — Track quantity, unit cost, and low-stock thresholds for consumable items such as components, chemicals, and materials.
7. **Incident Reporting** — Log equipment damage, faults, and maintenance events with a severity level and resolution workflow.
8. **Notifications** — In-app notification system alerts users about due dates, low stock, incident updates, and more.
9. **Activity Log** — Immutable audit trail recording who did what and when across the entire system.
10. **Dashboard** — Role-aware home screen summarising key metrics: equipment availability, active borrows, upcoming reservations, and low-stock alerts.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | Django 4.2 |
| Database (default) | SQLite (PostgreSQL supported) |
| Frontend styling | Tailwind CSS (via CDN) |
| Forms | django-crispy-forms + crispy-tailwind |
| Filtering | django-filter |
| Static file serving | WhiteNoise |
| Environment config | python-decouple |
| Task queue (optional) | Celery + Redis |
| Image handling | Pillow |
| Production WSGI | Gunicorn |

---

## Installation

### 1. Clone or download the project

```bash
git clone <repository-url> SSELabTrack
cd SSELabTrack
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the sample environment file and edit it for your setup:

```bash
cp .env.example .env
```

Open `.env` and set at minimum `SECRET_KEY`. All other values have sensible defaults for local development (see [Sample .env Configuration](#sample-env-configuration) below).

### 5. Run database migrations

```bash
python3 manage.py migrate
```

### 6. Load sample data (recommended for development)

```bash
python3 manage.py seed_data
```

This creates an admin account, 5 member accounts, 7 equipment categories, 5 locations, 12 equipment items, 1 kit, 1 project, and 8 consumable items.

### 7. (Optional) Create your own superuser

```bash
python3 manage.py createsuperuser
```

### 8. Start the development server

```bash
python3 manage.py runserver
```

Open http://127.0.0.1:8000 in your browser.

---

## Default Credentials (after `seed_data`)

| Role | Email | Password |
|---|---|---|
| Admin | admin@sselabtrack.local | admin123 |
| Member | alice@lab.local | member123 |
| Member | bob@lab.local | member123 |
| Member | carol@lab.local | member123 |
| Member | david@lab.local | member123 |
| Member | eve@lab.local | member123 |

> **Important:** Change all passwords before deploying to any non-local environment.

The Django admin panel is available at http://127.0.0.1:8000/admin/ using the admin credentials above.

---

## URL Structure / Navigation Guide

| URL | Description |
|---|---|
| `/` | Redirects to `/dashboard/` |
| `/dashboard/` | Home screen with summary metrics |
| `/accounts/login/` | Login page |
| `/accounts/register/` | New user registration |
| `/accounts/profile/` | View and edit your profile |
| `/equipment/` | Equipment list and search |
| `/equipment/<id>/` | Equipment detail and lifecycle history |
| `/borrowing/` | Active and past borrows |
| `/borrowing/checkout/<id>/` | Check out an equipment item |
| `/reservations/` | Upcoming and past reservations |
| `/reservations/create/` | Create a new reservation |
| `/kits/` | Lab kits list |
| `/kits/<id>/` | Kit detail and borrow |
| `/projects/` | Projects list |
| `/projects/<id>/` | Project detail and members |
| `/consumables/` | Consumables inventory |
| `/incidents/` | Incident reports |
| `/notifications/` | In-app notifications |
| `/activity/` | System-wide activity log |
| `/admin/` | Django admin panel (staff only) |

---

## App Structure Overview

```
SSELabTrack/
├── apps/
│   ├── accounts/          # CustomUser model, authentication, profiles
│   │   └── management/
│   │       └── commands/
│   │           └── seed_data.py   # Development data seeder
│   ├── activity/          # Audit trail / activity log
│   ├── borrowing/         # Equipment check-out and check-in
│   ├── consumables/       # Consumable stock and usage logs
│   ├── dashboard/         # Home screen and summary views
│   ├── equipment/         # Equipment, categories, locations, lifecycle
│   ├── incidents/         # Incident and maintenance reports
│   ├── kits/              # Equipment bundle kits
│   ├── notifications/     # In-app notification system
│   ├── projects/          # Projects and project membership
│   └── reservations/      # Equipment reservation calendar
├── config/
│   ├── settings.py        # Django settings (reads from .env)
│   ├── urls.py            # Root URL configuration
│   └── wsgi.py
├── static/                # Project-level static assets
├── templates/             # Project-level HTML templates
├── manage.py
├── requirements.txt
└── .env                   # Local environment config (not committed)
```

---

## Sample .env Configuration

Create a file named `.env` in the project root with the following content. Values shown are suitable for local development.

```dotenv
# Django core
SECRET_KEY=django-insecure-replace-this-with-a-long-random-string
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database — leave unset to use the default SQLite file.
# Uncomment and fill in to use PostgreSQL instead:
# DB_NAME=sselabtrack
# DB_USER=postgres
# DB_PASSWORD=yourpassword
# DB_HOST=localhost
# DB_PORT=5432

# Email — console backend is active by default (prints to terminal).
# Fill in SMTP credentials to send real emails:
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_HOST_USER=you@example.com
# EMAIL_HOST_PASSWORD=your-app-password

# Redis / Celery (only needed if you enable background tasks)
# REDIS_URL=redis://localhost:6379/0

# Logging level (DEBUG, INFO, WARNING, ERROR)
DJANGO_LOG_LEVEL=INFO
```

---

## Running in Production

1. Set `DEBUG=False` in `.env`.
2. Set a strong, unique `SECRET_KEY`.
3. Configure a PostgreSQL database and set the `DB_*` variables.
4. Set `ALLOWED_HOSTS` to your domain.
5. Run `python3 manage.py collectstatic`.
6. Serve with Gunicorn behind a reverse proxy (e.g., Nginx):

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

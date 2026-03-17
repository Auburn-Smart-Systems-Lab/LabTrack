# LabTrack

A full-featured lab equipment management system built with Django 4.2. LabTrack lets a lab track every piece of equipment it owns — from initial inventory through borrowing, reservations, incidents, and maintenance — with role-based access for admins and members.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start (Docker)](#quick-start-docker)
- [Local Development (no Docker)](#local-development-no-docker)
- [Environment Variables](#environment-variables)
- [Application Modules](#application-modules)
- [User Roles](#user-roles)
- [Admin Guide](#admin-guide)
- [Deployment Notes](#deployment-notes)
- [Troubleshooting](#troubleshooting)

---

## Features

| Module | Capabilities |
|---|---|
| **Equipment** | Add, edit, deactivate equipment; attach categories and locations; track status |
| **Borrowing** | Request, approve/reject, and return individual items or kits; return requires owner confirmation; overdue alerts |
| **Reservations** | Time-bound reservations auto-confirmed on creation; requester submits return, owner confirms; waitlist with automatic notification |
| **Kits** | Personal equipment bundles; optionally shared with all members; per-owner return approval for kit returns |
| **Consumables** | Track consumable stock, record usage, restock, and get low-stock alerts |
| **Incidents** | Report incidents against equipment; assign investigators; resolve with status transitions; maintenance scheduling |
| **Projects** | Create projects, manage membership and roles |
| **Notifications** | In-app notifications with links to related objects; mark individual or all as read |
| **Activity Log** | Immutable audit trail of every significant action across all modules |
| **Accounts** | Custom user model; admin assigns roles; members edit their own profile and change password |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 4.2, Python 3.11 |
| Database | PostgreSQL 15 (production) · SQLite (development) |
| Cache / Queue | Redis 7, Celery 5 |
| Frontend | Tailwind CSS (CDN), vanilla JS |
| Static files | WhiteNoise |
| Web server | Gunicorn + Nginx |
| Container | Docker, Docker Compose |

---

## Quick Start (Docker)

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) ≥ 24
- [Docker Compose](https://docs.docker.com/compose/) v2 (bundled with Docker Desktop)

### 1. Clone the repository

```bash
git clone <repo-url>
cd LabTrack
```

### 2. Create your environment file

```bash
cp .env.example .env
```

Open `.env` and set at minimum:

```env
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(50))">
DB_PASSWORD=a-strong-database-password
```

Everything else can stay at its default for a first run.

### 3. Build and start

```bash
docker compose up --build -d
```

This starts four containers:

| Container | Role |
|---|---|
| `db` | PostgreSQL 15 |
| `redis` | Redis 7 |
| `web` | Django + Gunicorn (port 8000, internal) |
| `nginx` | Reverse proxy (port 80, public) |

Migrations and `collectstatic` run automatically on first start.

### 4. Create the first admin user

```bash
docker compose exec web python manage.py createsuperuser
```

### 5. Open the app

Navigate to **http://localhost** in your browser.
The Django admin is at **http://localhost/admin/**.

### Useful commands

```bash
# View logs
docker compose logs -f web

# Run a management command
docker compose exec web python manage.py <command>

# Open a Django shell
docker compose exec web python manage.py shell

# Stop everything
docker compose down

# Stop and delete all data volumes (full reset)
docker compose down -v
```

---

## Local Development (no Docker)

### Prerequisites

- Python 3.11+

### 1. Create a virtual environment

```bash
python -m venv env
source env/bin/activate          # Windows: env\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

For local development set:

```env
DEBUG=True
SECRET_KEY=any-local-dev-key
# Leave DB_HOST blank — SQLite is used automatically
```

### 3. Run migrations and start

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open **http://127.0.0.1:8000**.

### Development with Docker (hot-reload)

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Mounts source code into the container and uses Django's dev server — code changes reflect immediately without rebuilding.

---

## Environment Variables

All variables are read from `.env` via `python-decouple`. None are mandatory when using SQLite in development.

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | insecure default | Django secret key. **Change in production.** |
| `DEBUG` | `True` | Set to `False` in production. |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated list of allowed hostnames. |
| `DB_HOST` | _(empty)_ | PostgreSQL host. Leave blank to use SQLite. |
| `DB_PORT` | `5432` | PostgreSQL port. |
| `DB_NAME` | `labtrack` | PostgreSQL database name. |
| `DB_USER` | `labtrack` | PostgreSQL user. |
| `DB_PASSWORD` | _(empty)_ | PostgreSQL password. |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL (Celery broker). |
| `EMAIL_HOST` | `smtp.gmail.com` | SMTP server. Leave unset to log emails to console. |
| `EMAIL_PORT` | `587` | SMTP port. |
| `EMAIL_HOST_USER` | _(empty)_ | SMTP username. |
| `EMAIL_HOST_PASSWORD` | _(empty)_ | SMTP password or app password. |
| `GUNICORN_WORKERS` | `3` | Number of Gunicorn worker processes. |
| `GUNICORN_TIMEOUT` | `120` | Gunicorn worker timeout in seconds. |
| `NGINX_PORT` | `80` | Host port Nginx listens on. |
| `DJANGO_LOG_LEVEL` | `INFO` | Django logging level. |

---

## Application Modules

### Accounts (`/accounts/`)

Handles authentication and user management.

- **Login / Logout** — standard session auth at `/accounts/login/`
- **Profile** — members edit name, contact details, bio, and profile photo
- **Password change** — available from the profile page under "Change Password"
- **Role assignment** — admins assign `ADMIN` or `MEMBER` roles to users from `/accounts/members/`
- **Custom user model** — `apps.accounts.CustomUser` extends `AbstractUser` with a `role` field and a `full_name` property

### Equipment (`/equipment/`)

Central inventory of all lab equipment.

- **Equipment list** — searchable and filterable by status, category, location
- **Equipment detail** — full borrow/reservation history, current borrower, linked incidents
- **Categories & Locations** — any authenticated member can add new categories and locations inline
- **Status values** — `Available`, `In Use`, `Under Maintenance`, `Retired`
- **Images** — equipment photos are stored in `media/equipment/`

### Borrowing (`/borrowing/`)

Manages check-out and check-in.

- **Borrow request** — member picks equipment or kit and a due date; admin or equipment owner approves or rejects
- **Return flow** — member submits return with condition (`Good`, `Damaged`, etc.) and notes; owner then confirms receipt
- **Kit returns** — each distinct equipment owner inside the kit must confirm their own items via the return queue; only when all confirm does the borrow close
- **Overdue tracking** — items past their due date are flagged `OVERDUE`; borrower and admins notified
- **Return queue** (`/borrowing/return-queue/`) — owners see all pending returns awaiting their confirmation, split between single-item returns and kit items

Borrow status lifecycle:
```
PENDING → APPROVED → ACTIVE → RETURN_PENDING → RETURNED
                  ↘ REJECTED
                             ↘ OVERDUE
```

### Reservations (`/reservations/`)

Time-bound reservations for future use.

- **Auto-confirmation** — reservations are confirmed immediately on creation
- **Calendar view** (`/reservations/calendar/`) — full-page calendar of all confirmed reservations
- **Return flow** — when the reservation period ends, the requester submits a return; the equipment/kit owner confirms
- **Waitlist** — users join the waitlist for a specific item; when a confirmed reservation is cancelled the next person in queue is notified

Reservation status lifecycle:
```
CONFIRMED → RETURN_PENDING → RETURNED
          ↘ CANCELLED
          ↘ EXPIRED
          ↘ COMPLETED
```

### Kits (`/kits/`)

Reusable bundles of equipment.

- **Personal kits** — every member creates, edits, and deletes their own kits; only visible to themselves unless shared
- **Shared kits** — enable "Share with all members" to make the kit publicly borrowable; appears in the "Shared Kits" section for everyone
- **Kit items** — add/remove individual equipment with optional quantity
- **Per-owner confirmation** — returning a kit creates one `KitItemReturnApproval` record per distinct equipment owner; the borrow closes only when all owners have confirmed

### Consumables (`/consumables/`)

Tracks non-returnable supplies.

- **Stock management** — current quantity, unit, and minimum threshold per item
- **Usage log** — record consumption events with amounts and notes
- **Restock** — add incoming stock
- **Low stock list** — items at or below their threshold are listed under `/consumables/low-stock/`

### Incidents (`/incidents/`)

Equipment fault and incident management.

- **Report incident** — any member reports an issue against a piece of equipment with title, description, and severity
- **Assignment** — reporter, equipment owner, or admin assigns an investigator; status auto-transitions to `Investigating`
- **Status flow** — `Open` → `Investigating` → `Resolved` → `Closed`
- **Maintenance** — link scheduled or completed maintenance records to incidents
- **Visibility** — all members can see all incidents; only reporter, assignee, or equipment owner can edit or resolve

### Projects (`/projects/`)

Light-weight project coordination.

- **Create and manage projects** — any member can create a project
- **Member roles** — Lead, Contributor, Observer
- **Project status** — Active, On Hold, Completed, Cancelled
- **Membership** — project lead (or admin) adds and removes members

### Notifications (`/notifications/`)

In-app notification system.

- **Automatically triggered** — every borrow approval/rejection, return, overdue flag, incident update, reservation change, and waitlist notification creates an in-app notification
- **Linked** — each notification includes a direct URL to the related object (e.g. `/borrowing/42/`)
- **Read state** — unread notifications are highlighted; mark individually or use "Mark All Read"
- **Badge** — live unread count in the navigation bar, loaded via `/notifications/unread-count/`

### Activity Log (`/activity/`)

Immutable audit trail.

- Every significant action (create, update, status change) across all modules is recorded with actor, timestamp, action type, and description
- Accessible to admins from the admin dashboard

---

## User Roles

| Role | What they can do |
|---|---|
| **Admin** | Everything — plus manage users/roles, view activity logs, access Django admin |
| **Member** | Full access to equipment, borrowing, reservations, kits, consumables, incidents, and projects; manage their own records |

> Roles are assigned by an Admin from **Members** (`/accounts/members/`). A newly registered user has no role until an admin assigns one.

---

## Admin Guide

### First-time setup after deployment

1. Run `createsuperuser` to create the initial admin account.
2. Log in and open **Admin → Members** to assign the `ADMIN` role to yourself.
3. Add **Categories** and **Locations** from the Equipment section before adding equipment.
4. Add equipment items.
5. (Optional) Create shared kits from the Kits section.

### Inviting new users

Users self-register at `/accounts/register/` (if registration is open) or are created via the Django admin at `/admin/accounts/customuser/`. An admin must then assign them a role before they can use the system.

### Managing members

- Go to **Members** (`/accounts/members/`)
- Click a member to view their profile and change their role
- Deactivate a user to prevent login without deleting their records

### Django admin panel

Available at `/admin/` for direct database inspection and bulk operations. Recommended only for recovery scenarios.

---

## Deployment Notes

### Production checklist

- [ ] `DEBUG=False`
- [ ] Strong unique `SECRET_KEY` (50+ characters)
- [ ] `ALLOWED_HOSTS` set to your domain(s)
- [ ] PostgreSQL configured with a strong password
- [ ] SMTP configured if email notifications are needed
- [ ] Nginx is the only publicly exposed port

### HTTPS / TLS

To add HTTPS, extend `nginx/nginx.conf` with a port-443 server block. With Certbot:

```bash
# Install certbot in the nginx container or use a standalone certbot container
docker compose exec nginx certbot --nginx -d yourdomain.com
```

Alternatively, place Caddy or Traefik in front of the Nginx container for automatic TLS.

### Scaling Gunicorn workers

Recommended formula: `(2 × CPU cores) + 1`. Set in `.env`:

```env
GUNICORN_WORKERS=5
```

### Database backups

```bash
# Create a backup
docker compose exec db pg_dump -U labtrack labtrack > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
docker compose exec -T db psql -U labtrack labtrack < backup_20250101_120000.sql
```

Also back up the `media_data` Docker volume (user-uploaded images):

```bash
docker run --rm \
  -v labtrack_media_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/media_backup.tar.gz /data
```

---

## Troubleshooting

### Container exits immediately / migrations fail

```bash
docker compose logs web
```

**Common causes:**
- `DB_HOST` is set but the database isn't ready — the entrypoint retries for 30 seconds. If PostgreSQL is slow to start, run `docker compose restart web`.
- Wrong `DB_PASSWORD` — verify it matches what is set in both `.env` and the `db` service.

### Static files return 404

```bash
docker compose exec web python manage.py collectstatic --noinput
docker compose restart nginx
```

### "CSRF verification failed" in production

Ensure `ALLOWED_HOSTS` includes your actual domain and that requests reach Django with the correct `Host` header. If behind a load balancer, also set:

```env
# In .env
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### Full reset (development)

```bash
docker compose down -v          # removes all volumes including the database
docker compose up -d            # fresh start; migrations run automatically
docker compose exec web python manage.py createsuperuser
```

### Check container status

```bash
docker compose ps
docker compose logs --tail=50 web
```

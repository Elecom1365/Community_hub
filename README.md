# Community Hub - Non-Profit Coordination Platform

A Django web application prototype for coordinating donations, volunteers, shifts, tasks, fundraising campaigns and urgent resource needs for a small non-profit organisation.

## Included functionality

- Login, logout and volunteer registration
- Administrator and volunteer roles
- Organisation membership and volunteer profile management
- Financial and in-kind donation records
- PDF donation receipts
- Fundraising campaigns and donation totals
- Shift creation, volunteer booking, capacity checks and booking cancellation
- Task creation, assignment and status updates
- Urgent resource needs board
- Dashboard, CSV report export and member role management
- Django admin interface
- Automated workflow and permission tests
- Synthetic demo data command

## Requirements

- Python 3.11 or later
- For the simplest local run, SQLite is used by default and PostgreSQL is not required
- PostgreSQL 15 or later if you want to run with PostgreSQL

## Windows setup using SQLite

1. Extract the ZIP to a folder such as `C:\Projects\community-hub`.
2. Open PowerShell in that folder.
3. Create a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

4. If PowerShell blocks environment activation, use this command in the current PowerShell window and activate again:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\.venv\Scripts\Activate.ps1
   ```

5. Install packages:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

6. Copy `.env.example` to `.env`. For a local SQLite run, keep `DB_ENGINE=sqlite`. Replace `SECRET_KEY` with a long random value before exposing the app to any network.
7. Apply database migrations:

   ```powershell
   python manage.py makemigrations core
   python manage.py migrate
   ```

8. Create a superuser if you want a separate administrator account:

   ```powershell
   python manage.py createsuperuser
   ```

9. Load synthetic demonstration records:

   ```powershell
   python manage.py seed_demo
   ```

10. Start the development server:

   ```powershell
   python manage.py runserver
   ```

11. Open `http://127.0.0.1:8000/` in your browser.

## Demo accounts

After running `python manage.py seed_demo`:

- Administrator: `demo-admin` / `ChangeMe123!`
- Volunteer: `demo-volunteer` / `ChangeMe123!`

These are demonstration credentials only. Do not use them on an internet-facing deployment or with real personal information. Change or delete these accounts before deployment.

## PostgreSQL configuration

1. Install PostgreSQL and create a database, for example `nonprofit_platform`.
2. Copy `.env.example` to `.env` and set:

   ```text
   DB_ENGINE=postgres
   DB_NAME=nonprofit_platform
   DB_USER=postgres
   DB_PASSWORD=your-local-database-password
   DB_HOST=127.0.0.1
   DB_PORT=5432
   ```

3. Run `python manage.py migrate`, `python manage.py seed_demo`, then `python manage.py runserver`.

## Run checks and tests

```powershell
python manage.py check
python manage.py test
```

The test suite checks dashboard access, donation recording, role restrictions and shift booking. Additional manual checks are still needed for the full feature set, accessibility, browser compatibility, security configuration and deployment environment.

## Application URLs

- `/` — Landing page
- `/login/` — Sign in
- `/signup/` — Volunteer registration
- `/dashboard/` — Dashboard
- `/donations/` — Donation records and receipt downloads (administrator)
- `/campaigns/` — Fundraising campaigns (administrator)
- `/shifts/` — Shifts and bookings
- `/tasks/` — Tasks and assignments
- `/needs/` — Urgent resource needs
- `/reports/` — Reports and CSV export (administrator)
- `/members/` — Organisation roles (administrator)
- `/profile/` — Volunteer profile
- `/admin/` — Django administration
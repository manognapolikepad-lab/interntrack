# InternTrack

InternTrack is a Django application for discovering internships, hackathons, workshops, and technical events, then keeping personal applications and deadlines organized in one place.

## Features

- Student registration, authentication, profile, skills, and education details.
- Opportunity discovery with search, type/location filters, sorting, pagination, and expired deadline labels.
- Save opportunities and track application status, date applied, and personal notes.
- Dashboard metrics, application status chart, recent activity, and upcoming deadlines.
- Django Admin management for opportunities, profiles, saved opportunities, and applications.
- SQLite for local development, with PostgreSQL selected through environment variables.

## Run locally

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` to explore the app and `http://127.0.0.1:8000/admin/` to manage listings. Create opportunity listings in Django Admin; the discovery page is empty until listings are added.

To load the included sample listings into a local database, run:

```bash
python manage.py loaddata sample_opportunities
```

The fixture uses fictional organizations and `example.com` application links. Alternatively, add and edit opportunities in Django Admin; the required fields and optional deadline/application URL are included in the listing form.

## Configuration

The defaults are intended for local development. Set the following environment variables for deployment:

- `DJANGO_SECRET_KEY`: a strong, private Django secret.
- `DJANGO_DEBUG=0`: disable debug mode.
- `DJANGO_ALLOWED_HOSTS`: comma-separated hostnames.
- `DB_ENGINE=postgresql`: select PostgreSQL instead of SQLite.
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`: PostgreSQL connection settings.

Set `DB_ENGINE=postgresql` only after provisioning a PostgreSQL database. The `psycopg` driver is included in `requirements.txt`.

## Validation

```bash
python manage.py check
python manage.py test
```

## Interface assets

The templates use Bootstrap 5, Chart.js, and Google Fonts through their CDNs; custom styling lives in `static/css/site.css`.
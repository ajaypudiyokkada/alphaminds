# AlphaMinds

AlphaMinds is a sports mental-performance and cognitive assessment platform, with a Django backend and an Expo React Native athlete app.

## Folder layout

```
backend/   Django backend + admin (manage.py, apps: athletes, assessments, kpis, ...)
mobile/    Expo React Native athlete app
docs/      Architecture and project overview documents
```

## Setup

Each side reads its configuration from a `.env` file that is not committed. Copy the example and fill in your values:

```bash
cp backend/.env.example backend/.env   # SECRET_KEY, DB_*, ALLOWED_HOSTS, CORS, JWT lifetimes
cp mobile/.env.example mobile/.env     # EXPO_PUBLIC_API_URL=http://<your-pc-ip>:8000/api/v1
```

(On Windows PowerShell: `Copy-Item backend/.env.example backend/.env`.)
## Running the backend

```bash
cd backend
pip install -r requirements.txt
python manage.py runserver
```

## Run with Docker

Requires Docker with Compose. The database is PostgreSQL 16.

```bash
cp backend/.env.example backend/.env      # set SECRET_KEY, DB_NAME, DB_USER, DB_PASSWORD
docker compose --env-file backend/.env up -d --build
docker compose ps                         # db should be "healthy", backend "running"
```

The backend container runs `migrate` on start and serves on http://localhost:8000 (gunicorn + WhiteNoise for static files). To load an existing data export:

```bash
docker compose exec backend python manage.py loaddata /tmp/mysql_dump.json   # after docker cp backup/mysql_dump.json <container>:/tmp/
```

To run Django outside Docker against the Postgres container, keep `DB_HOST=localhost` in `backend/.env`. `docker compose down` stops everything; the data persists in the `pgdata` volume.
## Running the mobile app

```bash
cd mobile
npm install
npm start          # expo start
# or: npm run android | npm run ios | npm run web
```

# AlphaMinds

AlphaMinds is a sports mental-performance and cognitive assessment platform, with a Django backend and an Expo React Native athlete app.

## Folder layout

```
backend/   Django backend + admin (manage.py, apps: athletes, assessments, kpis, ...)
mobile/    Expo React Native athlete app
docs/      Architecture and project overview documents
```

## Local setup (MySQL + runserver + expo start)

Local development uses MySQL. Each side reads its configuration from a `.env` file that is not committed:

```bash
cp backend/.env.example backend/.env   # SECRET_KEY, DB_* (MySQL), ALLOWED_HOSTS, CORS, JWT lifetimes
cp mobile/.env.example mobile/.env     # EXPO_PUBLIC_API_URL=http://<your-pc-ip>:8000/api/v1
```

(On Windows PowerShell: `Copy-Item backend/.env.example backend/.env`.)

Backend (needs a reachable MySQL server matching `backend/.env`):

```bash
cd backend
pip install -r requirements.txt
python manage.py runserver
```

Mobile app:

```bash
cd mobile
npm install
npm start          # expo start
# or: npm run android | npm run ios | npm run web
```

## Deploy (server, Docker + Postgres)

The server runs the backend in Docker against PostgreSQL 16. Docker and Postgres are not used for local development. These files have not been run yet; validate them at the first deploy.

```bash
cp backend/.env.example backend/.env      # use the PostgreSQL block: DB_ENGINE, DB_NAME, DB_USER, DB_PASSWORD, plus SECRET_KEY, DEBUG=False
docker compose --env-file backend/.env up -d --build
docker compose ps                         # db should be "healthy", backend "running"
```

The backend container runs `migrate` on start and serves on port 8000 (gunicorn + WhiteNoise for static files). Data persists in the `pgdata` volume.

`backup/mysql_dump.json` (a local, gitignored export of the MySQL data) gets loaded into Postgres on the server. Upload it to the server, then:

```bash
docker compose cp backup/mysql_dump.json backend:/tmp/mysql_dump.json
docker compose exec backend python manage.py loaddata /tmp/mysql_dump.json
```
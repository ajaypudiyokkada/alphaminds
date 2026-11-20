# AlphaMinds — production deploy

Stack: **nginx (host, TLS) → 127.0.0.1:8010 → gunicorn (Docker) → PostgreSQL (Docker)**.
Static files (landing CSS/JS/images, branding, favicons, admin) are served by **WhiteNoise inside the backend container**; nginx only proxies. Nothing else is published: the DB has no host port.

Docker project name `alphaminds`; containers `alphaminds_backend` / `alphaminds_db`; volume `alphaminds_pgdata`; network `alphaminds_internal`.

Replace `example.com` and `/srv/alphaminds` with your values.

## 0. Prerequisites

```bash
docker --version && docker compose version
sudo nginx -v && certbot --version
# the host port must be free (change it in docker-compose.yml AND the nginx config if not)
sudo ss -ltnp | grep ':8010' || echo "8010 free"
```

DNS: an `A` record for `example.com` (and `www`) pointing at the server.

## 1. Clone

```bash
sudo mkdir -p /srv/alphaminds && sudo chown $USER /srv/alphaminds
git clone https://github.com/ajaypudiyokkada/alphaminds.git /srv/alphaminds
cd /srv/alphaminds
git log --oneline -1        # confirm you are on main
```

## 2. Environment file

```bash
cp backend/.env.example backend/.env
python3 -c "import secrets; print(secrets.token_urlsafe(64))"   # use as SECRET_KEY
nano backend/.env
chmod 600 backend/.env
```

Set at least:

```
SECRET_KEY=<generated above>
DEBUG=False
ALLOWED_HOSTS=example.com,www.example.com
CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com
DB_ENGINE=django.db.backends.postgresql
DB_NAME=alphaminds
DB_USER=alphaminds
DB_PASSWORD=<new strong password — not the one used in development>
CORS_ALLOWED_ORIGINS=https://example.com
CORS_ALLOW_ALL_ORIGINS=False
JWT_ACCESS_LIFETIME_MINUTES=60
JWT_REFRESH_LIFETIME_DAYS=7
```

`DB_HOST`/`DB_PORT` are overridden by compose (`db:5432`). With `DEBUG=False`, session/CSRF cookies are `Secure` and `X-Forwarded-Proto` is trusted, so the site must be reached over HTTPS (step 8).

## 3. Start the stack

```bash
cd /srv/alphaminds
docker compose --env-file backend/.env up -d --build
docker compose ps
docker compose logs -f backend      # Ctrl-C when you see gunicorn "Listening at"
curl -sI http://127.0.0.1:8010/ | head -1
```

The backend command runs `migrate --noinput` on every start, then gunicorn. `collectstatic` already ran during the image build (see step 6).

## 4. Load the data (`backup/mysql_dump.json`)

The dump is **not in git** (`backup/` is ignored and excluded from the image) and it contains password hashes. Copy it from your machine:

```bash
# on your PC (from the repo root)
scp backend/backup/mysql_dump.json user@SERVER:/tmp/mysql_dump.json
```

```bash
# on the server
cd /srv/alphaminds
docker cp /tmp/mysql_dump.json alphaminds_backend:/tmp/mysql_dump.json
docker compose exec backend python manage.py loaddata /tmp/mysql_dump.json
# expected: Installed 595 object(s) from 1 fixture(s)

docker compose exec backend rm /tmp/mysql_dump.json
shred -u /tmp/mysql_dump.json
```

Load into a freshly migrated, empty database only. If `loaddata` fails midway, nothing is kept (it runs in one transaction) — fix the error and re-run.

## 5. Admin user

The dump already contains 4 users. Create an extra superuser only if you need one:

```bash
docker compose exec backend python manage.py createsuperuser
```

After loading, rotate credentials carried over from development:

```bash
docker compose exec backend python manage.py changepassword player.a
docker compose exec backend python manage.py changepassword <your-admin-username>
```

## 6. Static files

Static files are collected into the image at build time (`RUN python manage.py collectstatic` in `backend/Dockerfile`) and served by WhiteNoise with hashed, compressed names. To re-run manually, or after changing static files without rebuilding:

```bash
docker compose exec backend python manage.py collectstatic --noinput
```

Normally just rebuild: `docker compose --env-file backend/.env up -d --build`.

Verify:

```bash
curl -sI http://127.0.0.1:8010/static/landing/branding/favicon.ico | head -1     # 200
curl -s  http://127.0.0.1:8010/ | grep -o '/static/landing/css/[^"]*'            # hashed overrides/main css
```

## 7. nginx site (HTTP first; certbot adds TLS)

`/etc/nginx/sites-available/alphaminds`:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name example.com www.example.com;

    client_max_body_size 10m;

    location / {
        proxy_pass http://127.0.0.1:8010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/alphaminds /etc/nginx/sites-enabled/alphaminds
sudo nginx -t && sudo systemctl reload nginx
```

## 8. HTTPS (certbot)

```bash
sudo certbot --nginx -d example.com -d www.example.com --redirect
sudo certbot renew --dry-run
```

Certbot adds the `listen 443 ssl` block and the 80→443 redirect, keeping the `proxy_set_header` lines (so `X-Forwarded-Proto https` reaches Django).

## 9. Smoke test

```bash
curl -sI https://example.com/ | head -1                  # 200
curl -sI http://example.com/  | head -2                  # 301 -> https
curl -sI https://example.com/static/landing/css/main.css | head -1
```

In a browser: landing page renders with the logo and favicon, **Enquire Now** reaches the login page, login works (needs `CSRF_TRUSTED_ORIGINS`), `/admin/` opens. Mobile app: point `EXPO_PUBLIC_API_URL` (or the app's API base) at `https://example.com/api/v1`.

## Updating later

```bash
cd /srv/alphaminds && git pull
docker compose --env-file backend/.env up -d --build      # rebuilds, re-collects static, migrates
```

## Operations

```bash
docker compose logs --tail=100 backend
docker compose exec db psql -U alphaminds -d alphaminds
# backup
docker compose exec -T db pg_dump -U alphaminds alphaminds | gzip > ~/alphaminds-$(date +%F).sql.gz
docker compose down            # stop (data kept in volume alphaminds_pgdata)
```

Never run `docker compose down -v` unless you intend to delete the database.

## Optional hardening (not enabled)

- HSTS: once HTTPS is confirmed stable, add `add_header Strict-Transport-Security "max-age=31536000" always;` in the nginx 443 block (or set `SECURE_HSTS_SECONDS` in settings).
- Email uses the console backend; configure SMTP in `settings.py` before relying on password-reset or enquiry mails.

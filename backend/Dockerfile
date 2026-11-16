FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
# mysqlclient is only needed for the legacy MySQL export; skip it in the image
# (it needs system build libraries). Everything else installs from wheels.
RUN grep -v '^mysqlclient' requirements.txt > requirements.docker.txt \
    && pip install --no-cache-dir -r requirements.docker.txt

COPY . .

# collectstatic needs settings to import; provide throwaway values for the build only
RUN SECRET_KEY=build-only DB_ENGINE=django.db.backends.sqlite3 DB_NAME=/tmp/build.db \
    python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "alphaminds.wsgi:application", "--bind", "0.0.0.0:8000"]
# AlphaMinds

AlphaMinds is a sports mental-performance and cognitive assessment platform, with a Django backend and an Expo React Native athlete app.

## Folder layout

```
backend/   Django backend + admin (manage.py, apps: athletes, assessments, kpis, ...)
mobile/    Expo React Native athlete app
docs/      Architecture and project overview documents
```

## Running the backend

```bash
cd backend
pip install -r requirements.txt
python manage.py runserver
```

## Running the mobile app

```bash
cd mobile
npm install
npm start          # expo start
# or: npm run android | npm run ios | npm run web
```

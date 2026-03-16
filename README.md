# TaskFlow — Full-Stack Python Web App

A production-grade task manager with user authentication, a kanban board UI, REST API, and PostgreSQL — deployed to Azure via GitHub Actions CI/CD.

---

## Features

- **User auth** — register, login, logout with bcrypt-hashed passwords
- **Kanban board** — Todo / In Progress / Done columns
- **Task management** — create, update status (click to cycle), delete
- **Priority levels** — Low / Medium / High with colour-coded badges
- **Stats dashboard** — live task counts by status
- **REST API** — full CRUD at `/api/tasks`
- **PostgreSQL** in production, SQLite for local dev

---

## Project Structure

```
taskflow/
├── .github/workflows/deploy.yml   # CI/CD pipeline
├── templates/
│   ├── index.html                 # Landing + login/register page
│   └── dashboard.html             # Kanban board
├── app.py                         # Flask app + models + API
├── test_app.py                    # Pytest test suite
└── requirements.txt
```

---

## Local Development

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app.py
# Open http://localhost:8000
```

Uses SQLite locally — no database setup needed.

---

## Azure + PostgreSQL Setup

### 1. Create Azure Database for PostgreSQL

In the Azure Portal:
- Search **Azure Database for PostgreSQL** → Create **Flexible Server**
- Note the **host**, **username**, **password**, and **database name**

### 2. Set App Service Environment Variables

In your Azure Web App → **Configuration → Application Settings**, add:

| Name | Value |
|---|---|
| `DATABASE_URL` | `postgresql://user:pass@host/dbname?sslmode=require` |
| `SECRET_KEY` | any long random string |

### 3. Set Startup Command

In **Configuration → Stack settings**:
```
gunicorn --bind=0.0.0.0:8000 app:app
```

### 4. Update deploy.yml

```yaml
AZURE_WEBAPP_NAME: your-actual-app-name
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/register` | Create account |
| POST | `/api/login` | Login |
| POST | `/api/logout` | Logout |
| GET | `/api/me` | Current user |
| GET | `/api/tasks` | List all tasks |
| POST | `/api/tasks` | Create task |
| PATCH | `/api/tasks/:id` | Update task |
| DELETE | `/api/tasks/:id` | Delete task |
| GET | `/api/stats` | Task counts |
| GET | `/health` | Health check |

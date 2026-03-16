# Azure Web App - Python + GitHub Actions

A Python Flask web app configured for deployment to Azure App Service via GitHub Actions CI/CD.

---

## Project Structure

```
.
├── .github/
│   └── workflows/
│       └── deploy.yml        # CI/CD pipeline
├── app/
│   └── app.py                # Flask application
├── tests/
│   └── test_app.py           # Pytest tests
├── requirements.txt
├── startup.txt               # Azure startup command
└── .gitignore
```

---

## Local Development

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python app/app.py
# App available at http://localhost:8000
```

---

## Azure Setup

### 1. Create an Azure Web App

In the [Azure Portal](https://portal.azure.com):
- Create a new **Web App**
- Runtime: **Python 3.12**
- OS: **Linux**

Or with the Azure CLI:
```bash
az webapp create \
  --resource-group <YOUR_RG> \
  --plan <YOUR_PLAN> \
  --name <YOUR_APP_NAME> \
  --runtime "PYTHON:3.12"
```

### 2. Set the Startup Command

In Azure Portal → Your Web App → **Configuration → General Settings**:

```
gunicorn --bind=0.0.0.0:8000 app.app:app
```

### 3. Add the Publish Profile to GitHub Secrets

1. In Azure Portal → Your Web App → **Deployment Center** → **Manage publish profile** → Download it
2. In your GitHub repo → **Settings → Secrets and variables → Actions**
3. Create a new secret named:
   ```
   AZURE_WEBAPP_PUBLISH_PROFILE
   ```
   Paste the full XML content of the downloaded publish profile.

### 4. Update the workflow

In `.github/workflows/deploy.yml`, replace:
```yaml
AZURE_WEBAPP_NAME: your-app-name   # ← your actual app name here
```

---

## CI/CD Pipeline

| Trigger | Jobs |
|---|---|
| Push to `main` | ✅ Test → ✅ Deploy |
| Pull Request to `main` | ✅ Test only (no deploy) |

---

## Endpoints

| Route | Description |
|---|---|
| `GET /` | Returns a JSON hello message |
| `GET /health` | Health check — returns `{"status": "healthy"}` |

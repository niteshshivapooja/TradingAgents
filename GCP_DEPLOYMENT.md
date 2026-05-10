# Deploying TradingAgents Telegram Bot on GCP Cloud Run

This guide documents the working deployment process for the TradingAgents Telegram Bot on Google Cloud Run.

> **Note:** Replace all `YOUR_*` placeholders below with your actual values before running any commands.

---

## Prerequisites
- A Google Cloud Project with billing enabled.
- Use [GCP Cloud Shell](https://shell.cloud.google.com/) — it has `gcloud`, Docker, and Git pre-installed. 
- A fork of the repository on GitHub (so you can push your own changes).

---

## One-Time Setup

### 1. Authenticate and Configure GCP (Cloud Shell)
```bash
gcloud config set project YOUR_PROJECT_ID
```

### 2. Enable Required APIs
```bash
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com docs.googleapis.com drive.googleapis.com secretmanager.googleapis.com
```

### 3. Create Artifact Registry Repository
```bash
gcloud artifacts repositories create tradingagents-repo \
    --repository-format=docker \
    --location=us-central1 \
    --description="Docker repository for TradingAgents"

gcloud auth configure-docker us-central1-docker.pkg.dev
```

### 4. Clone Your Fork (Cloud Shell)
```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/TradingAgents.git
cd TradingAgents
```

### 5. Set Up Google Docs Service Account
```bash
# Create service account
gcloud iam service-accounts create gdocs-uploader \
    --description="Service account for uploading to Google Docs" \
    --display-name="GDocs Uploader"

# Generate JSON key
gcloud iam service-accounts keys create credentials.json \
    --iam-account=gdocs-uploader@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Store in Secret Manager
gcloud secrets create gdocs-credentials --data-file=credentials.json

# Grant Cloud Run access to the secret
PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)")
gcloud secrets add-iam-policy-binding gdocs-credentials \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

---

## Deploy / Update Workflow

Every time you make code changes and want to redeploy, follow these steps:

### Step 1: Commit and Push Changes (Local Machine)
```bash
# From /Users/niteshshivapooja/Github/TradingAgents
git add .
git commit -m "Your description of changes"
git push origin main
```

### Step 2: Pull Latest Changes (Cloud Shell)
```bash
cd TradingAgents
git pull origin main
```

### Step 3: Build a New Docker Image (Cloud Shell)
> **Important:** Increment the version tag each time (`:v2`, `:v3`, `:v4`, etc.) to ensure Cloud Run always uses the new image.

```bash
docker build --no-cache -f Dockerfile.bot \
    -t us-central1-docker.pkg.dev/YOUR_PROJECT_ID/tradingagents-repo/telegram-bot:v3 .
```

### Step 4: Push the Image (Cloud Shell)
```bash
docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/tradingagents-repo/telegram-bot:v3
```

### Step 5: Deploy to Cloud Run (Cloud Shell)
> **Important:** Update the `:v3` tag to match the tag you used in the build step above.

```bash
gcloud run deploy tradingagents-bot \
    --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/tradingagents-repo/telegram-bot:v3 \
    --region us-central1 \
    --allow-unauthenticated \
    --no-cpu-throttling \
    --set-env-vars TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN \
    --set-env-vars LLM_PROVIDER=google \
    --set-env-vars GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY \
    --set-env-vars DEEP_THINK_LLM=gemini-2.5-pro \
    --set-env-vars QUICK_THINK_LLM=gemini-2.5-flash \
    --set-secrets="/secrets/credentials.json=gdocs-credentials:latest" \
    --set-env-vars GOOGLE_APPLICATION_CREDENTIALS=/secrets/credentials.json \
    --set-env-vars WEBHOOK_URL=YOUR_CLOUD_RUN_SERVICE_URL \
    --memory 1024Mi \
    --cpu 1 \
    --max-instances 1
```

---

## Updating Only Environment Variables
If you only need to change an environment variable (e.g., API key) without rebuilding the image:

```bash
gcloud run services update tradingagents-bot \
    --region us-central1 \
    --update-env-vars KEY_NAME=new_value
```

---

## Service Details
| Setting | Value |
|---|---|
| **Service Name** | `tradingagents-bot` |
| **Project ID** | `YOUR_PROJECT_ID` |
| **Region** | `us-central1` |
| **Service URL** | `YOUR_CLOUD_RUN_SERVICE_URL` |
| **Deep Think Model** | `gemini-2.5-pro` |
| **Quick Think Model** | `gemini-2.5-flash` |

---

## Testing the Bot
Open Telegram and send your bot:
```
/start
/analyze NVDA 2026-01-15
```

---

## Known Issues & Fixes

### ❌ `RuntimeError: To use start_webhook, PTB must be installed via pip install "python-telegram-bot[webhooks]"`
**Fix:** Ensure `pyproject.toml` has `python-telegram-bot[webhooks]>=21.0` (not just `python-telegram-bot`). Rebuild and redeploy.

### ❌ Container fails to start / port 8080 timeout on first deploy
**Fix:** Always include `--set-env-vars WEBHOOK_URL=...` in the deploy command. Without it, the bot falls back to polling mode (no web server), and Cloud Run kills it.

### ❌ Bot starts analyzing but silently stops (Deep Think model never called, no errors)
**Fix:** This is caused by Cloud Run's default "CPU Throttling". Because the bot responds to the Telegram webhook immediately and processes the heavy LangGraph tasks in the background, Cloud Run thinks the request is done and throttles the CPU to near zero, freezing your bot mid-analysis. Ensure you have the `--no-cpu-throttling` flag in your `gcloud run deploy` command to allow background execution.

### ❌ `404 NOT_FOUND: models/gemini-3.1-flash is not found`
**Fix:** Use the correct model names: `gemini-2.5-pro` and `gemini-2.5-flash`. Update with:
```bash
gcloud run services update tradingagents-bot \
    --region us-central1 \
    --update-env-vars DEEP_THINK_LLM=gemini-2.5-pro \
    --update-env-vars QUICK_THINK_LLM=gemini-2.5-flash
```

### ❌ Redeployment still uses old code despite `git push`
**Fix:** Cloud Run pulls from the Docker image, not GitHub directly. Always run `git pull`, then `docker build`, then `docker push`, then `gcloud run deploy` in that order. Use a new version tag (`:v3`, `:v4`) to force a fresh pull.

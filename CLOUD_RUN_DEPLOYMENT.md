# Deploying TradingAgents Telegram Bot on GCP Cloud Run

This guide will walk you through deploying the TradingAgents Telegram Bot on Google Cloud Run. Cloud Run is a fully managed compute platform that automatically scales your stateless containers. It has a generous free tier and scales to zero when not in use, making it practically free for a low-traffic bot.

## Prerequisites
1. A Google Cloud Project with billing enabled (required for Cloud Run, but you stay in the free tier).
2. **Option A (Recommended):** Use [GCP Cloud Shell](https://shell.cloud.google.com/), which has `gcloud`, Docker, and Git pre-installed and is already authenticated.
3. **Option B:** Install [Google Cloud CLI (`gcloud`)](https://cloud.google.com/sdk/docs/install) and Docker on your local machine.

## 1. Authenticate and Configure GCP

**If using GCP Cloud Shell:**
You are already authenticated! Just ensure your project is set correctly and clone the repository:
```bash
gcloud config set project YOUR_PROJECT_ID
git clone https://github.com/TauricResearch/TradingAgents.git
cd TradingAgents
```

**If using your local machine:**
Open your terminal and run:
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

## 2. Enable Required APIs
Enable Cloud Run, Artifact Registry, and Cloud Build APIs:
```bash
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
```

## 3. Create an Artifact Registry Repository
Create a repository to store your Docker images:
```bash
gcloud artifacts repositories create tradingagents-repo \
    --repository-format=docker \
    --location=us-central1 \
    --description="Docker repository for TradingAgents"
```
Configure Docker to use Google Cloud credentials:
```bash
gcloud auth configure-docker us-central1-docker.pkg.dev
```

## 4. Build and Push the Docker Image
From the root of the `TradingAgents` repository, build the image using the `Dockerfile.bot`:
```bash
docker build -f Dockerfile.bot -t us-central1-docker.pkg.dev/triple-method-495107-g6/tradingagents-repo/telegram-bot:latest .
```
Push the image to Artifact Registry:
```bash
docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/tradingagents-repo/telegram-bot:latest
```

## 5. Deploy to Cloud Run (Initial Deployment)
Deploy the container to Cloud Run. We will set the `WEBHOOK_URL` in the next step once we have the generated URL.
```bash
gcloud run deploy tradingagents-bot \
    --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/tradingagents-repo/telegram-bot:latest \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars TELEGRAM_BOT_TOKEN=your_telegram_token_here \
    --set-env-vars OPENAI_API_KEY=your_openai_key_here \
    --memory 1024Mi \
    --cpu 1 \
    --max-instances 1
```
*Note: If you are using Google Docs integration, you can pass the credentials JSON content as a base64 string or use Google Secret Manager, but for simplicity, you can mount it or pass it as an env var.*

After deployment, `gcloud` will output a **Service URL** (e.g., `https://tradingagents-bot-xyz.a.run.app`).

## 6. Update the Webhook URL
Now that you have the Service URL, update the Cloud Run service to include the `WEBHOOK_URL` environment variable. This tells the bot to register itself with Telegram using this URL.
```bash
gcloud run services update tradingagents-bot \
    --region us-central1 \
    --update-env-vars WEBHOOK_URL=https://tradingagents-bot-xyz.a.run.app
```

## 7. Test the Bot
Send a message to your bot on Telegram:
```
/start
/analyze NVDA 2026-01-15
```
Cloud Run will automatically wake up, process the request, and send the response!

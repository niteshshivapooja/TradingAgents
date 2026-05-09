# Deploying TradingAgents Telegram Bot on GCP Cloud Run

This guide will walk you through deploying the TradingAgents Telegram Bot on Google Cloud Run. Cloud Run is a fully managed compute platform that automatically scales your stateless containers. It has a generous free tier and scales to zero when not in use, making it practically free for a low-traffic bot.

## Prerequisites
1. A Google Cloud Project with billing enabled (required for Cloud Run, but you stay in the free tier).
2. **Option A (Recommended):** Use [GCP Cloud Shell](https://shell.cloud.google.com/), which has `gcloud`, Docker, and Git pre-installed and is already authenticated.
3. **Option B:** Install [Google Cloud CLI (`gcloud`)](https://cloud.google.com/sdk/docs/install) and Docker on your local machine.

## 1. Authenticate and Configure GCP

**If using GCP Cloud Shell:**
You are already authenticated! Just ensure your project is set correctly. 

Before cloning, it is highly recommended to **Fork** the repository on GitHub so you can easily make custom changes and save them.
1. Go to [https://github.com/TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) and click **Fork** (leave "Copy the main branch only" checked).
2. In Cloud Shell, clone your new fork (replace `YOUR_USERNAME` with your GitHub username):
```bash
gcloud config set project YOUR_PROJECT_ID
git clone https://github.com/niteshshivapooja/TradingAgents.git
cd TradingAgents
```

3. **(Optional) Syncing Custom Changes:** If you modify the code and want to save those changes back to your GitHub fork, run:
```bash
git add .
git commit -m "Your commit message"
git push origin main
```

**If using your local machine:**
Open your terminal and run:
```bash
gcloud auth login
gcloud config set project triple-method-495107-g6
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
docker push us-central1-docker.pkg.dev/triple-method-495107-g6/tradingagents-repo/telegram-bot:latest
```

## 5. Get a Telegram Bot Token
Before deploying, you need a token to authenticate your bot with Telegram:
1. Open Telegram and search for **@BotFather**.
2. Send the command `/newbot` to BotFather.
3. Follow the prompts to choose a name and username for your bot.
4. BotFather will give you a **token** (e.g., `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`). Save this token; you will need it for the deployment step.

## 6. Set up Google Docs Integration
The bot uploads its trading reports to Google Docs. To allow this, you need a Google Service Account.

1. **Enable the required APIs:**
```bash
gcloud services enable docs.googleapis.com drive.googleapis.com secretmanager.googleapis.com
```

2. **Create a Service Account:**
```bash
gcloud iam service-accounts create gdocs-uploader \
    --description="Service account for uploading to Google Docs" \
    --display-name="GDocs Uploader"
```

3. **Generate a JSON key file:**
```bash
gcloud iam service-accounts keys create credentials.json \
    --iam-account=gdocs-uploader@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

4. **Store the key securely in Google Secret Manager:**
```bash
gcloud secrets create gdocs-credentials --data-file=credentials.json
```

5. **Grant Cloud Run access to the secret:**
```bash
# Get your project number
PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)")

# Grant the default compute service account access to the secret
gcloud secrets add-iam-policy-binding gdocs-credentials \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

## 7. Deploy to Cloud Run (Initial Deployment)
Deploy the container to Cloud Run and mount the credentials secret. We will set the `WEBHOOK_URL` in the next step once we have the generated URL.
```bash
gcloud run deploy tradingagents-bot \
    --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/tradingagents-repo/telegram-bot:latest \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars TELEGRAM_BOT_TOKEN=your_telegram_token_here \
    --set-env-vars LLM_PROVIDER=google \
    --set-env-vars GOOGLE_API_KEY=your_google_api_key_here \
    --set-env-vars DEEP_THINK_LLM=gemini-3.1-pro \
    --set-env-vars QUICK_THINK_LLM=gemini-3.1-flash \
    --set-secrets="/secrets/credentials.json=gdocs-credentials:latest" \
    --set-env-vars GOOGLE_APPLICATION_CREDENTIALS=/secrets/credentials.json \
    --memory 1024Mi \
    --cpu 1 \
    --max-instances 1
```

After deployment, `gcloud` will output a **Service URL** (e.g., `https://tradingagents-bot-xyz.a.run.app`).

## 8. Update the Webhook URL
Now that you have the Service URL, update the Cloud Run service to include the `WEBHOOK_URL` environment variable. This tells the bot to register itself with Telegram using this URL.
```bash
gcloud run services update tradingagents-bot \
    --region us-central1 \
    --update-env-vars WEBHOOK_URL=https://tradingagents-bot-xyz.a.run.app
```

## 9. Test the Bot
Send a message to your bot on Telegram:
```
/start
/analyze NVDA 2026-01-15
```
Cloud Run will automatically wake up, process the request, and send the response!

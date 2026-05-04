# Deploying TradingAgents on GCP Free Tier

This guide will walk you through deploying the TradingAgents Telegram Bot on a Google Cloud Platform (GCP) Free Tier VM.

## 1. Create a GCP VM Instance
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Navigate to **Compute Engine > VM instances**.
3. Click **Create Instance**.
4. Set the following configuration for the Free Tier:
   - **Region**: `us-central1`, `us-east1`, or `us-west1`.
   - **Machine type**: `e2-micro`.
   - **Boot disk**: Ubuntu 24.04 LTS (or similar Linux distribution), 30 GB Standard persistent disk.
5. Under **Firewall**, allow HTTP/HTTPS traffic if you plan to expose a web server (not strictly necessary for the Telegram bot).
6. Click **Create**.

## 2. Connect to the VM and Install Dependencies
1. SSH into your VM using the GCP Console.
2. Update the system and install Python 3.13 (or use the default Python 3.10+):
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y python3-pip python3-venv git
   ```

## 3. Clone the Repository
1. Clone the TradingAgents repository:
   ```bash
   git clone https://github.com/TauricResearch/TradingAgents.git
   cd TradingAgents
   ```
2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -e .
   ```

## 4. Set Up Environment Variables
1. Create a `.env` file in the root directory:
   ```bash
   cp .env.example .env
   nano .env
   ```
2. Add your LLM API keys (e.g., `OPENAI_API_KEY`).
3. Add your Telegram Bot Token:
   ```env
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   ```
4. Upload your Google Service Account JSON file to the VM and set its path:
   ```env
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/credentials.json
   ```

## 5. Run the Telegram Bot
To keep the bot running after you close the SSH session, you can use `nohup` or create a `systemd` service.

### Using `nohup`
```bash
nohup python telegram_bot.py > bot.log 2>&1 &
```

### Using `systemd` (Recommended)
1. Create a service file:
   ```bash
   sudo nano /etc/systemd/system/tradingbot.service
   ```
2. Add the following content (replace `/path/to/TradingAgents` with the actual path):
   ```ini
   [Unit]
   Description=TradingAgents Telegram Bot
   After=network.target

   [Service]
   User=your_username
   WorkingDirectory=/path/to/TradingAgents
   Environment="PATH=/path/to/TradingAgents/venv/bin"
   EnvironmentFile=/path/to/TradingAgents/.env
   ExecStart=/path/to/TradingAgents/venv/bin/python telegram_bot.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
3. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable tradingbot.service
   sudo systemctl start tradingbot.service
   ```
4. Check the status:
   ```bash
   sudo systemctl status tradingbot.service
   ```

Your bot is now running on GCP!

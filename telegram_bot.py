import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from gdocs_uploader import upload_to_gdocs

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to TradingAgents Bot!\n"
        "Use /analyze <ticker> <date> to get a trading report.\n"
        "Example: /analyze NVDA 2026-01-15"
    )

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /analyze <ticker> <date>\nExample: /analyze NVDA 2026-01-15")
        return
    
    ticker = context.args[0].upper()
    date = context.args[1]
    
    await update.message.reply_text(f"Starting analysis for {ticker} on {date}. This may take a few minutes...")
    
    try:
        ta = TradingAgentsGraph(debug=False, config=DEFAULT_CONFIG.copy())
        _, decision = ta.propagate(ticker, date)
        
        report_content = f"Trading Report for {ticker} on {date}\n\nDecision:\n{decision}"
        
        # Upload to Google Docs
        doc_url = upload_to_gdocs(f"Trading Report: {ticker} - {date}", report_content)
        
        await update.message.reply_text(f"Analysis complete!\nReport link: {doc_url}")
    except Exception as e:
        logging.error(f"Error during analysis: {e}")
        await update.message.reply_text(f"An error occurred during analysis: {e}")

if __name__ == '__main__':
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set.")
    
    app = ApplicationBuilder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyze", analyze))
    
    webhook_url = os.environ.get("WEBHOOK_URL")
    port = int(os.environ.get("PORT", 8080))
    
    if webhook_url:
        print(f"Starting Webhook on port {port} with URL {webhook_url}")
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path="webhook",
            webhook_url=f"{webhook_url}/webhook"
        )
    else:
        print("WEBHOOK_URL not set. Falling back to polling...")
        app.run_polling()

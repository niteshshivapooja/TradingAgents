import os
import asyncio
import queue
import threading
import logging
from telegram import Update, Message
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from gdocs_uploader import upload_to_gdocs

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Maps graph node names → user-friendly Telegram status messages
NODE_STATUS_MESSAGES = {
    "Market Analyst":       "📈 *Market Analyst* is gathering price & technical data...",
    "Social Analyst":       "💬 *Social Analyst* is scanning social media sentiment...",
    "News Analyst":         "📰 *News Analyst* is reading the latest news...",
    "Fundamentals Analyst": "🏦 *Fundamentals Analyst* is reviewing financial fundamentals...",
    "Bull Researcher":      "🐂 *Bull Researcher* is making the case to buy...",
    "Bear Researcher":      "🐻 *Bear Researcher* is making the case to sell...",
    "Research Manager":     "🔬 *Research Manager* is synthesizing analyst reports...",
    "Trader":               "💼 *Trader* is forming an investment plan...",
    "Aggressive Analyst":   "⚡ *Aggressive Risk Analyst* is assessing risk...",
    "Neutral Analyst":      "⚖️  *Neutral Risk Analyst* is assessing risk...",
    "Conservative Analyst": "🛡️ *Conservative Risk Analyst* is assessing risk...",
    "Portfolio Manager":    "📋 *Portfolio Manager* is making the final decision...",
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to TradingAgents Bot!\n"
        "Use /analyze <ticker> <date> to get a trading report.\n"
        "Example: /analyze NVDA 2026-01-15"
    )


async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text(
            "Usage: /analyze <ticker> <date>\nExample: /analyze NVDA 2026-01-15"
        )
        return

    ticker = context.args[0].upper()
    date = context.args[1]

    # Send an initial status message that we'll edit in-place as progress happens
    status_msg: Message = await update.message.reply_text(
        f"🚀 Starting analysis for *{ticker}* on `{date}`…\n_This may take several minutes._",
        parse_mode="Markdown",
    )

    async def update_status(text: str):
        """Edit the pinned status message in-place."""
        try:
            await status_msg.edit_text(text, parse_mode="Markdown")
        except Exception:
            pass  # Ignore no-change or rate-limit errors

    try:
        config = DEFAULT_CONFIG.copy()
        if os.environ.get("LLM_PROVIDER"):
            config["llm_provider"] = os.environ.get("LLM_PROVIDER")
        if os.environ.get("DEEP_THINK_LLM"):
            config["deep_think_llm"] = os.environ.get("DEEP_THINK_LLM")
        if os.environ.get("QUICK_THINK_LLM"):
            config["quick_think_llm"] = os.environ.get("QUICK_THINK_LLM")

        ta = TradingAgentsGraph(debug=False, config=config)

        # Resolve memory-log entries up front (mirrors internal propagate() behaviour)
        ta.ticker = ticker
        ta._resolve_pending_entries(ticker)

        past_context = ta.memory_log.get_past_context(ticker)
        init_state = ta.propagator.create_initial_state(ticker, date, past_context=past_context)
        graph_args = ta.propagator.get_graph_args()

        # ------------------------------------------------------------------ #
        # Stream the graph in a background thread (LangGraph is synchronous).
        # Each chunk is pushed onto a queue so the async event loop can pick   #
        # it up and send Telegram updates without blocking.                    #
        # ------------------------------------------------------------------ #
        chunk_queue: queue.Queue = queue.Queue()
        stream_done = threading.Event()

        def stream_worker():
            try:
                for chunk in ta.graph.stream(init_state, **graph_args):
                    chunk_queue.put(chunk)
            except Exception as exc:
                chunk_queue.put(exc)
            finally:
                stream_done.set()

        thread = threading.Thread(target=stream_worker, daemon=True)
        thread.start()

        seen_nodes: set = set()
        accumulated_state: dict = {}

        while not stream_done.is_set() or not chunk_queue.empty():
            try:
                chunk = chunk_queue.get_nowait()
            except queue.Empty:
                await asyncio.sleep(0.5)
                continue

            if isinstance(chunk, Exception):
                raise chunk

            # Each chunk is keyed by the node name that just finished
            for node_name, node_state in chunk.items():
                if isinstance(node_state, dict):
                    accumulated_state.update(node_state)
                    
                if node_name not in seen_nodes and node_name in NODE_STATUS_MESSAGES:
                    seen_nodes.add(node_name)
                    await update_status(NODE_STATUS_MESSAGES[node_name])

        thread.join()

        # ------------------------------------------------------------------ #
        # Extract the final trade decision from the accumulated state.         #
        # ------------------------------------------------------------------ #
        decision = None
        if "final_trade_decision" in accumulated_state:
            decision = ta.process_signal(accumulated_state["final_trade_decision"])

        if decision is None:
            # Fallback: run a full invoke to guarantee we have the complete state
            logging.warning("Could not extract decision from stream; falling back to invoke.")
            await update_status("📋 Finalising decision…")
            _, decision = ta.propagate(ticker, date)

        # ------------------------------------------------------------------ #
        # Upload report to Google Docs                                         #
        # ------------------------------------------------------------------ #
        await update_status("✅ Analysis complete! Uploading report to Google Docs…")

        # Build detailed report content as sections
        sections = []
        if "market_report" in accumulated_state:
            sections.append(("📈 Market Analyst Report", accumulated_state['market_report']))
        if "sentiment_report" in accumulated_state:
            sections.append(("💬 Sentiment Analyst Report", accumulated_state['sentiment_report']))
        if "news_report" in accumulated_state:
            sections.append(("📰 News Analyst Report", accumulated_state['news_report']))
        if "fundamentals_report" in accumulated_state:
            sections.append(("🏦 Fundamentals Analyst Report", accumulated_state['fundamentals_report']))

        sections.append(("🎯 Final Decision", str(decision)))

        doc_url = upload_to_gdocs(f"Trading Report: {ticker} - {date}", sections=sections)

        await update_status(
            f"✅ *Analysis complete for {ticker}!*\n\n"
            f"📄 [View Full Report]({doc_url})"
        )

    except Exception as e:
        logging.error(f"Error during analysis: {e}", exc_info=True)
        await update_status(f"❌ An error occurred during analysis:\n`{e}`")


if __name__ == '__main__':
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set.")
        
    doc_id = os.environ.get("DOCUMENT_ID")
    if not doc_id:
        raise ValueError("DOCUMENT_ID environment variable not set. Please create a Google Doc, share it with your service account, and set this variable.")

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
            webhook_url=f"{webhook_url}/webhook",
        )
    else:
        print("WEBHOOK_URL not set. Falling back to polling…")
        app.run_polling()

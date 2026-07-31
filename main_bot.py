import logging
import asyncio
import socket
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest
from src.config import TELEGRAM_BOT_TOKEN
from src.scraper import is_valid_linkedin_url
from src.pipeline import run_pipeline

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Force IPv4 resolution
old_getaddrinfo = socket.getaddrinfo
socket.getaddrinfo = lambda *args, **kwargs: [r for r in old_getaddrinfo(*args, **kwargs) if r[0] == socket.AF_INET]

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Executive CV Generator Ready!**\n\n"
        "Please send a valid **LinkedIn Job Posting URL** to generate your tailored CV and Cover Letter.\n\n"
        "📍 *Example:* `https://www.linkedin.com/jobs/view/4429205456/`",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    
    # 🛑 CRITICAL CHECK: Reject non-LinkedIn or malformed links instantly!
    if not is_valid_linkedin_url(user_input):
        await update.message.reply_text(
            "⚠️ **Invalid Link Format!**\n\n"
            "This bot strictly requires a valid LinkedIn job posting URL.\n\n"
            "📌 **Accepted Format:**\n"
            "`https://www.linkedin.com/jobs/view/<JOB_ID>/`",
            parse_mode="Markdown"
        )
        return

    status_msg = await update.message.reply_text("🚀 **Valid LinkedIn URL detected!**\n⏳ Running local Ollama pipeline...")

    try:
        metrics = await asyncio.to_thread(run_pipeline, user_input)
        summary = (
            f"✅ **Process Completed Successfully!**\n\n"
            f"🎯 **Role:** {metrics['role']}\n"
            f"🏢 **Company:** {metrics['company']}\n\n"
            f"⏱️ **Total Pipeline Time:** `{metrics['total_time_min']} mins`\n\n"
            f"📁 Files saved locally in `output/`"
        )
        await status_msg.edit_text(summary, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Pipeline Error: {e}", exc_info=True)
        await status_msg.edit_text(f"❌ **Processing Error:** {str(e)}")

if __name__ == "__main__":
    req = HTTPXRequest(connect_timeout=30.0, read_timeout=120.0, write_timeout=30.0, pool_timeout=30.0)
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).request(req).get_updates_request(req).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(poll_interval=1.0, timeout=30)
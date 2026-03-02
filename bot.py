# PolyGranted Scout - Divergence Hunter v3
# Polymarket Strategy: AI Consensus vs Human Implied Odds
import asyncio
import sys
import os
import json
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- Windows Fixes ---
if sys.platform == 'win32':
    import asyncio
    # Proactor is standard and more stable on 3.14+ Windows
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except:
        pass

# --- Configuration ---
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
AGENT_ID = "PolyGrantedScout"
BASE_URL = "https://gzydspfquuaudqeztorw.supabase.co/functions/v1/agent-api"

# File Persistence
LEDGER_FILE = "ledger.json"
WATCHLIST_FILE = "watchlist.json"
SUBSCRIBERS_FILE = "subscribers.json"

# Allowed Categories (Requested)
ALLOWED_CATEGORIES = {
    "crypto", "finance", "macro", "economy", "rates", "inflation", "bitcoin", "ethereum", "solana"
}

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Data Management ---

def load_json(filename, default):
    if not os.path.exists(filename):
        return default
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving {filename}: {e}")

# Initialize files
if not os.path.exists(LEDGER_FILE): save_json(LEDGER_FILE, {"balance": 10000.0, "trades": []})
if not os.path.exists(WATCHLIST_FILE): save_json(WATCHLIST_FILE, {"addresses": []})
if not os.path.exists(SUBSCRIBERS_FILE): save_json(SUBSCRIBERS_FILE, {"chat_ids": []})

# --- API Interaction ---

class PolyScanAPI:
    @staticmethod
    def get_categories():
        try:
            params = {"action": "categories", "agent_id": AGENT_ID}
            resp = requests.get(BASE_URL, params=params, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                # Handle {'ok': True, 'data': [...]} format
                if isinstance(data, dict) and 'data' in data:
                    all_cats = data['data']
                    return [c for c in all_cats if str(c).lower() in ALLOWED_CATEGORIES]
            return []
        except:
            return []

    @staticmethod
    def get_divergence():
        try:
            params = {"action": "ai-vs-humans", "agent_id": AGENT_ID}
            resp = requests.get(BASE_URL, params=params, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict) and 'data' in data:
                    return data['data']
            return []
        except:
            return []

    @staticmethod
    def get_whales():
        try:
            params = {"action": "whales", "agent_id": AGENT_ID}
            resp = requests.get(BASE_URL, params=params, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict) and 'data' in data:
                    return data['data']
            return []
        except:
            return []

# --- Strategy Logic ---

def run_scout_scan():
    logger.info("Starting Divergence Hunter v3 scan...")
    
    # 1. Dynamic category match
    dynamic_cats = PolyScanAPI.get_categories()
    
    # 2. Fetch Signals & Whales
    signals = PolyScanAPI.get_divergence()
    whales = PolyScanAPI.get_whales()
    
    valid_alerts = []
    
    # Process whales for quick lookup
    whale_map = {}
    if isinstance(whales, list):
        for w in whales:
            slug = w.get("slug")
            if slug:
                whale_map[slug] = w.get("whaleDirection", "Neutral") # Updated key from analysis

    if not isinstance(signals, list):
        return []

    for s in signals:
        # Filtering: Category (Must be in our whitelist)
        category = str(s.get("category", "")).lower()
        if category not in ALLOWED_CATEGORIES:
            continue
            
        # Extract Probability Data (Updated Keys)
        implied = float(s.get("polymarketPrice", 0) or 0)
        ai_consensus = float(s.get("aiConsensus", 0) or 0)
        
        # Prob range filter: 3% to 97%
        if implied < 0.03 or implied > 0.97:
            continue
            
        edge = ai_consensus - implied
        abs_edge = abs(edge)
        
        # Min edge 6.5%
        if abs_edge < 0.065:
            continue
            
        # Confirmation from whales
        slug = s.get("slug")
        whale_flow = whale_map.get(slug, "Neutral")
        
        decision = "BUY YES" if edge > 0 else "BUY NO"
        
        # Link construction
        e_slug = s.get("polymarketEventSlug")
        link = f"https://polymarket.com/event/{e_slug}/{slug}" if e_slug else f"https://polymarket.com/main-market/{slug}"
        
        alert = {
            "question": s.get("title", "Unknown Market"),
            "implied": implied * 100,
            "ai_consensus": ai_consensus * 100,
            "divergence": edge * 100,
            "whale_flow": whale_flow,
            "edge": abs_edge * 100,
            "decision": decision,
            "link": link
        }
        valid_alerts.append(alert)

    # Sort by edge and limit to 7
    valid_alerts.sort(key=lambda x: x["edge"], reverse=True)
    return valid_alerts[:7]

# --- Bot Handlers ---

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subs = load_json(SUBSCRIBERS_FILE, {"chat_ids": []})
    if chat_id not in subs.get("chat_ids", []):
        if "chat_ids" not in subs: subs["chat_ids"] = []
        subs["chat_ids"].append(chat_id)
        save_json(SUBSCRIBERS_FILE, subs)
    
    # Start job queue (scan every 15 minutes)
    jobs = context.job_queue.get_jobs_by_name(f"scan_{chat_id}")
    if not jobs:
        context.job_queue.run_repeating(scheduled_scan, interval=900, first=5, chat_id=chat_id, name=f"scan_{chat_id}")

    welcome = (
        "🎯 *PolyGranted Scout* v3\n\n"
        "Scanning for high-conviction Divergence in Crypto & Macro markets every 15m.\n\n"
        "Commands:\n"
        "/granted - Manual scan now\n"
        "/leaderboard - Top traders snapshot\n"
        "/follow [address] - Track whale activity\n"
        "/status - Bot health & ledger"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")

async def cmd_granted(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Scanning Divergence Hunter v3 API...")
    # Wrap sync call in thread to prevent blocking
    alerts = await asyncio.to_thread(run_scout_scan)
    
    if not alerts:
        await update.message.reply_text("✅ All clear — No high-conviction divergence right now. Monitoring Crypto & Macro markets.")
        return

    for a in alerts:
        msg = (
            "🎯 GRANTED WIN\n"
            f"{a['question']}\n"
            f"Implied: {a['implied']:.1f}% | AI Consensus: {a['ai_consensus']:.1f}% (Divergence {a['divergence']:+.1f}%)\n"
            f"Whale Flow: {a['whale_flow']}\n"
            f"Edge: +{a['edge']:.1f}% → ✅ {a['decision']}\n"
            f"Link: {a['link']}"
        )
        await update.message.reply_text(msg, disable_web_page_preview=True)

async def cmd_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Standard Polymarket Leaderboard Fallback
        resp = requests.get("https://data-api.polymarket.com/v1/leaderboard?limit=10", timeout=10)
        data = resp.json()
        traders = data if isinstance(data, list) else data.get("traders", [])
        text = "🏆 *Top 10 Traders (PnL)*\n\n"
        for i, t in enumerate(traders[:10]):
            name = t.get("userName") or f"{t.get('address', '0x')[:6]}..."
            pnl = float(t.get("pnl", 0))
            text += f"{i+1}. `{name}` — *${pnl:,.0f}*\n"
        await update.message.reply_text(text, parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ Leaderboard temporarily unavailable.")

async def cmd_follow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/follow 0xAddress`")
        return
    addr = context.args[0]
    watch = load_json(WATCHLIST_FILE, {"addresses": []})
    if addr not in watch["addresses"]:
        watch["addresses"].append(addr)
        save_json(WATCHLIST_FILE, watch)
        await update.message.reply_text(f"👀 Now following whale: `{addr}`", parse_mode="Markdown")
    else:
        await update.message.reply_text("Address already in watchlist.")

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ledger = load_json(LEDGER_FILE, {"balance": 10000.0, "trades": []})
    msg = (
        "🤖 *PolyGranted Scout Health*\n\n"
        f"💰 Paper Balance: ${ledger['balance']:,.2f}\n"
        f"📡 API Path: Supabase / Agent-API\n"
        f"⏲️ Scheduled Jobs: {len(context.job_queue.jobs())}\n"
        "📈 Strategy: Divergence Hunter v3"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def scheduled_scan(context: ContextTypes.DEFAULT_TYPE):
    # Wrap sync call in thread
    alerts = await asyncio.to_thread(run_scout_scan)
    if not alerts: return
        
    chat_id = context.job.chat_id
    for a in alerts:
        msg = (
            "🎯 GRANTED WIN\n"
            f"{a['question']}\n"
            f"Implied: {a['implied']:.1f}% | AI Consensus: {a['ai_consensus']:.1f}% (Divergence {a['divergence']:+.1f}%)\n"
            f"Whale Flow: {a['whale_flow']}\n"
            f"Edge: +{a['edge']:.1f}% → ✅ {a['decision']}\n"
            f"Link: {a['link']}"
        )
        await context.bot.send_message(chat_id=chat_id, text=msg, disable_web_page_preview=True)

# --- Application Startup ---

async def post_init(application: Application):
    subs = load_json(SUBSCRIBERS_FILE, {"chat_ids": []})
    for chat_id in subs.get("chat_ids", []):
        application.job_queue.run_repeating(scheduled_scan, interval=900, first=10, chat_id=chat_id, name=f"scan_{chat_id}")
    logger.info(f"Bot resumed for {len(subs.get('chat_ids', []))} subscribers.")

def main():
    if not TELEGRAM_TOKEN:
        print("TELEGRAM_TOKEN not found.")
        return

    application = Application.builder().token(TELEGRAM_TOKEN).post_init(post_init).build()
    
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("granted", cmd_granted))
    application.add_handler(CommandHandler("leaderboard", cmd_leaderboard))
    application.add_handler(CommandHandler("follow", cmd_follow))
    application.add_handler(CommandHandler("status", cmd_status))
    
    logger.info("PolyGranted Scout v3 starting...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

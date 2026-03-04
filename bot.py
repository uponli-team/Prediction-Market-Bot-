# PolyGranted Scout - Divergence Hunter v3
# Polymarket Strategy: AI Consensus vs Human Implied Odds
import asyncio
import sys
import os
import json
import logging
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- Logging Setup ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
load_dotenv()
AGENT_ID = "PolyGrantedScout"
BASE_URL = "https://gzydspfquuaudqeztorw.supabase.co/functions/v1/agent-api"

# File Persistence
DATA_DIR = os.getenv("DATA_DIR", ".")
LEDGER_FILE = os.path.join(DATA_DIR, "ledger.json")
WATCHLIST_FILE = os.path.join(DATA_DIR, "watchlist.json")
SUBSCRIBERS_FILE = os.path.join(DATA_DIR, "subscribers.json")
SENT_ALERTS_FILE = os.path.join(DATA_DIR, "sent_alerts.json")
USER_SEEN_FILE = os.path.join(DATA_DIR, "user_seen.json")

# Category IDs (Polymarket Gamma)
MARKET_CATEGORIES = {
    "crypto": "5466",
    "finance": "5510",
    "politics": "5481",
    "global_politics": "5483",
    "middle_east": "5549",
    "business": "5456"
}

# Geopolitical Escalation Keywords
GEOPOLITICAL_KEYWORDS = {
    "iran", "israel", "hezbollah", "lebanon", "middle east", "geopolitical", 
    "war", "conflict", "attack", "strike", "escalation", "missile", "drone", 
    "tehran", "tel aviv", "gaza", "palestine", "military", "netanyahu"
}

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
def init_files():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(LEDGER_FILE): save_json(LEDGER_FILE, {"balance": 10000.0, "trades": []})
    if not os.path.exists(WATCHLIST_FILE): save_json(WATCHLIST_FILE, {"addresses": []})
    if not os.path.exists(SUBSCRIBERS_FILE): save_json(SUBSCRIBERS_FILE, {"chat_ids": []})
    if not os.path.exists(SENT_ALERTS_FILE): save_json(SENT_ALERTS_FILE, {"hashes": []})
    if not os.path.exists(USER_SEEN_FILE): save_json(USER_SEEN_FILE, {})

init_files()

# --- API Interaction ---

class PolyScanAPI:
    @staticmethod
    def get_categories():
        return list(MARKET_CATEGORIES.keys())

    @staticmethod
    def get_divergence():
        retries = 3
        for i in range(retries):
            try:
                params = {"action": "ai-vs-humans", "agent_id": AGENT_ID}
                resp = requests.get(BASE_URL, params=params, timeout=20)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, dict) and 'data' in data:
                        return data['data']
                elif resp.status_code == 503:
                    logger.warning(f"API 503 (Attempt {i+1}/{retries}). Retrying in {2**(i+1)}s...")
                    import time
                    time.sleep(2**(i+1))
                    continue
                return []
            except Exception as e:
                logger.error(f"Divergence API error (Attempt {i+1}/{retries}): {e}")
                if i < retries - 1:
                    import time
                    time.sleep(1)
                continue
        return []

    @staticmethod
    def get_whales():
        retries = 3
        for i in range(retries):
            try:
                params = {"action": "whales", "agent_id": AGENT_ID}
                resp = requests.get(BASE_URL, params=params, timeout=20)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, dict) and 'data' in data:
                        return data['data']
                elif resp.status_code == 503:
                    logger.warning(f"Whale API 503 (Attempt {i+1}/{retries}). Retrying...")
                    import time
                    time.sleep(2**(i+1))
                    continue
                return []
            except Exception as e:
                logger.error(f"Whale API error: {e}")
                if i < retries - 1:
                    import time
                    time.sleep(1)
                continue
        return []

# --- Strategy Logic ---

def run_scout_scan():
    logger.info("Starting Divergence Hunter v3 scan...")
    
    # 2. Fetch Signals & Whales
    signals = PolyScanAPI.get_divergence()
    whales = PolyScanAPI.get_whales()
    
    if not isinstance(signals, list):
        return []

    # Process whales for quick lookup
    whale_map = {}
    if isinstance(whales, list):
        for w in whales:
            slug = w.get("slug")
            if slug:
                whale_map[slug] = w.get("whaleDirection", "Neutral")

    valid_alerts = []
    seen_events = set()

    # Initial filtering and data clean up
    potential_matches = []
    for s in signals:
        title = str(s.get("title", "")).lower()
        category_name = str(s.get("category", "")).lower()
        
        # Check if it matches geopolitical escalation keywords
        is_geopolitical = any(kw in title for kw in GEOPOLITICAL_KEYWORDS) or any(kw in category_name for kw in GEOPOLITICAL_KEYWORDS)
        
        # Logic: Match by ID if possible or fall back to name
        # Note: Current API doesn't provide categoryId, so we use category names for now 
        # but group them into our defined selections.
        selection = "other"
        if "crypto" in category_name: selection = "crypto"
        elif "politics" in category_name: selection = "politics"
        elif "finance" in category_name: selection = "finance"
        elif is_geopolitical or "middle east" in category_name: selection = "geopolitical"
        elif "business" in category_name: selection = "finance" # Map business to finance
        
        if selection == "other" and not is_geopolitical:
            continue
            
        implied = float(s.get("polymarketPrice", 0) or 0)
        ai_consensus = float(s.get("aiConsensus", 0) or 0)
        
        if implied < 0.02 or implied > 0.98:
            continue
            
        edge = ai_consensus - implied
        abs_edge = abs(edge)
        
        if abs_edge < 0.03:
            continue
        
        tag = "GRANTED WIN" if abs_edge >= 0.065 else "PROSPECT ALERT"
        
        # 3. Near-Term Prioritization (Ending within 7 days)
        is_near_term = False
        hurry_tag = ""
        try:
            end_date_str = s.get("endDate") or s.get("enddate")
            if end_date_str:
                # Handle ISO format (e.g., 2026-03-10T15:00:00Z)
                # Remove Z and replace T with space for simple parsing or use fromisoformat
                clean_date = end_date_str.replace('Z', '+00:00')
                end_dt = datetime.fromisoformat(clean_date)
                
                # Check if end_dt is naive or aware
                now = datetime.now(timezone.utc) if end_dt.tzinfo else datetime.now()
                
                if end_dt - now < timedelta(days=7):
                    is_near_term = True
                    hurry_tag = " 🔥 HURRY"
        except Exception as e:
            logger.debug(f"Date parsing error for {s.get('slug')}: {e}")

        potential_matches.append((s, abs_edge, edge, implied, ai_consensus, tag + hurry_tag, selection, is_near_term))

    # Sort all potentials: 1st by near_term (True first), 2nd by abs_edge (Descending)
    potential_matches.sort(key=lambda x: (x[7], x[1]), reverse=True)

    selection_counts = {}
    for s, abs_edge, edge, implied, ai_consensus, tag, selection, is_near_term in potential_matches:
        slug = s.get("slug")
        event_slug = s.get("polymarketEventSlug") or slug

        if event_slug in seen_events:
            continue
        
        # Max 5 per selection
        if selection_counts.get(selection, 0) >= 5:
            continue

        whale_flow = whale_map.get(slug, "Neutral")
        decision = "BUY YES" if edge > 0 else "BUY NO"
        
        link = f"https://polymarket.com/event/{event_slug}/{slug}" if event_slug != slug else f"https://polymarket.com/main-market/{slug}"
        
        alert = {
            "id": slug,
            "tag": tag,
            "question": s.get("title", "Unknown Market"),
            "implied": implied * 100,
            "ai_consensus": ai_consensus * 100,
            "divergence": edge * 100,
            "whale_flow": whale_flow,
            "edge": abs_edge * 100,
            "decision": decision,
            "link": link,
            "selection": selection,
            "category": s.get("category", selection)
        }
        valid_alerts.append(alert)
        seen_events.add(event_slug)
        selection_counts[selection] = selection_counts.get(selection, 0) + 1

    return valid_alerts

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
        "Scanning for high-edge Divergence in Crypto, Finance & Politics.\n\n"
        "Commands:\n"
        "/granted - Manual scan (all categories)\n"
        "/granted crypto - Only Crypto alerts\n"
        "/granted finance - Only Finance/Business\n"
        "/granted politics - US & Global Politics\n"
        "/granted geopolitics - Middle East & Escalations\n\n"
        "/status - Bot health & ledger"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")

async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Ping received from {update.effective_chat.id}")
    await update.message.reply_text("🏓 Pong! I am alive on " + ("Modal" if os.getenv("MODAL_PROJECT_NAME") else "Local PC"))

async def cmd_granted(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    logger.info(f"Command /granted received from user {chat_id}")
    
    # Selection logic: Check if user wants a specific selection
    selection_req = None
    if context.args:
        arg = context.args[0].lower()
        if arg in ["crypto", "finance", "politics", "geopolitics"]:
            selection_req = arg

    status_msg = "🔍 Scanning Divergence Hunter v3..."
    if selection_req:
        status_msg = f"🔍 Scanning {selection_req.upper()} Divergence..."
    
    await update.message.reply_text(status_msg)
    
    all_alerts = await asyncio.to_thread(run_scout_scan)
    
    if not all_alerts:
        await update.message.reply_text("✅ All clear — No divergence >= 3.0% right now.")
        return

    # User persistence
    user_seen = load_json(USER_SEEN_FILE, {})
    user_data = user_seen.get(chat_id, {})
    
    # If it's a list (old format), convert to dict
    if isinstance(user_data, list):
        user_data = {"seen_ids": user_data}
    
    seen_ids = set(user_data.get("seen_ids", []))

    # Filter by user preference
    filtered = all_alerts
    if selection_req:
        filtered = [a for a in all_alerts if a['selection'] == selection_req]
    
    if not filtered:
        await update.message.reply_text(f"✅ No updates in {selection_req or 'all categories'} yet.")
        return

    # Selection seen logic: ensure new users see fresh things, returning users see new things
    fresh_alerts = [a for a in filtered if a['id'] not in seen_ids]
    
    # If no fresh alerts, maybe show high edge ones even if seen? Or just say caught up.
    if not fresh_alerts:
        await update.message.reply_text("👋 You're all caught up! No fresh divergence found in your selection.")
        return

    # Prioritize GRANTED WINs
    selected = sorted(fresh_alerts, key=lambda x: (x['tag'] == 'GRANTED WIN', x['edge']), reverse=True)[:5]

    for a in selected:
        msg = (
            f"🎯 {a['tag']} | {a['selection'].upper()}\n"
            f"{a['question']}\n"
            f"Implied: {a['implied']:.1f}% | AI Consensus: {a['ai_consensus']:.1f}% (Div {a['divergence']:+.1f}%)\n"
            f"Edge: +{a['edge']:.1f}% → ✅ {a['decision']}\n"
            f"Link: {a['link']}"
        )
        await update.message.reply_text(msg, disable_web_page_preview=True)
        seen_ids.add(a['id'])

    # Save persistence
    user_data["seen_ids"] = list(seen_ids)[-200:]
    user_seen[chat_id] = user_data
    save_json(USER_SEEN_FILE, user_seen)

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
    sent_data = load_json(SENT_ALERTS_FILE, {"hashes": []})
    
    # In scheduled mode, prioritize GRANTED WIN alerts to minimize noise
    new_alerts_sent = 0
    for a in alerts:
        # Ignore PROSPECT ALERTs in automated feed unless edge is high
        if a['tag'] == "PROSPECT ALERT" and a['edge'] < 5.0:
            continue

        # Avoid repeating the SAME result again and again
        # Hash includes ID and the base implied price to detect price shifts
        alert_key = f"{a['id']}_{round(a['implied'] / 2) * 2}" # 2% price bins for deduplication
        if alert_key in sent_data["hashes"]:
            continue
            
        msg = (
            f"🎯 {a['tag']} | {a['selection'].upper()}\n"
            f"{a['question']}\n"
            f"Implied: {a['implied']:.1f}% | AI Consensus: {a['ai_consensus']:.1f}% (Div {a['divergence']:+.1f}%)\n"
            f"Edge: +{a['edge']:.1f}% → ✅ {a['decision']}\n"
            f"Link: {a['link']}"
        )
        await context.bot.send_message(chat_id=chat_id, text=msg, disable_web_page_preview=True)
        
        sent_data["hashes"].append(alert_key)
        new_alerts_sent += 1

    # Keep only last 200 hashes 
    if new_alerts_sent > 0:
        sent_data["hashes"] = sent_data["hashes"][-200:]
        save_json(SENT_ALERTS_FILE, sent_data)

# --- Application Startup ---

async def post_init(application: Application):
    subs = load_json(SUBSCRIBERS_FILE, {"chat_ids": []})
    for chat_id in subs.get("chat_ids", []):
        application.job_queue.run_repeating(scheduled_scan, interval=900, first=10, chat_id=chat_id, name=f"scan_{chat_id}")
    logger.info(f"Bot resumed for {len(subs.get('chat_ids', []))} subscribers.")

def main():
    # Windows Asyncio Fix (deprecated in 3.12, but handled by ProactorEventLoop by default in 3.8+)
    # We remove this to avoid DeprecationWarning on Python 3.12+
    # if sys.platform == 'win32':
    #     try:
    #         asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    #     except:
    #         pass
            
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        logger.error("TELEGRAM_TOKEN not found. Exiting.")
        return

    logger.info("Initializing Telegram Application...")
    application = Application.builder().token(token).post_init(post_init).build()
    
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("granted", cmd_granted))
    application.add_handler(CommandHandler("leaderboard", cmd_leaderboard))
    application.add_handler(CommandHandler("follow", cmd_follow))
    application.add_handler(CommandHandler("status", cmd_status))
    application.add_handler(CommandHandler("ping", cmd_ping))
    
    logger.info("PolyGranted Scout v3 starting polling...")
    try:
        application.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Polling error: {e}")
        raise e

if __name__ == "__main__":
    main()

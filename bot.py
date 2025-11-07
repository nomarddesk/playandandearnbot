import logging
import os
import json
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.error import Conflict

# Import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI package not available. AI features will be disabled.")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
SUPPORT_CHAT_ID = os.environ.get("SUPPORT_CHAT_ID")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

print("=" * 50)
print("ENHANCED GAMING BOT - ENVIRONMENT CHECK:")
print(f"TELEGRAM_TOKEN: {'✅ SET' if TELEGRAM_TOKEN else '❌ NOT SET'}")
print(f"SUPPORT_CHAT_ID: {'✅ SET' if SUPPORT_CHAT_ID else '❌ NOT SET'}")
print(f"OPENAI_API_KEY: {'✅ SET' if OPENAI_API_KEY else '❌ NOT SET'}")
print(f"OPENAI PACKAGE: {'✅ AVAILABLE' if OPENAI_AVAILABLE else '❌ NOT AVAILABLE'}")
if SUPPORT_CHAT_ID:
    print(f"SUPPORT_CHAT_ID value: {SUPPORT_CHAT_ID}")
print("=" * 50)

# Initialize OpenAI client
openai_client = None
if OPENAI_AVAILABLE and OPENAI_API_KEY:
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        print("✅ OpenAI client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize OpenAI client: {e}")
        openai_client = None
else:
    print("⚠️ OpenAI features disabled - package not available or API key missing")

# Database file path
DB_FILE = "/tmp/gaming_bot.db" if os.path.exists("/tmp") else "gaming_bot.db"

# Initialize Database
def init_database():
    """Initialize SQLite database for user progress tracking"""
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_progress (
                user_id INTEGER PRIMARY KEY,
                player_type TEXT DEFAULT 'new',
                current_step INTEGER DEFAULT 1,
                completed_steps TEXT DEFAULT '[]',
                vpn_used BOOLEAN DEFAULT FALSE,
                profile_created BOOLEAN DEFAULT FALSE,
                epic_activated BOOLEAN DEFAULT FALSE,
                game_launched BOOLEAN DEFAULT FALSE,
                reward_island_found BOOLEAN DEFAULT FALSE,
                full_setup_complete BOOLEAN DEFAULT FALSE,
                playtime_hours INTEGER DEFAULT 0,
                like_clicks INTEGER DEFAULT 0,
                favorites_saved BOOLEAN DEFAULT FALSE,
                influencer_name TEXT,
                language TEXT DEFAULT 'en',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS support_cases (
                case_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                case_type TEXT,
                issue_description TEXT,
                steps_completed TEXT,
                status TEXT DEFAULT 'open',
                assigned_to TEXT,
                resolution_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES player_progress (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ Database initialized successfully at {DB_FILE}")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print("⚠️ Using in-memory storage as fallback")

init_database()

HELPFUL_CHANNEL_LINK = "https://t.me/rejoinsnousetgagne"

# Define conversation states
SELECT_LANGUAGE, MAIN_MENU, NEW_PLAYER_FLOW, EXISTING_PLAYER_FLOW, SUPPORT_FLOW, USERNAME_COLLECTION = range(6)

# Game codes for reward island
REWARD_ISLAND_CODES = [
    "6086-7221-0564",
    "2753-4695-7191", 
    "9689-1352-5966",
    "4563-6624-9460",
    "4828-9033-2281"
]

# --- ENHANCED LANGUAGE STRINGS ---
BOT_TEXTS = {
    'en': {
        # Welcome and Main Menu
        'welcome_title': "🎮 **Ultimate Gaming Assistant**",
        'welcome_subtitle': "Your gateway to immersive gaming and exclusive rewards!",
        'disclaimer': "🔒 *Unofficial Guide: Not affiliated with Epic Games or Fortnite. We never ask for passwords.*",
        
        # Main Menu Options
        'new_player_option': "🚀 New Player Setup",
        'existing_player_option': "⚡ Player Check-In", 
        'support_option': "🆘 Support & Rewards",
        'channel_option': "📚 Game Guides",
        'language_option': "🌐 Language",
        
        # New Player Flow
        'new_player_welcome': "🎮 **New Player Setup Guide**\n\nWelcome to your gaming adventure! I'll guide you through setup so you can start playing and earning rewards immediately.",
        'cloud_session_note': "💡 *Cloud Gaming Note: Sessions last 1 hour. Relaunch to continue playing.*",
        
        # Steps with improved wording
        'step_1_vpn': "🔒 **Step 1: VPN Setup**\nDid you use a USA VPN for profile creation?",
        'vpn_guidance': "📱 **VPN Required**\n\nUse a USA VPN *only during profile setup* (not for playing). This ensures proper regional configuration.\n\nHave you configured your VPN?",
        
        'step_2_profile': "☁️ **Step 2: Gaming Profile**\nHave you created your cloud gaming profile?",
        'profile_guidance': "🎯 **Profile Setup**\n\nLet's create your gaming profile for optimal performance and rewards tracking.",
        
        'step_3_activation': "⚡ **Step 3: Account Activation**\nDid you activate with Epic Games?",
        'activation_guidance': "🔗 **Activation Required**\n\nConnect your cloud gaming to Epic Games to save progress and enable rewards.",
        
        'step_4_epic': "👤 **Step 4: Epic Profile**\nIs your Epic Games profile complete?",
        'epic_guidance': "🎮 **Profile Completion**\n\nFinalize your Epic profile for full feature access and reward eligibility.",
        
        'step_5_shortcut': "📱 **Step 5: Quick Access**\nDid you add the game to your home screen?",
        'shortcut_guidance': "🚀 **Instant Access**\n\nHome screen shortcuts provide fastest game launch and better experience.",
        
        'step_6_launch': "🎯 **Step 6: Game Launch**\nHave you successfully launched the game?",
        'launch_guidance': "🕹️ **Game Ready**\n\nLet's ensure the game launches properly for seamless gameplay.",
        
        'step_7_reward_island': "🏝️ **Step 7: Reward Access**\nAre you on the Reward Island?",
        'reward_guidance': "💰 **Earning Zone**\n\nThe Reward Island is where you accumulate points and unlock exclusive rewards.",
        'code_display': "🔑 **Access Codes:**\n{}\n\nCopy any code → Game search bar → Start earning!",
        
        'step_8_full_setup': "⚙️ **Step 8: Complete Setup**\nIs your full configuration complete?",
        'setup_guidance': "🎪 **Optimal Configuration**\n\nComplete setup ensures maximum earnings with friends and smooth gameplay.",
        
        'step_9_commitment': "⏰ **Step 9: Weekly Goals**\nCan you commit to 130 hours weekly?",
        'commitment_guidance': "🏆 **Reward Requirements**\n\nConsistent playtime is key to unlocking the best rewards and bonuses.",
        
        'step_10_engagement': "👍 **Step 10: Engagement**\nWill you click 'Like' before each session ends?",
        'engagement_guidance': "📊 **Activity Tracking**\n\nThe 'Like' button helps us track your engagement for reward calculations.",
        
        'step_11_favorites': "⭐ **Step 11: Quick Access**\nIs Reward Island saved in favorites?",
        'favorites_guidance': "🚀 **Efficient Gaming**\n\nFavorites save time and ensure you're always in the earning zone.",
        
        'step_12_influencer': "📢 **Step 12: Community**\nDid an influencer bring you here?",
        'influencer_prompt': "👥 **Community Recognition**\n\nPlease share the influencer's name for proper attribution:",
        
        # Existing Player Flow
        'existing_welcome': "⚡ **Player Check-In**\n\nWelcome back! Let's verify your setup and maximize your rewards.",
        'existing_cloud_note': "💡 *You know the routine: 1-hour sessions, relaunch to continue.*",
        
        # Support Flow
        'support_welcome': "🆘 **Support & Reward Verification**\n\nLet's identify any issues and verify your reward eligibility! 💰",
        'support_success': "✅ **Verification Complete!**\n\nOur team will review your case and contact you within 24 hours.",
        
        # Common Responses
        'yes_option': "✅ Yes",
        'no_option': "❌ No", 
        'need_help': "🆘 I need help",
        'already_done': "✅ Already done",
        'skip_step': "⏭️ Skip",
        'continue_next': "➡️ Continue",
        'back_previous': "⬅️ Back",
        'main_menu': "🏠 Main Menu",
        'join_channel': "📚 Join Channel",
        
        # Channel and Links
        'channel_invite': "Join our community for guides, tips, and support:",
        'channel_instructions': "Check our channel for detailed instructions:",
        
        # Support Specific
        'provide_username': "👤 **Contact Setup**\n\nPlease provide your Telegram username (starting with @) for support:",
        'username_saved': "✅ **Info Received!**\n\nSupport team will contact you soon. Keep playing!",
        'invalid_username': "❌ Please provide a valid @username",
    },
    'fr': {
        # French translations would go here
        'welcome_title': "🎮 **Assistant de Jeu Ultime**",
        'welcome_subtitle': "Votre passerelle vers le gaming immersif et les récompenses exclusives!",
        # ... other French translations
    }
}

# --- DATABASE FUNCTIONS ---
def get_player_progress(user_id):
    """Get player progress from database"""
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM player_progress WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'user_id': result[0],
                'player_type': result[1],
                'current_step': result[2],
                'completed_steps': json.loads(result[3]),
                'vpn_used': bool(result[4]),
                'profile_created': bool(result[5]),
                'epic_activated': bool(result[6]),
                'game_launched': bool(result[7]),
                'reward_island_found': bool(result[8]),
                'full_setup_complete': bool(result[9]),
                'playtime_hours': result[10],
                'like_clicks': result[11],
                'favorites_saved': bool(result[12]),
                'influencer_name': result[13],
                'language': result[14]
            }
        return None
    except Exception as e:
        logger.error(f"Database error in get_player_progress: {e}")
        return None

def update_player_progress(user_id, updates):
    """Update player progress in database"""
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = conn.cursor()
        
        # Build update query dynamically
        set_clause = []
        values = []
        
        for key, value in updates.items():
            if key == 'completed_steps' and isinstance(value, list):
                value = json.dumps(value)
            set_clause.append(f"{key} = ?")
            values.append(value)
        
        values.append(user_id)
        
        query = f'''
            INSERT OR REPLACE INTO player_progress 
            (user_id, {', '.join(updates.keys())}, updated_at)
            VALUES (?, {', '.join(['?' for _ in updates])}, CURRENT_TIMESTAMP)
        '''
        
        cursor.execute(query, [user_id] + values[:-1])
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Database error in update_player_progress: {e}")
        return False

def create_support_case(user_id, username, case_type, issue_desc, steps_completed):
    """Create a support case in database"""
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO support_cases 
            (user_id, username, case_type, issue_description, steps_completed)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, case_type, issue_desc, json.dumps(steps_completed)))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Database error in create_support_case: {e}")
        return False

# --- AI ASSISTANT FUNCTION ---
async def gaming_assistant_response(user_message, user_context, lang):
    """AI assistant for gaming-related queries"""
    if not openai_client:
        return "I'm currently learning more about gaming setups. For now, please use the structured menus for assistance."
    
    try:
        # Enhanced system prompt for gaming focus
        system_prompt = f"""You are a gaming assistant specialist helping users with Fortnite cloud gaming setup and rewards.

Key Knowledge:
- Cloud gaming sessions: 1-hour duration
- VPN requirement: USA VPN for profile creation only
- Reward system: Based on playtime and engagement
- Weekly target: 130 hours for optimal rewards
- Key steps: Profile setup, activation, reward island access

User Context: {user_context}

Respond helpfully and concisely in {lang.upper()} language. Guide users to appropriate menu options when needed."""

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"AI assistant error: {e}")
        return "I'm having trouble processing your request. Please try the menu options for specific help."

# --- ENHANCED FLOW MANAGEMENT ---
class FlowManager:
    """Manages different user flows with improved state handling"""
    
    def __init__(self):
        self.flows = {
            'new_player': self.new_player_flow,
            'existing_player': self.existing_player_flow,
            'support': self.support_flow
        }
    
    async def new_player_flow(self, update, context, step_number):
        """Enhanced new player flow with better step management"""
        user_id = update.effective_user.id
        lang = context.user_data.get('lang', 'en')
        texts = BOT_TEXTS[lang]
        
        flow_steps = {
            1: {
                'text': texts['step_1_vpn'],
                'keyboard': [
                    [texts['yes_option'], 'new_q1_yes'],
                    [texts['no_option'], 'new_q1_no']
                ]
            },
            2: {
                'text': texts['step_2_profile'],
                'keyboard': [
                    [texts['yes_option'], 'new_q2_yes'],
                    [texts['no_option'], 'new_q2_no']
                ]
            },
            # ... other steps with improved structure
        }
        
        current_step = flow_steps.get(step_number)
        if not current_step:
            return await self.complete_flow(update, context, 'new_player')
        
        # Add navigation buttons
        keyboard = []
        for btn_text, callback in current_step['keyboard']:
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=callback)])
        
        # Add back button if not first step
        if step_number > 1:
            keyboard.append([InlineKeyboardButton(texts['back_previous'], 
                                               callback_data=f"new_back_{step_number-1}")])
        
        keyboard.append([InlineKeyboardButton(texts['main_menu'], 
                                            callback_data="back_to_main")])
        
        query = update.callback_query
        if query:
            await query.edit_message_text(
                text=current_step['text'],
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                text=current_step['text'],
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        
        return NEW_PLAYER_FLOW
    
    async def existing_player_flow(self, update, context, step_number):
        """Enhanced existing player verification flow"""
        # Similar structure to new_player_flow but with different questions
        # Implementation details...
        pass
    
    async def support_flow(self, update, context, step_number):
        """Enhanced support and verification flow"""
        # Implementation details...
        pass
    
    async def complete_flow(self, update, context, flow_type):
        """Handle flow completion with reward tracking"""
        user_id = update.effective_user.id
        lang = context.user_data.get('lang', 'en')
        texts = BOT_TEXTS[lang]
        
        completion_message = {
            'new_player': "🎉 **Setup Complete!** You're ready to start earning rewards!",
            'existing_player': "✅ **Check-In Complete!** Your setup is optimized for maximum rewards!",
            'support': "🆗 **Case Logged!** Our team will contact you within 24 hours."
        }
        
        keyboard = [
            [InlineKeyboardButton(texts['main_menu'], callback_data="back_to_main")],
            [InlineKeyboardButton(texts['join_channel'], url=HELPFUL_CHANNEL_LINK)]
        ]
        
        query = update.callback_query
        if query:
            await query.edit_message_text(
                text=completion_message[flow_type],
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                text=completion_message[flow_type],
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        
        return MAIN_MENU

# Initialize flow manager
flow_manager = FlowManager()

# --- ENHANCED MESSAGE HANDLER ---
async def handle_intelligent_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Enhanced message handler with AI assistance"""
    user_message = update.message.text
    user_id = update.message.from_user.id
    lang = context.user_data.get('lang', 'en')
    
    # Get user context from database
    user_progress = get_player_progress(user_id)
    user_context = {
        'progress': user_progress,
        'current_flow': context.user_data.get('current_flow', 'general'),
        'language': lang
    }
    
    # Get AI response
    ai_response = await gaming_assistant_response(user_message, user_context, lang)
    
    # Create response with menu options
    texts = BOT_TEXTS[lang]
    keyboard = [
        [InlineKeyboardButton(texts['new_player_option'], callback_data="start_new_player")],
        [InlineKeyboardButton(texts['existing_player_option'], callback_data="start_existing_player")],
        [InlineKeyboardButton(texts['support_option'], callback_data="start_support")],
        [InlineKeyboardButton(texts['channel_option'], url=HELPFUL_CHANNEL_LINK)]
    ]
    
    await update.message.reply_text(
        text=f"🤖 {ai_response}\n\n💡 *Need specific help? Choose an option below:*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return context.user_data.get('current_state', MAIN_MENU)

# --- ENHANCED MAIN MENU ---
async def show_enhanced_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str = None):
    """Show enhanced main menu with better organization"""
    lang = context.user_data.get('lang', 'en')
    texts = BOT_TEXTS[lang]
    
    context.user_data['current_flow'] = 'general'
    context.user_data['current_state'] = MAIN_MENU
    
    welcome_text = message or f"{texts['welcome_title']}\n\n{texts['welcome_subtitle']}\n\n{texts['disclaimer']}"
    
    keyboard = [
        [InlineKeyboardButton(texts['new_player_option'], callback_data="start_new_player")],
        [InlineKeyboardButton(texts['existing_player_option'], callback_data="start_existing_player")],
        [InlineKeyboardButton(texts['support_option'], callback_data="start_support")],
        [
            InlineKeyboardButton(texts['channel_option'], callback_data="show_channel"),
            InlineKeyboardButton(texts['language_option'], callback_data="change_language")
        ]
    ]
    
    query = update.callback_query
    if query:
        await query.answer()
        try:
            await query.edit_message_text(
                text=welcome_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.warning(f"Menu edit failed: {e}")
    else:
        await update.message.reply_text(
            text=welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    return MAIN_MENU

# --- FLOW START HANDLERS ---
async def start_new_player_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start enhanced new player flow"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = context.user_data.get('lang', 'en')
    texts = BOT_TEXTS[lang]
    
    # Initialize player progress
    update_player_progress(user_id, {
        'player_type': 'new',
        'current_step': 1,
        'completed_steps': [],
        'language': lang
    })
    
    context.user_data['current_flow'] = 'new_player'
    context.user_data['current_state'] = NEW_PLAYER_FLOW
    context.user_data['current_step'] = 1
    
    welcome_text = f"{texts['new_player_welcome']}\n\n{texts['cloud_session_note']}"
    
    return await flow_manager.new_player_flow(update, context, 1)

async def start_existing_player_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start enhanced existing player flow"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = context.user_data.get('lang', 'en')
    
    # Update player progress
    update_player_progress(user_id, {
        'player_type': 'existing',
        'current_step': 1,
        'language': lang
    })
    
    context.user_data['current_flow'] = 'existing_player'
    context.user_data['current_state'] = EXISTING_PLAYER_FLOW
    context.user_data['current_step'] = 1
    
    return await flow_manager.existing_player_flow(update, context, 1)

async def start_support_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start enhanced support flow"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = context.user_data.get('lang', 'en')
    
    context.user_data['current_flow'] = 'support'
    context.user_data['current_state'] = SUPPORT_FLOW
    context.user_data['current_step'] = 1
    context.user_data['support_answers'] = []
    
    return await flow_manager.support_flow(update, context, 1)

# --- CHANNEL AND LANGUAGE HANDLERS ---
async def show_channel_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show channel information"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    texts = BOT_TEXTS[lang]
    
    keyboard = [
        [InlineKeyboardButton(texts['join_channel'], url=HELPFUL_CHANNEL_LINK)],
        [InlineKeyboardButton(texts['main_menu'], callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        text=texts['channel_invite'],
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )
    
    return MAIN_MENU

async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Change language preference"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [
            InlineKeyboardButton("English 🇬🇧", callback_data="set_lang_en"),
            InlineKeyboardButton("Français 🇫🇷", callback_data="set_lang_fr")
        ],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        text="🌐 **Select your language / Choisissez votre langue:**",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return MAIN_MENU

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Set user language preference"""
    query = update.callback_query
    lang = query.data.replace('set_lang_', '')
    context.user_data['lang'] = lang
    
    # Update in database if user exists
    user_id = update.effective_user.id
    update_player_progress(user_id, {'language': lang})
    
    await query.answer(f"Language set to {lang.upper()}")
    return await show_enhanced_menu(update, context)

# --- ERROR HANDLER ---
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors gracefully"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    if isinstance(context.error, Conflict):
        logger.warning("Bot conflict detected - another instance might be running")
        return
    
    try:
        if update and update.effective_message:
            lang = context.user_data.get('lang', 'en')
            texts = BOT_TEXTS[lang]
            await update.effective_message.reply_text(
                "⚠️ Sorry, I encountered an error. Please try again or use the menu options."
            )
    except Exception as e:
        logger.error(f"Error while sending error message: {e}")

# --- START COMMAND ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Enhanced start command with better presentation"""
    user = update.effective_user
    welcome_text = (
        "🎮 **Welcome to the Ultimate Gaming Assistant!**\n\n"
        "I'm here to help you:\n"
        "• Set up your gaming account 🚀\n"
        "• Maximize your rewards 💰\n"
        "• Resolve any issues 🛠️\n"
        "• Connect with our community 👥\n\n"
        "🔒 *Unofficial Guide - Not affiliated with Epic Games/Fortnite*\n\n"
        "Choose your path below:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("English 🇬🇧", callback_data="set_lang_en"),
            InlineKeyboardButton("Français 🇫🇷", callback_data="set_lang_fr")
        ]
    ]
    
    await update.message.reply_text(
        text=welcome_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return SELECT_LANGUAGE

# --- MAIN APPLICATION SETUP ---
def main() -> None:
    """Run the enhanced gaming bot"""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN environment variable not set!")
        print("❌ ERROR: TELEGRAM_TOKEN is required!")
        return

    # Create application with enhanced settings
    application = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .read_timeout(30)
        .write_timeout(30)
        .connect_timeout(30)
        .pool_timeout(30)
        .build()
    )

    # Add error handler
    application.add_error_handler(error_handler)

    # Enhanced conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_LANGUAGE: [
                CallbackQueryHandler(set_language, pattern="^set_lang_(en|fr)$")
            ],
            MAIN_MENU: [
                CallbackQueryHandler(start_new_player_flow, pattern="^start_new_player$"),
                CallbackQueryHandler(start_existing_player_flow, pattern="^start_existing_player$"),
                CallbackQueryHandler(start_support_flow, pattern="^start_support$"),
                CallbackQueryHandler(show_channel_info, pattern="^show_channel$"),
                CallbackQueryHandler(change_language, pattern="^change_language$"),
                CallbackQueryHandler(show_enhanced_menu, pattern="^back_to_main$"),
                # Enhanced message handler for free-form questions
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_intelligent_message),
            ],
            NEW_PLAYER_FLOW: [
                # New player flow handlers would be added here
                CallbackQueryHandler(show_enhanced_menu, pattern="^back_to_main$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_intelligent_message),
            ],
            EXISTING_PLAYER_FLOW: [
                # Existing player flow handlers would be added here
                CallbackQueryHandler(show_enhanced_menu, pattern="^back_to_main$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_intelligent_message),
            ],
            SUPPORT_FLOW: [
                # Support flow handlers would be added here
                CallbackQueryHandler(show_enhanced_menu, pattern="^back_to_main$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_intelligent_message),
            ],
            USERNAME_COLLECTION: [
                # Username collection handlers
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_intelligent_message),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
        per_message=False,
    )

    application.add_handler(conv_handler)

    # Enhanced startup message
    logger.info("Enhanced Gaming Bot starting...")
    print("🎮 ENHANCED GAMING BOT STARTING...")
    print("=" * 50)
    print(f"✅ TELEGRAM_TOKEN: {'Set' if TELEGRAM_TOKEN else 'Not Set'}")
    print(f"✅ SUPPORT_CHAT_ID: {'Set' if SUPPORT_CHAT_ID else 'Not Set'}")
    print(f"✅ OPENAI_API_KEY: {'Set' if OPENAI_API_KEY else 'Not Set'}")
    print(f"✅ OPENAI_CLIENT: {'Available' if openai_client else 'Not Available'}")
    print(f"✅ DATABASE: Enhanced schema at {DB_FILE}")
    print("🚀 FEATURES: AI Assistant, Progress Tracking, Multi-Language")
    print("🎯 FLOWS: New Player, Existing Player, Support")
    print("🛡️ ERROR HANDLING: Enhanced with conflict resolution")
    print("=" * 50)
    
    # Start the bot with enhanced configuration
    try:
        application.run_polling(
            poll_interval=1.0,
            timeout=30,
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
    except Conflict as e:
        logger.warning(f"Bot conflict on startup: {e}")
        print("⚠️ Another instance detected - normal in deployment")
    except Exception as e:
        logger.error(f"Failed to start enhanced bot: {e}")
        print(f"❌ Enhanced bot failed: {e}")

if __name__ == "__main__":
    main()

import logging
import os
import json
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,)

# Import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI package not available. AI features will be disabled.")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
SUPPORT_CHAT_ID = os.environ.get("SUPPORT_CHAT_ID")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///bot_data.db")

print("=" * 50)
print("ENVIRONMENT VARIABLES CHECK:")
print(f"TELEGRAM_TOKEN: {'✅ SET' if TELEGRAM_TOKEN else '❌ NOT SET'}")
print(f"SUPPORT_CHAT_ID: {'✅ SET' if SUPPORT_CHAT_ID else '❌ NOT SET'}")
print(f"OPENAI_API_KEY: {'✅ SET' if OPENAI_API_KEY else '❌ NOT SET'}")
print(f"OPENAI PACKAGE: {'✅ AVAILABLE' if OPENAI_AVAILABLE else '❌ NOT AVAILABLE'}")
print(f"DATABASE_URL: {'✅ SET' if DATABASE_URL else '❌ NOT SET'}")
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

# Database file path - Use a writable location
DB_FILE = "/tmp/bot_data.db" if os.path.exists("/tmp") else "bot_data.db"

# Initialize Database
def init_database():
    """Initialize SQLite database for user progress tracking"""
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                lang TEXT DEFAULT 'en',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                flow_type TEXT,
                step_name TEXT,
                step_data TEXT,
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                flow_data TEXT,
                status TEXT DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ Database initialized successfully at {DB_FILE}")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        # Continue without database - use in-memory storage as fallback
        print("⚠️ Using in-memory storage as fallback")

init_database()

HELPFUL_CHANNEL_LINK = "https://t.me/rejoinsnousetgagne"

# Define states
SELECT_LANG, MAIN_MENU, EXISTING_PLAYER_FLOW, NEW_PLAYER_FLOW, SUPPORT_FLOW, USERNAME_COLLECTION = range(6)

# Codes for the game
GAME_CODES = [
    "6086-7221-0564",
    "2753-4695-7191", 
    "9689-1352-5966",
    "4563-6624-9460",
    "4828-9033-2281"]

# --- FLOW DEFINITIONS ---
FLOW_QUESTIONS = {
    'new_player': [
        {'step': 'q1_vpn', 'question': 'Did you use a VPN?', 'type': 'yes_no'},
        {'step': 'q2_cloud_profile', 'question': 'Did you already create a cloud gaming profile?', 'type': 'yes_no_guidance'},
        {'step': 'q3_epic_code', 'question': 'Did you receive the code from Epic Games activation?', 'type': 'yes_no_guidance'},
        {'step': 'q4_epic_profile', 'question': 'Did you create your Epic Games profile?', 'type': 'yes_no_guidance'},
        {'step': 'q5_shortcut', 'question': 'Did you create a shortcut for the game?', 'type': 'yes_no_guidance'},
        {'step': 'q6_launch', 'question': 'Have you launched the game?', 'type': 'yes_no_guidance'},
        {'step': 'q7_reward_island', 'question': 'Have you searched and found the reward Island?', 'type': 'yes_no_guidance'},
        {'step': 'q8_full_setup', 'question': 'Did you follow the full setup instructions?', 'type': 'yes_no_guidance'},
        {'step': 'q9_play_time', 'question': 'Will you start the game and play 130 hours per week?', 'type': 'yes_no_ability'},
        {'step': 'q10_like_button', 'question': 'Will you click on the like button before each session ends?', 'type': 'yes_no_guidance'},
        {'step': 'q11_favorites', 'question': 'Will you save the reward Island to your favorites?', 'type': 'yes_no_guidance'},
        {'step': 'q12_influencer', 'question': 'Were you introduced to this game by an influencer?', 'type': 'influencer'}
    ],
    'existing_player': [
        {'step': 'q1_reward_island', 'question': 'Have you searched and found the reward Island?', 'type': 'yes_no_guidance'},
        {'step': 'q2_full_setup', 'question': 'Did you follow the full setup instructions?', 'type': 'yes_no_guidance'},
        {'step': 'q3_play_time', 'question': 'Did you start the game and play 130 hours per week?', 'type': 'yes_no_ability'},
        {'step': 'q4_like_button', 'question': 'Will you click on the like button before each session ends?', 'type': 'yes_no_guidance'},
        {'step': 'q5_favorites', 'question': 'Did you save the reward Island to your favorites?', 'type': 'yes_no_guidance'},
        {'step': 'q6_influencer', 'question': 'Were you introduced to this game by an influencer?', 'type': 'influencer'}
    ],
    'support': [
        {'step': 'q1_vpn', 'question': 'Did you use a VPN?', 'type': 'yes_no'},
        {'step': 'q2_cloud_profile', 'question': 'Did you already create a cloud gaming profile?', 'type': 'yes_no_guidance'},
        {'step': 'q3_epic_code', 'question': 'Did you receive the code from Epic Games activation?', 'type': 'yes_no_guidance'},
        {'step': 'q4_epic_profile', 'question': 'Did you create your Epic Games profile?', 'type': 'yes_no_guidance'},
        {'step': 'q5_shortcut', 'question': 'Did you create a shortcut for the game?', 'type': 'yes_no_guidance'},
        {'step': 'q6_launch', 'question': 'Have you launched the game?', 'type': 'yes_no_guidance'},
        {'step': 'q7_reward_island', 'question': 'Have you searched and found the reward Island?', 'type': 'yes_no_guidance'},
        {'step': 'q8_full_setup', 'question': 'Did you follow the full setup instructions?', 'type': 'yes_no_guidance'},
        {'step': 'q9_play_time', 'question': 'Did you start the game and play 130 hours per week?', 'type': 'yes_no_ability'},
        {'step': 'q10_like_button', 'question': 'Did you click on the like button before each session ends?', 'type': 'yes_no_guidance'},
        {'step': 'q11_favorites', 'question': 'Have you saved the reward Island to your favorites?', 'type': 'yes_no_guidance'},
        {'step': 'q12_influencer', 'question': 'Were you introduced to this game by an influencer?', 'type': 'influencer'},
        {'step': 'q13_completion', 'question': 'Did you complete every single step mentioned above?', 'type': 'yes_no_final'}
    ]
}

# --- COMPLETE KNOWLEDGE BASE ---
BOT_KNOWLEDGE_BASE = """
FORTNITE CLOUD GAMING BOT - COMPLETE KNOWLEDGE BASE

BOT PURPOSE:
This is a Telegram bot that helps users set up and play Fortnite through cloud gaming, specifically focusing on earning rewards through the reward island system.

GAME CODES FOR REWARD ISLAND:
{game_codes}

STRUCTURED FLOWS:
The bot has three main structured flows with specific questions. When a user is in a flow, guide them through the questions step by step.

NEW PLAYER FLOW QUESTIONS:
1. VPN Usage - Must use USA VPN for profile creation
2. Cloud Gaming Profile - Create at Xbox Cloud Gaming  
3. Epic Games Activation Code - Receive and enter activation code
4. Epic Games Profile - Create gaming profile
5. Shortcut Creation - Create homescreen shortcut
6. Game Launch - Launch Fortnite through cloud gaming
7. Reward Island - Search and find using game codes
8. Full Setup - Complete all configuration steps
9. Play Time - 130 hours per week requirement
10. Like Button - Click like button before each 1-hour session ends
11. Favorites - Save reward island to favorites
12. Influencer - Specify if introduced by influencer

EXISTING PLAYER FLOW QUESTIONS:
1. Reward Island Access - Have you found the reward island?
2. Full Setup Completion - Did you complete the full setup?
3. Play Time - 130 hours per week tracking
4. Like Button Usage - Regular usage during sessions
5. Favorites - Reward island in favorites
6. Influencer Attribution - Were you introduced by influencer?

SUPPORT FLOW QUESTIONS:
1-12. Same as New Player flow for troubleshooting
13. Final verification before support contact

USERNAME COLLECTION:
- After completing the support flow, ask for the user's Telegram username
- The username must start with @
- Send a detailed summary to the support team including:
  * User's Telegram username and ID
  * All flow answers and progress
  * Specific issues or needs identified
  * Conversation context if available

FLOW GUIDANCE:
- When user is in a structured flow, prioritize asking the next question in sequence
- Use button-based responses for flow questions (Yes/No/Guidance options)
- For "guidance" type questions, provide specific help when user needs assistance
- Track progress and remember where users left off

IMPORTANT LINKS:
- Cloud Gaming Profile: https://www.xbox.com/fr-FR/play/games/fortnite/BT5P2X999VH2
- Epic Games Activation: http://epicgames.com/activate
- Epic Games Profile: epicgames.com
- Game Launch: https://www.xbox.com/fr-FR/play/games/fortnite/BT5P2X999VH2
- Help Channel: {channel_link}

KEY REQUIREMENTS:
- VPN: Required only for initial profile creation (USA VPN)
- Play Time: 130 hours per week minimum
- Sessions: 1-hour sessions, must click like button before session ends
- Reward Island: Must be found using codes and saved to favorites
- Setup: Complete all steps before earning rewards

AI RESPONSE GUIDELINES:
- Be concise and directly address user's needs
- Use structured flows when appropriate
- Provide specific, actionable guidance
- Ask clarifying questions when needed
- Maintain conversation context
- Support both English and French
- Use callback codes for buttons, not display text

BUTTON CALLBACK CODES:
- new_player_start, existing_player_start, support_start
- back_to_main, continue_chat
- Flow answers: yes, no, need_guidance, already_done
""".format(game_codes=", ".join(GAME_CODES), channel_link=HELPFUL_CHANNEL_LINK)

# --- LANGUAGE STRINGS ---
STRINGS = {
    'en': {
        'disclaimer': "**Disclaimer:** This bot is an unofficial guide and is not affiliated with Epic Games or Fortnite. We will *never* ask for your password.",
        'lang_prompt': "Please select your language:",
        'welcome': "🤖 **AI-Powered Gaming Assistant**\n\nWelcome! I'm your intelligent assistant for Fortnite cloud gaming setup and rewards.",
        'new_player_btn': "🎮 New Player Setup",
        'existing_player_btn': "⚡ Existing Player",
        'helpful_channel_btn': "📚 Full Guide",
        'support_btn': "🆘 Support",
        'lang_btn': "🌐 Language",
        'helpful_channel_text': "Join our Telegram channel for complete guides and community:",
        'join_channel_btn': "Join Channel",
        'back_btn': "⬅️ Back",
        'ai_thinking': "🤔 Analyzing your question...",
        'ai_continue': "💬 Continue Chat",
        'ai_menu': "📱 Menu",
        'yes_btn': "✅ Yes",
        'no_btn': "❌ No",
        'need_guidance_btn': "🆘 I need guidance",
        'already_done_btn': "✅ Already done",
        'provide_influencer_btn': "👤 Provide influencer name",
        'skip_influencer_btn': "➡️ Skip",
        'flow_complete': "🎉 Flow completed! What would you like to do next?",
        'provide_username': "👤 **Support Contact**\n\nPlease provide your Telegram username (starting with @) so our support team can contact you:",
        'username_saved': "✅ Username saved! Our support team will contact you soon with the username you provided.",
        'invalid_username': "❌ Please provide a valid Telegram username starting with @ (example: @username)",
        'support_summary': "🆘 **New Support Request**\n\n👤 User: {username}\n🆔 User ID: {user_id}\n📋 Flow Type: {flow_type}\n\n📊 **Progress Summary:**\n{progress_summary}\n\n💬 **User Needs:** {user_needs}\n\nPlease contact the user to provide assistance.",
    },
    'fr': {
        'disclaimer': "**Avertissement :** Ce bot est un guide non officiel et n'est pas affilié à Epic Games ou Fortnite. Nous ne vous demanderons *jamais* votre mot de passe.",
        'lang_prompt': "Veuillez sélectionner votre langue :",
        'welcome': "🤖 **Assistant de Jeu IA**\n\nBienvenue ! Je suis votre assistant intelligent pour la configuration du jeu cloud Fortnite et les récompenses.",
        'new_player_btn': "🎮 Nouveau Joueur",
        'existing_player_btn': "⚡ Joueur Existant", 
        'helpful_channel_btn': "📚 Guide Complet",
        'support_btn': "🆘 Support",
        'lang_btn': "🌐 Langue",
        'helpful_channel_text': "Rejoignez notre canal Telegram pour des guides complets et la communauté :",
        'join_channel_btn': "Rejoindre le Canal",
        'back_btn': "⬅️ Retour",
        'ai_thinking': "🤔 Analyse de votre question...",
        'ai_continue': "💬 Continuer",
        'ai_menu': "📱 Menu",
        'yes_btn': "✅ Oui",
        'no_btn': "❌ Non",
        'need_guidance_btn': "🆘 J'ai besoin d'aide",
        'already_done_btn': "✅ Déjà fait",
        'provide_influencer_btn': "👤 Donner le nom de l'influenceur",
        'skip_influencer_btn': "➡️ Passer",
        'flow_complete': "🎉 Parcours terminé ! Que souhaitez-vous faire ensuite ?",
        'provide_username': "👤 **Contact Support**\n\nVeuillez fournir votre nom d'utilisateur Telegram (commençant par @) pour que notre équipe puisse vous contacter :",
        'username_saved': "✅ Nom d'utilisateur enregistré ! Notre équipe de support vous contactera bientôt avec le nom d'utilisateur que vous avez fourni.",
        'invalid_username': "❌ Veuillez fournir un nom d'utilisateur Telegram valide commençant par @ (exemple: @utilisateur)",
        'support_summary': "🆘 **Nouvelle Demande de Support**\n\n👤 Utilisateur: {username}\n🆔 ID Utilisateur: {user_id}\n📋 Type de Parcours: {flow_type}\n\n📊 **Résumé de la Progression:**\n{progress_summary}\n\n💬 **Besoins de l'Utilisateur:** {user_needs}\n\nVeuillez contacter l'utilisateur pour fournir une assistance.",
    }
}

# --- DATABASE FUNCTIONS ---
def get_user_data(user_id):
    """Get user data from database"""
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        
        cursor.execute('SELECT * FROM user_progress WHERE user_id = ? ORDER BY created_at', (user_id,))
        progress = cursor.fetchall()
        
        conn.close()
        
        user_data = {}
        if user:
            user_data = {
                'user_id': user[0],
                'username': user[1],
                'lang': user[2]
            }
        
        progress_data = {}
        for p in progress:
            progress_data[p[2]] = {
                'step_data': p[3],
                'completed': bool(p[4])
            }
        
        return user_data, progress_data
    except Exception as e:
        logger.error(f"Database error in get_user_data: {e}")
        return {}, {}

def save_user_data(user_id, username=None, lang=None):
    """Save or update user data"""
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, username, lang, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, username, lang))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Database error in save_user_data: {e}")
        return False

def save_progress(user_id, flow_type, step_name, step_data, completed=True):
    """Save user progress for a flow step"""
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_progress (user_id, flow_type, step_name, step_data, completed)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, flow_type, step_name, step_data, completed))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Database error in save_progress: {e}")
        return False

def create_support_ticket(user_id, username, flow_data):
    """Create a support ticket"""
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO support_tickets (user_id, username, flow_data)
            VALUES (?, ?, ?)
        ''', (user_id, username, json.dumps(flow_data)))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Database error in create_support_ticket: {e}")
        return False

# --- AI BRAIN CORE FUNCTION ---
async def ai_brain_response(user_message: str, user_context: dict, lang: str) -> dict:
    """AI Brain: Processes user messages and provides intelligent responses"""
    if not openai_client:
        return {
            "response": "I'm currently unavailable. Please try again later.",
            "buttons": ["menu"],
            "next_action": "menu"
        }
    
    try:
        # Get user data and context
        user_id = user_context['user_data']['user_id']
        current_flow = user_context.get('current_flow', 'general')
        conversation_history = user_context.get('conversation_history', [])
        
        # Get user progress from database
        user_data, progress_data = get_user_data(user_id)
        
        # Prepare system prompt
        system_prompt = f"""You are the AI brain of a Fortnite cloud gaming Telegram bot.

{BOT_KNOWLEDGE_BASE}

CURRENT USER CONTEXT:
- User ID: {user_id}
- Language: {lang.upper()}
- Current Flow: {current_flow}
- User Progress: {progress_data}

USER'S MESSAGE: "{user_message}"

RESPONSE REQUIREMENTS:
1. Be CONCISE and directly address the user's need
2. If user is in a structured flow, guide them to the next question
3. Use callback codes for buttons, NOT display text
4. Provide specific, actionable guidance
5. Ask clarifying questions if needed

RESPONSE FORMAT (JSON):
{{
    "response": "Your concise response",
    "buttons": ["callback_code1", "callback_code2", ...],
    "next_action": "continue/menu/start_flow/next_question",
    "flow_step": "step_name_if_applicable"
}}

Available button callback codes:
- Navigation: menu, back_to_main, continue_chat
- Flow starters: new_player_start, existing_player_start, support_start  
- Flow answers: yes, no, need_guidance, already_done, provide_influencer, skip_influencer
- Channel: join_channel"""

        # Build message history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        for msg in conversation_history[-4:]:
            messages.append(msg)
        
        messages.append({"role": "user", "content": user_message})
        
        # Generate AI response
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Parse JSON response
        try:
            parsed_response = json.loads(ai_response)
            
            # Ensure buttons use valid callback codes
            valid_codes = ['menu', 'back_to_main', 'continue_chat', 'new_player_start', 
                          'existing_player_start', 'support_start', 'yes', 'no', 
                          'need_guidance', 'already_done', 'provide_influencer', 
                          'skip_influencer', 'join_channel']
            
            filtered_buttons = [btn for btn in parsed_response.get('buttons', []) if btn in valid_codes]
            if not filtered_buttons and parsed_response.get('next_action') != 'next_question':
                filtered_buttons = ['menu', 'continue_chat']
            
            parsed_response['buttons'] = filtered_buttons
            return parsed_response
            
        except json.JSONDecodeError:
            logger.warning("AI response not in JSON format, using fallback")
            return {
                "response": ai_response,
                "buttons": ["menu", "continue_chat"],
                "next_action": "continue"
            }
            
    except Exception as e:
        logger.error(f"Error in AI brain: {e}")
        return {
            "response": "I'm having trouble processing your request. Please try again.",
            "buttons": ["menu"],
            "next_action": "menu"
        }

# --- FLOW MANAGEMENT FUNCTIONS ---
async def start_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, flow_type: str):
    """Start a structured flow"""
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = update.effective_user.id
    lang = context.user_data.get('lang', 'en')
    
    # Set flow context
    context.user_data['current_flow'] = flow_type
    context.user_data['flow_type'] = flow_type
    context.user_data['current_question'] = 0
    
    # Save user data
    save_user_data(user_id, lang=lang)
    
    # Start with first question
    return await ask_flow_question(update, context)

async def ask_flow_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask the current flow question"""
    user_id = update.effective_user.id
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    flow_type = context.user_data.get('flow_type')
    current_question = context.user_data.get('current_question', 0)
    
    if flow_type not in FLOW_QUESTIONS or current_question >= len(FLOW_QUESTIONS[flow_type]):
        return await complete_flow(update, context)
    
    question_data = FLOW_QUESTIONS[flow_type][current_question]
    question_text = question_data['question']
    question_type = question_data['type']
    
    # Create appropriate keyboard based on question type
    keyboard = []
    
    if question_type == 'yes_no':
        keyboard = [
            [InlineKeyboardButton(s['yes_btn'], callback_data="yes")],
            [InlineKeyboardButton(s['no_btn'], callback_data="no")]
        ]
    elif question_type == 'yes_no_guidance':
        keyboard = [
            [InlineKeyboardButton(s['yes_btn'], callback_data="yes")],
            [InlineKeyboardButton(s['no_btn'], callback_data="no")],
            [InlineKeyboardButton(s['need_guidance_btn'], callback_data="need_guidance")]
        ]
    elif question_type == 'yes_no_ability':
        keyboard = [
            [InlineKeyboardButton(s['yes_btn'], callback_data="yes")],
            [InlineKeyboardButton(s['no_btn'], callback_data="no")],
            [InlineKeyboardButton(s['already_done_btn'], callback_data="already_done")]
        ]
    elif question_type == 'influencer':
        keyboard = [
            [InlineKeyboardButton(s['provide_influencer_btn'], callback_data="provide_influencer")],
            [InlineKeyboardButton(s['skip_influencer_btn'], callback_data="skip_influencer")]
        ]
    elif question_type == 'yes_no_final':
        keyboard = [
            [InlineKeyboardButton(s['yes_btn'], callback_data="yes")],
            [InlineKeyboardButton(s['no_btn'], callback_data="no")]
        ]
    
    # Add navigation
    keyboard.append([InlineKeyboardButton(s['ai_menu'], callback_data="back_to_main")])
    
    # Send question
    query = update.callback_query
    if query:
        await query.edit_message_text(
            text=f"**{question_text}**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            text=f"**{question_text}**", 
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # Set appropriate state based on flow type
    if flow_type == 'new_player':
        context.user_data['current_state'] = NEW_PLAYER_FLOW
        return NEW_PLAYER_FLOW
    elif flow_type == 'existing_player':
        context.user_data['current_state'] = EXISTING_PLAYER_FLOW
        return EXISTING_PLAYER_FLOW
    elif flow_type == 'support':
        context.user_data['current_state'] = SUPPORT_FLOW
        return SUPPORT_FLOW
    
    return MAIN_MENU

async def handle_flow_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, answer: str):
    """Handle user's answer to flow question"""
    user_id = update.effective_user.id
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    flow_type = context.user_data.get('flow_type')
    current_question = context.user_data.get('current_question', 0)
    
    if flow_type not in FLOW_QUESTIONS or current_question >= len(FLOW_QUESTIONS[flow_type]):
        return await complete_flow(update, context)
    
    question_data = FLOW_QUESTIONS[flow_type][current_question]
    
    # Save progress
    save_progress(user_id, flow_type, question_data['step'], answer)
    
    # Handle special cases
    if answer == 'need_guidance':
        # Provide guidance based on current question
        guidance_text = await get_question_guidance(question_data, lang)
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            text=guidance_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(s['yes_btn'], callback_data="yes")],
                [InlineKeyboardButton(s['ai_menu'], callback_data="back_to_main")]
            ]),
            parse_mode='Markdown'
        )
        return context.user_data.get('current_state', MAIN_MENU)
    
    elif answer == 'provide_influencer':
        await ask_influencer_name(update, context)
        return context.user_data.get('current_state', MAIN_MENU)
    
    # Move to next question
    context.user_data['current_question'] = current_question + 1
    
    # For support flow, check if we need to collect username
    if flow_type == 'support' and current_question + 1 >= len(FLOW_QUESTIONS[flow_type]):
        return await ask_username(update, context)
    
    return await ask_flow_question(update, context)

async def get_question_guidance(question_data: dict, lang: str) -> str:
    """Get guidance text for a specific question"""
    step = question_data['step']
    
    guidance_texts = {
        'q1_vpn': {
            'en': "🔧 **VPN Guidance**\n\nYou need to use a USA VPN only for the initial profile creation (not for playing). Download a VPN app and connect to a USA server before creating your cloud gaming profile.",
            'fr': "🔧 **Guide VPN**\n\nVous devez utiliser un VPN USA uniquement pour la création du profil initial (pas pour jouer). Téléchargez une application VPN et connectez-vous à un serveur USA avant de créer votre profil cloud gaming."
        },
        'q2_cloud_profile': {
            'en': "🔧 **Cloud Profile Guidance**\n\nCreate your cloud gaming profile at: https://www.xbox.com/fr-FR/play/games/fortnite/BT5P2X999VH2\n\nMake sure you're using USA VPN during this step!",
            'fr': "🔧 **Guide Profil Cloud**\n\nCréez votre profil cloud gaming sur : https://www.xbox.com/fr-FR/play/games/fortnite/BT5P2X999VH2\n\nAssurez-vous d'utiliser un VPN USA pendant cette étape !"
        },
        # Add more guidance texts for other questions...
    }
    
    default_guidance = {
        'en': "🔧 **Guidance**\n\nPlease follow the instructions carefully. If you need more detailed help, join our channel for complete guides and community support.",
        'fr': "🔧 **Guide**\n\nVeuillez suivre les instructions attentivement. Si vous avez besoin d'aide plus détaillée, rejoignez notre canal pour des guides complets et le support communautaire."
    }
    
    guidance = guidance_texts.get(step, default_guidance)
    return guidance.get(lang, guidance['en'])

async def ask_influencer_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for influencer name"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="👤 **Influencer Information**\n\nPlease provide the name of the influencer who introduced you to this game:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(s['skip_influencer_btn'], callback_data="skip_influencer")],
            [InlineKeyboardButton(s['ai_menu'], callback_data="back_to_main")]
        ]),
        parse_mode='Markdown'
    )

async def ask_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for username for support contact"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(
            text=s['provide_username'],
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(s['ai_menu'], callback_data="back_to_main")]
            ]),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            text=s['provide_username'],
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(s['ai_menu'], callback_data="back_to_main")]
            ]),
            parse_mode='Markdown'
        )
    
    context.user_data['current_state'] = USERNAME_COLLECTION
    return USERNAME_COLLECTION

async def complete_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Complete the current flow"""
    user_id = update.effective_user.id
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    flow_type = context.user_data.get('flow_type')
    
    # Clear flow context
    context.user_data['current_flow'] = 'general'
    context.user_data['flow_type'] = None
    context.user_data['current_question'] = None
    
    keyboard = [
        [InlineKeyboardButton(s['ai_continue'], callback_data="continue_chat")],
        [InlineKeyboardButton(s['ai_menu'], callback_data="back_to_main")]
    ]
    
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(
            text=s['flow_complete'],
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            text=s['flow_complete'],
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    context.user_data['current_state'] = MAIN_MENU
    return MAIN_MENU

# --- CORE MESSAGE HANDLER (AI BRAIN) ---
async def handle_any_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Main message handler - ALL text messages go through the AI brain"""
    user_message = update.message.text
    user_id = update.message.from_user.id
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Show thinking indicator
    thinking_msg = await update.message.reply_text(s['ai_thinking'])
    
    # Prepare user context for AI
    user_context = {
        'conversation_history': context.user_data.get('conversation_history', []),
        'current_flow': context.user_data.get('current_flow', 'general'),
        'user_data': {
            'user_id': user_id,
            'language': lang,
            'flow_type': context.user_data.get('flow_type', 'unknown')
        }
    }
    
    # Get AI brain response
    ai_response = await ai_brain_response(user_message, user_context, lang)
    
    # Update conversation history
    if 'conversation_history' not in context.user_data:
        context.user_data['conversation_history'] = []
    
    context.user_data['conversation_history'].append({"role": "user", "content": user_message})
    context.user_data['conversation_history'].append({"role": "assistant", "content": ai_response['response']})
    
    # Keep only last 10 messages to manage context size
    context.user_data['conversation_history'] = context.user_data['conversation_history'][-10:]
    
    # Create keyboard from AI-suggested buttons
    keyboard = []
    buttons = ai_response.get('buttons', [])
    
    for callback_data in buttons:
        if callback_data == 'menu':
            keyboard.append([InlineKeyboardButton(s['ai_menu'], callback_data="back_to_main")])
        elif callback_data == 'continue_chat':
            keyboard.append([InlineKeyboardButton(s['ai_continue'], callback_data="continue_chat")])
        elif callback_data == 'new_player_start':
            keyboard.append([InlineKeyboardButton(s['new_player_btn'], callback_data="new_player_start")])
        elif callback_data == 'existing_player_start':
            keyboard.append([InlineKeyboardButton(s['existing_player_btn'], callback_data="existing_player_start")])
        elif callback_data == 'support_start':
            keyboard.append([InlineKeyboardButton(s['support_btn'], callback_data="support_start")])
        elif callback_data == 'join_channel':
            keyboard.append([InlineKeyboardButton(s['join_channel_btn'], url=HELPFUL_CHANNEL_LINK)])
        elif callback_data in ['yes', 'no', 'need_guidance', 'already_done', 'provide_influencer', 'skip_influencer']:
            # Flow answer buttons - handled in flow functions
            btn_text = {
                'yes': s['yes_btn'],
                'no': s['no_btn'], 
                'need_guidance': s['need_guidance_btn'],
                'already_done': s['already_done_btn'],
                'provide_influencer': s['provide_influencer_btn'],
                'skip_influencer': s['skip_influencer_btn']
            }.get(callback_data, callback_data)
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=callback_data)])
    
    # Always include menu if no buttons
    if not keyboard:
        keyboard.append([InlineKeyboardButton(s['ai_menu'], callback_data="back_to_main")])
    
    # Update thinking message with actual response
    await thinking_msg.edit_text(
        text=ai_response['response'],
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    # Handle next action suggested by AI
    next_action = ai_response.get('next_action', 'continue')
    
    if next_action == 'menu':
        return await show_main_menu(update, context)
    elif next_action == 'start_flow':
        flow_type = ai_response.get('flow_type', 'new_player')
        return await start_flow(update, context, flow_type)
    elif next_action == 'next_question':
        return await ask_flow_question(update, context)
    
    # Default: continue in current state
    current_state = context.user_data.get('current_state', MAIN_MENU)
    return current_state

# --- HELPER FUNCTIONS ---
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str = None):
    """Show main menu"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    context.user_data['current_flow'] = 'general'
    context.user_data['current_state'] = MAIN_MENU
    
    keyboard = [
        [InlineKeyboardButton(s['new_player_btn'], callback_data="new_player_start")],
        [InlineKeyboardButton(s['existing_player_btn'], callback_data="existing_player_start")],
        [InlineKeyboardButton(s['helpful_channel_btn'], callback_data="helpful_channel")],
        [InlineKeyboardButton(s['support_btn'], callback_data="support_start")],
    ]
    
    query = update.callback_query
    text_to_show = message or s['welcome']
    
    if query:
        await query.answer()
        try:
            await query.edit_message_text(
                text=text_to_show,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.warning(f"Failed to edit message: {e}")
    else:
        await update.message.reply_text(
            text=text_to_show,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    return MAIN_MENU

async def continue_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Continue chat callback"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    await query.edit_message_text(
        text="💬 **I'm listening! What would you like to know or what help do you need?**\n\nType your question and I'll help you with anything related to Fortnite cloud gaming setup and rewards.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(s['ai_menu'], callback_data="back_to_main")]
        ]),
        parse_mode='Markdown'
    )
    
    return context.user_data.get('current_state', MAIN_MENU)

async def show_helpful_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show channel link"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton(s['join_channel_btn'], url=HELPFUL_CHANNEL_LINK)],
        [InlineKeyboardButton(s['back_btn'], callback_data="back_to_main")]
    ]
    await query.edit_message_text(
        text=s['helpful_channel_text'],
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )
    
    return MAIN_MENU

async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle username collection for support"""
    username = update.message.text.strip()
    user_id = update.message.from_user.id
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    if not username.startswith('@'):
        await update.message.reply_text(
            text=s['invalid_username'],
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(s['ai_menu'], callback_data="back_to_main")]
            ])
        )
        return USERNAME_COLLECTION
    
    # Save username
    save_user_data(user_id, username=username)
    
    # Get user progress and create support summary
    user_data, progress_data = get_user_data(user_id)
    flow_type = context.user_data.get('flow_type', 'support')
    
    # Create progress summary
    progress_summary = ""
    for step, data in progress_data.items():
        status = "✅" if data.get('completed') else "❌"
        progress_summary += f"{status} {step}: {data.get('step_data', 'No data')}\n"
    
    if not progress_summary:
        progress_summary = "No progress data available"
    
    # Determine user needs based on progress
    user_needs = "Technical support and setup assistance"
    if progress_data:
        incomplete_steps = [step for step, data in progress_data.items() if not data.get('completed')]
        if incomplete_steps:
            user_needs = f"Help with steps: {', '.join(incomplete_steps)}"
    
    # Create support ticket
    create_support_ticket(user_id, username, progress_data)
    
    # Send detailed summary to support chat
    if SUPPORT_CHAT_ID:
        try:
            support_text = s['support_summary'].format(
                username=username,
                user_id=user_id,
                flow_type=flow_type,
                progress_summary=progress_summary,
                user_needs=user_needs
            )
            
            await context.bot.send_message(
                chat_id=int(SUPPORT_CHAT_ID),
                text=support_text,
                parse_mode='Markdown'
            )
            print(f"✅ Support request sent to chat {SUPPORT_CHAT_ID}")
        except Exception as e:
            logger.error(f"Failed to send to support chat: {e}")
            print(f"❌ Failed to send support request: {e}")
    
    await update.message.reply_text(
        text=s['username_saved'],
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(s['ai_menu'], callback_data="back_to_main")]
        ])
    )
    
    return await show_main_menu(update, context)

# --- BASIC HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start command"""
    text = (
        f"{STRINGS['en']['disclaimer']}\n\n"
        f"{STRINGS['fr']['disclaimer']}\n\n"
        "------\n\n"
        f"{STRINGS['en']['lang_prompt']}\n\n"
        f"{STRINGS['fr']['lang_prompt']}"
    )

    keyboard = [
        [
            InlineKeyboardButton("English 🇬🇧", callback_data="en"),
            InlineKeyboardButton("Français 🇫🇷", callback_data="fr"),
        ]
    ]
    
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(
            text=text, 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            disable_web_page_preview=True,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            text=text, 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            disable_web_page_preview=True,
            parse_mode='Markdown'
        )
        
    return SELECT_LANG

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Set language"""
    query = update.callback_query
    lang = query.data
    context.user_data['lang'] = lang
    
    # Save language preference
    user_id = update.effective_user.id
    save_user_data(user_id, lang=lang)
    
    return await show_main_menu(update, context)

def main() -> None:
    """Run the AI-powered bot"""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN environment variable not set!")
        print("❌ ERROR: TELEGRAM_TOKEN environment variable is required!")
        return

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_LANG: [
                CallbackQueryHandler(set_language, pattern="^(en|fr)$")
            ],
            MAIN_MENU: [
                CallbackQueryHandler(lambda u, c: start_flow(u, c, 'new_player'), pattern="^new_player_start$"),
                CallbackQueryHandler(lambda u, c: start_flow(u, c, 'existing_player'), pattern="^existing_player_start$"),
                CallbackQueryHandler(show_helpful_channel, pattern="^helpful_channel$"),
                CallbackQueryHandler(lambda u, c: start_flow(u, c, 'support'), pattern="^support_start$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
                CallbackQueryHandler(continue_chat, pattern="^continue_chat$"),
                # ALL text messages go to AI brain
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_any_message),
            ],
            NEW_PLAYER_FLOW: [
                CallbackQueryHandler(lambda u, c: handle_flow_answer(u, c, 'yes'), pattern="^yes$"),
                CallbackQueryHandler(lambda u, c: handle_flow_answer(u, c, 'no'), pattern="^no$"),
                CallbackQueryHandler(lambda u, c: handle_flow_answer(u, c, 'need_guidance'), pattern="^need_guidance$"),
                CallbackQueryHandler(lambda u, c: handle_flow_answer(u, c, 'already_done'), pattern="^already_done$"),
                CallbackQueryHandler(lambda u, c: handle_flow_answer(u, c, 'provide_influencer'), pattern="^provide_influencer$"),
                CallbackQueryHandler(lambda u, c: handle_flow_answer(u, c, 'skip_influencer'), pattern="^skip_influencer$"),
                CallbackQueryHandler(continue_chat, pattern="^continue_chat$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
                # ALL text messages go to AI brain
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_any_message),
            ],
            EXISTING_PLAYER_FLOW: [
                CallbackQueryHandler(lambda u, c: handle_flow_answer(u, c, 'yes'), pattern="^yes$"),
                CallbackQueryHandler(lambda u, c: handle_flow_answer(u, c, 'no'), pattern="^no$"),
                CallbackQueryHandler(lambda u, c: handle_flow_answer(u, c, 'need_guidance'), pattern="^need_guidance$"),
                CallbackQueryHandler(lambda u, c: handle_flow_answer(u, c, 'already_done'), pattern="^already_done$"),
                CallbackQueryHandler(lambda u, c: handle_flow_answer(u, c, 'provide_influencer'), pattern="^provide_influencer$"),
                CallbackQueryHandler(lambda u, c: handle_flow_answer(u, c, 'skip_influencer'), pattern="^skip_influencer$"),
                CallbackQueryHandler(continue_chat, pattern="^continue_chat$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
                # ALL text messages go to AI brain
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_any_message),
            ],
            SUPPORT_FLOW: [
                CallbackQueryHandler(lambda u, c: handle_flow_answer(u, c, 'yes'), pattern="^yes$"),
                CallbackQueryHandler(lambda u, c: handle_flow_answer(u, c, 'no'), pattern="^no$"),
                CallbackQueryHandler(lambda u, c: handle_flow_answer(u, c, 'need_guidance'), pattern="^need_guidance$"),
                CallbackQueryHandler(lambda u, c: handle_flow_answer(u, c, 'already_done'), pattern="^already_done$"),
                CallbackQueryHandler(lambda u, c: handle_flow_answer(u, c, 'provide_influencer'), pattern="^provide_influencer$"),
                CallbackQueryHandler(lambda u, c: handle_flow_answer(u, c, 'skip_influencer'), pattern="^skip_influencer$"),
                CallbackQueryHandler(continue_chat, pattern="^continue_chat$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
                # ALL text messages go to AI brain
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_any_message),
            ],
            USERNAME_COLLECTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
        ],
    )

    application.add_handler(conv_handler)

    logger.info("AI-Powered Bot is running...")
    print("🤖 AI-Powered Bot is starting...")
    print(f"✅ TELEGRAM_TOKEN: {'Set' if TELEGRAM_TOKEN else 'Not Set'}")
    print(f"✅ SUPPORT_CHAT_ID: {'Set' if SUPPORT_CHAT_ID else 'Not Set'}")
    print(f"✅ OPENAI_API_KEY: {'Set' if OPENAI_API_KEY else 'Not Set'}")
    print(f"✅ OPENAI_CLIENT: {'Available' if openai_client else 'Not Available'}")
    print(f"✅ DATABASE: Initialized at {DB_FILE}")
    print("🚀 ALL messages will be processed by AI Brain!")
    print("📊 User progress tracking: ENABLED")
    print("👤 Username collection for support: ENABLED")
    
    application.run_polling()

if __name__ == "__main__":
    main()

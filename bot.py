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

print("=" * 50)
print("ENHANCED EXISTING PLAYER BOT - ENVIRONMENT CHECK:")
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
DB_FILE = "/tmp/existing_player_bot.db" if os.path.exists("/tmp") else "existing_player_bot.db"

# Initialize Database
def init_database():
    """Initialize SQLite database for user progress tracking"""
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_progress (
                user_id INTEGER PRIMARY KEY,
                current_step INTEGER DEFAULT 1,
                completed_steps TEXT DEFAULT '[]',
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
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_conversations (
                conversation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                user_message TEXT,
                ai_response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

# Define states
SELECT_LANG, MAIN_MENU, EXISTING_PLAYER_FLOW, USERNAME_COLLECTION, AI_CHAT = range(5)

# Codes for the game
GAME_CODES = [
    "6086-7221-0564",
    "2753-4695-7191", 
    "9689-1352-5966",
    "4563-6624-9460",
    "4828-9033-2281"]

# --- ENHANCED LANGUAGE STRINGS ---
STRINGS = {
    'en': {
        'disclaimer': "**Disclaimer:** This bot is an unofficial guide and is not affiliated with Epic Games or Fortnite. We will *never* ask for your password.",
        'lang_prompt': "Please select your language:",
        'welcome': "🏆 Welcome Back Existing Player! Let's continue your gaming journey and maximize your rewards.",
        'helpful_channel_btn': "📚 Full Guide Channel",
        'support_btn': "🆘 Support",
        'ai_chat_btn': "🤖 AI Assistant",
        'lang_btn': "🌐 Change Language",
        'helpful_channel_text': "Join our helpful Telegram channel for the full guide, news, and community chat!",
        'join_channel_btn': "Join Channel Now",
        'back_btn': "⬅️ Back to Main Menu",
        'support_q2': "Okay. By providing your @username, you consent to our support team contacting you directly on Telegram. We will *only* use this to help with your question.\n\nPlease type your @username (like @myusername) to proceed.\n\nType /cancel to go back.",
        'support_thanks': "Thank you! Your @username has been noted. We will get in touch with you as soon as possible.\n\nReturning you to the main menu.",
        'support_cancel': "Support request cancelled. Returning to main menu.",
        'invalid_username': "That doesn't look like a valid @username. Please start with '@' and try again, or type /cancel.",
        
        # AI Chat
        'ai_welcome': "🤖 **AI Gaming Assistant**\n\nHello! I'm your AI gaming assistant. Ask me anything about:\n\n• Game setup & configuration\n• Reward system & earning tips\n• Troubleshooting issues\n• Best practices for maximum rewards\n\n*Type your question below or use the menu to return:*",
        'ai_thinking': "💭 Thinking...",
        'ai_support_suggestion': "\n\n🔔 *If you need personalized support, consider using the Support option in the main menu.*",
        'back_to_chat': "💬 Back to Chat",
        
        # Button texts
        'a_yes': "✅ Yes",
        'b_no': "❌ No",
        'yes_im_ready': "✅ Yes, I'm ready for the next step",
        'want_codes': "✅ Yes I want the best codes to play",
        'already_chose': "❌ No, I already chose one code",
        'finally_fixed': "✅ No I finally fix everything, I want to move to the next step",
        'will_play': "❌ No, I will play and let you know in the support session later on",
        'have_proof': "✅ No, I have proof I saved the reward Island to my favorites and I actually play on it",
        'next_question': "➡️ Next Question",
        'join_channel_only': "📚 Join Channel",
        
        # Specific custom buttons
        'b_1_yes': "✅ Yes",
        'b_2_no': "❌ No",
        'b_1_want_codes': "✅ Yes I want the best codes to play",
        'b_2_already_chose': "❌ No, I already chose one code",
        'b_1_guidance': "✅ Yes",
        'b_2_finally_fixed': "✅ No I finally fix everything, I want to move to the next step",
        'b_2_will_play': "❌ No, I will play and let you know in the support session later on",
        'b_2_have_proof': "✅ No, I have proof I saved the reward Island to my favorites and I actually play on it",
        
        # Code messages
        'codes_title': "🎮 **Best Game Codes:**\n\nJust copy one of them and enter it on the search bar:\n\n",
        
        # Navigation
        'back_to_previous': "⬅️ Back",
        'main_menu': "🏠 Main Menu",
        
        # Influencer question
        'provide_name': "Provide the name please:",
        
        # Existing player flow - UPDATED
        'existing_player_intro': "🎮 **Existing Player Check-In**\n\nBecause you are playing on the cloud, your session will last for 1 hour. The game will close, and you will have to launch it again to keep playing.\n\nYou probably know it cause you already follow all the instructions\n\n**1. Have you searched and found the reward Island?**",
        'existing_q2_text': "**2. Did you follow the full setup to be able to play with friends and earn a lot together without any worries?**",
        'existing_q3_text': "**3. Did you start the game and play 130 hours for free this week?**",
        'existing_q4_text': "**4. With your existing account, will you click on the like button every single time before your 1 hour play session ended during your 130 hours of play this week?**",
        'existing_q5_text': "**5. Did you save the reward Island to your favorites?**",
        'existing_q6_text': "**6. Were you introduced to this game by an influencer?**",
        
        # Common responses - UPDATED
        'reward_island_reminder': "🔍 **Reward Island Reminder**\n\nNo, you have to search the reward Island in the search bar and just choose it. Do you want our guidance for that?",
        'full_setup_reminder': "⚙️ **Full Setup Reminder**\n\nNo, you have to follow the exact setup. Do you need our guidance?",
        'play_hours_reminder': "⏰ **Play Hours Reminder**\n\nNo, you have to start the game and play every single day for free before aiming for the reward. Are you able to play at least 130 hours a week?",
        'like_button_reminder': "👍 **Like Button Reminder**\n\nNo, You have to click on the like button every single time before your 1 hour play session ended during your 130 hours a week. Do you want our guidance on that?",
        'favorites_reminder': "⭐ **Favorites Reminder**\n\nNo, you have to save the reward Island to your favorites and play. Do you want our guidance on that?",
        
        # Links and guidance
        'channel_instruction_9': "📖 **Instruction 9**\n\nPlease check our channel and look for instruction 9:",
        'channel_instruction_10': "📖 **Instruction 10**\n\nPlease check our channel and look for instruction 10:",
        'channel_instruction_11': "📖 **Instruction 11**\n\nPlease check our channel and look for instruction 11:",
        'channel_instruction_12': "📖 **Instruction 12**\n\nPlease check our channel and look for instruction 12:",
        'channel_instruction_13': "📖 **Instruction 13**\n\nPlease check our channel and look for instruction 13:",
    },
    'fr': {
        'disclaimer': "**Avertissement :** Ce bot est un guide non officiel et n'est pas affilié à Epic Games ou Fortnite. Nous ne vous demanderons *jamais* votre mot de passe.",
        'lang_prompt': "Veuillez sélectionner votre langue :",
        'welcome': "🏆 Bienvenue Joueur Existant ! Continuons votre aventure de jeu et maximisons vos récompenses.",
        'helpful_channel_btn': "📚 Guide Complet Chaîne",
        'support_btn': "🆘 Support",
        'ai_chat_btn': "🤖 Assistant IA",
        'lang_btn': "🌐 Changer de Langue",
        'helpful_channel_text': "Rejoignez notre canal Telegram pour le guide complet, les actualités et pour discuter avec la communauté !",
        'join_channel_btn': "Rejoindre le Canal",
        'back_btn': "⬅️ Retour au Menu Principal",
        'support_q2': "D'accord. En fournissant votre @nomdutilisateur, vous acceptez que notre équipe d'assistance vous contacte directement sur Telegram. Nous l'utiliserons *uniquement* pour répondre à votre question.\n\nVeuillez taper votre @nomdutilisateur (comme @monpseudo) pour continuer.\n\nTapez /cancel pour revenir.",
        'support_thanks': "Merci ! Votre @nomdutilisateur a été noté. Nous vous contacterons dès que possible.\n\nRetour au menu principal.",
        'support_cancel': "Demande d'aide annulée. Retour au menu principal.",
        'invalid_username': "Cela ne ressemble pas à un @nomdutilisateur valide. Veuillez commencer par '@' et réessayer, ou tapez /cancel.",
        
        # AI Chat - French
        'ai_welcome': "🤖 **Assistant IA Gaming**\n\nBonjour! Je suis votre assistant IA gaming. Demandez-moi n'importe quoi sur:\n\n• Configuration jeu & paramètres\n• Système de récompenses & conseils de gains\n• Résolution de problèmes\n• Meilleures pratiques pour des récompenses maximum\n\n*Tapez votre question ci-dessous ou utilisez le menu pour revenir:*",
        'ai_thinking': "💭 Réflexion...",
        'ai_support_suggestion': "\n\n🔔 *Si vous avez besoin d'un support personnalisé, envisagez d'utiliser l'option Support dans le menu principal.*",
        'back_to_chat': "💬 Retour au Chat",
        
        # Button texts - French - UPDATED
        'a_yes': "✅ Oui",
        'b_no': "❌ Non",
        'yes_im_ready': "✅ Oui, je suis prêt pour l'étape suivante",
        'want_codes': "✅ Oui je veux les meilleurs codes pour jouer",
        'already_chose': "❌ Non, j'ai déjà choisi un code",
        'finally_fixed': "✅ Non j'ai finalement tout réparé, je veux passer à l'étape suivante",
        'will_play': "❌ Non, je vais jouer et vous tiens au courant lors de la session de support",
        'have_proof': "✅ Non, j'ai la preuve que je l'ai sauvegardé et que j'y joue réellement",
        'next_question': "➡️ Question Suivante",
        'join_channel_only': "📚 Rejoindre le Canal",
        
        # Specific custom buttons - French - UPDATED
        'b_1_yes': "✅ Oui",
        'b_2_no': "❌ Non",
        'b_1_want_codes': "✅ Oui je veux les meilleurs codes pour jouer",
        'b_2_already_chose': "❌ Non, j'ai déjà choisi un code",
        'b_1_guidance': "✅ Oui",
        'b_2_finally_fixed': "✅ Non j'ai finalement tout réparé, je veux passer à l'étape suivante",
        'b_2_will_play': "❌ Non, je vais jouer et vous tiens au courant lors de la session de support",
        'b_2_have_proof': "✅ Non, j'ai la preuve que je l'ai sauvegardé et que j'y joue réellement",
        
        # Code messages - French
        'codes_title': "🎮 **Meilleurs Codes de Jeu:**\n\nCopiez simplement l'un d'entre eux et entrez-le dans la barre de recherche :\n\n",
        
        # Navigation - French
        'back_to_previous': "⬅️ Retour",
        'main_menu': "🏠 Menu Principal",
        
        # Influencer question - French
        'provide_name': "Fournissez le nom s'il vous plaît :",
        
        # Existing player flow - French - UPDATED
        'existing_player_intro': "🎮 **Vérification Joueur Existant**\n\nParce que vous jouez sur le cloud, votre session durera 1 heure. Le jeu se fermera et vous devrez le relancer pour continuer à jouer.\n\nVous le savez probablement car vous suivez déjà toutes les instructions\n\n**1. Avez-vous recherché et trouvé l'île de récompense ?**",
        'existing_q2_text': "**2. Avez-vous suivi la configuration complète pour pouvoir jouer avec des amis et gagner beaucoup ensemble sans aucun souci ?**",
        'existing_q3_text': "**3. Avez-vous commencé le jeu et joué 130 heures gratuitement cette semaine ?**",
        'existing_q4_text': "**4. Avec votre compte existant, cliquerez-vous sur le bouton like à chaque fois avant que votre session de jeu d'1 heure ne se termine pendant vos 130 heures de jeu cette semaine ?**",
        'existing_q5_text': "**5. Avez-vous enregistré l'île de récompense dans vos favoris ?**",
        'existing_q6_text': "**6. Avez-vous été présenté à ce jeu par un influenceur ?**",
        
        # Common responses - French - UPDATED
        'reward_island_reminder': "🔍 **Rappel Île de Récompense**\n\nNon, vous devez rechercher l'île de récompense dans la barre de recherche et la choisir, voulez-vous notre aide pour cela ?",
        'full_setup_reminder': "⚙️ **Rappel Configuration Complète**\n\nNon, vous devez suivre la configuration exacte, avez-vous besoin de notre aide ?",
        'play_hours_reminder': "⏰ **Rappel Heures de Jeu**\n\nNon, vous devez commencer le jeu et jouer chaque jour gratuitement avant de viser la récompense, êtes-vous capable de jouer au moins 130 heures par semaine ?",
        'like_button_reminder': "👍 **Rappel Bouton Like**\n\nNon, vous devez cliquer sur le bouton like à chaque fois avant que votre session de jeu d'1 heure ne se termine pendant vos 130 heures par semaine, voulez-vous notre aide pour cela ?",
        'favorites_reminder': "⭐ **Rappel Favoris**\n\nNon, vous devez enregistrer l'île de récompense dans vos favoris et jouer, voulez-vous notre aide pour cela ?",
        
        # Links and guidance - French
        'channel_instruction_9': "📖 **Instruction 9**\n\nVeuillez consulter notre canal et chercher l'instruction 9 :",
        'channel_instruction_10': "📖 **Instruction 10**\n\nVeuillez consulter notre canal et chercher l'instruction 10 :",
        'channel_instruction_11': "📖 **Instruction 11**\n\nVeuillez consulter notre canal et chercher l'instruction 11 :",
        'channel_instruction_12': "📖 **Instruction 12**\n\nVeuillez consulter notre canal et chercher l'instruction 12 :",
        'channel_instruction_13': "📖 **Instruction 13**\n\nVeuillez consulter notre canal et chercher l'instruction 13 :",
    }}

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
                'current_step': result[1],
                'completed_steps': json.loads(result[2]),
                'reward_island_found': bool(result[3]),
                'full_setup_complete': bool(result[4]),
                'playtime_hours': result[5],
                'like_clicks': result[6],
                'favorites_saved': bool(result[7]),
                'influencer_name': result[8],
                'language': result[9]
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

def save_chat_conversation(user_id, user_message, ai_response):
    """Save chat conversation to database"""
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO chat_conversations 
            (user_id, user_message, ai_response)
            VALUES (?, ?, ?)
        ''', (user_id, user_message, ai_response))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Database error in save_chat_conversation: {e}")
        return False

# --- AI ASSISTANT FUNCTION ---
async def gaming_assistant_response(user_message, user_context, lang):
    """AI assistant for gaming-related queries with enhanced support suggestion"""
    if not openai_client:
        return "I'm currently learning more about gaming setups. For now, please use the structured menus for assistance."
    
    try:
        # Enhanced system prompt for gaming focus with support suggestion
        system_prompt = f"""You are a gaming assistant specialist helping existing players with Fortnite cloud gaming and rewards.

Key Knowledge for Existing Players:
- Cloud gaming sessions: 1-hour duration, relaunch required
- Reward system: Based on playtime and engagement
- Weekly target: 130 hours for optimal rewards
- Important: Reward Island access, like button clicks, favorites setup
- Support process: Users can contact support via menu

User Context: {user_context}

Respond helpfully and concisely in {lang.upper()} language. 
If the user seems to have complex issues that require personal assistance, gently suggest using the Support option.
Keep responses conversational and engaging."""

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Add support suggestion for complex issues
        support_keywords = ['problem', 'issue', 'error', 'not working', 'help', 'support', 'trouble', 'fix', 'broken', 'stuck']
        if any(keyword in user_message.lower() for keyword in support_keywords):
            texts = STRINGS[lang]
            ai_response += texts['ai_support_suggestion']
        
        return ai_response
    except Exception as e:
        logger.error(f"AI assistant error: {e}")
        return "I'm having trouble processing your request. Please try the menu options for specific help."

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
    
    # Show typing action
    await update.message.chat.send_action(action="typing")
    
    # Get AI response
    ai_response = await gaming_assistant_response(user_message, user_context, lang)
    
    # Save conversation to database
    save_chat_conversation(user_id, user_message, ai_response)
    
    # Create response with menu options
    s = STRINGS[lang]
    keyboard = [
        [InlineKeyboardButton(s['back_to_chat'], callback_data="continue_ai_chat")],
        [InlineKeyboardButton(s['support_btn'], callback_data="contact_support")],
        [InlineKeyboardButton(s['main_menu'], callback_data="back_to_main")]
    ]
    
    await update.message.reply_text(
        text=ai_response,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return AI_CHAT

# --- AI CHAT FLOW ---
async def start_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start AI chat conversation"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    context.user_data['current_flow'] = 'ai_chat'
    
    keyboard = [
        [InlineKeyboardButton(s['main_menu'], callback_data="back_to_main")],
        [InlineKeyboardButton(s['support_btn'], callback_data="contact_support")]
    ]
    
    await query.edit_message_text(
        text=s['ai_welcome'],
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return AI_CHAT

async def continue_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Continue AI chat conversation"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    keyboard = [
        [InlineKeyboardButton(s['main_menu'], callback_data="back_to_main")],
        [InlineKeyboardButton(s['support_btn'], callback_data="contact_support")]
    ]
    
    await query.edit_message_text(
        text=s['ai_welcome'],
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return AI_CHAT

# --- Helper Functions ---
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str = None):
    """Helper function to show the main menu in the user's language."""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    keyboard = [
        [InlineKeyboardButton("🏆 Start Existing Player Check", callback_data="existing_player_start")],
        [InlineKeyboardButton(s['ai_chat_btn'], callback_data="start_ai_chat")],
        [InlineKeyboardButton(s['helpful_channel_btn'], callback_data="helpful_channel")],
        [InlineKeyboardButton(s['support_btn'], callback_data="contact_support")],
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
            logger.warning(f"Failed to edit message, might be same as old: {e}")
    else:
        await update.message.reply_text(
            text=text_to_show,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    return MAIN_MENU

# --- EXISTING PLAYER FLOW - FIXED BUTTONS ---
async def existing_player_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Flow - Start"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    context.user_data['existing_player_qa'] = []  # Initialize Q&A storage
    
    context.user_data['existing_q1_text'] = s['existing_player_intro'].split('\n')[-1]
    text = s['existing_player_intro']
    
    keyboard = [
        [InlineKeyboardButton(s['a_yes'], callback_data="existing_q1_yes")],
        [InlineKeyboardButton(s['b_no'], callback_data="existing_q1_no")],
        [InlineKeyboardButton(s['back_btn'], callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return EXISTING_PLAYER_FLOW

async def existing_q1_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Q1 - Yes -> Q2"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store Q&A
    context.user_data['existing_player_qa'].append((context.user_data.get('existing_q1_text'), "Yes"))

    context.user_data['existing_q2_text_key'] = 'existing_q2_text'
    text = s['existing_q2_text']
    
    keyboard = [
        [InlineKeyboardButton(s['yes_im_ready'], callback_data="existing_q2_yes")],
        [InlineKeyboardButton(s['b_no'], callback_data="existing_q2_no")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="existing_player_start")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return EXISTING_PLAYER_FLOW

async def existing_q1_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Q1 - No -> Show codes guidance"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store Q&A
    context.user_data['existing_player_qa'].append((context.user_data.get('existing_q1_text'), "No"))
    
    text = s['reward_island_reminder']
    
    keyboard = [
        [InlineKeyboardButton(s['b_1_want_codes'], callback_data="existing_show_codes")],
        [InlineKeyboardButton(s['b_2_already_chose'], callback_data="existing_q2_yes")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="existing_player_start")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return EXISTING_PLAYER_FLOW

async def existing_show_codes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player - Show codes -> Q2"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    codes_text = s['codes_title'] + "\n".join(GAME_CODES)
    
    keyboard = [
        [InlineKeyboardButton(s['next_question'], callback_data="existing_q2_yes")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="existing_q1_no")]
    ]
    
    await query.edit_message_text(text=codes_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return EXISTING_PLAYER_FLOW

async def existing_q2_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Q2 - Yes -> Q3"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store Q&A
    context.user_data['existing_player_qa'].append((s[context.user_data.get('existing_q2_text_key', 'existing_q2_text')], "Yes"))

    context.user_data['existing_q3_text_key'] = 'existing_q3_text'
    text = s['existing_q3_text']
    
    keyboard = [
        [InlineKeyboardButton(s['a_yes'], callback_data="existing_q3_yes")],
        [InlineKeyboardButton(s['b_no'], callback_data="existing_q3_no")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="existing_q1_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return EXISTING_PLAYER_FLOW

async def existing_q2_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Q2 - No -> Ask if they need guidance"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store Q&A
    context.user_data['existing_player_qa'].append((s['existing_q2_text'], "No"))
    
    text = s['full_setup_reminder']
    
    keyboard = [
        [InlineKeyboardButton(s['b_1_guidance'], callback_data="existing_channel_instruction_9")],
        [InlineKeyboardButton(s['b_2_finally_fixed'], callback_data="existing_q3_yes")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="existing_q1_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return EXISTING_PLAYER_FLOW

async def existing_channel_instruction_9(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player - Forward to channel instruction 9"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    text = f"{s['channel_instruction_9']} {HELPFUL_CHANNEL_LINK}"
    
    keyboard = [
        [InlineKeyboardButton(s['join_channel_only'], url=HELPFUL_CHANNEL_LINK)]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return EXISTING_PLAYER_FLOW

async def existing_q3_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Q3 - Yes -> Q4"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store Q&A
    context.user_data['existing_player_qa'].append((s[context.user_data.get('existing_q3_text_key', 'existing_q3_text')], "Yes"))
        
    context.user_data['existing_q4_text_key'] = 'existing_q4_text'
    text = s['existing_q4_text']
    
    keyboard = [
        [InlineKeyboardButton(s['a_yes'], callback_data="existing_q4_yes")],
        [InlineKeyboardButton(s['b_no'], callback_data="existing_q4_no")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="existing_q2_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return EXISTING_PLAYER_FLOW

async def existing_q3_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Q3 - No -> Ask if they can play 130 hours"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store Q&A
    context.user_data['existing_player_qa'].append((s['existing_q3_text'], "No"))
    
    text = s['play_hours_reminder']
    
    keyboard = [
        [InlineKeyboardButton(s['b_1_yes'], callback_data="existing_q4_yes")],
        [InlineKeyboardButton(s['b_2_no'], callback_data="existing_channel_instruction_10")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="existing_q2_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return EXISTING_PLAYER_FLOW

async def existing_channel_instruction_10(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player - Forward to channel instruction 10"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    text = f"{s['channel_instruction_10']} {HELPFUL_CHANNEL_LINK}"
    
    keyboard = [
        [InlineKeyboardButton(s['join_channel_only'], url=HELPFUL_CHANNEL_LINK)]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return EXISTING_PLAYER_FLOW

async def existing_q4_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Q4 - Yes -> Q5"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store Q&A
    context.user_data['existing_player_qa'].append((s[context.user_data.get('existing_q4_text_key', 'existing_q4_text')], "Yes"))
        
    context.user_data['existing_q5_text_key'] = 'existing_q5_text'
    text = s['existing_q5_text']
    
    keyboard = [
        [InlineKeyboardButton(s['a_yes'], callback_data="existing_q5_yes")],
        [InlineKeyboardButton(s['b_no'], callback_data="existing_q5_no")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="existing_q3_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return EXISTING_PLAYER_FLOW

async def existing_q4_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Q4 - No -> Ask if they want guidance"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store Q&A
    context.user_data['existing_player_qa'].append((s['existing_q4_text'], "No"))
    
    text = s['like_button_reminder']
    
    keyboard = [
        [InlineKeyboardButton(s['b_1_guidance'], callback_data="existing_channel_instruction_11")],
        [InlineKeyboardButton(s['b_2_will_play'], callback_data="existing_q5_yes")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="existing_q3_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return EXISTING_PLAYER_FLOW

async def existing_channel_instruction_11(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player - Forward to channel instruction 11"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    text = f"{s['channel_instruction_11']} {HELPFUL_CHANNEL_LINK}"
    
    keyboard = [
        [InlineKeyboardButton(s['join_channel_only'], url=HELPFUL_CHANNEL_LINK)]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return EXISTING_PLAYER_FLOW

async def existing_q5_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Q5 - Yes -> Q6 (INFLUENCER QUESTION)"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store Q&A
    context.user_data['existing_player_qa'].append((s[context.user_data.get('existing_q5_text_key', 'existing_q5_text')], "Yes"))

    context.user_data['existing_q6_text_key'] = 'existing_q6_text'
    text = s['existing_q6_text']
    
    keyboard = [
        [InlineKeyboardButton(s['a_yes'], callback_data="existing_influencer_yes")],
        [InlineKeyboardButton(s['b_no'], callback_data="existing_influencer_no")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="existing_q4_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return EXISTING_PLAYER_FLOW

async def existing_q5_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Q5 - No -> Ask if they want guidance"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store Q&A
    context.user_data['existing_player_qa'].append((s['existing_q5_text'], "No"))
    
    text = s['favorites_reminder']
    
    keyboard = [
        [InlineKeyboardButton(s['b_1_guidance'], callback_data="existing_channel_instruction_12")],
        [InlineKeyboardButton(s['b_2_have_proof'], callback_data="existing_q6_yes")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="existing_q4_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return EXISTING_PLAYER_FLOW

async def existing_channel_instruction_12(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player - Forward to channel instruction 12"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    text = f"{s['channel_instruction_12']} {HELPFUL_CHANNEL_LINK}"
    
    keyboard = [
        [InlineKeyboardButton(s['join_channel_only'], url=HELPFUL_CHANNEL_LINK)]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return EXISTING_PLAYER_FLOW

async def existing_q6_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Q6 - Yes (from Q5) -> Influencer question"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store Q&A
    context.user_data['existing_player_qa'].append((s['existing_q5_text'], "No, but have proof"))

    context.user_data['existing_q6_text_key'] = 'existing_q6_text'
    text = s['existing_q6_text']
    
    keyboard = [
        [InlineKeyboardButton(s['a_yes'], callback_data="existing_influencer_yes")],
        [InlineKeyboardButton(s['b_no'], callback_data="existing_influencer_no")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="existing_q5_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return EXISTING_PLAYER_FLOW

async def existing_influencer_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player - Influencer Yes -> Ask for name"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store Q&A
    context.user_data['existing_player_qa'].append((s['existing_q6_text'], "Yes"))
    
    text = s['provide_name']
    
    keyboard = [
        [InlineKeyboardButton(s['next_question'], callback_data="existing_ask_username")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="existing_q6_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return EXISTING_PLAYER_FLOW

async def existing_influencer_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player - Influencer No -> Forward to channel"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store Q&A
    context.user_data['existing_player_qa'].append((s['existing_q6_text'], "No"))
    
    text = f"{s['channel_instruction_13']} {HELPFUL_CHANNEL_LINK}"
    
    keyboard = [
        [InlineKeyboardButton(s['join_channel_only'], url=HELPFUL_CHANNEL_LINK)]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return EXISTING_PLAYER_FLOW

async def existing_ask_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player - Ask for username"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    context.user_data['flow_type'] = 'existing_player'
    
    await query.edit_message_text(text=s['support_q2'], parse_mode='Markdown')
    return USERNAME_COLLECTION

# --- Conversation Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point: Shows disclaimer and asks for language."""
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
    """Stores the chosen language and shows the main menu."""
    query = update.callback_query
    lang = query.data
    context.user_data['lang'] = lang
    
    # Update user progress in database
    user_id = update.effective_user.id
    update_player_progress(user_id, {'language': lang})
    
    return await show_main_menu(update, context)

async def show_helpful_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Shows the helpful channel link."""
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

async def contact_support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start support flow"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    context.user_data['flow_type'] = 'support'
    
    await query.edit_message_text(text=s['support_q2'], parse_mode='Markdown')
    return USERNAME_COLLECTION

# --- USERNAME COLLECTION ---
async def collect_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Collect username and send Q&A to support team"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    username = update.message.text
    
    if username.startswith('@') and len(username) > 2:
        logger.info(f"*** EXISTING PLAYER - USERNAME COLLECTION from user {update.message.from_user.id}: {username} ***")
        
        if not SUPPORT_CHAT_ID:
            logger.error("SUPPORT_CHAT_ID is not set in environment variables")
            await update.message.reply_text("❌ Support feature is currently unavailable. Please try again later.")
            return await show_main_menu(update, context)
        
        try:
            user = update.effective_user
            user_username = user.username if user.username else "No username"
            first_name = user.first_name if user.first_name else "No first name"
            last_name = user.last_name if user.last_name else "No last name"
            
            flow_type = context.user_data.get('flow_type', 'existing_player')
            qa_data = context.user_data.get('existing_player_qa', [])
            flow_title = "🏆 EXISTING PLAYER QUESTIONNAIRE" if flow_type == 'existing_player' else "🆘 SUPPORT REQUEST"
            
            support_message = (
                f"🚨 **{flow_title}** 🚨\n"
                f"👤 User: {first_name} {last_name}\n"
                f"📛 User's Telegram: @{user_username}\n"
                f"💬 Provided Username: {username}\n"
                f"🆔 User ID: `{user.id}`\n"
                f"⏰ Time: {update.message.date.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🌐 Language: {lang.upper()}\n\n"
            )
            
            if qa_data:
                support_message += "**Questions & Answers:**\n"
                for i, (question, answer) in enumerate(qa_data, 1):
                    # Check if question is a full string or a key, display gracefully
                    q_text = STRINGS.get(lang, STRINGS['en']).get(question, question)
                    support_message += f"{i}. {q_text.split('\n')[-1].strip()}\n   ➤ **{answer}**\n\n"
            else:
                support_message += "**No Q&A data collected.**\n\n"
            
            support_message += f"**Flow Type:** {flow_type.replace('_', ' ').title()}"
            
            await context.bot.send_message(
                chat_id=SUPPORT_CHAT_ID,
                text=support_message,
                parse_mode='Markdown'
            )
            
            # Create support case in database
            create_support_case(
                user_id=user.id,
                username=username,
                case_type=flow_type,
                issue_description='User requested support',
                steps_completed=qa_data
            )
            
            # Clear QA data after submission
            context.user_data.pop('existing_player_qa', None)
            
            await update.message.reply_text(text=s['support_thanks'], reply_markup=ReplyKeyboardRemove())
            return await show_main_menu(update, context)
            
        except Exception as e:
            logger.error(f"Error sending support message to group: {e}")
            await update.message.reply_text("❌ There was an error sending your information. Please try again later.")
            return await show_main_menu(update, context)
    else:
        await update.message.reply_text(text=s['invalid_username'])
        return USERNAME_COLLECTION

async def cancel_support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User types /cancel during the support flow."""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    await update.message.reply_text(text=s['support_cancel'], reply_markup=ReplyKeyboardRemove())
    return await show_main_menu(update, context)

def main() -> None:
    """Run the bot."""
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
                CallbackQueryHandler(existing_player_start, pattern="^existing_player_start$"),
                CallbackQueryHandler(start_ai_chat, pattern="^start_ai_chat$"),
                CallbackQueryHandler(show_helpful_channel, pattern="^helpful_channel$"),
                CallbackQueryHandler(contact_support, pattern="^contact_support$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
            EXISTING_PLAYER_FLOW: [
                CallbackQueryHandler(existing_q1_yes, pattern="^existing_q1_yes$"),
                CallbackQueryHandler(existing_q1_no, pattern="^existing_q1_no$"),
                CallbackQueryHandler(existing_show_codes, pattern="^existing_show_codes$"),
                CallbackQueryHandler(existing_q2_yes, pattern="^existing_q2_yes$"),
                CallbackQueryHandler(existing_q2_no, pattern="^existing_q2_no$"),
                CallbackQueryHandler(existing_channel_instruction_9, pattern="^existing_channel_instruction_9$"),
                CallbackQueryHandler(existing_q3_yes, pattern="^existing_q3_yes$"),
                CallbackQueryHandler(existing_q3_no, pattern="^existing_q3_no$"),
                CallbackQueryHandler(existing_channel_instruction_10, pattern="^existing_channel_instruction_10$"),
                CallbackQueryHandler(existing_q4_yes, pattern="^existing_q4_yes$"),
                CallbackQueryHandler(existing_q4_no, pattern="^existing_q4_no$"),
                CallbackQueryHandler(existing_channel_instruction_11, pattern="^existing_channel_instruction_11$"),
                CallbackQueryHandler(existing_q5_yes, pattern="^existing_q5_yes$"),
                CallbackQueryHandler(existing_q5_no, pattern="^existing_q5_no$"),
                CallbackQueryHandler(existing_channel_instruction_12, pattern="^existing_channel_instruction_12$"),
                CallbackQueryHandler(existing_q6_yes, pattern="^existing_q6_yes$"),
                CallbackQueryHandler(existing_influencer_yes, pattern="^existing_influencer_yes$"),
                CallbackQueryHandler(existing_influencer_no, pattern="^existing_influencer_no$"),
                CallbackQueryHandler(existing_ask_username, pattern="^existing_ask_username$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
            USERNAME_COLLECTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_username),
                CommandHandler("cancel", cancel_support), 
            ],
            AI_CHAT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_intelligent_message),
                CallbackQueryHandler(continue_ai_chat, pattern="^continue_ai_chat$"),
                CallbackQueryHandler(contact_support, pattern="^contact_support$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            CommandHandler("cancel", cancel_support) 
        ],
    )

    application.add_handler(conv_handler)

    logger.info("Enhanced Existing Player Bot is running...")
    print("🤖 ENHANCED EXISTING PLAYER BOT is starting...")
    print("=" * 50)
    print(f"✅ TELEGRAM_TOKEN: {'Set' if TELEGRAM_TOKEN else 'Not Set'}")
    print(f"✅ SUPPORT_CHAT_ID: {'Set' if SUPPORT_CHAT_ID else 'Not Set'}")
    print(f"✅ OPENAI_API_KEY: {'Set' if OPENAI_API_KEY else 'Not Set'}")
    print(f"✅ OPENAI_CLIENT: {'Available' if openai_client else 'Not Available'}")
    print(f"✅ DATABASE: Enhanced schema at {DB_FILE}")
    print("🚀 FEATURES: AI Assistant, Progress Tracking, Multi-Language")
    print("🎯 FLOWS: Existing Player Check, AI Chat, Support")
    print("=" * 50)
    
    application.run_polling()

if __name__ == "__main__":
    main()

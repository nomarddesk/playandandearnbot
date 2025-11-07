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
print("EXISTING PLAYER BOT - ENVIRONMENT VARIABLES CHECK:")
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
        print("⚠️ Using in-memory storage as fallback")

init_database()

HELPFUL_CHANNEL_LINK = "https://t.me/rejoinsnousetgagne"

# Define states
SELECT_LANG, MAIN_MENU, EXISTING_PLAYER_FLOW, USERNAME_COLLECTION = range(4)

# Codes for the game
GAME_CODES = [
    "6086-7221-0564",
    "2753-4695-7191", 
    "9689-1352-5966",
    "4563-6624-9460",
    "4828-9033-2281"]

# --- COMPLETE KNOWLEDGE BASE ---
BOT_KNOWLEDGE_BASE = """
EXISTING PLAYER BOT - COMPLETE KNOWLEDGE BASE

BOT PURPOSE:
This is a Telegram bot specifically for existing Fortnite cloud gaming players who want to maximize their rewards through the reward island system.

GAME CODES FOR REWARD ISLAND:
{game_codes}

EXISTING PLAYER FLOW QUESTIONS:
1. Reward Island Access - Have you found the reward island?
2. Full Setup Completion - Did you complete the full setup?
3. Play Time - 130 hours per week tracking
4. Like Button Usage - Regular usage during sessions
5. Favorites - Reward island in favorites
6. Influencer Attribution - Were you introduced by influencer?

USERNAME COLLECTION:
- After completing the flow, ask for the user's Telegram username
- The username must start with @
- Send a detailed summary to the support team including:
  * User's Telegram username and ID
  * All flow answers and progress
  * Specific issues or needs identified

FLOW GUIDANCE:
- When user is in the structured flow, guide them through questions step by step
- Use button-based responses for flow questions
- For "guidance" type questions, provide specific help when user needs assistance
- Track progress and remember where users left off
- Users can navigate back to previous questions using the back button

IMPORTANT LINKS:
- Help Channel: {channel_link}

KEY REQUIREMENTS FOR EXISTING PLAYERS:
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
- existing_player_start, back_to_main, continue_chat, back_to_previous
- Flow answers: yes, no, need_guidance, already_done
""".format(game_codes=", ".join(GAME_CODES), channel_link=HELPFUL_CHANNEL_LINK)

# --- LANGUAGE STRINGS ---
STRINGS = {
    'en': {
        'disclaimer': "**Disclaimer:** This bot is an unofficial guide and is not affiliated with Epic Games or Fortnite. We will *never* ask for your password.",
        'lang_prompt': "Please select your language:",
        'welcome': "🏆 Welcome Back Existing Player! Let's continue your gaming journey and maximize your rewards.",
        'helpful_channel_btn': "Full guide in channel",
        'support_btn': "Support",
        'lang_btn': "🌐 Change Language",
        'helpful_channel_text': "Join our helpful Telegram channel for the full guide, news, and community chat!",
        'join_channel_btn': "Join Channel Now",
        'back_btn': "⬅️ Back to Main Menu",
        'support_q2': "Okay. By providing your @username, you consent to our support team contacting you directly on Telegram. We will *only* use this to help with your question.\n\nPlease type your @username (like @myusername) to proceed.\n\nType /cancel to go back.",
        'support_thanks': "Thank you! Your @username has been noted. We will get in touch with you as soon as possible.\n\nReturning you to the main menu.",
        'support_cancel': "Support request cancelled. Returning to main menu.",
        'invalid_username': "That doesn't look like a valid @username. Please start with '@' and try again, or type /cancel.",
        
        # AI Brain texts
        'ai_thinking': "🤔 Analyzing your question...",
        'ai_continue': "💬 Continue Chat",
        'ai_menu': "📱 Menu",
        
        # Button texts
        'a_yes': "A Yes",
        'b_no': "B No",
        'yes_im_ready': "A Yes, I'm ready for the next step",
        'want_codes': "Yes I want the best codes to play",
        'already_chose': "No , I already choosed one code",
        'finally_fixed': "No I finally fix everything, I want to move to the next step",
        'will_play': "No, I will play and let you know in the support session later on",
        'have_proof': "No , I have proof I saved the reward Island to my favorites and I actually play on it",
        'next_question': "Next Question",
        'join_channel_only': "Join Channel",
        
        # Specific custom buttons
        'b_1_yes': "B - 1 Yes",
        'b_2_no': "B - 2 No",
        'b_1_want_codes': "B - 1 Yes I want the best codes to play",
        'b_2_already_chose': "B - 2 No , I already choosed one code",
        'b_1_guidance': "B - 1 Yes",
        'b_2_finally_fixed': "B - 2 No I finally fix everything, I want to move to the next step",
        'b_2_will_play': "B - 2 No, I will play and let you know in the support session later on",
        'b_2_have_proof': "B - 2 No , I have proof I saved the reward Island to my favorites and I actually play on it",
        
        # Code messages
        'codes_title': "Just copy one of them and enter it on the search bar:\n\n",
        
        # Navigation
        'back_to_previous': "⬅️ Back",
        'main_menu': "🏠 Main Menu",
        
        # Influencer question
        'provide_name': "Provide the name please:",
        
        # Existing player flow
        'existing_player_intro': "Because you are playing on the cloud, your session will last for 1 hour. The game will close, and you will have to launch it again to keep playing.\nYou probably know it cause you already follow all the instructions\n\n1 Have you searched and found the reward Island?",
        'existing_q2_text': "2 Did you follow the full setup to be able to play with friends and earn a lot together without any worries?",
        'existing_q3_text': "3 Did you start the game and play 130 hours for free this week?",
        'existing_q4_text': "4 With your existing account ,  will you click on the like button every single time before your 1 hour play session ended during your 130 hours of play this week?",
        'existing_q5_text': "5 Did you save the reward Island to your favorites?",
        'existing_q6_text': "12 Were you introduced to this game by an influencer?",
        
        # Common responses
        'reward_island_reminder': "No, you have to search the reward Island in the search bar and just choose it , do you want our guidance for that?",
        'full_setup_reminder': "No, you have to follow the exact setup , do you need our guidance?",
        'play_hours_reminder': "No, you have to start the game and play every single day for free before aiming for the reward, are you able to play at least 130 hours a week?",
        'like_button_reminder': "No, You have to click on the like button every single time before your 1 hour play session ended during your 130 hours a week , do you want our guidance on that?",
        'favorites_reminder': "No , you have to save the reward Island to your favorites and play , do you want our guidance on that?",
        
        # Links and guidance
        'channel_instruction_9': "Please check our channel and look for instruction 9:",
        'channel_instruction_10': "Please check our channel and look for instruction 10:",
        'channel_instruction_11': "Please check our channel and look for instruction 11:",
        'channel_instruction_12': "Please check our channel and look for instruction 12:",
        'channel_instruction_13': "Please check our channel and look for instruction 13:",
    },
    'fr': {
        'disclaimer': "**Avertissement :** Ce bot est un guide non officiel et n'est pas affilié à Epic Games ou Fortnite. Nous ne vous demanderons *jamais* votre mot de passe.",
        'lang_prompt': "Veuillez sélectionner votre langue :",
        'welcome': "🏆 Bienvenue Joueur Existant ! Continuons votre aventure de jeu et maximisons vos récompenses.",
        'helpful_channel_btn': "Guide complet sur le canal",
        'support_btn': "Support",
        'lang_btn': "🌐 Changer de Langue",
        'helpful_channel_text': "Rejoignez notre canal Telegram pour le guide complet, les actualités et pour discuter avec la communauté !",
        'join_channel_btn': "Rejoindre le Canal",
        'back_btn': "⬅️ Retour au Menu Principal",
        'support_q2': "D'accord. En fournissant votre @nomdutilisateur, vous acceptez que notre équipe d'assistance vous contacte directement sur Telegram. Nous l'utiliserons *uniquement* pour répondre à votre question.\n\nVeuillez taper votre @nomdutilisateur (comme @monpseudo) pour continuer.\n\nTapez /cancel pour revenir.",
        'support_thanks': "Merci ! Votre @nomdutilisateur a été noté. Nous vous contacterons dès que possible.\n\nRetour au menu principal.",
        'support_cancel': "Demande d'aide annulée. Retour au menu principal.",
        'invalid_username': "Cela ne ressemble pas à un @nomdutilisateur valide. Veuillez commencer par '@' et réessayer, ou tapez /cancel.",
        
        # AI Brain texts - French
        'ai_thinking': "🤔 Analyse de votre question...",
        'ai_continue': "💬 Continuer",
        'ai_menu': "📱 Menu",
        
        # Button texts - French
        'a_yes': "A Oui",
        'b_no': "B Non",
        'yes_im_ready': "A Oui, je suis prêt pour l'étape suivante",
        'want_codes': "Oui je veux les meilleurs codes pour jouer",
        'already_chose': "Non, j'ai déjà choisi un code",
        'finally_fixed': "Non j'ai finalement tout réparé, je veux passer à l'étape suivante",
        'will_play': "Non, je vais jouer et vous tiens au courant lors de la session de support",
        'have_proof': "Non, j'ai la preuve que je l'ai sauvegardé et que j'y joue réellement",
        'next_question': "Question Suivante",
        'join_channel_only': "Rejoindre le Canal",
        
        # Specific custom buttons
        'b_1_yes': "B - 1 Oui",
        'b_2_no': "B - 2 Non",
        'b_1_want_codes': "B - 1 Oui je veux les meilleurs codes pour jouer",
        'b_2_already_chose': "B - 2 Non, j'ai déjà choisi un code",
        'b_1_guidance': "B - 1 Oui",
        'b_2_finally_fixed': "B - 2 Non j'ai finalement tout réparé, je veux passer à l'étape suivante",
        'b_2_will_play': "B - 2 Non, je vais jouer et vous tiens au courant lors de la session de support",
        'b_2_have_proof': "B - 2 Non, j'ai la preuve que je l'ai sauvegardé et que j'y joue réellement",
        
        # Code messages - French
        'codes_title': "Copiez simplement l'un d'entre eux et entrez-le dans la barre de recherche :\n\n",
        
        # Navigation - French
        'back_to_previous': "⬅️ Retour",
        'main_menu': "🏠 Menu Principal",
        
        # Influencer question - French
        'provide_name': "Fournissez le nom s'il vous plaît :",
        
        # Existing player flow - French
        'existing_player_intro': "Parce que vous jouez sur le cloud, votre session durera 1 heure. Le jeu se fermera et vous devrez le relancer pour continuer à jouer.\nVous le savez probablement car vous suivez déjà toutes les instructions\n\n1 Avez-vous recherché et trouvé l'île de récompense ?",
        'existing_q2_text': "2 Avez-vous suivi la configuration complète pour pouvoir jouer avec des amis et gagner beaucoup ensemble sans aucun souci ?",
        'existing_q3_text': "3 Avez-vous commencé le jeu et joué 130 heures gratuitement cette semaine ?",
        'existing_q4_text': "4 Avec votre compte existant, cliquerez-vous sur le bouton like à chaque fois avant que votre session de jeu d'1 heure ne se termine pendant vos 130 heures de jeu cette semaine ?",
        'existing_q5_text': "5 Avez-vous enregistré l'île de récompense dans vos favoris ?",
        'existing_q6_text': "12 Avez-vous été présenté à ce jeu par un influenceur ?",
        
        # Common responses - French
        'reward_island_reminder': "Non, vous devez rechercher l'île de récompense dans la barre de recherche et la choisir, voulez-vous notre aide pour cela ?",
        'full_setup_reminder': "Non, vous devez suivre la configuration exacte, avez-vous besoin de notre aide ?",
        'play_hours_reminder': "Non, vous devez commencer le jeu et jouer chaque jour gratuitement avant de viser la récompense, êtes-vous capable de jouer au moins 130 heures par semaine ?",
        'like_button_reminder': "Non, vous devez cliquer sur le bouton like à chaque fois avant que votre session de jeu d'1 heure ne se termine pendant vos 130 heures par semaine, voulez-vous notre aide pour cela ?",
        'favorites_reminder': "Non, vous devez enregistrer l'île de récompense dans vos favoris et jouer, voulez-vous notre aide pour cela ?",
        
        # Links and guidance - French
        'channel_instruction_9': "Veuillez consulter notre canal et chercher l'instruction 9 :",
        'channel_instruction_10': "Veuillez consulter notre canal et chercher l'instruction 10 :",
        'channel_instruction_11': "Veuillez consulter notre canal et chercher l'instruction 11 :",
        'channel_instruction_12': "Veuillez consulter notre canal et chercher l'instruction 12 :",
        'channel_instruction_13': "Veuillez consulter notre canal et chercher l'instruction 13 :",
    }}

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
        system_prompt = f"""You are the AI brain of an existing player Fortnite cloud gaming Telegram bot.

{BOT_KNOWLEDGE_BASE}

CURRENT USER CONTEXT:
- User ID: {user_id}
- Language: {lang.upper()}
- Current Flow: {current_flow}
- User Progress: {progress_data}

USER'S MESSAGE: "{user_message}"

RESPONSE REQUIREMENTS:
1. Be CONCISE and directly address the user's need
2. If user is in the existing player flow, guide them to the next question
3. Use callback codes for buttons, NOT display text
4. Provide specific, actionable guidance
5. Ask clarifying questions if needed
6. Include back_to_previous button when user is in a flow (except first question)

RESPONSE FORMAT (JSON):
{{
    "response": "Your concise response",
    "buttons": ["callback_code1", "callback_code2", ...],
    "next_action": "continue/menu/start_flow/next_question",
    "flow_step": "step_name_if_applicable"
}}

Available button callback codes:
- Navigation: menu, back_to_main, continue_chat, back_to_previous
- Flow starters: existing_player_start  
- Flow answers: yes, no, need_guidance, already_done
- Channel: join_channel"""

        # Build message history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        for msg in conversation_history[-4:]:
            messages.append(msg)
        
        messages.append({"role": "user", "content": user_message})
        
        # Generate AI response
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Parse JSON response
        try:
            parsed_response = json.loads(ai_response)
            
            # Ensure buttons use valid callback codes
            valid_codes = ['menu', 'back_to_main', 'continue_chat', 'back_to_previous', 'existing_player_start', 
                          'yes', 'no', 'need_guidance', 'already_done', 'join_channel']
            
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
        elif callback_data == 'existing_player_start':
            keyboard.append([InlineKeyboardButton("🏆 Start Existing Player Check", callback_data="existing_player_start")])
        elif callback_data == 'join_channel':
            keyboard.append([InlineKeyboardButton(s['join_channel_btn'], url=HELPFUL_CHANNEL_LINK)])
        elif callback_data == 'back_to_previous':
            keyboard.append([InlineKeyboardButton(s['back_to_previous'], callback_data="back_to_previous")])
        elif callback_data in ['yes', 'no', 'need_guidance', 'already_done']:
            # Flow answer buttons
            btn_text = {
                'yes': s['a_yes'],
                'no': s['b_no'], 
                'need_guidance': s['b_1_guidance'],
                'already_done': s['b_2_finally_fixed']
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
        return await existing_player_start(update, context)
    
    # Default: continue in current state
    current_state = context.user_data.get('current_state', MAIN_MENU)
    return current_state

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

# --- Helper Functions ---
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str = None):
    """Helper function to show the main menu in the user's language."""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    context.user_data['current_flow'] = 'general'
    context.user_data['current_state'] = MAIN_MENU
    
    keyboard = [
        [InlineKeyboardButton("🏆 Start Existing Player Check", callback_data="existing_player_start")],
        [InlineKeyboardButton(s['helpful_channel_btn'], callback_data="helpful_channel")],
        [InlineKeyboardButton(s['support_btn'], callback_data="contact_support")],
        [InlineKeyboardButton(s['ai_continue'], callback_data="continue_chat")],
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

# --- EXISTING PLAYER FLOW ---
async def existing_player_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Flow - Start"""
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = update.effective_user.id
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    context.user_data['existing_player_qa'] = []  # Initialize Q&A storage
    context.user_data['current_flow'] = 'existing_player'
    context.user_data['current_state'] = EXISTING_PLAYER_FLOW
    
    # Save user data
    save_user_data(user_id, lang=lang)

    context.user_data['existing_q1_text'] = s['existing_player_intro'].split('\n')[-1]
    text = s['existing_player_intro']
    
    keyboard = [
        [InlineKeyboardButton(s['a_yes'], callback_data="existing_q1_yes")],
        [InlineKeyboardButton(s['b_no'], callback_data="existing_q1_no")],
        [InlineKeyboardButton(s['back_btn'], callback_data="back_to_main")]
    ]
    
    if query:
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
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
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
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
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
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
    
    await query.edit_message_text(text=codes_text, reply_markup=InlineKeyboardMarkup(keyboard))
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
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
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
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
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
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
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
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
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
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
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
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
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
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
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
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
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
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
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
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
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
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
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
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
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
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
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
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
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
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
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
    
    # Save language preference
    user_id = update.effective_user.id
    save_user_data(user_id, lang=lang)
    
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
            flow_title = "🏆 EXISTING PLAYER QUESTIONNAIRE"
            
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
            
            # Create support ticket
            create_support_ticket(user.id, username, qa_data)
            
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

# --- ERROR HANDLER ---
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    if isinstance(context.error, Conflict):
        logger.warning("Bot conflict detected - another instance might be running")
        return
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "Sorry, I encountered an error. Please try again."
            )
    except Exception as e:
        logger.error(f"Error while sending error message: {e}")

def main() -> None:
    """Run the bot."""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN environment variable not set!")
        print("❌ ERROR: TELEGRAM_TOKEN environment variable is required!")
        return

    # Create application with specific settings to avoid conflicts
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

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_LANG: [
                CallbackQueryHandler(set_language, pattern="^(en|fr)$")
            ],
            MAIN_MENU: [
                CallbackQueryHandler(existing_player_start, pattern="^existing_player_start$"),
                CallbackQueryHandler(show_helpful_channel, pattern="^helpful_channel$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
                CallbackQueryHandler(continue_chat, pattern="^continue_chat$"),
                # ALL text messages go to AI brain
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_any_message),
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
                # ALL text messages go to AI brain
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_any_message),
            ],
            USERNAME_COLLECTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_username),
                CommandHandler("cancel", cancel_support), 
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            CommandHandler("cancel", cancel_support) 
        ],
        per_message=False,
    )

    application.add_handler(conv_handler)

    logger.info("AI-Powered Existing Player Bot is running...")
    print("🤖 AI-POWERED EXISTING PLAYER BOT is starting...")
    print(f"✅ TELEGRAM_TOKEN: {'Set' if TELEGRAM_TOKEN else 'Not Set'}")
    print(f"✅ SUPPORT_CHAT_ID: {'Set' if SUPPORT_CHAT_ID else 'Not Set'}")
    print(f"✅ OPENAI_API_KEY: {'Set' if OPENAI_API_KEY else 'Not Set'}")
    print(f"✅ OPENAI_CLIENT: {'Available' if openai_client else 'Not Available'}")
    print(f"✅ DATABASE: Initialized at {DB_FILE}")
    print("🚀 ALL messages will be processed by AI Brain!")
    print("📊 User progress tracking: ENABLED")
    print("👤 Username collection for support: ENABLED")
    print("🛡️ Error handling: ENABLED")
    
    # Start the bot with proper error handling
    try:
        application.run_polling(
            poll_interval=1.0,
            timeout=30,
            drop_pending_updates=True
        )
    except Conflict as e:
        logger.warning(f"Bot conflict detected on startup: {e}")
        print("⚠️ Another bot instance might be running. This is normal in some deployment environments.")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        print(f"❌ Bot failed to start: {e}")

if __name__ == "__main__":
    main()

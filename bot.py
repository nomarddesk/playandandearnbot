import logging
import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,)

# Try to import OpenAI
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
print("ENVIRONMENT VARIABLES CHECK:")
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

HELPFUL_CHANNEL_LINK = "https://t.me/rejoinsnousetgagne"

# Define states
SELECT_LANG, MAIN_MENU, EXISTING_PLAYER_FLOW, NEW_PLAYER_FLOW, SUPPORT_FLOW, USERNAME_COLLECTION, AI_CHAT_FLOW = range(7)

# Codes for the game
GAME_CODES = [
    "6086-7221-0564",
    "2753-4695-7191", 
    "9689-1352-5966",
    "4563-6624-9460",
    "4828-9033-2281"]

# --- LANGUAGE STRINGS ---
STRINGS = {
    'en': {
        'disclaimer': "**Disclaimer:** This bot is an unofficial guide and is not affiliated with Epic Games or Fortnite. We will *never* ask for your password.",
        'lang_prompt': "Please select your language:",
        'welcome': "Welcome! You're diving into an immersive gaming adventure. This bot will help you set up your account, join the game, and start playing.",
        'new_player_btn': "New player",
        'existing_player_btn': "Existing player",
        'helpful_channel_btn': "Full guide in channel",
        'support_btn': "Support",
        'lang_btn': "🌐 Change Language",
        'helpful_channel_text': "Join our helpful Telegram channel for the full guide, news, and community chat!",
        'join_channel_btn': "Join Channel Now",
        'back_btn': "⬅️ Back to Main Menu",
        
        # AI Chat Flow
        'ai_chat_btn': "🤖 AI Assistant",
        'ai_chat_welcome': "🤖 **AI Assistant Activated**\n\nI'm your personal gaming assistant! I can help you with:\n\n• Setting up your account\n• Game setup and configuration\n• Troubleshooting issues\n• Answering any questions\n\nJust type your question and I'll help you! You can ask me anything about the game setup process.",
        'ai_thinking': "🤔 Thinking...",
        'ai_continue_chat': "💬 Continue chatting",
        'ai_switch_to_buttons': "🔘 Switch to button mode",
        'ai_go_to_menu': "🏠 Main Menu",
        
        # Common questions for context
        'new_player_intro': "New player setup involves: VPN usage, cloud gaming profile creation, Epic Games activation, shortcut creation, game launching, reward island setup, and playing requirements.",
        'existing_player_intro': "Existing player setup involves: reward island verification, full setup completion, play time tracking, like button usage, favorites setup, and influencer attribution.",
        'support_flow_intro': "Support process involves troubleshooting VPN, cloud gaming profiles, Epic Games setup, game launching, reward island access, and play time verification.",
    },
    'fr': {
        'disclaimer': "**Avertissement :** Ce bot est un guide non officiel et n'est pas affilié à Epic Games ou Fortnite. Nous ne vous demanderons *jamais* votre mot de passe.",
        'lang_prompt': "Veuillez sélectionner votre langue :",
        'welcome': "Bienvenue ! Tu plonges dans une aventure de jeu immersive. Ce bot t'aidera à configurer ton compte, à rejoindre la partie et à commencer à jouer.",
        'new_player_btn': "Nouveau joueur",
        'existing_player_btn': "Joueur existant",
        'helpful_channel_btn': "Guide complet sur le canal",
        'support_btn': "Support",
        'lang_btn': "🌐 Changer de Langue",
        'helpful_channel_text': "Rejoignez notre canal Telegram pour le guide complet, les actualités et pour discuter avec la communauté !",
        'join_channel_btn': "Rejoindre le Canal",
        'back_btn': "⬅️ Retour au Menu Principal",
        
        # AI Chat Flow - French
        'ai_chat_btn': "🤖 Assistant IA",
        'ai_chat_welcome': "🤖 **Assistant IA Activé**\n\nJe suis votre assistant de jeu personnel ! Je peux vous aider avec :\n\n• La configuration de votre compte\n• L'installation et la configuration du jeu\n• La résolution de problèmes\n• Répondre à toutes vos questions\n\nTapez simplement votre question et je vous aiderai ! Vous pouvez me demander n'importe quoi sur le processus de configuration du jeu.",
        'ai_thinking': "🤔 Réflexion...",
        'ai_continue_chat': "💬 Continuer à discuter",
        'ai_switch_to_buttons': "🔘 Passer au mode boutons",
        'ai_go_to_menu': "🏠 Menu Principal",
        
        # Common questions for context - French
        'new_player_intro': "La configuration du nouveau joueur implique : l'utilisation du VPN, la création de profil de cloud gaming, l'activation Epic Games, la création de raccourcis, le lancement du jeu, la configuration de l'île de récompense et les exigences de jeu.",
        'existing_player_intro': "La configuration du joueur existant implique : la vérification de l'île de récompense, l'achèvement de la configuration complète, le suivi du temps de jeu, l'utilisation du bouton like, la configuration des favoris et l'attribution de l'influenceur.",
        'support_flow_intro': "Le processus de support implique le dépannage du VPN, des profils de cloud gaming, de la configuration Epic Games, du lancement du jeu, de l'accès à l'île de récompense et de la vérification du temps de jeu.",
    }
}

# --- KNOWLEDGE BASE FOR AI ---
BOT_KNOWLEDGE_BASE = """
GAME SETUP KNOWLEDGE BASE:

GAME CODES: {codes}

NEW PLAYER SETUP PROCESS:
1. VPN Usage: Must use USA VPN for profile creation, but not for playing
2. Cloud Gaming Profile: Create at Xbox Cloud Gaming
3. Epic Games Activation: Receive and enter activation code
4. Epic Games Profile: Create gaming profile
5. Shortcut Creation: Create homescreen shortcut for easy access
6. Game Launch: Launch Fortnite through cloud gaming
7. Reward Island: Search and find using game codes
8. Full Setup: Complete all configuration steps
9. Play Time: 130 hours per week requirement
10. Like Button: Click like button before each 1-hour session ends
11. Favorites: Save reward island to favorites
12. Influencer: Specify if introduced by influencer

EXISTING PLAYER PROCESS:
1. Reward Island: Verify access to reward island
2. Full Setup: Confirm complete setup
3. Play Time: Track 130 hours per week
4. Like Button: Regular usage during sessions
5. Favorites: Reward island in favorites
6. Influencer: Attribution if applicable

SUPPORT PROCESS:
- Troubleshoot VPN issues
- Help with cloud gaming profile creation
- Assist with Epic Games activation and setup
- Guide through game launching
- Help find reward island
- Verify play time and like button usage
- Collect username for support team contact

COMMON LINKS:
- Cloud Gaming: https://www.xbox.com/fr-FR/play/games/fortnite/BT5P2X999VH2
- Epic Games Activation: http://epicgames.com/activate
- Epic Games Profile: epicgames.com
- Game Launch: https://www.xbox.com/fr-FR/play/games/fortnite/BT5P2X999VH2
- Help Channel: {channel_link}

USER FLOW OPTIONS:
- New Player: For first-time setup and configuration
- Existing Player: For players who already have accounts
- Support: For technical issues and troubleshooting
- AI Assistant: For conversational help and guidance

RESPONSE GUIDELINES:
- Be helpful, friendly, and encouraging
- Ask clarifying questions if unsure about user's situation
- Provide step-by-step guidance when needed
- Suggest appropriate next steps based on user's progress
- Always maintain a positive and supportive tone
""".format(codes=", ".join(GAME_CODES), channel_link=HELPFUL_CHANNEL_LINK)

# --- AI CHATBOT FUNCTIONS ---
async def generate_chat_response(user_message: str, conversation_history: list, lang: str) -> dict:
    """
    Generate AI chatbot response using the bot's knowledge base
    """
    if not openai_client:
        return {
            "response": "I'm currently unavailable. Please use the button-based menu for assistance.",
            "suggested_flow": None,
            "needs_clarification": False
        }
    
    try:
        # Prepare system prompt with knowledge base
        system_prompt = f"""You are a helpful gaming assistant for Fortnite cloud gaming setup. Use the following knowledge base to answer questions:

{BOT_KNOWLEDGE_BASE}

USER'S LANGUAGE: {lang.upper()}

CONVERSATION GUIDELINES:
1. Analyze the user's message to understand their situation
2. Determine if they are a new player, existing player, or need support
3. Ask clarifying questions if their situation is unclear
4. Provide specific, actionable advice based on the knowledge base
5. Guide them through the appropriate setup process
6. Be conversational and friendly
7. Suggest moving to specific flows (new player, existing player, support) when appropriate

RESPONSE FORMAT (JSON):
{{
    "response": "Your conversational response to the user",
    "suggested_flow": "new_player/existing_player/support/continue_chat",
    "needs_clarification": true/false,
    "clarification_question": "Question to ask if clarification needed"
}}

Focus on being helpful and guiding users to the right solution."""

        # Build messages for conversation context
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history for context (last 10 messages)
        for msg in conversation_history[-10:]:
            messages.append(msg)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Generate response
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=800
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Parse JSON response
        try:
            return json.loads(ai_response)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            logger.warning("AI response not in JSON format, using fallback")
            return {
                "response": ai_response,
                "suggested_flow": "continue_chat",
                "needs_clarification": False
            }
            
    except Exception as e:
        logger.error(f"Error generating AI chat response: {e}")
        return {
            "response": "I'm having trouble processing your request right now. Please try again or use the menu buttons for assistance.",
            "suggested_flow": None,
            "needs_clarification": False
        }

async def determine_user_intent(user_message: str, lang: str) -> str:
    """
    Quickly determine user's main intent for initial routing
    """
    if not openai_client:
        return "general"
    
    try:
        system_prompt = f"""Analyze the user's message and determine their primary intent:
- "new_player": User needs help with initial setup, account creation, first-time configuration
- "existing_player": User has existing account and needs help with features, optimization, or advanced setup
- "support": User has problems, errors, or technical issues needing troubleshooting
- "general": General questions or unclear intent

User message: "{user_message}"
Language: {lang}

Respond with ONLY the intent category name."""

        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use faster model for intent detection
            messages=[{"role": "system", "content": system_prompt}],
            temperature=0.3,
            max_tokens=50
        )
        
        intent = response.choices[0].message.content.strip().lower()
        return intent if intent in ["new_player", "existing_player", "support", "general"] else "general"
        
    except Exception as e:
        logger.error(f"Error determining user intent: {e}")
        return "general"

# --- HELPER FUNCTIONS ---
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str = None):
    """Show the main menu"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    keyboard = [
        [InlineKeyboardButton(s['new_player_btn'], callback_data="new_player_start")],
        [InlineKeyboardButton(s['existing_player_btn'], callback_data="existing_player_start")],
        [InlineKeyboardButton(s['helpful_channel_btn'], callback_data="helpful_channel")],
        [InlineKeyboardButton(s['support_btn'], callback_data="contact_support")],
        [InlineKeyboardButton(s['ai_chat_btn'], callback_data="ai_chat_start")],
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
    
    context.user_data['current_state'] = 'main_menu'
    return MAIN_MENU

# --- AI CHAT FLOW ---
async def ai_chat_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start AI chat flow"""
    query = update.callback_query
    if query:
        await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Initialize chat context
    context.user_data['ai_conversation'] = []
    context.user_data['current_state'] = 'ai_chat'
    
    welcome_text = s['ai_chat_welcome']
    
    keyboard = [
        [InlineKeyboardButton(s['ai_switch_to_buttons'], callback_data="back_to_main")],
        [InlineKeyboardButton(s['ai_go_to_menu'], callback_data="back_to_main")]
    ]
    
    if query:
        await query.edit_message_text(
            text=welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            text=welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    return AI_CHAT_FLOW

async def handle_ai_chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user messages in AI chat flow"""
    user_message = update.message.text
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Show thinking indicator
    thinking_msg = await update.message.reply_text(s['ai_thinking'])
    
    # Get conversation history
    conversation_history = context.user_data.get('ai_conversation', [])
    
    # Generate AI response
    ai_response = await generate_chat_response(user_message, conversation_history, lang)
    
    # Update conversation history
    conversation_history.append({"role": "user", "content": user_message})
    conversation_history.append({"role": "assistant", "content": ai_response['response']})
    context.user_data['ai_conversation'] = conversation_history[-20:]  # Keep last 20 messages
    
    # Build response with appropriate buttons
    keyboard = []
    response_text = ai_response['response']
    
    # Add suggested flow buttons if relevant
    if ai_response.get('suggested_flow'):
        if ai_response['suggested_flow'] == 'new_player':
            keyboard.append([InlineKeyboardButton("🚀 Start New Player Setup", callback_data="new_player_start")])
        elif ai_response['suggested_flow'] == 'existing_player':
            keyboard.append([InlineKeyboardButton("🎮 Existing Player Setup", callback_data="existing_player_start")])
        elif ai_response['suggested_flow'] == 'support':
            keyboard.append([InlineKeyboardButton("🆘 Get Support", callback_data="support_start")])
    
    # Always include chat continuation options
    keyboard.append([InlineKeyboardButton(s['ai_continue_chat'], callback_data="ai_continue_chat")])
    keyboard.append([InlineKeyboardButton(s['ai_switch_to_buttons'], callback_data="back_to_main")])
    
    # Update the thinking message with actual response
    await thinking_msg.edit_text(
        text=response_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return AI_CHAT_FLOW

async def ai_continue_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Continue AI chat after button selection"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    await query.edit_message_text(
        text="💬 **I'm listening! What would you like to know or what help do you need?**\n\nJust type your question and I'll help you with your gaming setup.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(s['ai_switch_to_buttons'], callback_data="back_to_main")],
            [InlineKeyboardButton(s['ai_go_to_menu'], callback_data="back_to_main")]
        ]),
        parse_mode='Markdown'
    )
    
    return AI_CHAT_FLOW

# --- FREE TEXT HANDLER FOR MAIN MENU ---
async def handle_main_menu_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle free text in main menu - route to AI chat"""
    user_message = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    # Quick intent analysis
    user_intent = await determine_user_intent(user_message, lang)
    
    # Store the user's first message for context
    context.user_data['initial_message'] = user_message
    context.user_data['detected_intent'] = user_intent
    
    # Start AI chat with the user's message as context
    return await ai_chat_start(update, context)

# --- BASIC HANDLERS (Keep your existing ones) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point"""
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
    """Set language and show main menu"""
    query = update.callback_query
    lang = query.data
    context.user_data['lang'] = lang
    
    return await show_main_menu(update, context)

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

# --- SIMPLIFIED FLOW STARTERS ---
async def new_player_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start new player flow"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    context.user_data['flow_type'] = 'new_player'
    
    text = f"🎮 **New Player Setup**\n\n{s['new_player_intro']}\n\n💬 *You can ask me anything about the setup process!*"
    
    keyboard = [
        [InlineKeyboardButton("🤖 Ask AI Assistant", callback_data="ai_chat_start")],
        [InlineKeyboardButton(s['back_btn'], callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    return NEW_PLAYER_FLOW

async def existing_player_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start existing player flow"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    context.user_data['flow_type'] = 'existing_player'
    
    text = f"🎯 **Existing Player**\n\n{s['existing_player_intro']}\n\n💬 *What do you need help with?*"
    
    keyboard = [
        [InlineKeyboardButton("🤖 Ask AI Assistant", callback_data="ai_chat_start")],
        [InlineKeyboardButton(s['back_btn'], callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    return EXISTING_PLAYER_FLOW

async def support_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start support flow"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    context.user_data['flow_type'] = 'support'
    
    text = f"🆘 **Support**\n\n{s['support_flow_intro']}\n\n💬 *Tell me what issues you're experiencing!*"
    
    keyboard = [
        [InlineKeyboardButton("🤖 Ask AI Assistant", callback_data="ai_chat_start")],
        [InlineKeyboardButton(s['back_btn'], callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    return SUPPORT_FLOW

def main() -> None:
    """Run the bot with AI chatbot"""
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
                CallbackQueryHandler(new_player_start, pattern="^new_player_start$"),
                CallbackQueryHandler(existing_player_start, pattern="^existing_player_start$"),
                CallbackQueryHandler(show_helpful_channel, pattern="^helpful_channel$"),
                CallbackQueryHandler(support_start, pattern="^contact_support$"),
                CallbackQueryHandler(ai_chat_start, pattern="^ai_chat_start$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu_text),
            ],
            AI_CHAT_FLOW: [
                CallbackQueryHandler(ai_continue_chat, pattern="^ai_continue_chat$"),
                CallbackQueryHandler(ai_chat_start, pattern="^ai_chat_start$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
                CallbackQueryHandler(new_player_start, pattern="^new_player_start$"),
                CallbackQueryHandler(existing_player_start, pattern="^existing_player_start$"),
                CallbackQueryHandler(support_start, pattern="^support_start$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_chat_message),
            ],
            NEW_PLAYER_FLOW: [
                CallbackQueryHandler(ai_chat_start, pattern="^ai_chat_start$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
            EXISTING_PLAYER_FLOW: [
                CallbackQueryHandler(ai_chat_start, pattern="^ai_chat_start$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
            SUPPORT_FLOW: [
                CallbackQueryHandler(ai_chat_start, pattern="^ai_chat_start$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
        ],
    )

    application.add_handler(conv_handler)

    logger.info("Bot is running with AI Chatbot...")
    print("🤖 Bot is starting with AI Chatbot Assistant...")
    print(f"✅ TELEGRAM_TOKEN: {'Set' if TELEGRAM_TOKEN else 'Not Set'}")
    print(f"✅ SUPPORT_CHAT_ID: {'Set' if SUPPORT_CHAT_ID else 'Not Set'}")
    print(f"✅ OPENAI_API_KEY: {'Set' if OPENAI_API_KEY else 'Not Set'}")
    print(f"✅ OPENAI_CLIENT: {'Available' if openai_client else 'Not Available'}")
    
    application.run_polling()

if __name__ == "__main__":
    main()

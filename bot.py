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
SELECT_LANG, MAIN_MENU, EXISTING_PLAYER_FLOW, NEW_PLAYER_FLOW, SUPPORT_FLOW, USERNAME_COLLECTION = range(6)

# Codes for the game
GAME_CODES = [
    "6086-7221-0564",
    "2753-4695-7191", 
    "9689-1352-5966",
    "4563-6624-9460",
    "4828-9033-2281"]

# --- COMPLETE KNOWLEDGE BASE ---
BOT_KNOWLEDGE_BASE = """
FORTNITE CLOUD GAMING BOT - COMPLETE KNOWLEDGE BASE

BOT PURPOSE:
This is a Telegram bot that helps users set up and play Fortnite through cloud gaming, specifically focusing on earning rewards through the reward island system.

GAME CODES FOR REWARD ISLAND:
{game_codes}

MAIN USER FLOWS:

1. NEW PLAYER FLOW:
- Question 1: VPN Usage - Must use USA VPN for profile creation (but not for playing)
- Question 2: Cloud Gaming Profile - Create at Xbox Cloud Gaming
- Question 3: Epic Games Activation Code - Receive and enter activation code
- Question 4: Epic Games Profile - Create gaming profile
- Question 5: Shortcut Creation - Create homescreen shortcut
- Question 6: Game Launch - Launch Fortnite through cloud gaming
- Question 7: Reward Island - Search and find using game codes
- Question 8: Full Setup - Complete all configuration steps
- Question 9: Play Time - 130 hours per week requirement
- Question 10: Like Button - Click like button before each 1-hour session ends
- Question 11: Favorites - Save reward island to favorites
- Question 12: Influencer - Specify if introduced by influencer

2. EXISTING PLAYER FLOW:
- Question 1: Reward Island Access - Have you found the reward island?
- Question 2: Full Setup Completion - Did you complete the full setup?
- Question 3: Play Time - 130 hours per week tracking
- Question 4: Like Button Usage - Regular usage during sessions
- Question 5: Favorites - Reward island in favorites
- Question 6: Influencer Attribution - Were you introduced by influencer?

3. SUPPORT FLOW:
- Question 1: VPN Usage troubleshooting
- Question 2: Cloud Gaming Profile issues
- Question 3: Epic Games Activation problems
- Question 4: Epic Games Profile creation
- Question 5: Shortcut creation help
- Question 6: Game launching issues
- Question 7: Reward Island access problems
- Question 8: Full setup completion
- Question 9: Play time verification (130 hours/week)
- Question 10: Like button usage confirmation
- Question 11: Favorites setup
- Question 12: Influencer information
- Question 13: Final verification before support contact

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

COMMON ISSUES AND SOLUTIONS:
- VPN Issues: Use USA VPN only for profile creation, not for playing
- Activation Problems: Check spam folder for Epic Games code
- Game Not Launching: Ensure cloud gaming profile is properly set up
- Reward Island Not Found: Use correct codes and search properly
- Play Time Tracking: Must play 130 hours weekly and use like button

SUPPORT PROCESS:
- Users answer all questions to identify their exact issue
- If all steps completed correctly, they can claim rewards
- Final step: Provide @username for support team contact
- Support team reviews screenshots and processes rewards

BOT BEHAVIOR:
- Always helpful and encouraging
- Guides users through appropriate steps
- Asks clarifying questions when needed
- Provides specific instructions and links
- Maintains conversation context
- Supports both English and French

RESPONSE GUIDELINES:
- Be specific and actionable
- Provide step-by-step guidance when needed
- Ask questions to understand user's exact situation
- Suggest next appropriate steps
- Always be positive and supportive
- Use the user's preferred language (English/French)
""".format(game_codes=", ".join(GAME_CODES), channel_link=HELPFUL_CHANNEL_LINK)

# --- LANGUAGE STRINGS ---
STRINGS = {
    'en': {
        'disclaimer': "**Disclaimer:** This bot is an unofficial guide and is not affiliated with Epic Games or Fortnite. We will *never* ask for your password.",
        'lang_prompt': "Please select your language:",
        'welcome': "🤖 **AI-Powered Gaming Assistant**\n\nWelcome! I'm your intelligent assistant for Fortnite cloud gaming setup and rewards. I can help you with:\n\n• New player setup\n• Existing player optimization\n• Technical support\n• Reward system guidance\n\nJust type your question or use the menu below!",
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
    },
    'fr': {
        'disclaimer': "**Avertissement :** Ce bot est un guide non officiel et n'est pas affilié à Epic Games ou Fortnite. Nous ne vous demanderons *jamais* votre mot de passe.",
        'lang_prompt': "Veuillez sélectionner votre langue :",
        'welcome': "🤖 **Assistant de Jeu IA**\n\nBienvenue ! Je suis votre assistant intelligent pour la configuration du jeu cloud Fortnite et les récompenses. Je peux vous aider avec :\n\n• Configuration nouveau joueur\n• Optimisation joueur existant\n• Support technique\n• Guide du système de récompenses\n\nTapez simplement votre question ou utilisez le menu ci-dessous !",
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
    }
}

# --- AI BRAIN CORE FUNCTION ---
async def ai_brain_response(user_message: str, user_context: dict, lang: str) -> dict:
    """
    AI Brain: Processes all user messages and provides intelligent responses
    using the complete bot knowledge base.
    """
    if not openai_client:
        return {
            "response": "I'm currently unavailable. Please try again later.",
            "buttons": ["Menu"],
            "next_action": "menu"
        }
    
    try:
        # Get conversation history
        conversation_history = user_context.get('conversation_history', [])
        current_flow = user_context.get('current_flow', 'general')
        user_data = user_context.get('user_data', {})
        
        # Prepare system prompt with complete knowledge
        system_prompt = f"""You are the AI brain of a Fortnite cloud gaming Telegram bot. Use this complete knowledge base:

{BOT_KNOWLEDGE_BASE}

CURRENT USER CONTEXT:
- Language: {lang.upper()}
- Current Flow: {current_flow}
- Conversation History: {len(conversation_history)} messages

USER'S MESSAGE: "{user_message}"

RESPONSE REQUIREMENTS:
1. Analyze the user's message and understand their intent
2. Provide helpful, accurate information from the knowledge base
3. Guide users to appropriate next steps
4. Ask clarifying questions if their situation is unclear
5. Suggest specific flows (new player, existing player, support) when relevant
6. Be conversational, friendly, and encouraging
7. Provide actionable steps and specific instructions
8. Use the user's preferred language consistently

RESPONSE FORMAT (JSON):
{{
    "response": "Your helpful response to the user",
    "buttons": ["Button1", "Button2", ...],
    "next_action": "continue/menu/specific_flow",
    "needs_clarification": true/false,
    "clarification_question": "Question to ask if clarification needed"
}}

Available button options: New Player, Existing Player, Support, Menu, Continue Chat, Join Channel"""

        # Build message history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent conversation history for context
        for msg in conversation_history[-6:]:  # Last 6 messages for context
            messages.append(msg)
        
        messages.append({"role": "user", "content": user_message})
        
        # Generate AI response
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
                "buttons": ["Menu", "Continue Chat"],
                "next_action": "continue"
            }
            
    except Exception as e:
        logger.error(f"Error in AI brain: {e}")
        return {
            "response": "I'm having trouble processing your request. Please try again.",
            "buttons": ["Menu"],
            "next_action": "menu"
        }

# --- CORE MESSAGE HANDLER (AI BRAIN) ---
async def handle_any_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Main message handler - ALL text messages go through the AI brain
    """
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
    
    # Keep only last 20 messages to manage context size
    context.user_data['conversation_history'] = context.user_data['conversation_history'][-20:]
    
    # Create keyboard from AI-suggested buttons
    keyboard = []
    buttons = ai_response.get('buttons', [])
    
    for button_text in buttons:
        if button_text.lower() in ['new player', 'nouveau joueur']:
            keyboard.append([InlineKeyboardButton(s['new_player_btn'], callback_data="new_player_start")])
        elif button_text.lower() in ['existing player', 'joueur existant']:
            keyboard.append([InlineKeyboardButton(s['existing_player_btn'], callback_data="existing_player_start")])
        elif button_text.lower() in ['support', 'soutien']:
            keyboard.append([InlineKeyboardButton(s['support_btn'], callback_data="support_start")])
        elif button_text.lower() in ['menu', 'accueil']:
            keyboard.append([InlineKeyboardButton(s['ai_menu'], callback_data="back_to_main")])
        elif button_text.lower() in ['continue chat', 'continuer']:
            keyboard.append([InlineKeyboardButton(s['ai_continue'], callback_data="continue_chat")])
        elif button_text.lower() in ['join channel', 'rejoindre le canal']:
            keyboard.append([InlineKeyboardButton(s['join_channel_btn'], url=HELPFUL_CHANNEL_LINK)])
        else:
            # Generic button
            keyboard.append([InlineKeyboardButton(button_text, callback_data="continue_chat")])
    
    # Always include basic navigation
    if not any(s['ai_menu'] in str(button) for row in keyboard for button in row):
        keyboard.append([InlineKeyboardButton(s['ai_menu'], callback_data="back_to_main")])
    
    # Update thinking message with actual response
    await thinking_msg.edit_text(
        text=ai_response['response'],
        reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
        parse_mode='Markdown'
    )
    
    # Handle next action suggested by AI
    next_action = ai_response.get('next_action', 'continue')
    if next_action == 'menu':
        return await show_main_menu(update, context)
    elif next_action == 'new_player':
        context.user_data['current_flow'] = 'new_player'
        return NEW_PLAYER_FLOW
    elif next_action == 'existing_player':
        context.user_data['current_flow'] = 'existing_player'
        return EXISTING_PLAYER_FLOW
    elif next_action == 'support':
        context.user_data['current_flow'] = 'support'
        return SUPPORT_FLOW
    
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

# --- FLOW STARTERS ---
async def new_player_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start new player flow"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    context.user_data['current_flow'] = 'new_player'
    context.user_data['flow_type'] = 'new_player'
    context.user_data['current_state'] = NEW_PLAYER_FLOW
    
    text = "🎮 **New Player Setup**\n\nI'll help you get started with Fortnite cloud gaming! This includes:\n\n• VPN setup for profile creation\n• Cloud gaming profile creation\n• Epic Games activation\n• Game setup and configuration\n• Reward island access\n\nWhat specific help do you need with the new player setup?"
    
    keyboard = [
        [InlineKeyboardButton(s['ai_continue'], callback_data="continue_chat")],
        [InlineKeyboardButton(s['ai_menu'], callback_data="back_to_main")]
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
    
    context.user_data['current_flow'] = 'existing_player'
    context.user_data['flow_type'] = 'existing_player'
    context.user_data['current_state'] = EXISTING_PLAYER_FLOW
    
    text = "⚡ **Existing Player**\n\nI can help you with advanced setup, optimization, and reward tracking! This includes:\n\n• Reward island verification\n• Play time optimization\n• Like button usage\n• Favorites management\n• Performance tips\n\nWhat would you like assistance with?"
    
    keyboard = [
        [InlineKeyboardButton(s['ai_continue'], callback_data="continue_chat")],
        [InlineKeyboardButton(s['ai_menu'], callback_data="back_to_main")]
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
    
    context.user_data['current_flow'] = 'support'
    context.user_data['flow_type'] = 'support'
    context.user_data['current_state'] = SUPPORT_FLOW
    
    text = "🆘 **Support**\n\nI'm here to help with any technical issues or problems you're experiencing! This includes:\n\n• VPN troubleshooting\n• Account setup issues\n• Game launching problems\n• Reward access issues\n• Technical errors\n\nPlease describe the issue you're facing in detail."
    
    keyboard = [
        [InlineKeyboardButton(s['ai_continue'], callback_data="continue_chat")],
        [InlineKeyboardButton(s['ai_menu'], callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    return SUPPORT_FLOW

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
                CallbackQueryHandler(new_player_start, pattern="^new_player_start$"),
                CallbackQueryHandler(existing_player_start, pattern="^existing_player_start$"),
                CallbackQueryHandler(show_helpful_channel, pattern="^helpful_channel$"),
                CallbackQueryHandler(support_start, pattern="^support_start$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
                CallbackQueryHandler(continue_chat, pattern="^continue_chat$"),
                # ALL text messages go to AI brain
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_any_message),
            ],
            NEW_PLAYER_FLOW: [
                CallbackQueryHandler(continue_chat, pattern="^continue_chat$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
                # ALL text messages go to AI brain
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_any_message),
            ],
            EXISTING_PLAYER_FLOW: [
                CallbackQueryHandler(continue_chat, pattern="^continue_chat$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
                # ALL text messages go to AI brain
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_any_message),
            ],
            SUPPORT_FLOW: [
                CallbackQueryHandler(continue_chat, pattern="^continue_chat$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
                # ALL text messages go to AI brain
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_any_message),
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
    print("🚀 ALL messages will be processed by AI Brain!")
    
    application.run_polling()

if __name__ == "__main__":
    main()

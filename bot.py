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

# Try to import OpenAI, but handle gracefully if not available
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

# Initialize OpenAI client only if available and API key is set
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
        'support_q1': "Have you already read the 'New player' guide and the 'Full guide in channel'?",
        'yes_btn': "Yes, I still have a question",
        'no_btn': "No, I will check them now",
        'support_q1_no': "Please review those guides first. They answer most questions! 🙏\n\nReturning you to the main menu.",
        'support_q2': "Okay. By providing your @username, you consent to our support team contacting you directly on Telegram. We will *only* use this to help with your question.\n\nPlease type your @username (like @myusername) to proceed.\n\nType /cancel to go back.",
        'support_thanks': "Thank you! Your @username has been noted. We will get in touch with you as soon as possible.\n\nReturning you to the main menu.",
        'support_cancel': "Support request cancelled. Returning to main menu.",
        'invalid_username': "That doesn't look like a valid @username. Please start with '@' and try again, or type /cancel.",
        'username_prompt': "Okay. By providing your @username, you consent to our support team contacting you directly on Telegram. We will *only* use this to help with your question.\n\nPlease type your @username (like @myusername) to proceed.\n\nType /cancel to go back.",
        
        # Support flow
        'support_flow_title': "Support",
        'support_flow_intro': "In order to get in touch with us, you need to answer these questions so we can determine which stage of the process you're at. If everything has been done correctly, you'll be able to claim your reward 💰💰",
        'support_q1_text': "1 Did you use a VPN?",
        'support_q2_text': "2 - Did you already create a cloud gaming profile?",
        'support_q3_text': "3 - Did you receive the code from epic games to activate your cloud gaming account?",
        'support_q4_text': "4 Did you create your epic games profile?",
        'support_q5_text': "5 Did you create a shortcut of the cloud gaming to play it like an installed app directly from your Homescreen?",
        'support_q6_text': "6 Have you launched the game?",
        'support_q7_text': "7 Have you searched and found the reward Island?",
        'support_q8_text': "8 Did you follow the full setup to be able to play with friends and earn a lot together without any worries?",
        'support_q9_text': "9 Did you start the game and play 130 hours for free this week?",
        'support_q10_text': "10 Did you click on the like button every single time before your 1 hour play session ended during your 130 hours of play this week?",
        'support_q11_text': "11 Have you saved the reward Island to your favorites?",
        'support_q12_text': "12 Were you introduced to this game by an influencer?",
        'support_q13_text': "13 Make sure you completed every single step before sending us your @, did you completed every single step and play at least 130 hours this week?",
        
        # Common responses
        'vpn_reminder': "Please download and use a VPN in USA before going any further to create all your authentic profiles but to play you don't use it.\n\nDid you finally use a VPN?",
        'cloud_gaming_reminder': "Please create a cloud gaming profile. Do you want our assistance?",
        'epic_code_reminder': "Please you have to receive the code, do you want our guidance to help you with that?",
        'epic_profile_reminder': "No please you have to create your epic games profile, do you want our guidance?",
        'shortcut_reminder': "No. You have to create a shortcut to play fortnite from your homescreen, do you want our guidance with that?",
        'launch_game_reminder': "No you have to launch the game, do you need our guidance?",
        'reward_island_reminder': "No, you have to search the reward Island in the search bar and just choose it , do you want our guidance for that?",
        'full_setup_reminder': "No, you have to follow the exact setup , do you need our guidance?",
        'play_hours_reminder': "No, you have to start the game and play every single day for free before aiming for the reward, are you able to play at least 130 hours a week?",
        'like_button_reminder': "No, You have to click on the like button every single time before your 1 hour play session ended during your 130 hours a week , do you want our guidance on that?",
        'favorites_reminder': "No , you have to save the reward Island to your favorites and play , do you want our guidance on that?",
        'expert_review_text': "One of the expert will review all the screenshots of the game and you will earn",
        
        # Button texts
        'a_yes': "A Yes",
        'b_no': "B No",
        'a_if_yes': "A If yes",
        'b_if_no': "B If no",
        'yes_i_received': "A Yes I received the code , I want the next step",
        'yes_im_ready': "A Yes, I'm ready for the next step",
        'yes_i_did': "A Yes , I did it and I will send you all the necessary screenshots",
        'want_codes': "Yes I want the best codes to play",
        'already_chose': "No , I already choosed one code",
        'want_assistance': "Yes",
        'already_have': "No I already have one, I want the next step",
        'finally_fixed': "No I finally fix everything, I want to move to the next step",
        'will_play': "No, I will play and let you know in the support session later on",
        'have_proof': "No , I have proof I saved the reward Island to my favorites and I actually play on it",
        'have_proof_played': "No, I have proof that I played 130 hours this week and I liked every single time , and I am wishing to share it with you guys",
        'see_channel': "yes I want to see it in the channel",
        'completed': "Completed",
        'next_question': "Next Question",
        'join_channel_only': "Join Channel",
        
        # Specific custom buttons
        'b_1_if_yes': "B - 1 If yes",
        'b_2_if_no': "B - 2 if no",
        'b_1_yes': "B - 1 Yes",
        'b_2_no_already_have': "B - 2 No I already have one, I want the next step",
        'b_2_no': "B - 2 No",
        'b_1_see_channel': "B - 1 yes I want to see it in the channel",
        'b_2_no_shortcut': "B - 2 No I finally create a shortcut",
        'b_2_no_already_chose': "B - 2 No , I already choosed one code",
        'b_2_no_fix_everything': "B - 2 No I finally fix everything, I want to move to the next step",
        'b_2_no_will_play': "B - 2 No, I will play and let you know in the support session later on",
        'b_2_no_have_proof_saved': "B - 2 No , I have proof I saved the reward Island to my favorites and I actually play on it",
        'b_2_no_have_proof_played': "B - 2 No, I have proof that I played 130 hours this week and I liked every single time , and I am wishing to share it with you guys",
        'b_2_no_fix_next_step': "B - 2 No I finally fix everything, I want to move to the next step",
        
        # Code messages
        'codes_title': "Just copy one of them and enter it on the search bar:\n\n",
        'support_codes_title': "Here are the codes for the reward Island:\n\n",
        
        # Navigation
        'back_to_previous': "⬅️ Back",
        'back_to_support': "⬅️ Back to Support",
        'back_to_existing': "⬅️ Back to Existing Player", 
        'back_to_new': "⬅️ Back to New Player",
        'main_menu': "🏠 Main Menu",
        
        # Influencer question
        'provide_name': "Provide the name please:",
        
        # Existing player flow
        'existing_player_intro': "Because you are playing on the cloud, your session will last for 1 hour. The game will close, and you will have to launch it again to keep playing.\nYou probably know it cause you already follow all the instructions\n\n1 Have you searched and found the reward Island?",
        'existing_q2_text': "2 Did you follow the full setup to be able to play with friends and earn a lot together without any worries?",
        'existing_q3_text': "3 Did you start the game and play 130 hours for free this week?",
        'existing_q4_text': "4 With your existing account ,  will you click on the like button every single time before your 1 hour play session ended during your 130 hours of play this week?",
        'existing_q5_text': "5 Did you save the reward Island to your favorites?",
        'existing_q6_text': "6 Were you introduced to this game by an influencer?",
        
        # New player flow
        'new_player_intro': "New player:\n\nYou're diving into an immersive gaming adventure.This bot will help you set up your account, join the game, start playing and earning\nBecause you are playing on the cloud, your session will last for 1 hour. The game will close, and you will have to launch it again to keep playing.\n\n1 Did you use a VPN?",
        'new_q2_text': "2 - Did you already create a cloud gaming profile?",
        'new_q3_text': "3 - Did you receive the code from epic games to activate your cloud gaming account?",
        'new_q4_text': "4 Did you create your epic games profile?",
        'new_q5_text': "5 Did you create a shortcut of the cloud gaming to play it like an installed app directly from your Homescreen?",
        'new_q6_text': "6 Have you launched the game?",
        'new_q7_text': "7 Have you searched and found the reward Island?",
        'new_q8_text': "8 Did you follow the full setup to be able to play with friends and earn a lot together without any worries?",
        'new_q9_text': "9 Will you start the game and play 130 hours for free this week?",
        'new_q10_text': "10 With your new account , will you click on the like button every single time before your 1 hour play session ended during your 130 hours of play this week?",
        'new_q11_text': "11 Will you save the reward Island to your favorites?",
        'new_q12_text': "12 Were you introduced to this game by an influencer?",
        
        # Links and guidance
        'cloud_gaming_link': "Here's the link to create your cloud gaming profile:\nhttps://www.xbox.com/fr-FR/play/games/fortnite/BT5P2X999VH2",
        'epic_activate_link': "Here's the activation link:\nhttp://epicgames.com/activate",
        'epic_create_link': "Create your Epic Games profile here:\nepicgames.com",
        'launch_game_link': "Launch the game here:\nhttps://www.xbox.com/fr-FR/play/games/fortnite/BT5P2X999VH2",
        'channel_guidance': "Please check our channel for guidance:",
        'channel_instruction_9': "Please check our channel and look for instruction 9:",
        'channel_instruction_10': "Please check our channel and look for instruction 10:",
        'channel_instruction_11': "Please check our channel and look for instruction 11:",
        'channel_instruction_12': "Please check our channel and look for instruction 12:",
        'channel_instruction_13': "Please check our channel and look for instruction 13:",
        
        # AI Features (will be used when available)
        'ai_assistance_btn': "🤖 AI Assistant",
        'ai_welcome': "🤖 **AI Assistant**\n\nI can help answer your questions and guide you through the process. What would you like to know?",
        'ai_thinking': "🤔 Let me think about that...",
        'ai_suggestion': "💡 **Suggestion:**",
        'ai_question': "❓ **Question:**",
        'ai_continue': "Continue with AI",
        'ai_go_back': "⬅️ Back to Menu",
        'ai_analyzing_flow': "🔍 Analyzing your progress...",
        'ai_understanding': "I understand you're working on:",
        'ai_next_steps': "📋 **Recommended Next Steps:**",
        'ai_type_response': "💬 You can type your response or use the buttons below:",
        'ai_unavailable': "⚠️ AI features are currently unavailable. Please use the button options below.",
    },
    'fr': {
        # ... (French translations remain the same as in your original code)
        # Add the AI-related French strings similarly
        'ai_assistance_btn': "🤖 Assistant IA",
        'ai_welcome': "🤖 **Assistant IA**\n\nJe peux répondre à vos questions et vous guider dans le processus. Que souhaitez-vous savoir ?",
        'ai_thinking': "🤔 Laissez-moi réfléchir à cela...",
        'ai_suggestion': "💡 **Suggestion :**",
        'ai_question': "❓ **Question :**",
        'ai_continue': "Continuer avec l'IA",
        'ai_go_back': "⬅️ Retour au Menu",
        'ai_analyzing_flow': "🔍 Analyse de votre progression...",
        'ai_understanding': "Je comprends que vous travaillez sur :",
        'ai_next_steps': "📋 **Prochaines Étapes Recommandées :**",
        'ai_type_response': "💬 Vous pouvez taper votre réponse ou utiliser les boutons ci-dessous :",
        'ai_unavailable': "⚠️ Les fonctionnalités IA sont actuellement indisponibles. Veuillez utiliser les options de bouton ci-dessous.",
    }}

# --- SIMPLIFIED AI FUNCTIONS (with fallbacks) ---
async def generate_ai_response_simple(user_context: dict, current_question: str, user_response: str, lang: str) -> dict:
    """
    Simplified AI response generator with fallbacks
    """
    if not openai_client:
        return {
            "response": STRINGS[lang]['ai_unavailable'],
            "next_question": None,
            "buttons": [],
            "should_redirect": False
        }
    
    try:
        # Simple prompt for basic assistance
        system_prompt = f"""You are a helpful gaming assistant. User language: {lang}
Current question: {current_question}
User response: {user_response}

Provide brief, helpful guidance. Keep it under 2 sentences."""
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use cheaper model for basic functionality
            messages=[{"role": "system", "content": system_prompt}],
            temperature=0.7,
            max_tokens=150
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        return {
            "response": ai_response,
            "next_question": None,
            "buttons": ["Next Question" if lang == 'en' else "Question Suivante"],
            "should_redirect": False
        }
            
    except Exception as e:
        logger.error(f"Error in simple AI response: {e}")
        return {
            "response": STRINGS[lang]['ai_unavailable'],
            "next_question": None,
            "buttons": [],
            "should_redirect": False
        }

# --- HELPER FUNCTIONS ---
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str = None):
    """Helper function to show the main menu in the user's language."""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    keyboard = [
        [InlineKeyboardButton(s['new_player_btn'], callback_data="new_player_start")],
        [InlineKeyboardButton(s['existing_player_btn'], callback_data="existing_player_start")],
        [InlineKeyboardButton(s['helpful_channel_btn'], callback_data="helpful_channel")],
        [InlineKeyboardButton(s['support_btn'], callback_data="contact_support")],
    ]
    
    # Only show AI button if available
    if openai_client:
        keyboard.append([InlineKeyboardButton(s['ai_assistance_btn'], callback_data="ai_assistance_start")])
    
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

# --- SIMPLE AI ASSISTANCE FLOW ---
async def ai_assistance_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start simple AI assistance flow"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    if not openai_client:
        await query.edit_message_text(
            text=s['ai_unavailable'],
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(s['back_btn'], callback_data="back_to_main")]
            ])
        )
        return MAIN_MENU
    
    text = s['ai_welcome']
    
    keyboard = [
        [InlineKeyboardButton(s['new_player_btn'], callback_data="new_player_start")],
        [InlineKeyboardButton(s['existing_player_btn'], callback_data="existing_player_start")],
        [InlineKeyboardButton(s['support_btn'], callback_data="support_start")],
        [InlineKeyboardButton(s['back_btn'], callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    return MAIN_MENU

# --- KEEP ALL YOUR ORIGINAL FLOW HANDLERS ---
# [Include all your original new_player_start, existing_player_start, support_start, 
#  and all the question handlers exactly as they were in your working code]

async def new_player_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Flow - Start"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    context.user_data['new_player_qa'] = []  # Initialize Q&A storage
    
    # Store Q1 text to use in subsequent handlers
    context.user_data['new_q1_text'] = s['new_player_intro'].split('\n')[-1]

    text = s['new_player_intro']
    
    keyboard = [
        [InlineKeyboardButton(s['a_yes'], callback_data="new_q1_yes")],
        [InlineKeyboardButton(s['b_no'], callback_data="new_q1_no")],
        [InlineKeyboardButton(s['back_btn'], callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

# [Continue with all your existing handlers...]
# new_q1_yes, new_q1_no, new_q2_yes, etc.
# existing_player_start, existing_q1_yes, etc.
# support_start, support_q1_yes, etc.

# --- CONVERSATION HANDLERS ---
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

# [Include all your other existing handlers like collect_username, cancel_support, etc.]

def main() -> None:
    """Run the bot."""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN environment variable not set!")
        print("❌ ERROR: TELEGRAM_TOKEN environment variable is required!")
        return

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Use your existing conversation handler structure
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
                CallbackQueryHandler(ai_assistance_start, pattern="^ai_assistance_start$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
            EXISTING_PLAYER_FLOW: [
                # [Include all your existing existing player handlers]
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
            NEW_PLAYER_FLOW: [
                # [Include all your existing new player handlers]
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
            SUPPORT_FLOW: [
                # [Include all your existing support handlers]
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
            USERNAME_COLLECTION: [
                # [Include your username collection handlers]
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            CommandHandler("cancel", cancel_support) 
        ],
    )

    application.add_handler(conv_handler)

    logger.info("Bot is running...")
    print("🤖 Bot is starting...")
    print(f"✅ TELEGRAM_TOKEN: {'Set' if TELEGRAM_TOKEN else 'Not Set'}")
    print(f"✅ SUPPORT_CHAT_ID: {'Set' if SUPPORT_CHAT_ID else 'Not Set'}")
    print(f"✅ OPENAI_API_KEY: {'Set' if OPENAI_API_KEY else 'Not Set'}")
    print(f"✅ OPENAI_CLIENT: {'Available' if openai_client else 'Not Available'}")
    
    application.run_polling()

if __name__ == "__main__":
    main()

import logging
import os
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

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
# Get environment variables from Render
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
SUPPORT_CHAT_ID = os.environ.get("SUPPORT_CHAT_ID")  # Support group chat ID from environment

# Debug: Print environment variables
print("=" * 50)
print("ENVIRONMENT VARIABLES CHECK:")
print(f"TELEGRAM_TOKEN: {'✅ SET' if TELEGRAM_TOKEN else '❌ NOT SET'}")
print(f"SUPPORT_CHAT_ID: {'✅ SET' if SUPPORT_CHAT_ID else '❌ NOT SET'}")
if SUPPORT_CHAT_ID:
    print(f"SUPPORT_CHAT_ID value: {SUPPORT_CHAT_ID}")
print("=" * 50)

# !!! IMPORTANT: Fill these in with your information !!!
YOUR_PLAYGROUND_NAME = "My Awesome Playground"  # The *exact name* to search for in Fortnite
YOUR_PLAYGROUND_LINK = "https://your-fortnite-playground-link.com"  # The direct link for existing players
HELPFUL_CHANNEL_LINK = "https://t.me/rejoinsnousetgagne"
# !!!!!!!!!!!!!!!!!!!!!


# --- LANGUAGE STRINGS ---
STRINGS = {
    'en': {
        'disclaimer': (
            "**Disclaimer:** This bot is an unofficial guide and is not affiliated with "
            "Epic Games or Fortnite. We will *never* ask for your password."
        ),
        'lang_prompt': "Please select your language:",
        'welcome': (
            "Welcome! You're diving into an immersive gaming adventure. "
            "This bot will help you set up your account, join the game, and start playing."
        ),
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
        'support_q2': (
            "Okay. By providing your @username, you consent to our support team "
            "contacting you directly on Telegram. We will *only* use this to help with your question.\n\n"
            "Please type your @username (like @myusername) to proceed.\n\n"
            "Type /cancel to go back."
        ),
        'support_thanks': "Thank you! Your @username has been noted. We will get in touch with you as soon as possible.\n\nReturning you to the main menu.",
        'support_cancel': "Support request cancelled. Returning to main menu.",
        'invalid_username': "That doesn't look like a valid @username. Please start with '@' and try again, or type /cancel.",
        'username_prompt': (
            "Okay. By providing your @username, you consent to our support team "
            "contacting you directly on Telegram. We will *only* use this to help with your question.\n\n"
            "Please type your @username (like @myusername) to proceed.\n\n"
            "Type /cancel to go back."
        ),
    },
    'fr': {
        'disclaimer': (
            "**Avertissement :** Ce bot est un guide non officiel et n'est pas affilié à "
            "Epic Games ou Fortnite. Nous ne vous demanderons *jamais* votre mot de passe."
        ),
        'lang_prompt': "Veuillez sélectionner votre langue :",
        'welcome': (
            "Bienvenue ! Tu plonges dans une aventure de jeu immersive. "
            "Ce bot t'aidera à configurer ton compte, à rejoindre la partie et à commencer à jouer."
        ),
        'new_player_btn': "Nouveau joueur",
        'existing_player_btn': "Joueur existant",
        'helpful_channel_btn': "Guide complet sur le canal",
        'support_btn': "Support",
        'lang_btn': "🌐 Changer de Langue",
        'helpful_channel_text': "Rejoignez notre canal Telegram pour le guide complet, les actualités et pour discuter avec la communauté !",
        'join_channel_btn': "Rejoindre le Canal",
        'back_btn': "⬅️ Retour au Menu Principal",
        'support_q1': "Avez-vous déjà lu le guide 'Nouveau joueur' et le 'Guide complet sur le canal' ?",
        'yes_btn': "Oui, j'ai encore une question",
        'no_btn': "Non, je vais les voir maintenant",
        'support_q1_no': "Veuillez d'abord consulter ces guides. Ils répondent à la plupart des questions ! 🙏\n\nRetour au menu principal.",
        'support_q2': (
            "D'accord. En fournissant votre @nomdutilisateur, vous acceptez que notre équipe d'assistance "
            "vous contacte directement sur Telegram. Nous l'utiliserons *uniquement* pour répondre à votre question.\n\n"
            "Veuillez taper votre @nomdutilisateur (comme @monpseudo) pour continuer.\n\n"
            "Tapez /cancel pour revenir."
        ),
        'support_thanks': "Merci ! Votre @nomdutilisateur a été noté. Nous vous contacterons dès que possible.\n\nRetour au menu principal.",
        'support_cancel': "Demande d'aide annulée. Retour au menu principal.",
        'invalid_username': "Cela ne ressemble pas à un @nomdutilisateur valide. Veuillez commencer par '@' et réessayer, ou tapez /cancel.",
        'username_prompt': (
            "D'accord. En fournissant votre @nomdutilisateur, vous acceptez que notre équipe d'assistance "
            "vous contacte directement sur Telegram. Nous l'utiliserons *uniquement* pour répondre à votre question.\n\n"
            "Veuillez taper votre @nomdutilisateur (comme @monpseudo) pour continuer.\n\n"
            "Tapez /cancel pour revenir."
        ),
    }
}

# Define states
SELECT_LANG, MAIN_MENU, EXISTING_PLAYER_FLOW, NEW_PLAYER_FLOW, SUPPORT_FLOW, USERNAME_COLLECTION = range(6)

# --- Helper Functions ---
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str = None):
    """Helper function to show the main menu in the user's language."""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    keyboard = [
        [InlineKeyboardButton(s['new_player_btn'], callback_data="new_player_start")],
        [InlineKeyboardButton(s['existing_player_btn'], callback_data="existing_player_link")],
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

# --- EXISTING PLAYER FLOW ---

async def existing_player_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Flow - Question 1"""
    # Initialize user data for existing player flow
    context.user_data['existing_player_qa'] = []
    
    query = update.callback_query
    await query.answer()
    
    text = (
        "Because you are playing on the cloud, your session will last for 1 hour. The game will close, and you will have to launch it again to keep playing.\n"
        "You probably know it cause you already follow all the instructions\n\n"
        "1 Have you searched and found the reward Island?"
    )
    
    keyboard = [
        [InlineKeyboardButton("A Yes", callback_data="existing_q1_yes")],
        [InlineKeyboardButton("B No", callback_data="existing_q1_no")],
        [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return EXISTING_PLAYER_FLOW

async def existing_q1_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Q1 - Yes -> Q2"""
    # Store the question and answer
    context.user_data['existing_player_qa'].append(("1. Have you searched and found the reward Island?", "A Yes"))
    
    query = update.callback_query
    await query.answer()
    
    text = "2 Did you follow the full setup to be able to play with friends and earn a lot together without any worries?"
    
    keyboard = [
        [InlineKeyboardButton("A Yes, I'm ready for the next step", callback_data="existing_q2_yes")],
        [InlineKeyboardButton("B No", callback_data="existing_q2_no")],
        [InlineKeyboardButton("⬅️ Back", callback_data="existing_player_start")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return EXISTING_PLAYER_FLOW

async def existing_q1_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Q1 - No"""
    # Store the question and answer
    context.user_data['existing_player_qa'].append(("1. Have you searched and found the reward Island?", "B No"))
    
    query = update.callback_query
    await query.answer()
    
    text = "No, you have to search the reward Island in the search bar and just choose it, do you want our guidance for that?"
    
    keyboard = [
        [InlineKeyboardButton("Yes I want the best codes to play", callback_data="existing_q1_codes")],
        [InlineKeyboardButton("No, I already choosed one code", callback_data="existing_q2_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="existing_player_start")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return EXISTING_PLAYER_FLOW

async def existing_q1_codes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player - Show codes"""
    query = update.callback_query
    await query.answer()
    
    text = "Just copy one of them and enter it on the search bar\n\n[CODES WILL BE DISPLAYED HERE]"
    
    keyboard = [
        [InlineKeyboardButton("Next Question", callback_data="existing_q2_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="existing_q1_no")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return EXISTING_PLAYER_FLOW

async def existing_q2_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Q2 - Yes -> Q3"""
    # Store the question and answer
    context.user_data['existing_player_qa'].append(("2. Did you follow the full setup to be able to play with friends and earn a lot together without any worries?", "A Yes, I'm ready for the next step"))
    
    query = update.callback_query
    await query.answer()
    
    text = "3 Did you start the game and play 130 hours for free this week?"
    
    keyboard = [
        [InlineKeyboardButton("A Yes", callback_data="existing_q3_yes")],
        [InlineKeyboardButton("B No", callback_data="existing_q3_no")],
        [InlineKeyboardButton("⬅️ Back", callback_data="existing_q1_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return EXISTING_PLAYER_FLOW

async def existing_q2_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Q2 - No"""
    # Store the question and answer
    context.user_data['existing_player_qa'].append(("2. Did you follow the full setup to be able to play with friends and earn a lot together without any worries?", "B No"))
    
    query = update.callback_query
    await query.answer()
    
    text = "No, you have to follow the exact setup, do you need our guidance?"
    
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="existing_channel_forward")],
        [InlineKeyboardButton("No I finally fix everything", callback_data="existing_q3_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="existing_q1_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return EXISTING_PLAYER_FLOW

async def existing_q3_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Q3 - Yes -> Q4"""
    # Store the question and answer
    context.user_data['existing_player_qa'].append(("3. Did you start the game and play 130 hours for free this week?", "A Yes"))
    
    query = update.callback_query
    await query.answer()
    
    text = "4 With your existing account, will you click on the like button every single time before your 1 hour play session ended during your 130 hours of play this week?"
    
    keyboard = [
        [InlineKeyboardButton("A Yes", callback_data="existing_q4_yes")],
        [InlineKeyboardButton("B No", callback_data="existing_q4_no")],
        [InlineKeyboardButton("⬅️ Back", callback_data="existing_q2_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return EXISTING_PLAYER_FLOW

async def existing_q3_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Q3 - No"""
    # Store the question and answer
    context.user_data['existing_player_qa'].append(("3. Did you start the game and play 130 hours for free this week?", "B No"))
    
    query = update.callback_query
    await query.answer()
    
    text = "No, you have to start the game and play every single day for free before aiming for the reward, are you able to play at least 130 hours a week?"
    
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="existing_q4_yes")],
        [InlineKeyboardButton("No", callback_data="existing_channel_forward")],
        [InlineKeyboardButton("⬅️ Back", callback_data="existing_q2_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return EXISTING_PLAYER_FLOW

async def existing_q4_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Q4 - Yes -> Q5"""
    # Store the question and answer
    context.user_data['existing_player_qa'].append(("4. With your existing account, will you click on the like button every single time before your 1 hour play session ended during your 130 hours of play this week?", "A Yes"))
    
    query = update.callback_query
    await query.answer()
    
    text = "5 Did you save the reward Island to your favorites?"
    
    keyboard = [
        [InlineKeyboardButton("A Yes", callback_data="existing_q5_yes")],
        [InlineKeyboardButton("B No", callback_data="existing_q5_no")],
        [InlineKeyboardButton("⬅️ Back", callback_data="existing_q3_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return EXISTING_PLAYER_FLOW

async def existing_q4_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Q4 - No"""
    # Store the question and answer
    context.user_data['existing_player_qa'].append(("4. With your existing account, will you click on the like button every single time before your 1 hour play session ended during your 130 hours of play this week?", "B No"))
    
    query = update.callback_query
    await query.answer()
    
    text = "No, You have to click on the like button every single time before your 1 hour play session ended during your 130 hours a week, do you want our guidance on that?"
    
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="existing_channel_forward")],
        [InlineKeyboardButton("No, I will play and let you know", callback_data="existing_q5_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="existing_q3_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return EXISTING_PLAYER_FLOW

async def existing_q5_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Q5 - Yes -> Q6"""
    # Store the question and answer
    context.user_data['existing_player_qa'].append(("5. Did you save the reward Island to your favorites?", "A Yes"))
    
    query = update.callback_query
    await query.answer()
    
    text = "6 Were you introduced to this game by an influencer?"
    
    keyboard = [
        [InlineKeyboardButton("A Yes", callback_data="existing_influencer_yes")],
        [InlineKeyboardButton("B No", callback_data="existing_channel_forward")],
        [InlineKeyboardButton("⬅️ Back", callback_data="existing_q4_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return EXISTING_PLAYER_FLOW

async def existing_q5_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Q5 - No"""
    # Store the question and answer
    context.user_data['existing_player_qa'].append(("5. Did you save the reward Island to your favorites?", "B No"))
    
    query = update.callback_query
    await query.answer()
    
    text = "No, you have to save the reward Island to your favorites and play, do you want our guidance on that?"
    
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="existing_channel_forward")],
        [InlineKeyboardButton("No, I have proof I saved it", callback_data="existing_q5_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="existing_q4_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return EXISTING_PLAYER_FLOW

async def existing_influencer_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player - Influencer Yes"""
    # Store the question and answer
    context.user_data['existing_player_qa'].append(("6. Were you introduced to this game by an influencer?", "A Yes"))
    
    query = update.callback_query
    await query.answer()
    
    text = "Provide the name please: [USER WOULD TYPE THE NAME]"
    
    keyboard = [
        [InlineKeyboardButton("Completed", callback_data="existing_ask_username")],
        [InlineKeyboardButton("⬅️ Back", callback_data="existing_q5_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return EXISTING_PLAYER_FLOW

async def existing_ask_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player - Ask for username after completing questions"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store that this is from existing player flow
    context.user_data['flow_type'] = 'existing_player'
    
    await query.edit_message_text(text=s['username_prompt'], parse_mode='Markdown')
    return USERNAME_COLLECTION

async def existing_channel_forward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Forward to channel from existing player flow"""
    query = update.callback_query
    await query.answer()
    
    text = f"Please check our channel for guidance: {HELPFUL_CHANNEL_LINK}"
    
    keyboard = [
        [InlineKeyboardButton("⬅️ Back to Existing Player", callback_data="existing_player_start")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return EXISTING_PLAYER_FLOW

# --- NEW PLAYER FLOW ---

async def new_player_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Flow - Start"""
    # Initialize user data for new player flow
    context.user_data['new_player_qa'] = []
    
    query = update.callback_query
    await query.answer()
    
    text = (
        "New player:\n\n"
        "You're diving into an immersive gaming adventure. This bot will help you set up your account, join the game, start playing and earning.\n"
        "Because you are playing on the cloud, your session will last for 1 hour. The game will close, and you will have to launch it again to keep playing.\n\n"
        "1 Did you use a VPN?"
    )
    
    keyboard = [
        [InlineKeyboardButton("A If yes", callback_data="new_q1_yes")],
        [InlineKeyboardButton("B If no", callback_data="new_q1_no")],
        [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q1_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q1 - Yes -> Q2"""
    # Store the question and answer
    context.user_data['new_player_qa'].append(("1. Did you use a VPN?", "A If yes"))
    
    query = update.callback_query
    await query.answer()
    
    text = "2 - Did you already create a cloud gaming profile?"
    
    keyboard = [
        [InlineKeyboardButton("A if yes", callback_data="new_q2_yes")],
        [InlineKeyboardButton("B if no", callback_data="new_q2_no")],
        [InlineKeyboardButton("⬅️ Back", callback_data="new_player_start")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q1_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q1 - No"""
    # Store the question and answer
    context.user_data['new_player_qa'].append(("1. Did you use a VPN?", "B If no"))
    
    query = update.callback_query
    await query.answer()
    
    text = "Please download and use a VPN in USA before going any further to create all your authentic profiles but to play you don't use it.\n\nDid you finally use a VPN?"
    
    keyboard = [
        [InlineKeyboardButton("If yes", callback_data="new_q2_yes")],
        [InlineKeyboardButton("if no", callback_data="new_channel_forward")],
        [InlineKeyboardButton("⬅️ Back", callback_data="new_player_start")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q2_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q2 - Yes -> Q3"""
    # Store the question and answer
    context.user_data['new_player_qa'].append(("2. Did you already create a cloud gaming profile?", "A if yes"))
    
    query = update.callback_query
    await query.answer()
    
    text = "3 - Did you receive the code from epic games to activate your cloud gaming account?"
    
    keyboard = [
        [InlineKeyboardButton("A Yes I received the code", callback_data="new_q3_yes")],
        [InlineKeyboardButton("B No", callback_data="new_q3_no")],
        [InlineKeyboardButton("⬅️ Back", callback_data="new_q1_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q2_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q2 - No"""
    # Store the question and answer
    context.user_data['new_player_qa'].append(("2. Did you already create a cloud gaming profile?", "B if no"))
    
    query = update.callback_query
    await query.answer()
    
    text = "Please create a cloud gaming profile. Do you want our assistance?"
    
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="new_cloud_gaming_link")],
        [InlineKeyboardButton("No I already have one", callback_data="new_q3_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="new_q1_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_cloud_gaming_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player - Cloud Gaming Link"""
    query = update.callback_query
    await query.answer()
    
    text = "Here's the link to create your cloud gaming profile:\nhttps://www.xbox.com/fr-FR/play/games/fortnite/BT5P2X999VH2"
    
    keyboard = [
        [InlineKeyboardButton("Next Question", callback_data="new_q3_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="new_q2_no")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q3_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q3 - Yes -> Q4"""
    # Store the question and answer
    context.user_data['new_player_qa'].append(("3. Did you receive the code from epic games to activate your cloud gaming account?", "A Yes I received the code"))
    
    query = update.callback_query
    await query.answer()
    
    text = "4 Did you create your epic games profile?"
    
    keyboard = [
        [InlineKeyboardButton("A Yes", callback_data="new_q4_yes")],
        [InlineKeyboardButton("B No", callback_data="new_q4_no")],
        [InlineKeyboardButton("⬅️ Back", callback_data="new_q2_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q3_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q3 - No"""
    # Store the question and answer
    context.user_data['new_player_qa'].append(("3. Did you receive the code from epic games to activate your cloud gaming account?", "B No"))
    
    query = update.callback_query
    await query.answer()
    
    text = "Please you have to receive the code, do you want our guidance to help you with that?"
    
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="new_epic_activate")],
        [InlineKeyboardButton("No", callback_data="new_channel_forward")],
        [InlineKeyboardButton("⬅️ Back", callback_data="new_q2_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_epic_activate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player - Epic Games Activate"""
    query = update.callback_query
    await query.answer()
    
    text = "Here's the activation link:\nhttp://epicgames.com/activate"
    
    keyboard = [
        [InlineKeyboardButton("Next Question", callback_data="new_q4_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="new_q3_no")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q4_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q4 - Yes -> Q5"""
    # Store the question and answer
    context.user_data['new_player_qa'].append(("4. Did you create your epic games profile?", "A Yes"))
    
    query = update.callback_query
    await query.answer()
    
    text = "5 Did you create a shortcut of the cloud gaming to play it like an installed app directly from your Homescreen?"
    
    keyboard = [
        [InlineKeyboardButton("A Yes", callback_data="new_q5_yes")],
        [InlineKeyboardButton("B No", callback_data="new_q5_no")],
        [InlineKeyboardButton("⬅️ Back", callback_data="new_q3_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q4_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q4 - No"""
    # Store the question and answer
    context.user_data['new_player_qa'].append(("4. Did you create your epic games profile?", "B No"))
    
    query = update.callback_query
    await query.answer()
    
    text = "No please you have to create your epic games profile, do you need our guidance?"
    
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="new_epic_create")],
        [InlineKeyboardButton("No", callback_data="new_channel_forward")],
        [InlineKeyboardButton("⬅️ Back", callback_data="new_q3_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_epic_create(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player - Epic Games Create"""
    query = update.callback_query
    await query.answer()
    
    text = "Create your Epic Games profile here:\nepicgames.com"
    
    keyboard = [
        [InlineKeyboardButton("Next Question", callback_data="new_q5_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="new_q4_no")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q5_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q5 - Yes -> Q6"""
    # Store the question and answer
    context.user_data['new_player_qa'].append(("5. Did you create a shortcut of the cloud gaming to play it like an installed app directly from your Homescreen?", "A Yes"))
    
    query = update.callback_query
    await query.answer()
    
    text = "6 Have you launched the game?"
    
    keyboard = [
        [InlineKeyboardButton("A Yes", callback_data="new_q6_yes")],
        [InlineKeyboardButton("B No", callback_data="new_q6_no")],
        [InlineKeyboardButton("⬅️ Back", callback_data="new_q4_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q5_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q5 - No"""
    # Store the question and answer
    context.user_data['new_player_qa'].append(("5. Did you create a shortcut of the cloud gaming to play it like an installed app directly from your Homescreen?", "B No"))
    
    query = update.callback_query
    await query.answer()
    
    text = "No. You have to create a shortcut to play fortnite from your homescreen, do you want our guidance with that?"
    
    keyboard = [
        [InlineKeyboardButton("yes I want to see it in the channel", callback_data="new_channel_forward")],
        [InlineKeyboardButton("No I finally create a shortcut", callback_data="new_q6_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="new_q4_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q6_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q6 - Yes -> Q7"""
    # Store the question and answer
    context.user_data['new_player_qa'].append(("6. Have you launched the game?", "A Yes"))
    
    query = update.callback_query
    await query.answer()
    
    text = "7 Have you searched and found the reward Island?"
    
    keyboard = [
        [InlineKeyboardButton("A Yes", callback_data="new_q7_yes")],
        [InlineKeyboardButton("B No", callback_data="new_q7_no")],
        [InlineKeyboardButton("⬅️ Back", callback_data="new_q5_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q6_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q6 - No"""
    # Store the question and answer
    context.user_data['new_player_qa'].append(("6. Have you launched the game?", "B No"))
    
    query = update.callback_query
    await query.answer()
    
    text = "No you have to launch the game, do you need our guidance?"
    
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="new_launch_game")],
        [InlineKeyboardButton("No", callback_data="new_channel_forward")],
        [InlineKeyboardButton("⬅️ Back", callback_data="new_q5_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_launch_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player - Launch Game"""
    query = update.callback_query
    await query.answer()
    
    text = "Launch the game here:\nhttps://www.xbox.com/fr-FR/play/games/fortnite/BT5P2X999VH2"
    
    keyboard = [
        [InlineKeyboardButton("Next Question", callback_data="new_q7_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="new_q6_no")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q7_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q7 - Yes -> Q8"""
    # Store the question and answer
    context.user_data['new_player_qa'].append(("7. Have you searched and found the reward Island?", "A Yes"))
    
    query = update.callback_query
    await query.answer()
    
    text = "8 Did you follow the full setup to be able to play with friends and earn a lot together without any worries?"
    
    keyboard = [
        [InlineKeyboardButton("A Yes, I'm ready for the next step", callback_data="new_q8_yes")],
        [InlineKeyboardButton("B No", callback_data="new_q8_no")],
        [InlineKeyboardButton("⬅️ Back", callback_data="new_q6_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q7_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q7 - No"""
    # Store the question and answer
    context.user_data['new_player_qa'].append(("7. Have you searched and found the reward Island?", "B No"))
    
    query = update.callback_query
    await query.answer()
    
    text = "No, you have to search the reward Island in the search bar and just choose it, do you want our guidance for that?"
    
    keyboard = [
        [InlineKeyboardButton("Yes I want the best codes to play", callback_data="new_q1_codes")],
        [InlineKeyboardButton("No, I already choosed one code", callback_data="new_q8_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="new_q6_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q1_codes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player - Show codes"""
    query = update.callback_query
    await query.answer()
    
    text = "Just copy one of them and enter it on the search bar\n\n[CODES WILL BE DISPLAYED HERE]"
    
    keyboard = [
        [InlineKeyboardButton("Next Question", callback_data="new_q8_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="new_q7_no")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q8_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q8 - Yes -> Q9"""
    # Store the question and answer
    context.user_data['new_player_qa'].append(("8. Did you follow the full setup to be able to play with friends and earn a lot together without any worries?", "A Yes, I'm ready for the next step"))
    
    query = update.callback_query
    await query.answer()
    
    text = "9 Will you start the game and play 130 hours for free this week?"
    
    keyboard = [
        [InlineKeyboardButton("A Yes", callback_data="new_q9_yes")],
        [InlineKeyboardButton("B No", callback_data="new_q9_no")],
        [InlineKeyboardButton("⬅️ Back", callback_data="new_q7_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q8_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q8 - No"""
    # Store the question and answer
    context.user_data['new_player_qa'].append(("8. Did you follow the full setup to be able to play with friends and earn a lot together without any worries?", "B No"))
    
    query = update.callback_query
    await query.answer()
    
    text = "No, you have to follow the exact setup, do you need our guidance?"
    
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="new_channel_forward")],
        [InlineKeyboardButton("No I finally fix everything", callback_data="new_q9_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="new_q7_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q9_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q9 - Yes -> Q10"""
    # Store the question and answer
    context.user_data['new_player_qa'].append(("9. Will you start the game and play 130 hours for free this week?", "A Yes"))
    
    query = update.callback_query
    await query.answer()
    
    text = "10 With your new account, will you click on the like button every single time before your 1 hour play session ended during your 130 hours of play this week?"
    
    keyboard = [
        [InlineKeyboardButton("A Yes", callback_data="new_q10_yes")],
        [InlineKeyboardButton("B No", callback_data="new_q10_no")],
        [InlineKeyboardButton("⬅️ Back", callback_data="new_q8_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q9_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q9 - No"""
    # Store the question and answer
    context.user_data['new_player_qa'].append(("9. Will you start the game and play 130 hours for free this week?", "B No"))
    
    query = update.callback_query
    await query.answer()
    
    text = "No, you have to start the game and play every single day for free before aiming for the reward, are you able to play at least 130 hours a week?"
    
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="new_q10_yes")],
        [InlineKeyboardButton("No", callback_data="new_channel_forward")],
        [InlineKeyboardButton("⬅️ Back", callback_data="new_q8_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q10_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q10 - Yes -> Q11"""
    # Store the question and answer
    context.user_data['new_player_qa'].append(("10. With your new account, will you click on the like button every single time before your 1 hour play session ended during your 130 hours of play this week?", "A Yes"))
    
    query = update.callback_query
    await query.answer()
    
    text = "11 Will you save the reward Island to your favorites?"
    
    keyboard = [
        [InlineKeyboardButton("A Yes", callback_data="new_q11_yes")],
        [InlineKeyboardButton("B No", callback_data="new_q11_no")],
        [InlineKeyboardButton("⬅️ Back", callback_data="new_q9_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q10_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q10 - No"""
    # Store the question and answer
    context.user_data['new_player_qa'].append(("10. With your new account, will you click on the like button every single time before your 1 hour play session ended during your 130 hours of play this week?", "B No"))
    
    query = update.callback_query
    await query.answer()
    
    text = "No, You have to click on the like button every single time before your 1 hour play session ended during your 130 hours a week, do you want our guidance on that?"
    
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="new_channel_forward")],
        [InlineKeyboardButton("No, I will play and let you know", callback_data="new_q11_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="new_q9_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q11_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q11 - Yes -> Q12"""
    # Store the question and answer
    context.user_data['new_player_qa'].append(("11. Will you save the reward Island to your favorites?", "A Yes"))
    
    query = update.callback_query
    await query.answer()
    
    text = "12 Were you introduced to this game by an influencer?"
    
    keyboard = [
        [InlineKeyboardButton("A Yes", callback_data="new_influencer_yes")],
        [InlineKeyboardButton("B No", callback_data="new_channel_forward")],
        [InlineKeyboardButton("⬅️ Back", callback_data="new_q10_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q11_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q11 - No"""
    # Store the question and answer
    context.user_data['new_player_qa'].append(("11. Will you save the reward Island to your favorites?", "B No"))
    
    query = update.callback_query
    await query.answer()
    
    text = "No, you have to save the reward Island to your favorites and play, do you want our guidance on that?"
    
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="new_channel_forward")],
        [InlineKeyboardButton("No, I have proof I saved it", callback_data="new_q11_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="new_q10_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_influencer_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player - Influencer Yes"""
    # Store the question and answer
    context.user_data['new_player_qa'].append(("12. Were you introduced to this game by an influencer?", "A Yes"))
    
    query = update.callback_query
    await query.answer()
    
    text = "Provide the name please: [USER WOULD TYPE THE NAME]"
    
    keyboard = [
        [InlineKeyboardButton("Completed", callback_data="new_ask_username")],
        [InlineKeyboardButton("⬅️ Back", callback_data="new_q11_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_ask_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player - Ask for username after completing questions"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store that this is from new player flow
    context.user_data['flow_type'] = 'new_player'
    
    await query.edit_message_text(text=s['username_prompt'], parse_mode='Markdown')
    return USERNAME_COLLECTION

async def new_channel_forward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Forward to channel from new player flow"""
    query = update.callback_query
    await query.answer()
    
    text = f"Please check our channel for guidance: {HELPFUL_CHANNEL_LINK}"
    
    keyboard = [
        [InlineKeyboardButton("⬅️ Back to New Player", callback_data="new_player_start")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

# --- SUPPORT FLOW (UPDATED) ---

async def support_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Flow - Start"""
    query = update.callback_query
    await query.answer()
    
    text = (
        "Support:\n\n"
        "In order to get in touch with us, you need to answer these questions so we can determine which stage of the process you're at. "
        "If everything has been done correctly, you'll be able to claim your reward 💰💰\n\n"
        "1 Did you use a VPN?"
    )
    
    keyboard = [
        [InlineKeyboardButton("A If yes", callback_data="support_q1_yes")],
        [InlineKeyboardButton("B If no", callback_data="support_q1_no")],
        [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_q1_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Q1 - Yes -> Q2"""
    query = update.callback_query
    await query.answer()
    
    text = "2 - Did you already create a cloud gaming profile?"
    
    keyboard = [
        [InlineKeyboardButton("A if yes", callback_data="support_q2_yes")],
        [InlineKeyboardButton("B if no", callback_data="support_q2_no")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_start")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_q1_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Q1 - No -> Ask if they finally used VPN"""
    query = update.callback_query
    await query.answer()
    
    text = "Please download and use a VPN in USA before going any further to create all your authentic profiles but to play you don't use it.\n\nDid you finally use a VPN?"
    
    keyboard = [
        [InlineKeyboardButton("If yes", callback_data="support_q2_yes")],
        [InlineKeyboardButton("if no", callback_data="support_channel_only")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_start")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_q2_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Q2 - Yes -> Q3"""
    query = update.callback_query
    await query.answer()
    
    text = "3 - Did you receive the code from epic games to activate your cloud gaming account?"
    
    keyboard = [
        [InlineKeyboardButton("A Yes I received the code", callback_data="support_q3_yes")],
        [InlineKeyboardButton("B No", callback_data="support_q3_no")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_q1_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_q2_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Q2 - No -> Ask if they want assistance"""
    query = update.callback_query
    await query.answer()
    
    text = "Please create a cloud gaming profile. Do you want our assistance?"
    
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="support_cloud_gaming_link")],
        [InlineKeyboardButton("No I already have one", callback_data="support_q3_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_q1_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_cloud_gaming_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support - Cloud Gaming Link -> Q3"""
    query = update.callback_query
    await query.answer()
    
    text = "Here's the link to create your cloud gaming profile:\nhttps://www.xbox.com/fr-FR/play/games/fortnite/BT5P2X999VH2"
    
    keyboard = [
        [InlineKeyboardButton("Next Question", callback_data="support_q3_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_q2_no")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_q3_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Q3 - Yes -> Q4"""
    query = update.callback_query
    await query.answer()
    
    text = "4 Did you create your epic games profile?"
    
    keyboard = [
        [InlineKeyboardButton("A Yes", callback_data="support_q4_yes")],
        [InlineKeyboardButton("B No", callback_data="support_q4_no")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_q2_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_q3_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Q3 - No -> Ask if they want guidance"""
    query = update.callback_query
    await query.answer()
    
    text = "Please you have to receive the code, do you want our guidance to help you with that?"
    
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="support_epic_activate")],
        [InlineKeyboardButton("No", callback_data="support_channel_only")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_q2_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_epic_activate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support - Epic Games Activate -> Q4"""
    query = update.callback_query
    await query.answer()
    
    text = "Here's the activation link:\nhttp://epicgames.com/activate"
    
    keyboard = [
        [InlineKeyboardButton("Next Question", callback_data="support_q4_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_q3_no")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_q4_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Q4 - Yes -> Q5"""
    query = update.callback_query
    await query.answer()
    
    text = "5 Did you create a shortcut of the cloud gaming to play it like an installed app directly from your Homescreen?"
    
    keyboard = [
        [InlineKeyboardButton("A Yes", callback_data="support_q5_yes")],
        [InlineKeyboardButton("B No", callback_data="support_q5_no")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_q3_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_q4_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Q4 - No -> Ask if they want guidance"""
    query = update.callback_query
    await query.answer()
    
    text = "No please you have to create your epic games profile, do you want our guidance?"
    
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="support_epic_create")],
        [InlineKeyboardButton("No", callback_data="support_channel_only")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_q3_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_epic_create(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support - Epic Games Create -> Q5"""
    query = update.callback_query
    await query.answer()
    
    text = "Create your Epic Games profile here:\nepicgames.com"
    
    keyboard = [
        [InlineKeyboardButton("Next Question", callback_data="support_q5_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_q4_no")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_q5_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Q5 - Yes -> Q6"""
    query = update.callback_query
    await query.answer()
    
    text = "6 Have you launched the game?"
    
    keyboard = [
        [InlineKeyboardButton("A Yes", callback_data="support_q6_yes")],
        [InlineKeyboardButton("B No", callback_data="support_q6_no")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_q4_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_q5_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Q5 - No -> Ask if they want guidance"""
    query = update.callback_query
    await query.answer()
    
    text = "No. You have to create a shortcut to play fortnite from your homescreen, do you want our guidance with that?"
    
    keyboard = [
        [InlineKeyboardButton("yes I want to see it in the channel", callback_data="support_channel_only")],
        [InlineKeyboardButton("No I finally create a shortcut", callback_data="support_q6_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_q4_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_q6_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Q6 - Yes -> Q7"""
    query = update.callback_query
    await query.answer()
    
    text = "7 Have you searched and found the reward Island?"
    
    keyboard = [
        [InlineKeyboardButton("A Yes", callback_data="support_q7_yes")],
        [InlineKeyboardButton("B No", callback_data="support_q7_no")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_q5_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_q6_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Q6 - No -> Ask if they need guidance"""
    query = update.callback_query
    await query.answer()
    
    text = "No you have to launch the game, do you need our guidance?"
    
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="support_launch_game")],
        [InlineKeyboardButton("No", callback_data="support_channel_only")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_q5_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_launch_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support - Launch Game -> Q7"""
    query = update.callback_query
    await query.answer()
    
    text = "Launch the game here:\nhttps://www.xbox.com/fr-FR/play/games/fortnite/BT5P2X999VH2"
    
    keyboard = [
        [InlineKeyboardButton("Next Question", callback_data="support_q7_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_q6_no")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_q7_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Q7 - Yes -> Q8"""
    query = update.callback_query
    await query.answer()
    
    text = "8 Did you follow the full setup to be able to play with friends and earn a lot together without any worries?"
    
    keyboard = [
        [InlineKeyboardButton("A Yes, I'm ready for the next step", callback_data="support_q8_yes")],
        [InlineKeyboardButton("B No", callback_data="support_q8_no")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_q6_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_q7_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Q7 - No -> Ask if they want guidance"""
    query = update.callback_query
    await query.answer()
    
    text = "No, you have to search the reward Island in the search bar and just choose it, do you want our guidance for that?"
    
    keyboard = [
        [InlineKeyboardButton("Yes I want the best codes to play", callback_data="support_show_codes")],
        [InlineKeyboardButton("No, I already choosed one code", callback_data="support_q8_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_q6_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_show_codes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support - Show codes -> Q8"""
    query = update.callback_query
    await query.answer()
    
    text = "Just copy one of them and enter it on the search bar\n\n[CODES WILL BE DISPLAYED HERE]"
    
    keyboard = [
        [InlineKeyboardButton("Next Question", callback_data="support_q8_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_q7_no")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_q8_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Q8 - Yes -> Q9"""
    query = update.callback_query
    await query.answer()
    
    text = "9 Did you start the game and play 130 hours for free this week?"
    
    keyboard = [
        [InlineKeyboardButton("A Yes", callback_data="support_q9_yes")],
        [InlineKeyboardButton("B No", callback_data="support_q9_no")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_q7_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_q8_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Q8 - No -> Ask if they need guidance"""
    query = update.callback_query
    await query.answer()
    
    text = "No, you have to follow the exact setup, do you need our guidance?"
    
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="support_channel_only")],
        [InlineKeyboardButton("No I finally fix everything", callback_data="support_q9_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_q7_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_q9_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Q9 - Yes -> Q10"""
    query = update.callback_query
    await query.answer()
    
    text = "10 Did you click on the like button every single time before your 1 hour play session ended during your 130 hours of play this week?"
    
    keyboard = [
        [InlineKeyboardButton("A Yes", callback_data="support_q10_yes")],
        [InlineKeyboardButton("B No", callback_data="support_q10_no")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_q8_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_q9_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Q9 - No -> Ask if they can play 130 hours"""
    query = update.callback_query
    await query.answer()
    
    text = "No, you have to start the game and play every single day for free before aiming for the reward, are you able to play at least 130 hours a week?"
    
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="support_q10_yes")],
        [InlineKeyboardButton("No", callback_data="support_channel_only")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_q8_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_q10_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Q10 - Yes -> Q11"""
    query = update.callback_query
    await query.answer()
    
    text = "11 Have you saved the reward Island to your favorites?"
    
    keyboard = [
        [InlineKeyboardButton("A Yes", callback_data="support_q11_yes")],
        [InlineKeyboardButton("B No", callback_data="support_q11_no")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_q9_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_q10_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Q10 - No -> Ask if they want guidance"""
    query = update.callback_query
    await query.answer()
    
    text = "No, You have to click on the like button every single time before your 1 hour play session ended during your 130 hours a week, do you want our guidance on that?"
    
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="support_channel_only")],
        [InlineKeyboardButton("No, I have proof that I played 130 hours this week and I liked every single time", callback_data="support_q11_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_q9_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_q11_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Q11 - Yes -> Q12"""
    query = update.callback_query
    await query.answer()
    
    text = "12 Were you introduced to this game by an influencer?"
    
    keyboard = [
        [InlineKeyboardButton("A Yes", callback_data="support_influencer_yes")],
        [InlineKeyboardButton("B No", callback_data="support_expert_review")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_q10_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_q11_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Q11 - No -> Ask if they want guidance"""
    query = update.callback_query
    await query.answer()
    
    text = "No, you have to save the reward Island to your favorites and play, do you want our guidance on that?"
    
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="support_channel_only")],
        [InlineKeyboardButton("No, I have proof I saved it", callback_data="support_q11_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_q10_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_influencer_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support - Influencer Yes -> Q13"""
    query = update.callback_query
    await query.answer()
    
    text = "Provide the name please: [USER WOULD TYPE THE NAME]"
    
    keyboard = [
        [InlineKeyboardButton("Next Question", callback_data="support_q13")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_q11_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_expert_review(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support - Expert Review -> Q13"""
    query = update.callback_query
    await query.answer()
    
    text = "One of the expert will review all the screenshots of the game and you will earn"
    
    keyboard = [
        [InlineKeyboardButton("Next Question", callback_data="support_q13")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_q11_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_q13(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Q13 - Final Question"""
    query = update.callback_query
    await query.answer()
    
    text = (
        "13 Make sure you completed every single step before sending us your @, did you completed every single step and play at least 130 hours this week?"
    )
    
    keyboard = [
        [InlineKeyboardButton("A Yes, I did it and I will send you all the necessary screenshots", callback_data="support_get_username_start")],
        [InlineKeyboardButton("B No", callback_data="support_channel_only")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_influencer_yes")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_get_username_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support - Ask for username"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store that this is from support flow
    context.user_data['flow_type'] = 'support'
    
    await query.edit_message_text(text=s['support_q2'], parse_mode='Markdown')
    return USERNAME_COLLECTION

async def support_channel_only(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Forward to channel only (no back to support or main menu)"""
    query = update.callback_query
    await query.answer()
    
    text = f"Please check our channel for guidance: {HELPFUL_CHANNEL_LINK}"
    
    keyboard = [
        [InlineKeyboardButton("Join Channel", url=HELPFUL_CHANNEL_LINK)]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_channel_forward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Forward to channel from support flow"""
    query = update.callback_query
    await query.answer()
    
    text = f"Please check our channel for guidance: {HELPFUL_CHANNEL_LINK}"
    
    keyboard = [
        [InlineKeyboardButton("⬅️ Back to Support", callback_data="support_start")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

# --- USERNAME COLLECTION AND SUPPORT MESSAGE SENDING ---

async def collect_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Collect username and send Q&A to support team"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    username = update.message.text
    
    if username.startswith('@') and len(username) > 2:
        logger.info(f"*** USERNAME COLLECTION from user {update.message.from_user.id}: {username} ***")
        
        # Check if SUPPORT_CHAT_ID is configured
        if not SUPPORT_CHAT_ID:
            logger.error("SUPPORT_CHAT_ID is not set in environment variables")
            await update.message.reply_text(
                "❌ Support feature is currently unavailable. Please try again later."
            )
            return await show_main_menu(update, context)
        
        try:
            # Get user information
            user = update.effective_user
            user_username = user.username if user.username else "No username"
            first_name = user.first_name if user.first_name else "No first name"
            last_name = user.last_name if user.last_name else "No last name"
            
            # Get flow type and Q&A data
            flow_type = context.user_data.get('flow_type', 'unknown')
            qa_data = []
            
            if flow_type == 'existing_player':
                qa_data = context.user_data.get('existing_player_qa', [])
                flow_title = "🏆 EXISTING PLAYER QUESTIONNAIRE"
            elif flow_type == 'new_player':
                qa_data = context.user_data.get('new_player_qa', [])
                flow_title = "🎮 NEW PLAYER QUESTIONNAIRE"
            elif flow_type == 'support':
                qa_data = []  # Support flow doesn't store Q&A in the same way
                flow_title = "🆘 SUPPORT REQUEST"
            else:
                qa_data = []
                flow_title = "❓ UNKNOWN FLOW"
            
            # Create support message with Q&A
            support_message = (
                f"🚨 **{flow_title}** 🚨\n"
                f"👤 User: {first_name} {last_name}\n"
                f"📛 User's Telegram: @{user_username}\n"
                f"💬 Provided Username: {username}\n"
                f"🆔 User ID: `{user.id}`\n"
                f"⏰ Time: {update.message.date.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🌐 Language: {lang.upper()}\n\n"
            )
            
            # Add Q&A if available
            if qa_data:
                support_message += "**Questions & Answers:**\n"
                for i, (question, answer) in enumerate(qa_data, 1):
                    support_message += f"{i}. {question}\n   ➤ {answer}\n\n"
            else:
                support_message += "**No Q&A data collected.**\n\n"
            
            support_message += f"**Flow Type:** {flow_type.replace('_', ' ').title()}"
            
            # Send to support group
            await context.bot.send_message(
                chat_id=SUPPORT_CHAT_ID,
                text=support_message,
                parse_mode='Markdown'
            )
            
            # Confirm to user
            await update.message.reply_text(text=s['support_thanks'], reply_markup=ReplyKeyboardRemove())
            return await show_main_menu(update, context)
            
        except Exception as e:
            logger.error(f"Error sending support message to group: {e}")
            await update.message.reply_text(
                "❌ There was an error sending your information. Please try again later."
            )
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
    # Check for required environment variables
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN environment variable not set!")
        print("❌ ERROR: TELEGRAM_TOKEN environment variable is required!")
        print("💡 Please set TELEGRAM_TOKEN in your Render environment variables")
        return

    if not SUPPORT_CHAT_ID:
        print("⚠️  WARNING: SUPPORT_CHAT_ID environment variable not set.")
        print("💡 Support feature will not work until you set SUPPORT_CHAT_ID in Render")

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_LANG: [
                CallbackQueryHandler(set_language, pattern="^(en|fr)$")
            ],
            MAIN_MENU: [
                CallbackQueryHandler(new_player_start, pattern="^new_player_start$"),
                CallbackQueryHandler(existing_player_start, pattern="^existing_player_link$"),
                CallbackQueryHandler(show_helpful_channel, pattern="^helpful_channel$"),
                CallbackQueryHandler(support_start, pattern="^contact_support$"), 
                CallbackQueryHandler(start, pattern="^change_language$"), 
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
            EXISTING_PLAYER_FLOW: [
                CallbackQueryHandler(existing_q1_yes, pattern="^existing_q1_yes$"),
                CallbackQueryHandler(existing_q1_no, pattern="^existing_q1_no$"),
                CallbackQueryHandler(existing_q1_codes, pattern="^existing_q1_codes$"),
                CallbackQueryHandler(existing_q2_yes, pattern="^existing_q2_yes$"),
                CallbackQueryHandler(existing_q2_no, pattern="^existing_q2_no$"),
                CallbackQueryHandler(existing_q3_yes, pattern="^existing_q3_yes$"),
                CallbackQueryHandler(existing_q3_no, pattern="^existing_q3_no$"),
                CallbackQueryHandler(existing_q4_yes, pattern="^existing_q4_yes$"),
                CallbackQueryHandler(existing_q4_no, pattern="^existing_q4_no$"),
                CallbackQueryHandler(existing_q5_yes, pattern="^existing_q5_yes$"),
                CallbackQueryHandler(existing_q5_no, pattern="^existing_q5_no$"),
                CallbackQueryHandler(existing_influencer_yes, pattern="^existing_influencer_yes$"),
                CallbackQueryHandler(existing_ask_username, pattern="^existing_ask_username$"),
                CallbackQueryHandler(existing_channel_forward, pattern="^existing_channel_forward$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
            NEW_PLAYER_FLOW: [
                CallbackQueryHandler(new_q1_yes, pattern="^new_q1_yes$"),
                CallbackQueryHandler(new_q1_no, pattern="^new_q1_no$"),
                CallbackQueryHandler(new_q2_yes, pattern="^new_q2_yes$"),
                CallbackQueryHandler(new_q2_no, pattern="^new_q2_no$"),
                CallbackQueryHandler(new_cloud_gaming_link, pattern="^new_cloud_gaming_link$"),
                CallbackQueryHandler(new_q3_yes, pattern="^new_q3_yes$"),
                CallbackQueryHandler(new_q3_no, pattern="^new_q3_no$"),
                CallbackQueryHandler(new_epic_activate, pattern="^new_epic_activate$"),
                CallbackQueryHandler(new_q4_yes, pattern="^new_q4_yes$"),
                CallbackQueryHandler(new_q4_no, pattern="^new_q4_no$"),
                CallbackQueryHandler(new_epic_create, pattern="^new_epic_create$"),
                CallbackQueryHandler(new_q5_yes, pattern="^new_q5_yes$"),
                CallbackQueryHandler(new_q5_no, pattern="^new_q5_no$"),
                CallbackQueryHandler(new_q6_yes, pattern="^new_q6_yes$"),
                CallbackQueryHandler(new_q6_no, pattern="^new_q6_no$"),
                CallbackQueryHandler(new_launch_game, pattern="^new_launch_game$"),
                CallbackQueryHandler(new_q7_yes, pattern="^new_q7_yes$"),
                CallbackQueryHandler(new_q7_no, pattern="^new_q7_no$"),
                CallbackQueryHandler(new_q1_codes, pattern="^new_q1_codes$"),
                CallbackQueryHandler(new_q8_yes, pattern="^new_q8_yes$"),
                CallbackQueryHandler(new_q8_no, pattern="^new_q8_no$"),
                CallbackQueryHandler(new_q9_yes, pattern="^new_q9_yes$"),
                CallbackQueryHandler(new_q9_no, pattern="^new_q9_no$"),
                CallbackQueryHandler(new_q10_yes, pattern="^new_q10_yes$"),
                CallbackQueryHandler(new_q10_no, pattern="^new_q10_no$"),
                CallbackQueryHandler(new_q11_yes, pattern="^new_q11_yes$"),
                CallbackQueryHandler(new_q11_no, pattern="^new_q11_no$"),
                CallbackQueryHandler(new_influencer_yes, pattern="^new_influencer_yes$"),
                CallbackQueryHandler(new_ask_username, pattern="^new_ask_username$"),
                CallbackQueryHandler(new_channel_forward, pattern="^new_channel_forward$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
            SUPPORT_FLOW: [
                CallbackQueryHandler(support_q1_yes, pattern="^support_q1_yes$"),
                CallbackQueryHandler(support_q1_no, pattern="^support_q1_no$"),
                CallbackQueryHandler(support_q2_yes, pattern="^support_q2_yes$"),
                CallbackQueryHandler(support_q2_no, pattern="^support_q2_no$"),
                CallbackQueryHandler(support_cloud_gaming_link, pattern="^support_cloud_gaming_link$"),
                CallbackQueryHandler(support_q3_yes, pattern="^support_q3_yes$"),
                CallbackQueryHandler(support_q3_no, pattern="^support_q3_no$"),
                CallbackQueryHandler(support_epic_activate, pattern="^support_epic_activate$"),
                CallbackQueryHandler(support_q4_yes, pattern="^support_q4_yes$"),
                CallbackQueryHandler(support_q4_no, pattern="^support_q4_no$"),
                CallbackQueryHandler(support_epic_create, pattern="^support_epic_create$"),
                CallbackQueryHandler(support_q5_yes, pattern="^support_q5_yes$"),
                CallbackQueryHandler(support_q5_no, pattern="^support_q5_no$"),
                CallbackQueryHandler(support_q6_yes, pattern="^support_q6_yes$"),
                CallbackQueryHandler(support_q6_no, pattern="^support_q6_no$"),
                CallbackQueryHandler(support_launch_game, pattern="^support_launch_game$"),
                CallbackQueryHandler(support_q7_yes, pattern="^support_q7_yes$"),
                CallbackQueryHandler(support_q7_no, pattern="^support_q7_no$"),
                CallbackQueryHandler(support_show_codes, pattern="^support_show_codes$"),
                CallbackQueryHandler(support_q8_yes, pattern="^support_q8_yes$"),
                CallbackQueryHandler(support_q8_no, pattern="^support_q8_no$"),
                CallbackQueryHandler(support_q9_yes, pattern="^support_q9_yes$"),
                CallbackQueryHandler(support_q9_no, pattern="^support_q9_no$"),
                CallbackQueryHandler(support_q10_yes, pattern="^support_q10_yes$"),
                CallbackQueryHandler(support_q10_no, pattern="^support_q10_no$"),
                CallbackQueryHandler(support_q11_yes, pattern="^support_q11_yes$"),
                CallbackQueryHandler(support_q11_no, pattern="^support_q11_no$"),
                CallbackQueryHandler(support_influencer_yes, pattern="^support_influencer_yes$"),
                CallbackQueryHandler(support_expert_review, pattern="^support_expert_review$"),
                CallbackQueryHandler(support_q13, pattern="^support_q13$"),
                CallbackQueryHandler(support_get_username_start, pattern="^support_get_username_start$"),
                CallbackQueryHandler(support_channel_only, pattern="^support_channel_only$"),
                CallbackQueryHandler(support_channel_forward, pattern="^support_channel_forward$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
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
    )

    application.add_handler(conv_handler)

    logger.info("Bot is running...")
    print("🤖 Bot is starting...")
    print(f"✅ TELEGRAM_TOKEN: {'Set' if TELEGRAM_TOKEN else 'Not Set'}")
    print(f"✅ SUPPORT_CHAT_ID: {'Set' if SUPPORT_CHAT_ID else 'Not Set'}")
    if SUPPORT_CHAT_ID:
        print(f"📋 SUPPORT_CHAT_ID Value: {SUPPORT_CHAT_ID}")
    print("🚀 Bot is running...")
    
    application.run_polling()

if __name__ == "__main__":
    main()

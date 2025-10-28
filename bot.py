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
# SUPPORT_USERNAME is no longer needed
HELPFUL_CHANNEL_LINK = "https://t.me/rejoinsnousetgagne"
# !!!!!!!!!!!!!!!!!!!!!


# --- LANGUAGE STRINGS ---
STRINGS = {
    'en': {
        # --- NEW DISCLAIMER ---
        'disclaimer': (
            "**Disclaimer:** This bot is an unofficial guide and is not affiliated with "
            "Epic Games or Fortnite. We will *never* ask for your password."
        ),
        'lang_prompt': "Please select your language:",
        # --- WELCOME MESSAGE UPDATED (AD FRIENDLY) ---
        'welcome': (
            "Welcome! You're diving into an immersive gaming adventure. "
            "This bot will help you set up your account, join the game, and start playing."
        ),
        # --- END OF UPDATE ---
        'new_player_btn': "New player",
        'existing_player_btn': "Existing player",
        'helpful_channel_btn': "Full guide in channel",
        'support_btn': "Support",
        'lang_btn': "🌐 Change Language",
        'helpful_channel_text': "Join our helpful Telegram channel for the full guide, news, and community chat!",
        'join_channel_btn': "Join Channel Now",
        'existing_player_text': (
            "✅ Great! Here is the direct link to the playground:\n\n"
            f"{YOUR_PLAYGROUND_LINK}\n\n"
            "**Cloud Gaming Reminder:**\n"
            "Your session lasts for 1 hour. After that, you will need to relaunch the game "
            "and use this link again."
        ),
        'back_btn': "⬅️ Back to Main Menu",
        'support_q1': "Have you already read the 'New player' guide and the 'Full guide in channel'?",
        'yes_btn': "Yes, I still have a question",
        'no_btn': "No, I will check them now",
        'support_q1_no': "Please review those guides first. They answer most questions! 🙏\n\nReturning you to the main menu.",
        # --- SUPPORT Q2 UPDATED (AD FRIENDLY) ---
        'support_q2': (
            "Okay. By providing your @username, you consent to our support team "
            "contacting you directly on Telegram. We will *only* use this to help with your question.\n\n"
            "Please type your @username (like @myusername) to proceed.\n\n"
            "Type /cancel to go back."
        ),
        # --- END OF UPDATE ---
        'support_thanks': "Thank you! Your @username has been noted. We will get in touch with you as soon as possible.\n\nReturning you to the main menu.",
        'support_cancel': "Support request cancelled. Returning to main menu.",
        'invalid_username': "That doesn't look like a valid @username. Please start with '@' and try again, or type /cancel.",
        'guide1_text': (
            "**Step 1: Create Epic Games Account**\n\n"
            "This is required to play Fortnite. Go to the official site to create your account.\n\n"
            "When you're done, click 'Next Step'."
        ),
        'guide1_btn': "Go to Epic Games Site",
        'guide_next_btn': "Next Step ➡️",
        'guide2_text': (
            "**Step 2: Set Up Fortnite**\n\n"
            "After creating your Epic account, make sure Fortnite is added to your library and set up. "
            "For cloud gaming, you'll usually do this through your cloud service "
            "(like GeForce NOW, Xbox Cloud Gaming, etc.)."
        ),
        'guide3_text': (
            "**Step 3: Find My Playground**\n\n"
            "Once you are in Fortnite, go to the game search bar (Island Code) and "
            "type in this exact name:\n\n"
            f"`{YOUR_PLAYGROUND_NAME}`\n\n"
            "This will take you to my playground. Add it to your favorites!"
        ),
        'guide4_text': (
            "**Final Info: Cloud Gaming Limit**\n\n"
            "Because you are playing on the cloud, your session will last for **1 hour**. "
            "The game will close, and you will have to launch it again to keep playing.\n\n"
            "Next time, you can use the 'Existing Player' button on this bot to get the link faster!"
        ),
    },
    'fr': {
        # --- NEW DISCLAIMER ---
        'disclaimer': (
            "**Avertissement :** Ce bot est un guide non officiel et n'est pas affilié à "
            "Epic Games ou Fortnite. Nous ne vous demanderons *jamais* votre mot de passe."
        ),
        'lang_prompt': "Veuillez sélectionner votre langue :",
        # --- WELCOME MESSAGE UPDATED (AD FRIENDLY) ---
        'welcome': (
            "Bienvenue ! Tu plonges dans une aventure de jeu immersive. "
            "Ce bot t'aidera à configurer ton compte, à rejoindre la partie et à commencer à jouer."
        ),
        # --- END OF UPDATE ---
        'new_player_btn': "Nouveau joueur",
        'existing_player_btn': "Joueur existant",
        'helpful_channel_btn': "Guide complet sur le canal",
        'support_btn': "Support",
        'lang_btn': "🌐 Changer de Langue",
        'helpful_channel_text': "Rejoignez notre canal Telegram pour le guide complet, les actualités et pour discuter avec la communauté !",
        'join_channel_btn': "Rejoindre le Canal",
        'existing_player_text': (
            "✅ Parfait ! Voici le lien direct vers le terrain de jeu :\n\n"
            f"{YOUR_PLAYGROUND_LINK}\n\n"
            "**Rappel Cloud Gaming :**\n"
            "Votre session dure 1 heure. Après cela, vous devrez relancer le jeu "
            "et utiliser à nouveau ce lien."
        ),
        'back_btn': "⬅️ Retour au Menu Principal",
        'support_q1': "Avez-vous déjà lu le guide 'Nouveau joueur' et le 'Guide complet sur le canal' ?",
        'yes_btn': "Oui, j'ai encore une question",
        'no_btn': "Non, je vais les voir maintenant",
        'support_q1_no': "Veuillez d'abord consulter ces guides. Ils répondent à la plupart des questions ! 🙏\n\nRetour au menu principal.",
        # --- SUPPORT Q2 UPDATED (AD FRIENDLY) ---
        'support_q2': (
            "D'accord. En fournissant votre @nomdutilisateur, vous acceptez que notre équipe d'assistance "
            "vous contacte directement sur Telegram. Nous l'utiliserons *uniquement* pour répondre à votre question.\n\n"
            "Veuillez taper votre @nomdutilisateur (comme @monpseudo) pour continuer.\n\n"
            "Tapez /cancel pour revenir."
        ),
        # --- END OF UPDATE ---
        'support_thanks': "Merci ! Votre @nomdutilisateur a été noté. Nous vous contacterons dès que possible.\n\nRetour au menu principal.",
        'support_cancel': "Demande d'aide annulée. Retour au menu principal.",
        'invalid_username': "Cela ne ressemble pas à un @nomdutilisateur valide. Veuillez commencer par '@' et réessayer, ou tapez /cancel.",
        'guide1_text': (
            "**Étape 1 : Créer un compte Epic Games**\n\n"
            "Ceci est requis pour jouer à Fortnite. Allez sur le site officiel pour créer votre compte.\n\n"
            "Lorsque vous avez terminé, cliquez sur 'Étape suivante'."
        ),
        'guide1_btn': "Aller sur le site d'Epic Games",
        'guide_next_btn': "Étape Suivante ➡️",
        'guide2_text': (
            "**Étape 2 : Configurer Fortnite**\n\n"
            "Après avoir créé votre compte Epic, assurez-vous que Fortnite est ajouté à votre bibliothèque et configuré. "
            "Pour le cloud gaming, vous ferez généralement cela via votre service cloud "
            "(comme GeForce NOW, Xbox Cloud Gaming, etc.)."
        ),
        'guide3_text': (
            "**Étape 3 : Trouver mon terrain de jeu**\n\n"
            "Une fois dans Fortnite, allez dans la barre de recherche de jeu (Code d'île) et "
            "tapez ce nom exact :\n\n"
            f"`{YOUR_PLAYGROUND_NAME}`\n\n"
            "Cela vous amènera à mon terrain de jeu. Ajoutez-le à vos favoris !"
        ),
        'guide4_text': (
            "**Info Finale : Limite du Cloud Gaming**\n\n"
            "Parce que vous jouez sur le cloud, votre session durera **1 heure**. "
            "Le jeu se fermera, et vous devrez le relancer pour continuer à jouer.\n\n"
            "La prochaine fois, vous pourrez utiliser le bouton 'Joueur Existant' de ce bot pour obtenir le lien plus rapidement !"
        ),
    }
}


# Define states
SELECT_LANG, MAIN_MENU, GUIDE_STEPS, SUPPORT_Q1, SUPPORT_Q2 = range(5)

# --- Helper Functions ---
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str = None):
    """Helper function to show the main menu in the user's language."""
    lang = context.user_data.get('lang', 'en') # Default to English
    s = STRINGS[lang]
    
    keyboard = [
        [InlineKeyboardButton(s['new_player_btn'], callback_data="new_player_start")],
        [InlineKeyboardButton(s['existing_player_btn'], callback_data="existing_player_link")],
        [InlineKeyboardButton(s['helpful_channel_btn'], callback_data="helpful_channel")],
        [InlineKeyboardButton(s['support_btn'], callback_data="contact_support")],
    ]
    
    query = update.callback_query
    text_to_show = message or s['welcome'] # Show a custom message or the default welcome
    
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
        # This happens for /start or after text input
        await update.message.reply_text(
            text=text_to_show,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    return MAIN_MENU

# --- Conversation Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point: Shows disclaimer and asks for language."""
    
    # --- DISCLAIMER ADDED TO START ---
    text = (
        f"{STRINGS['en']['disclaimer']}\n\n"
        f"{STRINGS['fr']['disclaimer']}\n\n"
        "------\n\n"
        f"{STRINGS['en']['lang_prompt']}\n\n"
        f"{STRINGS['fr']['lang_prompt']}"
    )
    # --- END OF UPDATE ---

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

async def show_existing_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Shows the direct playground link and cloud gaming info."""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()

    keyboard = [[InlineKeyboardButton(s['back_btn'], callback_data="back_to_main")]]
    await query.edit_message_text(
        text=s['existing_player_text'],
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True,
        parse_mode='Markdown'
    )
    
    return MAIN_MENU 

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

# --- SUPPORT FLOW FUNCTIONS ---

async def support_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Step 1: Ask the FAQ question."""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton(s['yes_btn'], callback_data="support_yes")],
        [InlineKeyboardButton(s['no_btn'], callback_data="support_no")],
    ]
    
    await query.edit_message_text(text=s['support_q1'], reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_Q1

async def support_q1_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User clicked 'No', send them back to main menu."""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    return await show_main_menu(update, context, message=s['support_q1_no'])

async def support_ask_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User clicked 'Yes', ask for their @username."""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(text=s['support_q2'], parse_mode='Markdown')
    
    return SUPPORT_Q2 

async def support_get_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User sent their @username as a text message - forward to support group."""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    username = update.message.text
    
    if username.startswith('@') and len(username) > 2:
        logger.info(f"*** SUPPORT REQUEST from user {update.message.from_user.id}: {username} ***")
        
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
            
            # Create support message
            support_message = (
                "🚨 **Support Request** 🚨\n"
                f"👤 User: {first_name} {last_name}\n"
                f"📛 User's Username: @{user_username}\n"
                f"💬 Support Username Provided: {username}\n"
                f"🆔 User ID: `{user.id}`\n"
                f"⏰ Time: {update.message.date.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🌐 Language: {lang.upper()}"
            )
            
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
                "❌ There was an error sending your support request. Please try again later."
            )
            return await show_main_menu(update, context)
    else:
        await update.message.reply_text(text=s['invalid_username'])
        return SUPPORT_Q2 

async def cancel_support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User types /cancel during the support flow."""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    await update.message.reply_text(text=s['support_cancel'], reply_markup=ReplyKeyboardRemove())
    return await show_main_menu(update, context)

# --- END SUPPORT FLOW ---

# --- New Player Guide Steps (Unchanged) ---

async def guide_step_1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Guide Step 1: Create Epic Games Account."""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton(s['guide1_btn'], url="https://www.epicgames.com/id/register")],
        [InlineKeyboardButton(s['guide_next_btn'], callback_data="guide_step_2")],
        [InlineKeyboardButton(s['back_btn'], callback_data="back_to_main")],
    ]
    
    await query.edit_message_text(text=s['guide1_text'], reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True, parse_mode='Markdown')
    return GUIDE_STEPS

async def guide_step_2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Guide Step 2: Set up Fortnite."""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton(s['guide_next_btn'], callback_data="guide_step_3")],
        [InlineKeyboardButton(s['back_btn'], callback_data="back_to_main")],
    ]
    
    await query.edit_message_text(text=s['guide2_text'], reply_markup=InlineKeyboardMarkup(keyboard))
    return GUIDE_STEPS

async def guide_step_3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Guide Step 3: Find the Playground."""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton(s['guide_next_btn'], callback_data="guide_step_4")],
        [InlineKeyboardButton(s['back_btn'], callback_data="back_to_main")],
    ]
    
    await query.edit_message_text(text=s['guide3_text'], reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return GUIDE_STEPS

async def guide_step_4(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Guide Step 4: Cloud Gaming Info."""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton(s['back_btn'], callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(text=s['guide4_text'], reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return GUIDE_STEPS

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
                CallbackQueryHandler(guide_step_1, pattern="^new_player_start$"),
                CallbackQueryHandler(show_existing_link, pattern="^existing_player_link$"),
                CallbackQueryHandler(show_helpful_channel, pattern="^helpful_channel$"),
                CallbackQueryHandler(support_start, pattern="^contact_support$"), 
                CallbackQueryHandler(start, pattern="^change_language$"), 
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
            GUIDE_STEPS: [
                CallbackQueryHandler(guide_step_2, pattern="^guide_step_2$"),
                CallbackQueryHandler(guide_step_3, pattern="^guide_step_3$"),
                CallbackQueryHandler(guide_step_4, pattern="^guide_step_4$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
            SUPPORT_Q1: [
                CallbackQueryHandler(support_ask_username, pattern="^support_yes$"),
                CallbackQueryHandler(support_q1_no, pattern="^support_no$"),
                CommandHandler("cancel", cancel_support), 
            ],
            SUPPORT_Q2: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, support_get_username),
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

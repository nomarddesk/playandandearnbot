import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
# !!! IMPORTANT: Fill these in with your information !!!
YOUR_PLAYGROUND_NAME = "My Awesome Playground"  # The *exact name* to search for in Fortnite
YOUR_PLAYGROUND_LINK = "https://your-fortnite-playground-link.com"  # The direct link for existing players
# !!!!!!!!!!!!!!!!!!!!!

# Define states for conversation
SELECT_PATH, GUIDE_STEP = range(2)

# --- Helper Functions ---

def get_start_keyboard():
    """Returns the main menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🚀 New Player (Setup Guide)", callback_data="new_player_start")
        ],
        [
            InlineKeyboardButton("✅ Existing Player (Get Link)", callback_data="existing_player_link")
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

# --- Conversation Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sends a welcome message and the main menu."""
    welcome_text = (
        "Welcome! 👋\n\n"
        "This bot will help you get set up to play my Fortnite playground, "
        "especially for cloud gaming.\n\n"
        "Are you a new player who needs the setup guide, or an existing player "
        "who just needs the link?"
    )

    # If called from a button, edit the message. If from /start, send a new one.
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(text=welcome_text, reply_markup=get_start_keyboard())
    else:
        await update.message.reply_text(text=welcome_text, reply_markup=get_start_keyboard())
    
    return SELECT_PATH

async def show_existing_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Shows the direct playground link and cloud gaming info."""
    query = update.callback_query
    await query.answer()

    text = (
        "✅ Great! Here is the direct link to the playground:\n\n"
        f"{YOUR_PLAYGROUND_LINK}\n\n"
        "**Cloud Gaming Reminder:**\n"
        "Your session lasts for 1 hour. After that, you will need to relaunch the game "
        "and use this link again."
    )
    
    keyboard = [[InlineKeyboardButton("Back to Start", callback_data="start_over")]]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)
    
    return SELECT_PATH

# --- New Player Guide Steps ---

async def guide_step_1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Guide Step 1: Create Epic Games Account."""
    query = update.callback_query
    await query.answer()
    
    text = (
        "**Step 1: Create Epic Games Account**\n\n"
        "This is required to play Fortnite. Go to the official site to create your account.\n\n"
        "When you're done, click 'Next Step'."
    )
    
    keyboard = [
        [
            InlineKeyboardButton("Go to Epic Games Site", url="https://www.epicgames.com/id/register")
        ],
        [
            InlineKeyboardButton("Next Step ➡️", callback_data="guide_step_2")
        ],
        [
            InlineKeyboardButton("Back to Start", callback_data="start_over")
        ],
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return GUIDE_STEP

async def guide_step_2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Guide Step 2: Set up Fortnite."""
    query = update.callback_query
    await query.answer()
    
    text = (
        "**Step 2: Set Up Fortnite**\n\n"
        "After creating your Epic account, make sure Fortnite is added to your library and set up. "
        "For cloud gaming, you'll usually do this through your cloud service "
        "(like GeForce NOW, Xbox Cloud Gaming, etc.)."
    )
    
    keyboard = [
        [
            InlineKeyboardButton("Next Step ➡️", callback_data="guide_step_3")
        ],
        [
            InlineKeyboardButton("Back to Start", callback_data="start_over")
        ],
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return GUIDE_STEP

async def guide_step_3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Guide Step 3: Find the Playground."""
    query = update.callback_query
    await query.answer()
    
    text = (
        "**Step 3: Find My Playground**\n\n"
        "Once you are in Fortnite, go to the game search bar (Island Code) and "
        "type in this exact name:\n\n"
        f"`{YOUR_PLAYGROUND_NAME}`\n\n"
        "This will take you to my playground. Add it to your favorites!"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("Next Step ➡️", callback_data="guide_step_4")
        ],
        [
            InlineKeyboardButton("Back to Start", callback_data="start_over")
        ],
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return GUIDE_STEP

async def guide_step_4(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Guide Step 4: Cloud Gaming Info."""
    query = update.callback_query
    await query.answer()
    
    text = (
        "**Final Info: Cloud Gaming Limit**\n\n"
        "Because you are playing on the cloud, your session will last for **1 hour**. "
        "The game will close, and you will have to launch it again to keep playing.\n\n"
        "Next time, you can use the 'Existing Player' button on this bot to get the link faster!"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("Back to Start", callback_data="start_over")
        ]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return GUIDE_STEP


def main() -> None:
    """Run the bot."""
    # Get the token from environment variables
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        logger.error("TELEGRAM_TOKEN environment variable not set!")
        return

    # Create the Application
    application = Application.builder().token(token).build()

    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_PATH: [
                CallbackQueryHandler(guide_step_1, pattern="^new_player_start$"),
                CallbackQueryHandler(show_existing_link, pattern="^existing_player_link$"),
                CallbackQueryHandler(start, pattern="^start_over$"), # Allow "Back to Start"
            ],
            GUIDE_STEP: [
                CallbackQueryHandler(guide_step_2, pattern="^guide_step_2$"),
                CallbackQueryHandler(guide_step_3, pattern="^guide_step_3$"),
                CallbackQueryHandler(guide_step_4, pattern="^guide_step_4$"),
                CallbackQueryHandler(start, pattern="^start_over$"), # Allow "Back to Start"
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)

    # Run the bot
    logger.info("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()


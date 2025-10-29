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
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
SUPPORT_CHAT_ID = os.environ.get("SUPPORT_CHAT_ID")

print("=" * 50)
print("ENVIRONMENT VARIABLES CHECK:")
print(f"TELEGRAM_TOKEN: {'✅ SET' if TELEGRAM_TOKEN else '❌ NOT SET'}")
print(f"SUPPORT_CHAT_ID: {'✅ SET' if SUPPORT_CHAT_ID else '❌ NOT SET'}")
if SUPPORT_CHAT_ID:
    print(f"SUPPORT_CHAT_ID value: {SUPPORT_CHAT_ID}")
print("=" * 50)

# Basic configuration
YOUR_PLAYGROUND_NAME = "My Awesome Playground"
YOUR_PLAYGROUND_LINK = "https://your-fortnite-playground-link.com"
HELPFUL_CHANNEL_LINK = "https://t.me/rejoinsnousetgagne"

REWARD_ISLAND_CODES = [
    "1234-5678-9012",
    "3456-7890-1234", 
    "5678-9012-3456",
    "7890-1234-5678"
]

# --- LANGUAGE STRINGS ---
STRINGS = {
    'en': {
        'disclaimer': "**Disclaimer:** This bot is an unofficial guide and is not affiliated with Epic Games or Fortnite.",
        'lang_prompt': "Please select your language:",
        'welcome': "Welcome! Choose an option below:",
        'new_player_btn': "New player",
        'existing_player_btn': "Existing player", 
        'helpful_channel_btn': "Full guide in channel",
        'support_btn': "Support",
        'back_btn': "⬅️ Back",
        'yes_btn': "Yes",
        'no_btn': "No",
        
        # Existing player simple response
        'existing_player_text': f"✅ Direct link: {YOUR_PLAYGROUND_LINK}",
        'helpful_channel_text': f"Join our channel: {HELPFUL_CHANNEL_LINK}",
        
        # Support Flow
        'support_intro': "🔧 **Support System**\n\nAnswer these questions to get help:",
        'support_q1': "1. Have you read the new player guide and channel guide?",
        'support_q1_no': "Please check those guides first!",
        'support_q2': "2. Please provide your @username:",
        'support_thanks': "✅ Thank you! Support will contact you soon.",
        'support_cancel': "Support cancelled.",
        'invalid_username': "Please provide a valid @username",
        
        # New Player Flow
        'new_player_intro': "🎮 **New Player Setup**\n\nLet's get you started:",
        'new_player_q1': "1. Did you use a VPN?",
        'new_player_q1_no': "Please use a VPN for setup, then continue.",
        'new_player_complete': "🎉 New player setup complete! Start playing now.",
        
        # Existing Player Flow  
        'existing_player_flow_intro': "🎯 **Existing Player Check**\n\nLet's check your progress:",
        'existing_player_q1': "1. Have you found the reward Island?",
        'existing_player_complete': "✅ Existing player check complete! Keep playing!",
        
        # Common
        'forward_to_channel': f"📺 Check our channel: {HELPFUL_CHANNEL_LINK}",
    }
}

# Define states
SELECT_LANG, MAIN_MENU = range(2)

# Support Flow States
SUPPORT_Q1, SUPPORT_Q2 = range(2, 4)

# New Player Flow States  
NEW_PLAYER_Q1, NEW_PLAYER_Q2 = range(4, 6)

# Existing Player Flow States
EXISTING_PLAYER_Q1, EXISTING_PLAYER_Q2 = range(6, 8)

# --- HELPER FUNCTIONS ---
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str = None):
    """Show the main menu"""
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
        await query.edit_message_text(
            text=text_to_show,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            text=text_to_show,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    return MAIN_MENU

async def forward_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE, next_state=None):
    """Forward to channel"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(text=s['forward_to_channel'])
    
    if next_state:
        return await next_state(update, context)
    else:
        return await show_main_menu(update, context)

# --- SUPPORT FLOW ---
async def support_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start support flow"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    context.user_data['support_answers'] = {}
    
    keyboard = [
        [InlineKeyboardButton(s['yes_btn'], callback_data="support_q1_yes")],
        [InlineKeyboardButton(s['no_btn'], callback_data="support_q1_no")],
    ]
    
    await query.edit_message_text(
        text=f"{s['support_intro']}\n\n{s['support_q1']}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SUPPORT_Q1

async def support_q1_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Q1 Yes"""
    context.user_data['support_answers']['q1'] = 'yes'
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(text=s['support_q2'])
    return SUPPORT_Q2

async def support_q1_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Q1 No"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(text=s['support_q1_no'])
    return await show_main_menu(update, context)

async def support_get_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get support username"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    username = update.message.text
    
    if username.startswith('@') and len(username) > 1:
        # Send to support group
        if SUPPORT_CHAT_ID:
            try:
                user = update.effective_user
                support_message = (
                    "🚨 **Support Request**\n"
                    f"👤 User: {user.first_name} {user.last_name or ''}\n"
                    f"📛 Username: @{user.username or 'No username'}\n"
                    f"💬 Provided: {username}\n"
                    f"🆔 ID: {user.id}"
                )
                
                await context.bot.send_message(
                    chat_id=SUPPORT_CHAT_ID,
                    text=support_message,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Error sending to support: {e}")
        
        await update.message.reply_text(text=s['support_thanks'])
        return await show_main_menu(update, context)
    else:
        await update.message.reply_text(text=s['invalid_username'])
        return SUPPORT_Q2

async def cancel_support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel support"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    await update.message.reply_text(text=s['support_cancel'])
    return await show_main_menu(update, context)

# --- NEW PLAYER FLOW ---
async def new_player_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start new player flow"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    context.user_data['new_player_answers'] = {}
    
    keyboard = [
        [InlineKeyboardButton(s['yes_btn'], callback_data="new_player_q1_yes")],
        [InlineKeyboardButton(s['no_btn'], callback_data="new_player_q1_no")],
    ]
    
    await query.edit_message_text(
        text=f"{s['new_player_intro']}\n\n{s['new_player_q1']}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return NEW_PLAYER_Q1

async def new_player_q1_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q1 Yes"""
    context.user_data['new_player_answers']['q1_vpn'] = 'yes'
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    # Continue with more questions... (simplified for now)
    keyboard = [[InlineKeyboardButton(s['back_btn'], callback_data="back_to_main")]]
    await query.edit_message_text(
        text=s['new_player_complete'],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return MAIN_MENU

async def new_player_q1_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q1 No"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(text=s['new_player_q1_no'])
    return await forward_to_channel(update, context, new_player_start)

# --- EXISTING PLAYER FLOW ---
async def existing_player_flow_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start existing player flow"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    context.user_data['existing_player_answers'] = {}
    
    keyboard = [
        [InlineKeyboardButton(s['yes_btn'], callback_data="existing_player_q1_yes")],
        [InlineKeyboardButton(s['no_btn'], callback_data="existing_player_q1_no")],
    ]
    
    await query.edit_message_text(
        text=f"{s['existing_player_flow_intro']}\n\n{s['existing_player_q1']}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return EXISTING_PLAYER_Q1

async def existing_player_q1_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Q1 Yes"""
    context.user_data['existing_player_answers']['q1_island'] = 'yes'
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    # Continue with more questions... (simplified for now)
    keyboard = [[InlineKeyboardButton(s['back_btn'], callback_data="back_to_main")]]
    await query.edit_message_text(
        text=s['existing_player_complete'],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return MAIN_MENU

async def existing_player_q1_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Q1 No"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    # Show reward codes
    codes_text = "\n".join([f"• {code}" for code in REWARD_ISLAND_CODES])
    message = f"🏝️ Reward Island Codes:\n{codes_text}\n\nCopy one and search in the game!"
    
    keyboard = [[InlineKeyboardButton(s['back_btn'], callback_data="back_to_main")]]
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return MAIN_MENU

# --- BASIC HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start command"""
    text = (
        f"{STRINGS['en']['disclaimer']}\n\n"
        f"{STRINGS['en']['lang_prompt']}"
    )

    keyboard = [
        [InlineKeyboardButton("English 🇬🇧", callback_data="en")],
    ]
    
    if update.message:
        await update.message.reply_text(
            text=text, 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    return SELECT_LANG

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Set language"""
    query = update.callback_query
    await query.answer()
    
    lang = query.data
    context.user_data['lang'] = lang
    
    return await show_main_menu(update, context)

async def show_existing_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show existing player link (simple version)"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()

    keyboard = [[InlineKeyboardButton(s['back_btn'], callback_data="back_to_main")]]
    await query.edit_message_text(
        text=s['existing_player_text'],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return MAIN_MENU

async def show_helpful_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show channel link"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton(s['back_btn'], callback_data="back_to_main")]
    ]
    await query.edit_message_text(
        text=s['helpful_channel_text'],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return MAIN_MENU

def main() -> None:
    """Start the bot"""
    if not TELEGRAM_TOKEN:
        print("❌ ERROR: TELEGRAM_TOKEN not set!")
        return

    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_LANG: [
                CallbackQueryHandler(set_language, pattern="^en$")
            ],
            MAIN_MENU: [
                CallbackQueryHandler(new_player_start, pattern="^new_player_start$"),
                CallbackQueryHandler(show_existing_link, pattern="^existing_player_link$"),
                CallbackQueryHandler(show_helpful_channel, pattern="^helpful_channel$"),
                CallbackQueryHandler(support_start, pattern="^contact_support$"),
                CallbackQueryHandler(existing_player_flow_start, pattern="^existing_player_flow$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
            # Support Flow States
            SUPPORT_Q1: [
                CallbackQueryHandler(support_q1_yes, pattern="^support_q1_yes$"),
                CallbackQueryHandler(support_q1_no, pattern="^support_q1_no$"),
                CommandHandler("cancel", cancel_support),
            ],
            SUPPORT_Q2: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, support_get_username),
                CommandHandler("cancel", cancel_support),
            ],
            # New Player Flow States
            NEW_PLAYER_Q1: [
                CallbackQueryHandler(new_player_q1_yes, pattern="^new_player_q1_yes$"),
                CallbackQueryHandler(new_player_q1_no, pattern="^new_player_q1_no$"),
                CommandHandler("cancel", cancel_support),
            ],
            # Existing Player Flow States
            EXISTING_PLAYER_Q1: [
                CallbackQueryHandler(existing_player_q1_yes, pattern="^existing_player_q1_yes$"),
                CallbackQueryHandler(existing_player_q1_no, pattern="^existing_player_q1_no$"),
                CommandHandler("cancel", cancel_support),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)

    # Start the bot
    print("🤖 Bot is starting...")
    print("🚀 Bot is running and waiting for messages...")
    application.run_polling()

if __name__ == "__main__":
    main()

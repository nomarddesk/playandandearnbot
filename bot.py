import logging
import os
import json
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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

# Configuration
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
SUPPORT_CHAT_ID = os.environ.get("SUPPORT_CHAT_ID")

# Database setup
DB_FILE = "bot_data.db"

def init_database():
    """Initialize SQLite database"""
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_progress (
                user_id INTEGER PRIMARY KEY,
                current_step INTEGER DEFAULT 1,
                flow_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

init_database()

# Conversation states
MAIN_MENU, NEW_PLAYER_ONBOARDING, USERNAME_COLLECTION = range(3)

# Game codes
REWARD_CODES = [
    "6086-7221-0564",
    "2753-4695-7191",
    "9689-1352-5966", 
    "4563-6624-9460",
    "4828-9033-2281"
]

# Language strings
STRINGS = {
    'en': {
        # Main menu
        'welcome': "🌟 **Fortnite Gaming Adventure** 🌟\n\nWelcome to your ultimate gaming journey! I'll guide you through setting up your account and unlocking amazing rewards!",
        'new_player_btn': "🚀 Start Gaming Journey",
        'existing_player_btn': "⚡ Quick Status Check",
        'support_btn': "🆘 Get Help & Rewards",
        'channel_btn': "📚 Learn & Connect",
        
        # Common buttons
        'yes_btn': "✅ Yes, I did",
        'no_btn': "❌ Not yet", 
        'help_btn': "🆘 Need Help",
        'back_btn': "⬅️ Back",
        'main_menu_btn': "🏠 Main Menu",
        'next_btn': "➡️ Continue",
        'skip_btn': "⏭️ Skip",
        'show_codes_btn': "🎮 Get Codes",
        
        # New Player Flow - Completely Different Structure
        'onboarding_welcome': """🎯 **Your Gaming Journey Begins Now!**

I'll help you get set up step-by-step. Each session is 1 hour - perfect for quick gaming breaks!

Let's start with the basics:""",
        
        'step_1_title': "🔐 **Step 1: Secure Setup**",
        'step_1_question': "Did you use a USA VPN when creating your gaming profiles?",
        'step_1_help': """🌐 **VPN Setup Guide**

• VPN is ONLY needed for profile creation (not playing)
• Use any USA VPN service
• This ensures proper account setup

Ready to continue?""",
        
        'step_2_title': "☁️ **Step 2: Gaming Profile**", 
        'step_2_question': "Have you created your cloud gaming profile?",
        'step_2_help': """🎮 **Profile Creation**

Let's get your gaming profile ready!
Need step-by-step guidance?""",
        'step_2_link': "Create Profile",
        
        'step_3_title': "⚡ **Step 3: Account Activation**",
        'step_3_question': "Did you activate with Epic Games using the code?",
        'step_3_help': """🔗 **Activation Required**

Activation saves your progress and unlocks rewards!
Need the activation process?""",
        'step_3_link': "Activate Now",
        
        'step_4_title': "👤 **Step 4: Profile Setup**",
        'step_4_question': "Is your Epic Games profile fully set up?",
        'step_4_help': """🎨 **Complete Your Profile**

Your profile stores progress and achievements!
Want setup assistance?""",
        'step_4_link': "Setup Profile",
        
        'step_5_title': "📱 **Step 5: Quick Access**",
        'step_5_question': "Did you add the game to your home screen?",
        'step_5_help': """🚀 **Instant Access**

Home screen shortcut = Faster gaming!
Need the quick guide?""",
        
        'step_6_title': "🎮 **Step 6: Launch Game**",
        'step_6_question': "Have you successfully launched the game?",
        'step_6_help': """💫 **Let's Play!**

Ready to start your gaming adventure?
Need launching help?""",
        'step_6_link': "Launch Game",
        
        'step_7_title': "🏝️ **Step 7: Treasure Island**",
        'step_7_question': "Have you discovered the Reward Island?",
        'step_7_help': """💰 **Unlock Rewards!**

The Reward Island is where you earn amazing prizes!
Want the access codes?""",
        'step_7_codes': "🔑 **Your Treasure Codes:**\n{}\n\nCopy any code → Game search bar → Start earning! 🎉",
        
        'step_8_title': "⚙️ **Step 8: Complete Setup**",
        'step_8_question': "Is your full gaming setup complete?",
        'step_8_help': """🎯 **Optimize Your Setup**

Complete setup = Better gaming with friends + Maximum rewards!
Need the complete guide?""",
        
        'step_9_title': "⏰ **Step 9: Gaming Schedule**",
        'step_9_question': "Can you commit to 130 hours of gaming this week?",
        'step_9_help': """📅 **Weekly Gaming Plan**

130 hours weekly = Optimal rewards!
This includes background play time.

Can you achieve this?""",
        
        'step_10_title': "👍 **Step 10: Engagement**",
        'step_10_question': "Will you click 'Like' before each session ends?",
        'step_10_help': """📊 **Track Your Progress**

The 'Like' button helps us track your gaming sessions for rewards.

Need timing tips?""",
        
        'step_11_title': "⭐ **Step 11: Favorites**",
        'step_11_question': "Did you save Reward Island to favorites?",
        'step_11_help': """💫 **Quick Return**

Favorites = Instant access to earning opportunities!
Want the setup guide?""",
        
        'step_12_title': "🤝 **Step 12: Community**", 
        'step_12_question': "Did someone refer you to our gaming community?",
        'step_12_prompt': "Awesome! Please share their name so we can thank them:",
        'step_12_skip': "No problem! Welcome to our amazing gaming community! 🎉",
        
        'onboarding_complete': """🎊 **Congratulations! Setup Complete!**

You're now ready to:
• Play and earn amazing rewards 🎁
• Join our gaming community 👥  
• Maximize your gaming experience ⚡

**Next Step:** Provide your username for reward tracking!""",
        
        'username_prompt': "👤 **Final Step: Username**\n\nPlease share your Telegram username (starting with @):",
        'username_saved': "✅ Perfect! Our team will contact you soon with next steps and reward information!",
        'invalid_username': "❌ Please provide a valid username starting with @ (example: @YourUsername)",
        
        # Channel
        'channel_text': "Join our community for exclusive guides, tips, and support!",
        'join_channel_btn': "Join Community"
    }
}

# Database functions
def save_user_progress(user_id, step, flow_data):
    """Save user progress"""
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_progress 
            (user_id, current_step, flow_data, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, step, json.dumps(flow_data)))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error saving progress: {e}")
        return False

def get_user_progress(user_id):
    """Get user progress"""
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('SELECT current_step, flow_data FROM user_progress WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0], json.loads(result[1]) if result[1] else {}
        return 1, {}
    except Exception as e:
        logger.error(f"Error getting progress: {e}")
        return 1, {}

# Helper functions
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu"""
    s = STRINGS['en']
    
    keyboard = [
        [InlineKeyboardButton(s['new_player_btn'], callback_data="new_player_start")],
        [InlineKeyboardButton(s['existing_player_btn'], callback_data="existing_player_start")],
        [InlineKeyboardButton(s['support_btn'], callback_data="support_start")],
        [InlineKeyboardButton(s['channel_btn'], callback_data="channel_link")],
    ]
    
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(
            text=s['welcome'],
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            text=s['welcome'],
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    return MAIN_MENU

async def start_new_player_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the new player onboarding flow"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    s = STRINGS['en']
    
    # Initialize flow data
    context.user_data['onboarding_step'] = 1
    context.user_data['onboarding_data'] = {}
    
    # Save initial progress
    save_user_progress(user_id, 1, {})
    
    # Show first step
    return await show_onboarding_step(update, context)

async def show_onboarding_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current onboarding step"""
    step = context.user_data.get('onboarding_step', 1)
    s = STRINGS['en']
    
    step_titles = {
        1: (s['step_1_title'], s['step_1_question']),
        2: (s['step_2_title'], s['step_2_question']),
        3: (s['step_3_title'], s['step_3_question']),
        4: (s['step_4_title'], s['step_4_question']),
        5: (s['step_5_title'], s['step_5_question']),
        6: (s['step_6_title'], s['step_6_question']),
        7: (s['step_7_title'], s['step_7_question']),
        8: (s['step_8_title'], s['step_8_question']),
        9: (s['step_9_title'], s['step_9_question']),
        10: (s['step_10_title'], s['step_10_question']),
        11: (s['step_11_title'], s['step_11_question']),
        12: (s['step_12_title'], s['step_12_question'])
    }
    
    if step == 1:
        # First step - show welcome
        title, question = step_titles[step]
        text = f"{s['onboarding_welcome']}\n\n{title}\n{question}"
    else:
        title, question = step_titles[step]
        text = f"{title}\n{question}"
    
    # Create appropriate keyboard
    if step == 1:
        keyboard = [
            [InlineKeyboardButton(s['yes_btn'], callback_data=f"step_{step}_yes")],
            [InlineKeyboardButton(s['no_btn'], callback_data=f"step_{step}_no")],
            [InlineKeyboardButton(s['main_menu_btn'], callback_data="back_to_main")]
        ]
    elif step == 7:
        # Reward Island step - special buttons
        keyboard = [
            [InlineKeyboardButton(s['yes_btn'], callback_data=f"step_{step}_yes")],
            [InlineKeyboardButton(s['show_codes_btn'], callback_data=f"step_{step}_codes")],
            [InlineKeyboardButton(s['back_btn'], callback_data=f"step_{step-1}_yes")]
        ]
    elif step == 12:
        # Final step - influencer question
        keyboard = [
            [InlineKeyboardButton(s['yes_btn'], callback_data=f"step_{step}_yes")],
            [InlineKeyboardButton(s['no_btn'], callback_data=f"step_{step}_no")],
            [InlineKeyboardButton(s['back_btn'], callback_data=f"step_{step-1}_yes")]
        ]
    else:
        # Regular step buttons
        keyboard = [
            [InlineKeyboardButton(s['yes_btn'], callback_data=f"step_{step}_yes")],
            [InlineKeyboardButton(s['no_btn'], callback_data=f"step_{step}_no")],
            [InlineKeyboardButton(s['back_btn'], callback_data=f"step_{step-1}_yes")]
        ]
    
    query = update.callback_query
    if query:
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    return NEW_PLAYER_ONBOARDING

# Step handlers - Completely different implementation
async def handle_step_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle yes answer for any step"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    step = context.user_data.get('onboarding_step', 1)
    
    # Store answer
    context.user_data['onboarding_data'][f'step_{step}'] = 'yes'
    
    # Move to next step
    if step < 12:
        context.user_data['onboarding_step'] = step + 1
        save_user_progress(user_id, step + 1, context.user_data['onboarding_data'])
        return await show_onboarding_step(update, context)
    else:
        # All steps completed
        return await complete_onboarding(update, context)

async def handle_step_no(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle no answer for any step"""
    query = update.callback_query
    await query.answer()
    
    step = context.user_data.get('onboarding_step', 1)
    s = STRINGS['en']
    
    # Get help text for current step
    help_texts = {
        1: s['step_1_help'],
        2: s['step_2_help'],
        3: s['step_3_help'],
        4: s['step_4_help'],
        5: s['step_5_help'],
        6: s['step_6_help'],
        7: s['step_7_help'],
        8: s['step_8_help'],
        9: s['step_9_help'],
        10: s['step_10_help'],
        11: s['step_11_help'],
        12: s['step_12_help']
    }
    
    help_text = help_texts.get(step, "Need help with this step?")
    
    # Create help keyboard
    if step == 2:
        keyboard = [
            [InlineKeyboardButton(s['step_2_link'], url="https://www.xbox.com/play")],
            [InlineKeyboardButton(s['next_btn'], callback_data=f"step_{step}_yes")],
            [InlineKeyboardButton(s['back_btn'], callback_data=f"step_{step-1}_yes")]
        ]
    elif step == 3:
        keyboard = [
            [InlineKeyboardButton(s['step_3_link'], url="http://epicgames.com/activate")],
            [InlineKeyboardButton(s['next_btn'], callback_data=f"step_{step}_yes")],
            [InlineKeyboardButton(s['back_btn'], callback_data=f"step_{step-1}_yes")]
        ]
    elif step == 4:
        keyboard = [
            [InlineKeyboardButton(s['step_4_link'], url="http://epicgames.com")],
            [InlineKeyboardButton(s['next_btn'], callback_data=f"step_{step}_yes")],
            [InlineKeyboardButton(s['back_btn'], callback_data=f"step_{step-1}_yes")]
        ]
    elif step == 6:
        keyboard = [
            [InlineKeyboardButton(s['step_6_link'], url="https://www.xbox.com/play/games/fortnite/BT5P2X999VH2")],
            [InlineKeyboardButton(s['next_btn'], callback_data=f"step_{step}_yes")],
            [InlineKeyboardButton(s['back_btn'], callback_data=f"step_{step-1}_yes")]
        ]
    elif step == 7:
        # Special case for reward codes
        codes_text = s['step_7_codes'].format("\n".join(REWARD_CODES))
        help_text = codes_text
        keyboard = [
            [InlineKeyboardButton(s['next_btn'], callback_data=f"step_{step}_yes")],
            [InlineKeyboardButton(s['back_btn'], callback_data=f"step_{step-1}_yes")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(s['next_btn'], callback_data=f"step_{step}_yes")],
            [InlineKeyboardButton(s['back_btn'], callback_data=f"step_{step-1}_yes")]
        ]
    
    await query.edit_message_text(
        text=help_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return NEW_PLAYER_ONBOARDING

async def handle_step_codes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show reward codes"""
    query = update.callback_query
    await query.answer()
    
    s = STRINGS['en']
    codes_text = s['step_7_codes'].format("\n".join(REWARD_CODES))
    
    keyboard = [
        [InlineKeyboardButton(s['next_btn'], callback_data="step_7_yes")],
        [InlineKeyboardButton(s['back_btn'], callback_data="show_step_7")]
    ]
    
    await query.edit_message_text(
        text=codes_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return NEW_PLAYER_ONBOARDING

async def show_step_7(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show step 7 question"""
    context.user_data['onboarding_step'] = 7
    return await show_onboarding_step(update, context)

async def complete_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Complete the onboarding process"""
    query = update.callback_query
    await query.answer()
    
    s = STRINGS['en']
    
    # Save completion
    user_id = update.effective_user.id
    save_user_progress(user_id, 99, context.user_data['onboarding_data'])  # 99 = completed
    
    await query.edit_message_text(
        text=s['onboarding_complete'],
        parse_mode='Markdown'
    )
    
    # Ask for username
    await query.message.reply_text(
        text=s['username_prompt'],
        parse_mode='Markdown'
    )
    
    return USERNAME_COLLECTION

async def collect_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Collect user's Telegram username"""
    s = STRINGS['en']
    
    username = update.message.text.strip()
    
    if username.startswith('@') and len(username) > 1:
        # Valid username
        user_id = update.effective_user.id
        user_data = context.user_data.get('onboarding_data', {})
        
        # Create support ticket (simplified)
        ticket_data = {
            'user_id': user_id,
            'username': username,
            'flow_type': 'new_player',
            'onboarding_data': user_data,
            'completed_at': update.message.date.isoformat()
        }
        
        # In a real implementation, you'd save this to database
        logger.info(f"New player onboarding completed: {ticket_data}")
        
        await update.message.reply_text(
            text=s['username_saved'],
            parse_mode='Markdown'
        )
        
        # Return to main menu
        return await show_main_menu(update, context)
    else:
        await update.message.reply_text(
            text=s['invalid_username'],
            parse_mode='Markdown'
        )
        return USERNAME_COLLECTION

# Other menu handlers
async def handle_existing_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle existing player flow"""
    query = update.callback_query
    await query.answer()
    
    s = STRINGS['en']
    await query.edit_message_text(
        text="⚡ **Existing Player Check**\n\nThis feature is coming soon!",
        parse_mode='Markdown'
    )
    return await show_main_menu(update, context)

async def handle_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle support flow"""
    query = update.callback_query
    await query.answer()
    
    s = STRINGS['en']
    await query.edit_message_text(
        text="🆘 **Support & Rewards**\n\nThis feature is coming soon!",
        parse_mode='Markdown'
    )
    return await show_main_menu(update, context)

async def show_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show channel link"""
    query = update.callback_query
    await query.answer()
    
    s = STRINGS['en']
    
    keyboard = [
        [InlineKeyboardButton(s['join_channel_btn'], url="https://t.me/yourchannel")],
        [InlineKeyboardButton(s['main_menu_btn'], callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        text=s['channel_text'],
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return MAIN_MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversation"""
    await update.message.reply_text(
        "Operation cancelled. Use /start to begin again.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main():
    """Start the bot"""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN environment variable is required")
        return
    
    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Conversation handler for new player flow
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", show_main_menu),
            CallbackQueryHandler(show_main_menu, pattern="^back_to_main$")
        ],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(start_new_player_flow, pattern="^new_player_start$"),
                CallbackQueryHandler(handle_existing_player, pattern="^existing_player_start$"),
                CallbackQueryHandler(handle_support, pattern="^support_start$"),
                CallbackQueryHandler(show_channel, pattern="^channel_link$"),
            ],
            NEW_PLAYER_ONBOARDING: [
                # Step yes handlers
                CallbackQueryHandler(handle_step_yes, pattern="^step_1_yes$"),
                CallbackQueryHandler(handle_step_yes, pattern="^step_2_yes$"),
                CallbackQueryHandler(handle_step_yes, pattern="^step_3_yes$"),
                CallbackQueryHandler(handle_step_yes, pattern="^step_4_yes$"),
                CallbackQueryHandler(handle_step_yes, pattern="^step_5_yes$"),
                CallbackQueryHandler(handle_step_yes, pattern="^step_6_yes$"),
                CallbackQueryHandler(handle_step_yes, pattern="^step_7_yes$"),
                CallbackQueryHandler(handle_step_yes, pattern="^step_8_yes$"),
                CallbackQueryHandler(handle_step_yes, pattern="^step_9_yes$"),
                CallbackQueryHandler(handle_step_yes, pattern="^step_10_yes$"),
                CallbackQueryHandler(handle_step_yes, pattern="^step_11_yes$"),
                CallbackQueryHandler(handle_step_yes, pattern="^step_12_yes$"),
                
                # Step no handlers
                CallbackQueryHandler(handle_step_no, pattern="^step_1_no$"),
                CallbackQueryHandler(handle_step_no, pattern="^step_2_no$"),
                CallbackQueryHandler(handle_step_no, pattern="^step_3_no$"),
                CallbackQueryHandler(handle_step_no, pattern="^step_4_no$"),
                CallbackQueryHandler(handle_step_no, pattern="^step_5_no$"),
                CallbackQueryHandler(handle_step_no, pattern="^step_6_no$"),
                CallbackQueryHandler(handle_step_no, pattern="^step_7_no$"),
                CallbackQueryHandler(handle_step_no, pattern="^step_8_no$"),
                CallbackQueryHandler(handle_step_no, pattern="^step_9_no$"),
                CallbackQueryHandler(handle_step_no, pattern="^step_10_no$"),
                CallbackQueryHandler(handle_step_no, pattern="^step_11_no$"),
                CallbackQueryHandler(handle_step_no, pattern="^step_12_no$"),
                
                # Special handlers
                CallbackQueryHandler(handle_step_codes, pattern="^step_7_codes$"),
                CallbackQueryHandler(show_step_7, pattern="^show_step_7$"),
                
                # Navigation
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
            USERNAME_COLLECTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_username)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    # Add handlers
    application.add_handler(conv_handler)
    
    # Start bot
    logger.info("Bot starting...")
    application.run_polling()

if __name__ == "__main__":
    main()

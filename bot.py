import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get bot token from environment
TOKEN = os.getenv('TELEGRAM_TOKEN')
if not TOKEN:
    logger.error("❌ TELEGRAM_TOKEN environment variable is not set!")
    exit(1)

print(f"✅ Bot token found: {TOKEN[:10]}...")

# Game codes
REWARD_CODES = [
    "6086-7221-0564",
    "2753-4695-7191", 
    "9689-1352-5966",
    "4563-6624-9460",
    "4828-9033-2281"
]

# Store user progress in memory (for simplicity)
user_progress = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message with main menu"""
    user_id = update.effective_user.id
    
    # Initialize user progress
    user_progress[user_id] = {
        'current_step': 0,
        'answers': {},
        'flow_type': None
    }
    
    welcome_text = """🌟 **Fortnite Gaming Assistant** 🌟

Welcome to your ultimate gaming journey! I'll help you:
• Set up your gaming account 🎮
• Find reward islands 🏝️  
• Maximize your earnings 💰

Choose your path:"""
    
    keyboard = [
        [InlineKeyboardButton("🚀 New Player Setup", callback_data="new_player")],
        [InlineKeyboardButton("⚡ Existing Player Check", callback_data="existing_player")],
        [InlineKeyboardButton("🆘 Support & Rewards", callback_data="support")],
        [InlineKeyboardButton("📚 Guides & Community", callback_data="channel")]
    ]
    
    if update.message:
        await update.message.reply_text(
            welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await update.callback_query.edit_message_text(
            welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all callback queries"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    # Initialize user progress if not exists
    if user_id not in user_progress:
        user_progress[user_id] = {'current_step': 0, 'answers': {}, 'flow_type': None}
    
    if data == "new_player":
        await start_new_player_flow(update, context)
    elif data == "existing_player":
        await query.edit_message_text(
            "⚡ **Existing Player Check**\n\nComing soon! Use /start to return to main menu.",
            parse_mode='Markdown'
        )
    elif data == "support":
        await query.edit_message_text(
            "🆘 **Support & Rewards**\n\nComing soon! Use /start to return to main menu.",
            parse_mode='Markdown'
        )
    elif data == "channel":
        keyboard = [[InlineKeyboardButton("Join Community", url="https://t.me/example")]]
        await query.edit_message_text(
            "📚 **Guides & Community**\n\nJoin our community for exclusive content!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    elif data.startswith("step_"):
        await handle_step_response(update, context)
    elif data == "back_to_main":
        await start(update, context)

async def start_new_player_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start the new player onboarding flow"""
    user_id = update.effective_user.id
    user_progress[user_id]['current_step'] = 1
    user_progress[user_id]['flow_type'] = 'new_player'
    
    welcome_text = """🎯 **New Player Setup Guide**

Welcome to your gaming adventure! I'll guide you through every step to set up your account and start earning rewards.

💡 **Note:** Each cloud gaming session lasts 1 hour. You'll need to relaunch after each session.

**Step 1/12: VPN Setup** 🔒
Did you use a USA VPN when creating your profiles?"""
    
    keyboard = [
        [InlineKeyboardButton("✅ Yes", callback_data="step_1_yes")],
        [InlineKeyboardButton("❌ No", callback_data="step_1_no")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_main")]
    ]
    
    await update.callback_query.edit_message_text(
        welcome_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_step_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle step responses in the new player flow"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Extract step number and response
    data_parts = query.data.split('_')
    step = int(data_parts[1])
    response = data_parts[2]
    
    # Store the answer
    user_progress[user_id]['answers'][f'step_{step}'] = response
    
    # Define all steps with their questions and help texts
    steps = {
        1: {
            'question': "**Step 1/12: VPN Setup** 🔒\nDid you use a USA VPN when creating your profiles?",
            'help': "⚠️ **VPN Required**\n\nYou need a USA VPN only for profile creation (not playing). This ensures your profiles are created correctly.\n\nReady to continue?"
        },
        2: {
            'question': "**Step 2/12: Cloud Gaming Profile** ☁️\nHave you created your cloud gaming profile?",
            'help': "Let's create your cloud gaming profile!\nNeed step-by-step assistance?"
        },
        3: {
            'question': "**Step 3/12: Epic Games Activation** 🎯\nDid you receive and enter the Epic Games activation code?",
            'help': "You need to activate your account with Epic Games to save your progress and rewards.\nNeed guidance?"
        },
        4: {
            'question': "**Step 4/12: Epic Games Profile** 👤\nDid you create your Epic Games profile?",
            'help': "Your Epic Games profile is essential for saving progress and receiving rewards.\nNeed help setting it up?"
        },
        5: {
            'question': "**Step 5/12: Home Screen Shortcut** 📱\nDid you add the game to your home screen for easy access?",
            'help': "Adding a shortcut lets you launch the game instantly!\nWant to see how it's done?"
        },
        6: {
            'question': "**Step 6/12: Game Launch** 🚀\nHave you successfully launched the game?",
            'help': "Let's get the game started!\nNeed launching assistance?"
        },
        7: {
            'question': "**Step 7/12: Reward Island Discovery** 🏝️\nHave you found the Reward Island using our special codes?",
            'help': "The Reward Island is where you'll earn amazing rewards!\nWant the latest access codes?"
        },
        8: {
            'question': "**Step 8/12: Complete Setup** ⚙️\nDid you finish the full setup to play with friends and maximize earnings?",
            'help': "Complete setup ensures you can play with friends and earn without issues.\nNeed the setup guide?"
        },
        9: {
            'question': "**Step 9/12: Weekly Commitment** ⏰\nCan you commit to playing 130 hours this week?",
            'help': "Regular playtime is key to earning rewards! We recommend 130 hours weekly.\nCan you meet this goal?"
        },
        10: {
            'question': "**Step 10/12: Engagement Promise** 👍\nWill you click the 'Like' button before each 1-hour session ends?",
            'help': "The 'Like' button helps track your engagement and is required for rewards.\nNeed reminders on when to click?"
        },
        11: {
            'question': "**Step 11/12: Favorites Setup** ⭐\nDid you save the Reward Island to your favorites?",
            'help': "Saving to favorites lets you quickly return to the Reward Island.\nWant to learn how?"
        },
        12: {
            'question': "**Step 12/12: Community Credit** 🤝\nDid an influencer introduce you to this game?",
            'help': "No problem! Let's complete your setup."
        }
    }
    
    if response == "no":
        # Show help for current step
        current_step = steps[step]
        
        if step == 7:  # Special case for reward codes
            codes_text = "🎮 **Reward Island Access Codes:**\n" + "\n".join(REWARD_CODES) + "\n\nCopy any code and paste it in the game's search bar!"
            help_text = codes_text
            keyboard = [
                [InlineKeyboardButton("➡️ Continue", callback_data=f"step_{step}_yes")],
                [InlineKeyboardButton("⬅️ Back", callback_data=f"step_{step-1}_yes")]
            ]
        else:
            help_text = current_step['help']
            keyboard = [
                [InlineKeyboardButton("✅ I'm Ready", callback_data=f"step_{step}_yes")],
                [InlineKeyboardButton("⬅️ Back", callback_data=f"step_{step-1}_yes" if step > 1 else "new_player")]
            ]
        
        await query.edit_message_text(
            help_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return
    
    # Move to next step or complete
    if step < 12:
        next_step = step + 1
        user_progress[user_id]['current_step'] = next_step
        
        next_question = steps[next_step]['question']
        
        if next_step == 12:  # Special keyboard for last step
            keyboard = [
                [InlineKeyboardButton("✅ Yes", callback_data=f"step_{next_step}_yes")],
                [InlineKeyboardButton("❌ No", callback_data=f"step_{next_step}_no")],
                [InlineKeyboardButton("⬅️ Back", callback_data=f"step_{step}_yes")]
            ]
        else:
            keyboard = [
                [InlineKeyboardButton("✅ Yes", callback_data=f"step_{next_step}_yes")],
                [InlineKeyboardButton("❌ No", callback_data=f"step_{next_step}_no")],
                [InlineKeyboardButton("⬅️ Back", callback_data=f"step_{step}_yes")]
            ]
        
        await query.edit_message_text(
            next_question,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        # All steps completed
        await complete_onboarding(update, context)

async def complete_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Complete the onboarding process"""
    user_id = update.effective_user.id
    
    completion_text = """🎉 **Setup Complete!**

Congratulations! You've successfully completed all setup steps.

You're now ready to:
• Play and earn amazing rewards 🎁
• Join our gaming community 👥
• Maximize your gaming experience ⚡

**Final Step:** Please share your Telegram username (starting with @) so we can contact you:"""
    
    await update.callback_query.edit_message_text(
        completion_text,
        parse_mode='Markdown'
    )
    
    # Set state to wait for username
    user_progress[user_id]['waiting_for_username'] = True

async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle username input"""
    user_id = update.effective_user.id
    
    if user_id not in user_progress or not user_progress[user_id].get('waiting_for_username'):
        await update.message.reply_text("Please use /start to begin.")
        return
    
    username = update.message.text.strip()
    
    if username.startswith('@') and len(username) > 1:
        # Valid username
        user_progress[user_id]['telegram_username'] = username
        
        # Save user data (in a real app, you'd save to database)
        logger.info(f"User {user_id} completed onboarding with username {username}")
        
        await update.message.reply_text(
            "✅ Perfect! Our team will contact you soon with next steps and reward information!\n\nUse /start to explore more features.",
            parse_mode='Markdown'
        )
        
        # Reset waiting state
        user_progress[user_id]['waiting_for_username'] = False
        
    else:
        await update.message.reply_text(
            "❌ Please provide a valid Telegram username starting with @ (example: @username)\n\nPlease try again:"
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message"""
    await update.message.reply_text(
        "Need help? Use /start to begin the setup process or contact support through our community channel."
    )

def main() -> None:
    """Start the bot"""
    print("🤖 Starting Fortnite Gaming Assistant Bot...")
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username))
    
    # Start the bot
    print("✅ Bot is running! Press Ctrl+C to stop.")
    application.run_polling()

if __name__ == '__main__':
    main()

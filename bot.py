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
SUPPORT_CHAT_ID = os.environ.get("SUPPORT_CHAT_ID")

# Debug: Print environment variables
print("=" * 50)
print("ENVIRONMENT VARIABLES CHECK:")
print(f"TELEGRAM_TOKEN: {'✅ SET' if TELEGRAM_TOKEN else '❌ NOT SET'}")
print(f"SUPPORT_CHAT_ID: {'✅ SET' if SUPPORT_CHAT_ID else '❌ NOT SET'}")
if SUPPORT_CHAT_ID:
    print(f"SUPPORT_CHAT_ID value: {SUPPORT_CHAT_ID}")
print("=" * 50)

# !!! IMPORTANT: Fill these in with your information !!!
YOUR_PLAYGROUND_NAME = "My Awesome Playground"
YOUR_PLAYGROUND_LINK = "https://your-fortnite-playground-link.com"
HELPFUL_CHANNEL_LINK = "https://t.me/rejoinsnousetgagne"
# !!!!!!!!!!!!!!!!!!!!!

# Reward Island Codes
REWARD_ISLAND_CODES = [
    "1234-5678-9012",
    "3456-7890-1234", 
    "5678-9012-3456",
    "7890-1234-5678"
]

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
        'existing_player_text': (
            "✅ Great! Here is the direct link to the playground:\n\n"
            f"{YOUR_PLAYGROUND_LINK}\n\n"
            "**Cloud Gaming Reminder:**\n"
            "Your session lasts for 1 hour. After that, you will need to relaunch the game and use this link again."
        ),
        'back_btn': "⬅️ Back to Main Menu",
        
        # Existing Player Flow Strings
        'existing_player_intro': (
            "🎮 *Existing Player Guide*\n\n"
            "Because you are playing on the cloud, your session will last for 1 hour. "
            "The game will close, and you will have to launch it again to keep playing.\n\n"
            "You probably know it cause you already follow all the instructions. "
            "Let's check your current progress! 🚀"
        ),
        
        # Common buttons
        'yes_btn': "Yes",
        'no_btn': "No",
        'forward_to_channel': "📺 Please check our channel for detailed guidance: {link}",
        'forward_to_channel_instruction': "📺 Please check instruction {number} in our channel: {link}",
        
        # Question 1 - Reward Island
        'q1_reward_island': "1. Have you searched and found the reward Island?",
        'q1_no_island': "You have to search the reward Island in the search bar and just choose it. Do you want our guidance for that?",
        'q1_codes_yes': "Yes, I want the best codes to play",
        'q1_codes_no': "No, I already chose one code",
        'q1_codes_list': "🏝️ Here are the best reward Island codes:\n{}\n\nJust copy one of them and enter it on the search bar.",
        
        # Question 2 - Full Setup
        'q2_full_setup': "2. Did you follow the full setup to be able to play with friends and earn a lot together without any worries?",
        'q2_no_setup': "You have to follow the exact setup. Do you need our guidance?",
        'q2_guidance_yes': "Yes, I need guidance",
        'q2_guidance_no': "No, I finally fixed everything",
        
        # Question 3 - Play Hours
        'q3_play_hours': "3. Did you start the game and play 130 hours for free this week?",
        'q3_no_play': "You have to start the game and play every single day for free before aiming for the reward. Are you able to play at least 130 hours a week?",
        'q3_able_yes': "Yes, I can play 130 hours",
        'q3_able_no': "No, I cannot play that much",
        
        # Question 4 - Like Button
        'q4_like_button': "4. With your existing account, will you click on the like button every single time before your 1 hour play session ended during your 130 hours of play this week?",
        'q4_no_like': "You have to click on the like button every single time before your 1 hour play session ended during your 130 hours a week. Do you want our guidance on that?",
        'q4_guidance_yes': "Yes, I need guidance",
        'q4_guidance_no': "No, I will play and let you know later",
        
        # Question 5 - Save Favorites
        'q5_save_favorites': "5. Did you save the reward Island to your favorites?",
        'q5_no_save': "You have to save the reward Island to your favorites and play. Do you want our guidance on that?",
        'q5_guidance_yes': "Yes, I need guidance",
        'q5_guidance_no': "No, I have proof I saved it",
        
        # Question 6 - Influencer
        'q6_influencer': "6. Were you introduced to this game by an influencer?",
        'q6_influencer_yes': "Yes",
        'q6_influencer_no': "No",
        'q6_provide_name': "Please provide the influencer's name:",
        
        # Existing Player Completion
        'existing_player_complete': "🎉 Excellent! You've completed the existing player check. You're all set to continue playing and earning! 🎮\n\nKeep up the great work and remember to:\n• Play your 130 hours this week\n• Click the like button before each session ends\n• Keep the reward Island in your favorites\n\nIf you encounter any issues, use the Support option in the main menu!",
        
        # Guide steps (kept for backward compatibility)
        'guide1_text': "**Step 1: Create Epic Games Account**\n\nThis is required to play Fortnite. Go to the official site to create your account.\n\nWhen you're done, click 'Next Step'.",
        'guide1_btn': "Go to Epic Games Site",
        'guide_next_btn': "Next Step ➡️",
        'guide2_text': "**Step 2: Set Up Fortnite**\n\nAfter creating your Epic account, make sure Fortnite is added to your library and set up. For cloud gaming, you'll usually do this through your cloud service (like GeForce NOW, Xbox Cloud Gaming, etc.).",
        'guide3_text': f"**Step 3: Find My Playground**\n\nOnce you are in Fortnite, go to the game search bar (Island Code) and type in this exact name:\n\n`{YOUR_PLAYGROUND_NAME}`\n\nThis will take you to my playground. Add it to your favorites!",
        'guide4_text': "**Final Info: Cloud Gaming Limit**\n\nBecause you are playing on the cloud, your session will last for **1 hour**. The game will close, and you will have to launch it again to keep playing.\n\nNext time, you can use the 'Existing Player' button on this bot to get the link faster!",
        
        'support_thanks': "Thank you! Your @username has been noted. We will get in touch with you as soon as possible.\n\nReturning you to the main menu.",
        'support_cancel': "Support request cancelled. Returning to main menu.",
        'invalid_username': "That doesn't look like a valid @username. Please start with '@' and try again, or type /cancel.",
    }
}

# Define states
SELECT_LANG, MAIN_MENU, GUIDE_STEPS = range(3)
# Support flow states
SUPPORT_STATES = range(3, 17)
# New Player flow states
NEW_PLAYER_STATES = range(17, 30)
# Existing Player flow states
EXISTING_PLAYER_STATES = range(30, 37)

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

async def forward_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE, next_state=None, instruction_number=None):
    """Helper to forward user to channel and either continue or return to menu."""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    if instruction_number:
        text = s['forward_to_channel_instruction'].format(number=instruction_number, link=HELPFUL_CHANNEL_LINK)
    else:
        text = s['forward_to_channel'].format(link=HELPFUL_CHANNEL_LINK)
    
    await query.edit_message_text(text=text)
    
    if next_state:
        # Continue to next question after showing channel message
        return await next_state(update, context)
    else:
        # Return to main menu
        return await show_main_menu(update, context)

# --- EXISTING PLAYER FLOW FUNCTIONS ---

async def existing_player_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the existing player comprehensive guide."""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    # Reset existing player data
    context.user_data['existing_player_answers'] = {}
    context.user_data['existing_player_data'] = {}  # For storing text responses
    
    # Start with introduction and question 1
    keyboard = [
        [InlineKeyboardButton(s['yes_btn'], callback_data="existing_player_q1_yes")],
        [InlineKeyboardButton(s['no_btn'], callback_data="existing_player_q1_no")],
    ]
    
    await query.edit_message_text(
        text=f"{s['existing_player_intro']}\n\n{s['q1_reward_island']}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    return EXISTING_PLAYER_STATES[0]  # Q1

# Question 1: Reward Island
async def existing_player_q1_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User found reward island -> go to question 2"""
    context.user_data['existing_player_answers']['q1_reward_island'] = 'yes'
    return await existing_player_ask_question_2(update, context)

async def existing_player_q1_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User didn't find reward island -> offer codes"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton(s['q1_codes_yes'], callback_data="existing_player_q1_no_yes")],
        [InlineKeyboardButton(s['q1_codes_no'], callback_data="existing_player_q1_no_no")],
    ]
    
    await query.edit_message_text(
        text=s['q1_no_island'],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return EXISTING_PLAYER_STATES[0]

async def existing_player_q1_no_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User wants codes"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    codes_text = "\n".join([f"• {code}" for code in REWARD_ISLAND_CODES])
    
    await query.edit_message_text(
        text=s['q1_codes_list'].format(codes_text)
    )
    return await existing_player_ask_question_2(update, context)

async def existing_player_q1_no_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User claims to have chosen code -> go to question 2"""
    context.user_data['existing_player_answers']['q1_reward_island'] = 'yes_claimed'
    return await existing_player_ask_question_2(update, context)

# Question 2: Full Setup
async def existing_player_ask_question_2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask question 2 about full setup"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton(s['yes_btn'], callback_data="existing_player_q2_yes")],
        [InlineKeyboardButton(s['no_btn'], callback_data="existing_player_q2_no")],
    ]
    
    await query.edit_message_text(
        text=s['q2_full_setup'],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return EXISTING_PLAYER_STATES[1]

async def existing_player_q2_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User completed setup -> go to question 3"""
    context.user_data['existing_player_answers']['q2_full_setup'] = 'yes'
    return await existing_player_ask_question_3(update, context)

async def existing_player_q2_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User didn't complete setup -> offer guidance"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton(s['q2_guidance_yes'], callback_data="existing_player_q2_no_yes")],
        [InlineKeyboardButton(s['q2_guidance_no'], callback_data="existing_player_q2_no_no")],
    ]
    
    await query.edit_message_text(
        text=s['q2_no_setup'],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return EXISTING_PLAYER_STATES[1]

async def existing_player_q2_no_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User needs guidance -> forward to channel with instruction 9"""
    return await forward_to_channel(update, context, existing_player_ask_question_3, instruction_number=9)

async def existing_player_q2_no_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User claims to have fixed everything -> go to question 3"""
    context.user_data['existing_player_answers']['q2_full_setup'] = 'yes_claimed'
    return await existing_player_ask_question_3(update, context)

# Question 3: Play Hours
async def existing_player_ask_question_3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask question 3 about play hours"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton(s['yes_btn'], callback_data="existing_player_q3_yes")],
        [InlineKeyboardButton(s['no_btn'], callback_data="existing_player_q3_no")],
    ]
    
    await query.edit_message_text(
        text=s['q3_play_hours'],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return EXISTING_PLAYER_STATES[2]

async def existing_player_q3_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User played 130 hours -> go to question 4"""
    context.user_data['existing_player_answers']['q3_play_hours'] = 'yes'
    return await existing_player_ask_question_4(update, context)

async def existing_player_q3_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User didn't play 130 hours -> ask if able"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton(s['q3_able_yes'], callback_data="existing_player_q3_no_yes")],
        [InlineKeyboardButton(s['q3_able_no'], callback_data="existing_player_q3_no_no")],
    ]
    
    await query.edit_message_text(
        text=s['q3_no_play'],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return EXISTING_PLAYER_STATES[2]

async def existing_player_q3_no_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User can play 130 hours -> go to question 4"""
    context.user_data['existing_player_answers']['q3_play_hours'] = 'able_yes'
    return await existing_player_ask_question_4(update, context)

async def existing_player_q3_no_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User cannot play 130 hours -> forward to channel with instruction 10"""
    return await forward_to_channel(update, context, instruction_number=10)

# Question 4: Like Button
async def existing_player_ask_question_4(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask question 4 about like button"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton(s['yes_btn'], callback_data="existing_player_q4_yes")],
        [InlineKeyboardButton(s['no_btn'], callback_data="existing_player_q4_no")],
    ]
    
    await query.edit_message_text(
        text=s['q4_like_button'],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return EXISTING_PLAYER_STATES[3]

async def existing_player_q4_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User will click like button -> go to question 5"""
    context.user_data['existing_player_answers']['q4_like_button'] = 'yes'
    return await existing_player_ask_question_5(update, context)

async def existing_player_q4_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User won't click like button -> offer guidance"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton(s['q4_guidance_yes'], callback_data="existing_player_q4_no_yes")],
        [InlineKeyboardButton(s['q4_guidance_no'], callback_data="existing_player_q4_no_no")],
    ]
    
    await query.edit_message_text(
        text=s['q4_no_like'],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return EXISTING_PLAYER_STATES[3]

async def existing_player_q4_no_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User needs guidance -> forward to channel with instruction 11"""
    return await forward_to_channel(update, context, existing_player_ask_question_5, instruction_number=11)

async def existing_player_q4_no_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User will let us know later -> go to question 5"""
    context.user_data['existing_player_answers']['q4_like_button'] = 'will_let_know'
    return await existing_player_ask_question_5(update, context)

# Question 5: Save Favorites
async def existing_player_ask_question_5(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask question 5 about saving favorites"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton(s['yes_btn'], callback_data="existing_player_q5_yes")],
        [InlineKeyboardButton(s['no_btn'], callback_data="existing_player_q5_no")],
    ]
    
    await query.edit_message_text(
        text=s['q5_save_favorites'],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return EXISTING_PLAYER_STATES[4]

async def existing_player_q5_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User saved to favorites -> go to question 6"""
    context.user_data['existing_player_answers']['q5_save_favorites'] = 'yes'
    return await existing_player_ask_question_6(update, context)

async def existing_player_q5_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User didn't save to favorites -> offer guidance"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton(s['q5_guidance_yes'], callback_data="existing_player_q5_no_yes")],
        [InlineKeyboardButton(s['q5_guidance_no'], callback_data="existing_player_q5_no_no")],
    ]
    
    await query.edit_message_text(
        text=s['q5_no_save'],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return EXISTING_PLAYER_STATES[4]

async def existing_player_q5_no_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User needs guidance -> forward to channel with instruction 12"""
    return await forward_to_channel(update, context, existing_player_ask_question_6, instruction_number=12)

async def existing_player_q5_no_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User has proof -> go to question 6"""
    context.user_data['existing_player_answers']['q5_save_favorites'] = 'has_proof'
    return await existing_player_ask_question_6(update, context)

# Question 6: Influencer
async def existing_player_ask_question_6(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask question 6 about influencer"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton(s['q6_influencer_yes'], callback_data="existing_player_q6_yes")],
        [InlineKeyboardButton(s['q6_influencer_no'], callback_data="existing_player_q6_no")],
    ]
    
    await query.edit_message_text(
        text=s['q6_influencer'],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return EXISTING_PLAYER_STATES[5]

async def existing_player_q6_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User was introduced by influencer -> ask for name"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text=s['q6_provide_name']
    )
    return EXISTING_PLAYER_STATES[6]  # Special state for influencer name

async def existing_player_q6_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User wasn't introduced by influencer -> forward to channel with instruction 13"""
    return await forward_to_channel(update, context, instruction_number=13)

async def existing_player_influencer_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store influencer name and complete existing player flow"""
    influencer_name = update.message.text
    context.user_data['existing_player_data']['influencer_name'] = influencer_name
    context.user_data['existing_player_answers']['q6_influencer'] = f'yes: {influencer_name}'
    
    # Complete the existing player flow
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    await update.message.reply_text(
        text=s['existing_player_complete'],
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(s['back_btn'], callback_data="back_to_main")]
        ])
    )
    return MAIN_MENU

async def cancel_existing_player(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel existing player flow"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    await update.message.reply_text(text="Existing player guide cancelled. Returning to main menu.", reply_markup=ReplyKeyboardRemove())
    return await show_main_menu(update, context)

# Update the existing_player_link function to start the flow instead of showing direct link
async def existing_player_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the existing player flow instead of showing direct link"""
    return await existing_player_start(update, context)

# [Rest of the code remains the same - you need to integrate this into your existing bot structure]

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

    # Create existing player states dictionary
    existing_player_states = {}
    
    # Question 1
    existing_player_states[EXISTING_PLAYER_STATES[0]] = [
        CallbackQueryHandler(existing_player_q1_yes, pattern="^existing_player_q1_yes$"),
        CallbackQueryHandler(existing_player_q1_no, pattern="^existing_player_q1_no$"),
        CallbackQueryHandler(existing_player_q1_no_yes, pattern="^existing_player_q1_no_yes$"),
        CallbackQueryHandler(existing_player_q1_no_no, pattern="^existing_player_q1_no_no$"),
        CommandHandler("cancel", cancel_existing_player),
    ]
    
    # Question 2
    existing_player_states[EXISTING_PLAYER_STATES[1]] = [
        CallbackQueryHandler(existing_player_q2_yes, pattern="^existing_player_q2_yes$"),
        CallbackQueryHandler(existing_player_q2_no, pattern="^existing_player_q2_no$"),
        CallbackQueryHandler(existing_player_q2_no_yes, pattern="^existing_player_q2_no_yes$"),
        CallbackQueryHandler(existing_player_q2_no_no, pattern="^existing_player_q2_no_no$"),
        CommandHandler("cancel", cancel_existing_player),
    ]
    
    # Question 3
    existing_player_states[EXISTING_PLAYER_STATES[2]] = [
        CallbackQueryHandler(existing_player_q3_yes, pattern="^existing_player_q3_yes$"),
        CallbackQueryHandler(existing_player_q3_no, pattern="^existing_player_q3_no$"),
        CallbackQueryHandler(existing_player_q3_no_yes, pattern="^existing_player_q3_no_yes$"),
        CallbackQueryHandler(existing_player_q3_no_no, pattern="^existing_player_q3_no_no$"),
        CommandHandler("cancel", cancel_existing_player),
    ]
    
    # Question 4
    existing_player_states[EXISTING_PLAYER_STATES[3]] = [
        CallbackQueryHandler(existing_player_q4_yes, pattern="^existing_player_q4_yes$"),
        CallbackQueryHandler(existing_player_q4_no, pattern="^existing_player_q4_no$"),
        CallbackQueryHandler(existing_player_q4_no_yes, pattern="^existing_player_q4_no_yes$"),
        CallbackQueryHandler(existing_player_q4_no_no, pattern="^existing_player_q4_no_no$"),
        CommandHandler("cancel", cancel_existing_player),
    ]
    
    # Question 5
    existing_player_states[EXISTING_PLAYER_STATES[4]] = [
        CallbackQueryHandler(existing_player_q5_yes, pattern="^existing_player_q5_yes$"),
        CallbackQueryHandler(existing_player_q5_no, pattern="^existing_player_q5_no$"),
        CallbackQueryHandler(existing_player_q5_no_yes, pattern="^existing_player_q5_no_yes$"),
        CallbackQueryHandler(existing_player_q5_no_no, pattern="^existing_player_q5_no_no$"),
        CommandHandler("cancel", cancel_existing_player),
    ]
    
    # Question 6
    existing_player_states[EXISTING_PLAYER_STATES[5]] = [
        CallbackQueryHandler(existing_player_q6_yes, pattern="^existing_player_q6_yes$"),
        CallbackQueryHandler(existing_player_q6_no, pattern="^existing_player_q6_no$"),
        CommandHandler("cancel", cancel_existing_player),
    ]
    
    # Influencer name input
    existing_player_states[EXISTING_PLAYER_STATES[6]] = [
        MessageHandler(filters.TEXT & ~filters.COMMAND, existing_player_influencer_name),
        CommandHandler("cancel", cancel_existing_player),
    ]

    # [You would integrate this into your existing conversation handler]
    # This is just a partial implementation - you need to combine it with your existing code

if __name__ == "__main__":
    main()

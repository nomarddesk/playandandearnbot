import os
import logging
import random
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    ContextTypes, 
    filters
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration - Get from Render environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
SUPPORT_CHAT_ID = os.getenv('SUPPORT_CHAT_ID')

# Debug: Print environment variables to verify they're being read
print("=" * 50)
print("ENVIRONMENT VARIABLES CHECK:")
print(f"BOT_TOKEN: {'✅ SET' if BOT_TOKEN else '❌ NOT SET'}")
print(f"SUPPORT_CHAT_ID: {'✅ SET' if SUPPORT_CHAT_ID else '❌ NOT SET'}")
if SUPPORT_CHAT_ID:
    print(f"SUPPORT_CHAT_ID value: {SUPPORT_CHAT_ID}")
print("=" * 50)

# Game configuration
INITIAL_BALANCE = 1000
MIN_BET = 50
MAX_BET = 5000

# User data storage (in production, use a database)
user_data = {}

class User:
    def __init__(self, user_id):
        self.user_id = user_id
        self.balance = INITIAL_BALANCE
        self.last_claim = None
        self.games_played = 0
        self.total_winnings = 0

def get_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = User(user_id)
    return user_data[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when the command /start is issued."""
    user = get_user(update.effective_user.id)
    
    welcome_text = (
        "🎮 Welcome to Play & Earn Bot! 🎮\n\n"
        "💰 Your balance: ${:,}\n"
        "🎲 Play games and earn money!\n\n"
        "Available commands:\n"
        "/play - Start a new game\n"
        "/balance - Check your balance\n"
        "/daily - Claim daily bonus\n"
        "/support - Contact support\n"
        "/leaderboard - Top players"
    ).format(user.balance)
    
    await update.message.reply_text(welcome_text)

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check user balance."""
    user = get_user(update.effective_user.id)
    
    balance_text = (
        "💰 Your Balance:\n"
        "Cash: ${:,}\n"
        "Games Played: {}\n"
        "Total Winnings: ${:,}"
    ).format(user.balance, user.games_played, user.total_winnings)
    
    await update.message.reply_text(balance_text)

async def daily_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Claim daily bonus."""
    user = get_user(update.effective_user.id)
    now = datetime.now()
    
    if user.last_claim and (now - user.last_claim).days < 1:
        next_claim = user.last_claim + timedelta(days=1)
        time_left = next_claim - now
        hours = int(time_left.seconds // 3600)
        minutes = int((time_left.seconds % 3600) // 60)
        
        await update.message.reply_text(
            f"⏰ You've already claimed your daily bonus today!\n"
            f"Next bonus in: {hours}h {minutes}m"
        )
        return
    
    # Daily bonus amount (random between 100-500)
    bonus = random.randint(100, 500)
    user.balance += bonus
    user.last_claim = now
    
    await update.message.reply_text(
        f"🎉 Daily Bonus Claimed!\n"
        f"💰 You received: ${bonus:,}\n"
        f"💵 New balance: ${user.balance:,}\n\n"
        f"Come back tomorrow for more!"
    )

async def play_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a new game."""
    user = get_user(update.effective_user.id)
    
    if user.balance < MIN_BET:
        await update.message.reply_text(
            f"❌ Insufficient balance! You need at least ${MIN_BET} to play.\n"
            f"💰 Your balance: ${user.balance:,}\n\n"
            f"Use /daily to claim your daily bonus!"
        )
        return
    
    keyboard = [
        [InlineKeyboardButton("🎯 Number Guess ($50)", callback_data="game_number_50")],
        [InlineKeyboardButton("🎯 Number Guess ($100)", callback_data="game_number_100")],
        [InlineKeyboardButton("🎯 Number Guess ($200)", callback_data="game_number_200")],
        [InlineKeyboardButton("🎰 Slot Machine ($300)", callback_data="game_slot_300")],
        [InlineKeyboardButton("🎰 Slot Machine ($500)", callback_data="game_slot_500")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎮 Choose a game to play:\n\n"
        "🎯 Number Guess - Guess the correct number (2x payout)\n"
        "🎰 Slot Machine - Match symbols to win big (up to 10x payout)\n\n"
        f"💰 Your balance: ${user.balance:,}",
        reply_markup=reply_markup
    )

async def handle_game_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle game selection from inline keyboard."""
    query = update.callback_query
    await query.answer()
    
    user = get_user(query.from_user.id)
    game_data = query.data.split('_')
    game_type = game_data[1]
    bet_amount = int(game_data[2])
    
    if user.balance < bet_amount:
        await query.edit_message_text(
            f"❌ Insufficient balance! You need ${bet_amount} to play this game.\n"
            f"💰 Your balance: ${user.balance:,}"
        )
        return
    
    # Deduct bet amount
    user.balance -= bet_amount
    user.games_played += 1
    
    if game_type == "number":
        await play_number_guess(query, bet_amount, user)
    elif game_type == "slot":
        await play_slot_machine(query, bet_amount, user)

async def play_number_guess(query, bet_amount, user):
    """Play number guessing game."""
    # Generate random number between 1-10
    winning_number = random.randint(1, 10)
    
    # Simulate some "thinking" time
    await query.edit_message_text("🎯 Rolling the dice...")
    await asyncio.sleep(1.5)
    
    # Player's guess (random for this simulation)
    player_guess = random.randint(1, 10)
    
    if player_guess == winning_number:
        win_amount = bet_amount * 2
        user.balance += win_amount
        user.total_winnings += win_amount
        
        await query.edit_message_text(
            f"🎉 YOU WON! 🎉\n\n"
            f"🎯 Your guess: {player_guess}\n"
            f"🎯 Winning number: {winning_number}\n"
            f"💰 Bet: ${bet_amount:,}\n"
            f"💰 Won: ${win_amount:,}\n"
            f"💵 New balance: ${user.balance:,}"
        )
    else:
        await query.edit_message_text(
            f"😔 Better luck next time!\n\n"
            f"🎯 Your guess: {player_guess}\n"
            f"🎯 Winning number: {winning_number}\n"
            f"💰 Bet lost: ${bet_amount:,}\n"
            f"💵 New balance: ${user.balance:,}"
        )

async def play_slot_machine(query, bet_amount, user):
    """Play slot machine game."""
    symbols = ['🍒', '🍋', '🍊', '🍇', '🔔', '💎', '7️⃣']
    
    await query.edit_message_text("🎰 Spinning the slots...")
    await asyncio.sleep(2)
    
    # Generate random slots
    slots = [random.choice(symbols) for _ in range(3)]
    slot_display = " | ".join(slots)
    
    # Check for wins
    if slots[0] == slots[1] == slots[2]:
        if slots[0] == '💎':
            multiplier = 10
        elif slots[0] == '7️⃣':
            multiplier = 5
        else:
            multiplier = 3
    elif slots[0] == slots[1] or slots[1] == slots[2]:
        multiplier = 2
    else:
        multiplier = 0
    
    if multiplier > 0:
        win_amount = bet_amount * multiplier
        user.balance += win_amount
        user.total_winnings += win_amount
        
        result_text = (
            f"🎰 SLOTS: {slot_display} 🎰\n\n"
            f"🎉 JACKPOT! {multiplier}x WIN! 🎉\n"
            f"💰 Bet: ${bet_amount:,}\n"
            f"💰 Won: ${win_amount:,}\n"
            f"💵 New balance: ${user.balance:,}"
        )
    else:
        result_text = (
            f"🎰 SLOTS: {slot_display} 🎰\n\n"
            f"😔 No winning combination\n"
            f"💰 Bet lost: ${bet_amount:,}\n"
            f"💵 New balance: ${user.balance:,}"
        )
    
    await query.edit_message_text(result_text)

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show top players by balance."""
    if not user_data:
        await update.message.reply_text("No players yet! Be the first to play!")
        return
    
    top_players = sorted(user_data.values(), key=lambda x: x.balance, reverse=True)[:10]
    
    leaderboard_text = "🏆 TOP 10 PLAYERS 🏆\n\n"
    for i, player in enumerate(top_players, 1):
        try:
            user_profile = await context.bot.get_chat(player.user_id)
            username = user_profile.username if user_profile.username else f"User{player.user_id}"
            leaderboard_text += f"{i}. @{username} - ${player.balance:,}\n"
        except:
            leaderboard_text += f"{i}. User{player.user_id} - ${player.balance:,}\n"
    
    await update.message.reply_text(leaderboard_text)

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the support command - ask user for their username"""
    user_id = update.effective_user.id
    
    # Check if SUPPORT_CHAT_ID is configured
    if not SUPPORT_CHAT_ID:
        logger.error("SUPPORT_CHAT_ID is not set in environment variables")
        await update.message.reply_text(
            "❌ Support feature is currently unavailable. "
            "Please contact the administrator directly."
        )
        return
    
    # Store that user is in support mode
    context.user_data['awaiting_support'] = True
    
    await update.message.reply_text(
        "🆘 **Support Request** 🆘\n\n"
        "Please enter your username or any message for our support team. "
        "Our admins will contact you shortly.\n\n"
        "💡 **Tip:** Include your username if you haven't set one in Telegram yet."
    )

async def handle_support_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the user's support message and forward it to the support group"""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # Check if user is in support mode
    if context.user_data.get('awaiting_support'):
        # Check if SUPPORT_CHAT_ID is configured
        if not SUPPORT_CHAT_ID:
            await update.message.reply_text(
                "❌ Support feature is currently unavailable. "
                "Please try again later or contact the administrator directly."
            )
            context.user_data['awaiting_support'] = False
            return
        
        try:
            # Get user information
            user = update.effective_user
            username = user.username if user.username else "No username"
            first_name = user.first_name if user.first_name else "No first name"
            last_name = user.last_name if user.last_name else "No last name"
            
            # Create support message
            support_message = (
                "🚨 **Support Request** 🚨\n"
                f"👤 User: {first_name} {last_name}\n"
                f"📛 Username: @{username}\n"
                f"🆔 User ID: `{user_id}`\n"
                f"💬 Message: {user_message}\n"
                f"⏰ Time: {update.message.date.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            # Send to support group
            await context.bot.send_message(
                chat_id=SUPPORT_CHAT_ID,
                text=support_message,
                parse_mode='Markdown'
            )
            
            # Confirm to user
            await update.message.reply_text(
                "✅ **Message Sent Successfully!**\n\n"
                "Your message has been forwarded to our support team. "
                "We'll contact you shortly via Telegram.\n\n"
                "Thank you for your patience! 🙏"
            )
            
            # Reset support mode
            context.user_data['awaiting_support'] = False
            
        except Exception as e:
            logger.error(f"Error sending support message: {e}")
            await update.message.reply_text(
                "❌ **Error Sending Message**\n\n"
                "Sorry, there was an error sending your message to support. "
                "Please try again later or contact the administrator directly."
            )
            context.user_data['awaiting_support'] = False
    else:
        # If not in support mode, process as normal message
        await handle_message(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages that are not commands."""
    await update.message.reply_text(
        "🎮 I'm a gaming bot! Here's what you can do:\n\n"
        "🎮 /play - Start playing games\n"
        "💰 /balance - Check your balance\n"
        "🎁 /daily - Claim daily bonus\n"
        "🏆 /leaderboard - See top players\n"
        "🆘 /support - Contact support\n"
        "ℹ️ /start - Show welcome message"
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors and handle them gracefully."""
    logger.error(f"Exception while handling an update: {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ An error occurred. Please try again later."
        )

def main():
    """Start the bot."""
    # Check for required environment variables
    if not BOT_TOKEN:
        print("❌ ERROR: BOT_TOKEN environment variable is required!")
        print("💡 Please set BOT_TOKEN in your Render environment variables")
        print("📝 Go to your Render dashboard -> Environment -> Add BOT_TOKEN")
        return
    
    if not SUPPORT_CHAT_ID:
        print("⚠️  WARNING: SUPPORT_CHAT_ID environment variable not set.")
        print("💡 Support feature will not work until you set SUPPORT_CHAT_ID in Render")
        print("📝 Go to your Render dashboard -> Environment -> Add SUPPORT_CHAT_ID")
    
    # Create Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("play", play_game))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("daily", daily_bonus))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("support", support))
    
    # Add callback query handler for game selection
    application.add_handler(CallbackQueryHandler(handle_game_selection))
    
    # Add message handlers - support messages first
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_support_message
    ))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the Bot
    print("🤖 Bot is starting...")
    print(f"✅ Bot Token: {'Set' if BOT_TOKEN else 'Not Set'}")
    print(f"✅ Support Chat ID: {'Set' if SUPPORT_CHAT_ID else 'Not Set'}")
    if SUPPORT_CHAT_ID:
        print(f"📋 Support Chat ID Value: {SUPPORT_CHAT_ID}")
    print("🚀 Bot is running...")
    
    # FIXED: Remove the problematic parameter for python-telegram-bot v20+
    application.run_polling()

if __name__ == '__main__':
    main()

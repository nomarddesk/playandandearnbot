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
from openai import OpenAI

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
if SUPPORT_CHAT_ID:
    print(f"SUPPORT_CHAT_ID value: {SUPPORT_CHAT_ID}")
print("=" * 50)

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

HELPFUL_CHANNEL_LINK = "https://t.me/rejoinsnousetgagne"

# Define states
SELECT_LANG, MAIN_MENU, EXISTING_PLAYER_FLOW, NEW_PLAYER_FLOW, SUPPORT_FLOW, USERNAME_COLLECTION, AI_ASSISTED_FLOW = range(7)

# Codes for the game
GAME_CODES = [
    "6086-7221-0564",
    "2753-4695-7191", 
    "9689-1352-5966",
    "4563-6624-9460",
    "4828-9033-2281"]

# --- LANGUAGE STRINGS (UPDATED with AI assistance) ---
STRINGS = {
    'en': {
        # ... (keep all existing English strings the same) ...
        'ai_assistance_btn': "🤖 AI Assistance",
        'ai_welcome': "I'm your AI assistant! I can help answer your questions, provide guidance, and suggest the best next steps based on your situation. What would you like to know?",
        'ai_thinking': "🤔 Let me think about that...",
        'ai_suggestion': "💡 Based on your situation, I suggest:",
        'ai_question': "❓ Question:",
        'ai_continue': "Continue with AI assistance",
        'ai_go_back': "⬅️ Back to regular flow",
    },
    'fr': {
        # ... (keep all existing French strings the same) ...
        'ai_assistance_btn': "🤖 Assistance IA",
        'ai_welcome': "Je suis votre assistant IA ! Je peux répondre à vos questions, fournir des conseils et suggérer les meilleures prochaines étapes en fonction de votre situation. Que voudriez-vous savoir ?",
        'ai_thinking': "🤔 Laissez-moi réfléchir à cela...",
        'ai_suggestion': "💡 En fonction de votre situation, je suggère :",
        'ai_question': "❓ Question :",
        'ai_continue': "Continuer avec l'assistance IA",
        'ai_go_back': "⬅️ Retour au flux normal",
    }}

# --- AI ASSISTANCE FUNCTIONS ---
async def generate_ai_suggestion(user_context: dict, current_question: str, user_response: str, lang: str) -> dict:
    """
    Generate AI-powered suggestions based on user context and responses
    """
    if not openai_client:
        logger.warning("OpenAI client not available - returning default response")
        return {
            "suggestion": "Please check our channel for more guidance." if lang == 'en' else "Veuillez consulter notre canal pour plus de conseils.",
            "next_question": None,
            "should_redirect": True
        }
    
    try:
        # Build conversation context
        conversation_history = user_context.get('conversation_history', [])
        flow_type = user_context.get('flow_type', 'general')
        
        # Prepare system prompt based on language and flow type
        system_prompt = f"""You are a helpful gaming assistant for Fortnite and cloud gaming. The user is communicating in {lang.upper()}.
        
Current flow: {flow_type}
User's response: "{user_response}"
Current question: "{current_question}"

Based on the user's response and the conversation context, provide:
1. A helpful suggestion or guidance
2. A follow-up question if needed
3. Whether to redirect to specific resources

Respond in JSON format with:
- "suggestion": helpful text guidance
- "next_question": next question to ask (or null if none)
- "should_redirect": boolean indicating if user should be redirected to channel
- "confidence": confidence score (0-1) in your assessment

Keep responses concise and helpful."""
        
        # Add recent conversation context
        messages = [{"role": "system", "content": system_prompt}]
        for msg in conversation_history[-6:]:  # Last 6 messages for context
            messages.append(msg)
        
        messages.append({"role": "user", "content": f"Current situation: {current_question}\nMy response: {user_response}"})
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Parse JSON response
        try:
            return json.loads(ai_response)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            logger.warning("Failed to parse AI response as JSON, using fallback")
            return {
                "suggestion": ai_response,
                "next_question": "Would you like more specific help with this issue?" if lang == 'en' else "Souhaitez-vous une aide plus spécifique pour ce problème ?",
                "should_redirect": False,
                "confidence": 0.5
            }
            
    except Exception as e:
        logger.error(f"Error generating AI suggestion: {e}")
        return {
            "suggestion": "I'm having trouble processing your request. Please try again or check our channel for guidance." if lang == 'en' else "Je rencontre des difficultés à traiter votre demande. Veuillez réessayer ou consulter notre canal pour obtenir des conseils.",
            "next_question": None,
            "should_redirect": True
        }

async def analyze_user_progress(user_context: dict, lang: str) -> str:
    """
    Analyze user's progress and provide personalized recommendations
    """
    if not openai_client:
        return STRINGS[lang].get('channel_guidance', "Please check our channel for guidance.")
    
    try:
        qa_data = user_context.get('qa_data', [])
        flow_type = user_context.get('flow_type', 'general')
        
        if not qa_data:
            return "I don't have enough information about your progress yet. Please continue with the questions." if lang == 'en' else "Je n'ai pas encore assez d'informations sur votre progression. Veuillez continuer avec les questions."
        
        # Prepare analysis prompt
        system_prompt = f"""Analyze the user's progress in the {flow_type} flow and provide specific, actionable recommendations in {lang.upper()}.
        
User's Q&A history:
{chr(10).join([f"Q: {q} | A: {a}" for q, a in qa_data])}

Provide a concise analysis of:
1. What steps they've completed successfully
2. Where they might be stuck
3. Specific next steps they should take
4. Any common mistakes to avoid

Keep it encouraging and practical."""
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": system_prompt}],
            temperature=0.7,
            max_tokens=400
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"Error analyzing user progress: {e}")
        return "I'm unable to analyze your progress right now. Please continue with the guided flow." if lang == 'en' else "Je ne peux pas analyser votre progression pour le moment. Veuillez continuer avec le flux guidé."

# --- UPDATED HELPER FUNCTIONS ---
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str = None):
    """Helper function to show the main menu in the user's language."""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    keyboard = [
        [InlineKeyboardButton(s['new_player_btn'], callback_data="new_player_start")],
        [InlineKeyboardButton(s['existing_player_btn'], callback_data="existing_player_start")],
        [InlineKeyboardButton(s['helpful_channel_btn'], callback_data="helpful_channel")],
        [InlineKeyboardButton(s['support_btn'], callback_data="contact_support")],
        [InlineKeyboardButton(s['ai_assistance_btn'], callback_data="ai_assistance_start")],  # New AI assistance button
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

# --- AI ASSISTANCE FLOW ---
async def ai_assistance_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start AI assistance flow"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Initialize AI conversation context
    context.user_data['ai_conversation'] = {
        'history': [],
        'flow_type': 'ai_assistance',
        'qa_data': []
    }
    
    # Store initial message
    context.user_data['ai_conversation']['history'].append({
        "role": "assistant", 
        "content": s['ai_welcome']
    })
    
    keyboard = [
        [InlineKeyboardButton(s['new_player_btn'], callback_data="ai_new_player")],
        [InlineKeyboardButton(s['existing_player_btn'], callback_data="ai_existing_player")],
        [InlineKeyboardButton(s['support_btn'], callback_data="ai_support")],
        [InlineKeyboardButton(s['back_btn'], callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        text=s['ai_welcome'],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return AI_ASSISTED_FLOW

async def handle_ai_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle AI assistance category choice"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    choice = query.data
    ai_context = context.user_data.get('ai_conversation', {})
    
    # Map choices to flow types
    flow_map = {
        'ai_new_player': 'new_player',
        'ai_existing_player': 'existing_player', 
        'ai_support': 'support'
    }
    
    ai_context['flow_type'] = flow_map.get(choice, 'general')
    ai_context['history'].append({
        "role": "user",
        "content": f"User selected: {choice}"
    })
    
    # Generate AI suggestion based on choice
    thinking_msg = await query.edit_message_text(text=s['ai_thinking'])
    
    ai_suggestion = await generate_ai_suggestion(
        ai_context,
        f"User is interested in {ai_context['flow_type']} assistance",
        "Just starting",
        lang
    )
    
    # Build response
    response_text = f"{s['ai_suggestion']}\n\n{ai_suggestion['suggestion']}"
    
    if ai_suggestion.get('next_question'):
        response_text += f"\n\n{s['ai_question']} {ai_suggestion['next_question']}"
        # Store the current question for context
        ai_context['current_question'] = ai_suggestion['next_question']
    
    keyboard = []
    if ai_suggestion.get('should_redirect'):
        keyboard.append([InlineKeyboardButton(s['join_channel_btn'], url=HELPFUL_CHANNEL_LINK)])
    else:
        keyboard.append([InlineKeyboardButton(s['ai_continue'], callback_data="ai_continue_chat")])
    
    keyboard.append([InlineKeyboardButton(s['ai_go_back'], callback_data="ai_assistance_start")])
    
    await thinking_msg.edit_text(
        text=response_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    # Store AI response in history
    ai_context['history'].append({
        "role": "assistant",
        "content": response_text
    })
    
    return AI_ASSISTED_FLOW

async def ai_continue_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Continue AI conversation with free-form input"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    await query.edit_message_text(
        text="Please type your question or describe what you need help with:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(s['ai_go_back'], callback_data="ai_assistance_start")]])
    )
    
    context.user_data['awaiting_ai_input'] = True
    return AI_ASSISTED_FLOW

async def handle_ai_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process user's free-form message to AI"""
    if not context.user_data.get('awaiting_ai_input'):
        return AI_ASSISTED_FLOW
        
    user_message = update.message.text
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    ai_context = context.user_data.get('ai_conversation', {})
    
    # Add user message to history
    ai_context['history'].append({
        "role": "user",
        "content": user_message
    })
    
    # Show thinking message
    thinking_msg = await update.message.reply_text(s['ai_thinking'])
    
    # Generate AI response
    current_question = ai_context.get('current_question', 'General assistance')
    ai_suggestion = await generate_ai_suggestion(
        ai_context,
        current_question,
        user_message,
        lang
    )
    
    # Build response
    response_text = f"{ai_suggestion['suggestion']}"
    
    if ai_suggestion.get('next_question'):
        response_text += f"\n\n{s['ai_question']} {ai_suggestion['next_question']}"
        ai_context['current_question'] = ai_suggestion['next_question']
    
    keyboard = []
    if ai_suggestion.get('should_redirect'):
        keyboard.append([InlineKeyboardButton(s['join_channel_btn'], url=HELPFUL_CHANNEL_LINK)])
    else:
        keyboard.append([InlineKeyboardButton(s['ai_continue'], callback_data="ai_continue_chat")])
    
    keyboard.append([InlineKeyboardButton(s['ai_go_back'], callback_data="ai_assistance_start")])
    
    await thinking_msg.edit_text(
        text=response_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    # Store AI response in history
    ai_context['history'].append({
        "role": "assistant",
        "content": response_text
    })
    
    context.user_data['awaiting_ai_input'] = False
    return AI_ASSISTED_FLOW

# --- ENHANCED EXISTING FLOWS WITH AI SUGGESTIONS ---
async def enhanced_show_suggestion(update: Update, context: ContextTypes.DEFAULT_TYPE, question: str, user_response: str, flow_type: str) -> None:
    """
    Enhanced function to show AI suggestions during existing flows
    """
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Prepare user context for AI
    user_context = {
        'flow_type': flow_type,
        'conversation_history': context.user_data.get(f'{flow_type}_conversation', []),
        'qa_data': context.user_data.get(f'{flow_type}_qa', [])
    }
    
    # Generate AI suggestion
    ai_suggestion = await generate_ai_suggestion(user_context, question, user_response, lang)
    
    if ai_suggestion and ai_suggestion.get('suggestion'):
        suggestion_text = f"\n\n💡 {s['ai_suggestion']} {ai_suggestion['suggestion']}"
        
        # Send suggestion as a separate message
        query = update.callback_query
        if query:
            await query.message.reply_text(suggestion_text)
        else:
            await update.message.reply_text(suggestion_text)
        
        # Store in conversation history
        if f'{flow_type}_conversation' not in context.user_data:
            context.user_data[f'{flow_type}_conversation'] = []
        
        context.user_data[f'{flow_type}_conversation'].extend([
            {"role": "user", "content": f"Q: {question} | A: {user_response}"},
            {"role": "assistant", "content": ai_suggestion['suggestion']}
        ])

# --- MODIFIED EXISTING HANDLERS TO INCLUDE AI SUGGESTIONS ---
# Example modification for one handler - apply similar pattern to other handlers
async def new_q1_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q1 - Yes -> Q2 with AI suggestion"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store Q&A
    if not context.user_data['new_player_qa'] or context.user_data['new_player_qa'][-1][0] != context.user_data.get('new_q1_text'):
        context.user_data['new_player_qa'].append((context.user_data.get('new_q1_text', s['new_player_intro'].split('\n')[-1]), "Yes"))
    
    # Show AI suggestion
    await enhanced_show_suggestion(
        update, context, 
        context.user_data.get('new_q1_text', "VPN usage"), 
        "Yes", 
        "new_player"
    )
    
    context.user_data['new_q2_text_key'] = 'new_q2_text'
    text = s['new_q2_text']
    
    keyboard = [
        [InlineKeyboardButton(s['a_yes'], callback_data="new_q2_yes")],
        [InlineKeyboardButton(s['b_no'], callback_data="new_q2_no")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="new_player_start")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q1_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q1 - No -> Ask if they finally used VPN with AI suggestion"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store Q&A
    if not context.user_data['new_player_qa'] or context.user_data['new_player_qa'][-1][0] != context.user_data.get('new_q1_text'):
        context.user_data['new_player_qa'].append((context.user_data.get('new_q1_text', s['new_player_intro'].split('\n')[-1]), "No"))
    
    # Show AI suggestion
    await enhanced_show_suggestion(
        update, context,
        context.user_data.get('new_q1_text', "VPN usage"),
        "No",
        "new_player"
    )
    
    text = s['vpn_reminder']
    
    keyboard = [
        [InlineKeyboardButton(s['b_1_if_yes'], callback_data="new_q2_yes_from_q1_no")],
        [InlineKeyboardButton(s['b_2_if_no'], callback_data="new_channel_forward")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="new_player_start")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

# Add similar enhanced_show_suggestion calls to other key handlers...

# --- UPDATED MAIN FUNCTION ---
def main() -> None:
    """Run the bot."""
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
                CallbackQueryHandler(support_start, pattern="^contact_support$"),
                CallbackQueryHandler(ai_assistance_start, pattern="^ai_assistance_start$"),  # New AI assistance
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
            AI_ASSISTED_FLOW: [
                CallbackQueryHandler(handle_ai_choice, pattern="^ai_(new_player|existing_player|support)$"),
                CallbackQueryHandler(ai_continue_chat, pattern="^ai_continue_chat$"),
                CallbackQueryHandler(ai_assistance_start, pattern="^ai_assistance_start$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_message),
            ],
            EXISTING_PLAYER_FLOW: [
                # ... (keep all existing existing player handlers) ...
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
            NEW_PLAYER_FLOW: [
                # ... (keep all existing new player handlers) ...
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
            SUPPORT_FLOW: [
                # ... (keep all existing support handlers) ...
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
    print(f"✅ OPENAI_API_KEY: {'Set' if OPENAI_API_KEY else 'Not Set'}")
    if SUPPORT_CHAT_ID:
        print(f"📋 SUPPORT_CHAT_ID Value: {SUPPORT_CHAT_ID}")
    print("🚀 Bot is running with AI assistance...")
    
    application.run_polling()

if __name__ == "__main__":
    main()

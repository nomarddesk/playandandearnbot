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
    filters,
)

# Import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI package not available. AI features will be disabled.")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
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

# Initialize OpenAI client
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
    "4828-9033-2281"
]

# --- COMPLETE FLOW KNOWLEDGE BASE ---
BOT_KNOWLEDGE_BASE = """
FORTNITE CLOUD GAMING BOT - COMPLETE FLOW KNOWLEDGE

GAME CODES FOR REWARD ISLAND:
{game_codes}

IMPORTANT LINKS:
- Cloud Gaming Profile: https://www.xbox.com/fr-FR/play/games/fortnite/BT5P2X999VH2
- Epic Games Activation: http://epicgames.com/activate
- Epic Games Profile: epicgames.com
- Game Launch: https://www.xbox.com/fr-FR/play/games/fortnite/BT5P2X999VH2
- Help Channel: {channel_link}

EXISTING PLAYER FLOW:

INTRO: Because you are playing on the cloud, your session will last for 1 hour. The game will close, and you will have to launch it again to keep playing. You probably know it cause you already follow all the instructions.

QUESTION 1: Have you searched and found the reward Island?
- A Yes → QUESTION 2
- B No → "you have to search the reward Island in the search bar and just choose it, do you want our guidance for that?"
  - B-1 Yes I want the best codes to play → SHOW CODES: "just copy one of them and enter it on the search bar" → QUESTION 2
  - B-2 No, I already choosed one code → QUESTION 2

QUESTION 2: Did you follow the full setup to be able to play with friends and earn a lot together without any worries?
- A Yes, I'm ready for the next step → QUESTION 3
- B No → "you have to follow the exact setup, do you need our guidance?"
  - B-1 Yes → FORWARD TO CHANNEL instruction 9
  - B-2 No I finally fix everything, I want to move to the next step → QUESTION 3

QUESTION 3: Did you start the game and play 130 hours for free this week?
- A Yes → QUESTION 4
- B No → "you have to start the game and play every single day for free before aiming for the reward, are you able to play at least 130 hours a week?"
  - B-1 Yes → QUESTION 4
  - B-2 No → FORWARD TO CHANNEL instruction 10

QUESTION 4: With your existing account, will you click on the like button every single time before your 1 hour play session ended during your 130 hours of play this week?
- A Yes → QUESTION 5
- B No → "You have to click on the like button every single time before your 1 hour play session ended during your 130 hours a week, do you want our guidance on that?"
  - B-1 Yes → FORWARD TO CHANNEL instruction 11
  - B-2 No → "I will play and let you know in the support session later on" → QUESTION 5

QUESTION 5: Did you save the reward Island to your favorites?
- A Yes → QUESTION 6
- B No → "you have to save the reward Island to your favorites and play, do you want our guidance on that?"
  - B-1 Yes → FORWARD TO CHANNEL instruction 12
  - B-2 No, I have proof I saved the reward Island to my favorites and I actually play on it → QUESTION 6

QUESTION 6: Were you introduced to this game by an influencer?
- A Yes → "provide the name please:" → COLLECT USERNAME
- B No → FORWARD TO CHANNEL instruction 13

NEW PLAYER FLOW:

INTRO: You're diving into an immersive gaming adventure. This bot will help you set up your account, join the game, start playing and earning. Because you are playing on the cloud, your session will last for 1 hour. The game will close, and you will have to launch it again to keep playing.

QUESTION 1: Did you use a VPN?
- A If yes → QUESTION 2
- B If no → "please download and use a VPN in USA before going any further to create all your authentic profiles but to play you don't use it. Did you finally use a VPN?"
  - B-1 If yes → QUESTION 2
  - B-2 if no → FORWARD TO CHANNEL

QUESTION 2: Did you already create a cloud gaming profile?
- A if yes → QUESTION 3
- B if no → "please create a cloud gaming profile. Do you want our assistance?"
  - B-1 Yes → PROVIDE LINK: https://www.xbox.com/fr-FR/play/games/fortnite/BT5P2X999VH2
  - B-2 No I already have one, I want the next step → QUESTION 3

QUESTION 3: Did you receive the code from epic games to activate your cloud gaming account?
- A Yes I received the code, I want the next step → QUESTION 4
- B No → "please you have to receive the code, do you want our guidance to help you with that?"
  - B-1 Yes → PROVIDE LINK: http://epicgames.com/activate
  - B-2 No → FORWARD TO CHANNEL

QUESTION 4: Did you create your epic games profile?
- A Yes → QUESTION 5
- B No → "please you have to create your epic games profile, do you need our guidance?"
  - B-1 Yes → PROVIDE LINK: epicgames.com
  - B-2 No → FORWARD TO CHANNEL

QUESTION 5: Did you create a shortcut of the cloud gaming to play it like an installed app directly from your Homescreen?
- A Yes → QUESTION 6
- B No → "You have to create a shortcut to play fortnite from your homescreen, do you want our guidance with that?"
  - B-1 yes I want to see it in the channel → FORWARD TO CHANNEL
  - B-2 No I finally create a shortcut → QUESTION 6

QUESTION 6: Have you launched the game?
- A Yes → QUESTION 7
- B No → "you have to launch the game, do you need our guidance?"
  - B-1 Yes → PROVIDE LINK: https://www.xbox.com/fr-FR/play/games/fortnite/BT5P2X999VH2
  - B-2 No → FORWARD TO CHANNEL

QUESTION 7: Have you searched and found the reward Island?
- A Yes → QUESTION 8
- B No → "you have to search the reward Island in the search bar and just choose it, do you want our guidance for that?"
  - B-1 Yes I want the best codes to play → SHOW CODES: "just copy one of them and enter it on the search bar" → QUESTION 8
  - B-2 No, I already choosed one code → QUESTION 8

QUESTION 8: Did you follow the full setup to be able to play with friends and earn a lot together without any worries?
- A Yes, I'm ready for the next step → QUESTION 9
- B No → "you have to follow the exact setup, do you need our guidance?"
  - B-1 Yes → FORWARD TO CHANNEL
  - B-2 No I finally fix everything, I want to move to the next step → QUESTION 9

QUESTION 9: Will you start the game and play 130 hours for free this week?
- A Yes → QUESTION 10
- B No → "you have to start the game and play every single day for free before aiming for the reward, are you able to play at least 130 hours a week?"
  - B-1 Yes → QUESTION 10
  - B-2 No → FORWARD TO CHANNEL

QUESTION 10: With your new account, will you click on the like button every single time before your 1 hour play session ended during your 130 hours of play this week?
- A Yes → QUESTION 11
- B No → "You have to click on the like button every single time before your 1 hour play session ended during your 130 hours a week, do you want our guidance on that?"
  - B-1 Yes → FORWARD TO CHANNEL
  - B-2 No → "I will play and let you know in the support session later on" → QUESTION 11

QUESTION 11: Will you save the reward Island to your favorites?
- A Yes → QUESTION 12
- B No → "you have to save the reward Island to your favorites and play, do you want our guidance on that?"
  - B-1 Yes → FORWARD TO CHANNEL
  - B-2 No, I have proof I saved the reward Island to my favorites and I actually play on it → QUESTION 12

QUESTION 12: Were you introduced to this game by an influencer?
- A Yes → "provide the name please:" → COLLECT USERNAME
- B No → FORWARD TO CHANNEL

SUPPORT FLOW:

INTRO: In order to get in touch with us, you need to answer these questions so we can determine which stage of the process you're at. If everything has been done correctly, you'll be able to claim your reward 💰💰

QUESTION 1: Did you use a VPN?
- A If yes → QUESTION 2
- B If no → "please download and use a VPN in USA before going any further to create all your authentic profiles but to play you don't use it. Did you finally use a VPN?"
  - B-1 If yes → QUESTION 2
  - B-2 if no → FORWARD TO CHANNEL (NO BACK BUTTONS)

QUESTION 2: Did you already create a cloud gaming profile?
- A if yes → QUESTION 3
- B if no → "please create a cloud gaming profile. Do you want our assistance?"
  - B-1 Yes → PROVIDE LINK: https://www.xbox.com/fr-FR/play/games/fortnite/BT5P2X999VH2 → QUESTION 3
  - B-2 No I already have one, I want the next step → QUESTION 3

QUESTION 3: Did you receive the code from epic games to activate your cloud gaming account?
- A Yes I received the code, I want the next step → QUESTION 4
- B No → "please you have to receive the code, do you want our guidance to help you with that?"
  - B-1 Yes → PROVIDE LINK: http://epicgames.com/activate → QUESTION 4
  - B-2 No → FORWARD TO CHANNEL (NO BACK BUTTONS)

QUESTION 4: Did you create your epic games profile?
- A Yes → QUESTION 5
- B No → "please you have to create your epic games profile, do you want our guidance?"
  - B-1 Yes → PROVIDE LINK: epicgames.com → QUESTION 5
  - B-2 No → FORWARD TO CHANNEL (NO BACK BUTTONS)

QUESTION 5: Did you create a shortcut of the cloud gaming to play it like an installed app directly from your Homescreen?
- A Yes → QUESTION 6
- B No → "You have to create a shortcut to play fortnite from your homescreen, do you want our guidance with that?"
  - B-1 yes I want to see it in the channel → FORWARD TO CHANNEL (NO BACK BUTTONS)
  - B-2 No I finally create a shortcut → QUESTION 6

QUESTION 6: Have you launched the game?
- A Yes → QUESTION 7
- B No → "you have to launch the game, do you need our guidance?"
  - B-1 Yes → PROVIDE LINK: https://www.xbox.com/fr-FR/play/games/fortnite/BT5P2X999VH2 → QUESTION 7
  - B-2 No → FORWARD TO CHANNEL (NO BACK BUTTONS)

QUESTION 7: Have you searched and found the reward Island?
- A Yes → QUESTION 8
- B No → "you have to search the reward Island in the search bar and just choose it, do you want our guidance for that?"
  - B-1 Yes I want the best codes to play → SHOW CODES: "just copy one of them and enter it on the search bar" → QUESTION 8
  - B-2 No, I already choosed one code → QUESTION 8

QUESTION 8: Did you follow the full setup to be able to play with friends and earn a lot together without any worries?
- A Yes, I'm ready for the next step → QUESTION 9
- B No → "you have to follow the exact setup, do you need our guidance?"
  - B-1 Yes → FORWARD TO CHANNEL (NO BACK BUTTONS)
  - B-2 No I finally fix everything, I want to move to the next step → QUESTION 9

QUESTION 9: Did you start the game and play 130 hours for free this week?
- A Yes → QUESTION 10
- B No → "you have to start the game and play every single day for free before aiming for the reward, are you able to play at least 130 hours a week?"
  - B-1 Yes → QUESTION 10
  - B-2 No → FORWARD TO CHANNEL (NO BACK BUTTONS)

QUESTION 10: Did you click on the like button every single time before your 1 hour play session ended during your 130 hours of play this week?
- A Yes → QUESTION 11
- B No → "You have to click on the like button every single time before your 1 hour play session ended during your 130 hours a week, do you want our guidance on that?"
  - B-1 Yes → FORWARD TO CHANNEL (NO BACK BUTTONS)
  - B-2 No → "I have proof that I played 130 hours this week and I liked every single time, and I am wishing to share it with you guys" → QUESTION 11

QUESTION 11: Have you saved the reward Island to your favorites?
- A Yes → QUESTION 12
- B No → "you have to save the reward Island to your favorites and play, do you want our guidance on that?"
  - B-1 Yes → FORWARD TO CHANNEL (NO BACK BUTTONS)
  - B-2 No, I have proof I saved the reward Island to my favorites and I actually play on it → QUESTION 12

QUESTION 12: Were you introduced to this game by an influencer?
- A Yes → "provide the name please" → QUESTION 13
- B No → "One of the expert will review all the screenshots of the game and you will earn" → QUESTION 13

QUESTION 13: Make sure you completed every single step before sending us your @, did you completed every single step and play at least 130 hours this week?
- A Yes, I did it and I will send you all the necessary screenshots → "give us your @" → COLLECT USERNAME
- B No → FORWARD TO CHANNEL (NO BACK BUTTONS)

FINAL STEP FOR ALL FLOWS: COLLECT USERNAME
- Ask user to provide their @username
- Forward all conversation to support team
- Support team contacts user directly

RESPONSE GUIDELINES:
- Always follow the exact flow structure
- Ask one question at a time
- Provide specific guidance based on user answers
- Use appropriate links and codes when needed
- For support flow: NO BACK BUTTONS on channel forward options
- Always be helpful and encouraging
""".format(game_codes=", ".join(GAME_CODES), channel_link=HELPFUL_CHANNEL_LINK)

# --- LANGUAGE STRINGS ---
STRINGS = {
    'en': {
        'disclaimer': "**Disclaimer:** This bot is an unofficial guide and is not affiliated with Epic Games or Fortnite. We will *never* ask for your password.",
        'lang_prompt': "Please select your language:",
        'welcome': "🤖 **AI-Powered Gaming Assistant**\n\nWelcome! I'm your intelligent assistant for Fortnite cloud gaming setup and rewards. I can help you with:\n\n• New player setup\n• Existing player optimization\n• Technical support\n• Reward system guidance\n\nJust type your question or use the menu below!",
        'new_player_btn': "🎮 New Player Setup",
        'existing_player_btn': "⚡ Existing Player",
        'helpful_channel_btn': "📚 Full Guide",
        'support_btn': "🆘 Support",
        'lang_btn': "🌐 Language",
        'helpful_channel_text': "Join our Telegram channel for complete guides and community:",
        'join_channel_btn': "Join Channel",
        'back_btn': "⬅️ Back",
        'ai_thinking': "🤔 Analyzing your question...",
        'ai_continue': "💬 Continue",
        'ai_menu': "📱 Menu",
        'provide_username': "Please provide your @username so our support team can contact you directly:",
        'username_saved': "Thank you! Your username has been saved. Our support team will contact you shortly.",
        'invalid_username': "Please provide a valid @username starting with @",
    },
    'fr': {
        'disclaimer': "**Avertissement :** Ce bot est un guide non officiel et n'est pas affilié à Epic Games ou Fortnite. Nous ne vous demanderons *jamais* votre mot de passe.",
        'lang_prompt': "Veuillez sélectionner votre langue :",
        'welcome': "🤖 **Assistant de Jeu IA**\n\nBienvenue ! Je suis votre assistant intelligent pour la configuration du jeu cloud Fortnite et les récompenses. Je peux vous aider avec :\n\n• Configuration nouveau joueur\n• Optimisation joueur existant\n• Support technique\n• Guide du système de récompenses\n\nTapez simplement votre question ou utilisez le menu ci-dessous !",
        'new_player_btn': "🎮 Nouveau Joueur",
        'existing_player_btn': "⚡ Joueur Existant",
        'helpful_channel_btn': "📚 Guide Complet",
        'support_btn': "🆘 Support",
        'lang_btn': "🌐 Langue",
        'helpful_channel_text': "Rejoignez notre canal Telegram pour des guides complets et la communauté :",
        'join_channel_btn': "Rejoindre le Canal",
        'back_btn': "⬅️ Retour",
        'ai_thinking': "🤔 Analyse de votre question...",
        'ai_continue': "💬 Continuer",
        'ai_menu': "📱 Menu",
        'provide_username': "Veuillez fournir votre @nomdutilisateur pour que notre équipe de support puisse vous contacter directement :",
        'username_saved': "Merci ! Votre nom d'utilisateur a été enregistré. Notre équipe de support vous contactera sous peu.",
        'invalid_username': "Veuillez fournir un @nomdutilisateur valide commençant par @",
    }
}

# --- ENHANCED SUPPORT MESSAGE FUNCTION ---
async def send_to_support(update: Update, context: ContextTypes.DEFAULT_TYPE, username: str):
    """Send comprehensive user information and conversation summary to support team"""
    if not SUPPORT_CHAT_ID:
        logger.error("SUPPORT_CHAT_ID not set")
        return False
    
    try:
        user = update.effective_user
        user_data = context.user_data
        
        # Get conversation history for context
        conversation_history = user_data.get('conversation_history', [])
        current_flow = user_data.get('current_flow', 'unknown')
        flow_type = user_data.get('flow_type', 'unknown')
        current_question = user_data.get('current_question', 1)
        
        # Create conversation summary (last 8 messages for context)
        conversation_summary = ""
        if conversation_history:
            recent_messages = conversation_history[-8:]  # Last 8 messages for context
            conversation_summary = "**📝 Conversation Summary:**\n"
            for i, msg in enumerate(recent_messages):
                role = "👤 User" if msg['role'] == 'user' else "🤖 Bot"
                content = msg['content']
                # Truncate very long messages but keep important context
                if len(content) > 150:
                    content = content[:150] + "..."
                conversation_summary += f"{i+1}. {role}: {content}\n"
        
        # Create comprehensive support message
        support_message = f"""
🚨 **SUPPORT REQUEST - USER NEEDS ASSISTANCE** 🚨

**👤 USER INFORMATION:**
• **Name:** {user.first_name} {user.last_name or ''}
• **Telegram Username:** @{user.username or 'Not set'}
• **Provided Contact:** {username}
• **User ID:** `{user.id}`
• **Language:** {user_data.get('lang', 'en').upper()}

**📊 PROGRESS STATUS:**
• **Flow Type:** {flow_type.title() if flow_type != 'unknown' else 'General'}
• **Current Flow:** {current_flow.replace('_', ' ').title()}
• **Current Question:** {current_question}
• **Total Messages:** {len(conversation_history)}

{conversation_summary}

**🎯 ACTION REQUIRED:**
Please contact this user directly on Telegram using the provided username.
They have completed the questionnaire and are ready for personalized support.

**⏰ TIMESTAMP:** {update.message.date.strftime('%Y-%m-%d %H:%M:%S UTC')}

**💡 QUICK ACTIONS:**
• Click the username to message: {username}
• User ID for reference: `{user.id}`
• User's language: {user_data.get('lang', 'en').upper()}
        """
        
        await context.bot.send_message(
            chat_id=SUPPORT_CHAT_ID,
            text=support_message,
            parse_mode='Markdown'
        )
        
        logger.info(f"📤 Comprehensive support request sent for user {user.id} - Username: {username}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error sending to support: {e}")
        return False

# --- AI BRAIN CORE FUNCTION ---
async def ai_brain_response(user_message: str, user_context: dict, lang: str) -> dict:
    """
    AI Brain: Processes all user messages and provides intelligent responses
    using the complete bot knowledge base.
    """
    if not openai_client:
        return {
            "response": "I'm currently unavailable. Please try again later.",
            "buttons": ["Menu"],
            "next_action": "menu"
        }
    
    try:
        # Get conversation history
        conversation_history = user_context.get('conversation_history', [])
        current_flow = user_context.get('current_flow', 'general')
        current_question = user_context.get('current_question', 1)
        
        # Prepare system prompt with complete knowledge
        system_prompt = f"""You are the AI brain of a Fortnite cloud gaming Telegram bot. Use this complete knowledge base:

{BOT_KNOWLEDGE_BASE}

CURRENT CONTEXT:
- Language: {lang.upper()}
- Current Flow: {current_flow}
- Current Question: {current_question}
- User's Message: "{user_message}"

RESPONSE REQUIREMENTS:
1. Analyze the user's message within the context of the current flow and question
2. Follow the exact flow structure provided in the knowledge base
3. Ask the next appropriate question based on user's answer
4. Provide specific guidance, links, or codes when needed
5. For support flow: NO BACK BUTTONS on channel forward options
6. Be conversational but follow the structured flow
7. Move to username collection when user completes a flow
8. If unsure, ask clarifying questions

RESPONSE FORMAT (JSON):
{{
    "response": "Your response following the flow structure",
    "buttons": ["Option A", "Option B", "Menu", "Continue"],
    "next_question": next_question_number,
    "next_flow": "same/new_flow",
    "action": "ask_question/show_codes/provide_link/forward_channel/collect_username",
    "data": "link_or_codes_if_needed"
}}

Available button patterns:
- For choices: ["A Yes", "B No"] 
- For navigation: ["Menu", "Continue"]
- For channel: ["Join Channel"]
- Always include "Menu" for navigation"""

        # Build message history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent conversation history for context
        for msg in conversation_history[-6:]:
            messages.append(msg)
        
        messages.append({"role": "user", "content": user_message})
        
        # Generate AI response
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=800
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Parse JSON response
        try:
            return json.loads(ai_response)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            logger.warning("AI response not in JSON format, using fallback")
            return {
                "response": ai_response,
                "buttons": ["Menu", "Continue"],
                "next_question": current_question,
                "next_flow": current_flow,
                "action": "ask_question"
            }
            
    except Exception as e:
        logger.error(f"Error in AI brain: {e}")
        return {
            "response": "I'm having trouble processing your request. Please try again.",
            "buttons": ["Menu"],
            "next_question": 1,
            "next_flow": "general",
            "action": "ask_question"
        }

# --- CORE MESSAGE HANDLER ---
async def handle_any_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Main message handler - ALL text messages go through the AI brain
    """
    user_message = update.message.text
    user_id = update.message.from_user.id
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Check if we're collecting username
    if context.user_data.get('collecting_username'):
        if user_message.startswith('@') and len(user_message) > 1:
            # Send comprehensive support message
            success = await send_to_support(update, context, user_message)
            if success:
                await update.message.reply_text(s['username_saved'])
            else:
                await update.message.reply_text("Thank you! We've noted your username. Support will contact you soon.")
            
            context.user_data['collecting_username'] = False
            return await show_main_menu(update, context)
        else:
            await update.message.reply_text(s['invalid_username'])
            return USERNAME_COLLECTION
    
    # Show thinking indicator
    thinking_msg = await update.message.reply_text(s['ai_thinking'])
    
    # Prepare user context for AI
    user_context = {
        'conversation_history': context.user_data.get('conversation_history', []),
        'current_flow': context.user_data.get('current_flow', 'general'),
        'current_question': context.user_data.get('current_question', 1),
        'user_data': {
            'user_id': user_id,
            'language': lang,
            'flow_type': context.user_data.get('flow_type', 'unknown')
        }
    }
    
    # Get AI brain response
    ai_response = await ai_brain_response(user_message, user_context, lang)
    
    # Update conversation history
    if 'conversation_history' not in context.user_data:
        context.user_data['conversation_history'] = []
    
    context.user_data['conversation_history'].append({"role": "user", "content": user_message})
    context.user_data['conversation_history'].append({"role": "assistant", "content": ai_response['response']})
    
    # Keep only last 20 messages to manage context size
    context.user_data['conversation_history'] = context.user_data['conversation_history'][-20:]
    
    # Update flow and question state
    context.user_data['current_flow'] = ai_response.get('next_flow', user_context['current_flow'])
    context.user_data['current_question'] = ai_response.get('next_question', user_context['current_question'])
    
    # Handle special actions
    response_text = ai_response['response']
    
    # Add codes if action is show_codes
    if ai_response.get('action') == 'show_codes':
        codes_text = "\n".join(GAME_CODES)
        response_text += f"\n\n**Game Codes:**\n`{codes_text}`\n\nJust copy one of them and enter it on the search bar."
    
    # Add link if action is provide_link and data contains link
    if ai_response.get('action') == 'provide_link' and ai_response.get('data'):
        response_text += f"\n\n{ai_response['data']}"
    
    # Handle username collection
    if ai_response.get('action') == 'collect_username':
        context.user_data['collecting_username'] = True
        response_text += f"\n\n{s['provide_username']}"
    
    # Create keyboard from AI-suggested buttons
    keyboard = []
    buttons = ai_response.get('buttons', [])
    
    for button_text in buttons:
        if button_text.lower() in ['menu', 'accueil', '📱 menu']:
            keyboard.append([InlineKeyboardButton(s['ai_menu'], callback_data="back_to_main")])
        elif button_text.lower() in ['continue', 'continuer', '💬 continue']:
            keyboard.append([InlineKeyboardButton(s['ai_continue'], callback_data="continue_chat")])
        elif button_text.lower() in ['join channel', 'rejoindre le canal']:
            keyboard.append([InlineKeyboardButton(s['join_channel_btn'], url=HELPFUL_CHANNEL_LINK)])
        elif button_text.lower().startswith('a ') or button_text.lower().startswith('b '):
            # For A/B choices, use continue chat to maintain flow
            keyboard.append([InlineKeyboardButton(button_text, callback_data="continue_chat")])
        else:
            keyboard.append([InlineKeyboardButton(button_text, callback_data="continue_chat")])
    
    # Always include menu for navigation
    if not any(s['ai_menu'] in str(button) for row in keyboard for button in row):
        keyboard.append([InlineKeyboardButton(s['ai_menu'], callback_data="back_to_main")])
    
    # Update thinking message with actual response
    await thinking_msg.edit_text(
        text=response_text,
        reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
        parse_mode='Markdown'
    )
    
    # Handle username collection state
    if context.user_data.get('collecting_username'):
        return USERNAME_COLLECTION
    
    # Return appropriate state based on current flow
    current_flow = context.user_data.get('current_flow', 'general')
    if current_flow == 'new_player':
        return NEW_PLAYER_FLOW
    elif current_flow == 'existing_player':
        return EXISTING_PLAYER_FLOW
    elif current_flow == 'support':
        return SUPPORT_FLOW
    else:
        return MAIN_MENU

# --- HELPER FUNCTIONS ---
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str = None):
    """Show main menu"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Reset flow state
    context.user_data['current_flow'] = 'general'
    context.user_data['current_question'] = 1
    context.user_data['current_state'] = MAIN_MENU
    context.user_data['collecting_username'] = False
    
    keyboard = [
        [InlineKeyboardButton(s['new_player_btn'], callback_data="new_player_start")],
        [InlineKeyboardButton(s['existing_player_btn'], callback_data="existing_player_start")],
        [InlineKeyboardButton(s['helpful_channel_btn'], callback_data="helpful_channel")],
        [InlineKeyboardButton(s['support_btn'], callback_data="support_start")],
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
            logger.warning(f"Failed to edit message: {e}")
    else:
        await update.message.reply_text(
            text=text_to_show,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    return MAIN_MENU

async def continue_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Continue chat callback"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    await query.edit_message_text(
        text="💬 **I'm listening! Please continue with your answer or question...**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(s['ai_menu'], callback_data="back_to_main")]
        ]),
        parse_mode='Markdown'
    )
    
    return context.user_data.get('current_state', MAIN_MENU)

# --- FLOW STARTERS ---
async def new_player_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start new player flow"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['current_flow'] = 'new_player'
    context.user_data['flow_type'] = 'new_player'
    context.user_data['current_question'] = 1
    context.user_data['current_state'] = NEW_PLAYER_FLOW
    
    # Use AI to handle the flow start
    return await handle_any_message(update, context)

async def existing_player_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start existing player flow"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['current_flow'] = 'existing_player'
    context.user_data['flow_type'] = 'existing_player'
    context.user_data['current_question'] = 1
    context.user_data['current_state'] = EXISTING_PLAYER_FLOW
    
    # Use AI to handle the flow start
    return await handle_any_message(update, context)

async def support_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start support flow"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['current_flow'] = 'support'
    context.user_data['flow_type'] = 'support'
    context.user_data['current_question'] = 1
    context.user_data['current_state'] = SUPPORT_FLOW
    
    # Use AI to handle the flow start
    return await handle_any_message(update, context)

async def show_helpful_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show channel link"""
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

# --- BASIC HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start command"""
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
    """Set language"""
    query = update.callback_query
    lang = query.data
    context.user_data['lang'] = lang
    
    return await show_main_menu(update, context)

def main() -> None:
    """Run the AI-powered bot"""
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
                CallbackQueryHandler(support_start, pattern="^support_start$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
                CallbackQueryHandler(continue_chat, pattern="^continue_chat$"),
                # ALL text messages go to AI brain
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_any_message),
            ],
            NEW_PLAYER_FLOW: [
                CallbackQueryHandler(continue_chat, pattern="^continue_chat$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
                # ALL text messages go to AI brain
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_any_message),
            ],
            EXISTING_PLAYER_FLOW: [
                CallbackQueryHandler(continue_chat, pattern="^continue_chat$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
                # ALL text messages go to AI brain
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_any_message),
            ],
            SUPPORT_FLOW: [
                CallbackQueryHandler(continue_chat, pattern="^continue_chat$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
                # ALL text messages go to AI brain
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_any_message),
            ],
            USERNAME_COLLECTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_any_message),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
        ],
    )

    application.add_handler(conv_handler)

    logger.info("AI-Powered Bot is running...")
    print("🤖 AI-Powered Bot is starting...")
    print(f"✅ TELEGRAM_TOKEN: {'Set' if TELEGRAM_TOKEN else 'Not Set'}")
    print(f"✅ SUPPORT_CHAT_ID: {'Set' if SUPPORT_CHAT_ID else 'Not Set'}")
    print(f"✅ OPENAI_API_KEY: {'Set' if OPENAI_API_KEY else 'Not Set'}")
    print(f"✅ OPENAI_CLIENT: {'Available' if openai_client else 'Not Available'}")
    print("🚀 ALL messages will be processed by AI Brain!")
    print("📞 Enhanced support messaging enabled!")
    
    application.run_polling()

if __name__ == "__main__":
    main()

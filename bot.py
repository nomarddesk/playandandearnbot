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

HELPFUL_CHANNEL_LINK = "https://t.me/rejoinsnousetgagne"

# Define states
SELECT_LANG, MAIN_MENU, EXISTING_PLAYER_FLOW, NEW_PLAYER_FLOW, SUPPORT_FLOW, USERNAME_COLLECTION = range(6)

# Codes for the game - Using the codes from GameSupportBot
GAME_CODES = [
    "6086-7221-0564",
    "2753-4695-7191", 
    "9689-1352-5966",
    "4563-6624-9460",
    "4828-9033-2281"
]

# --- LANGUAGE STRINGS ---
STRINGS = {
    'en': {
        'disclaimer': "**Disclaimer:** This bot is an unofficial guide and is not affiliated with Epic Games or Fortnite. We will *never* ask for your password.",
        'lang_prompt': "Please select your language:",
        'welcome': "🎮 Welcome to the Gaming Support Bot! 🎮\n\nChoose your user type:",
        'support_btn': "💼 Support (Claiming Reward)",
        'new_player_btn': "👋 New Player", 
        'existing_player_btn': "🎯 Existing Player",
        'helpful_channel_btn': "Full guide in channel",
        'lang_btn': "🌐 Change Language",
        'helpful_channel_text': "Join our helpful Telegram channel for the full guide, news, and community chat!",
        'join_channel_btn': "Join Channel Now",
        'back_btn': "⬅️ Back to Main Menu",
        
        # Support flow
        'support_flow_title': "💼 SUPPORT FLOW",
        'support_flow_intro': "Let's verify your progress for reward claim",
        
        # Questions from GameSupportBot
        'support_q1_text': "1. Did you use a VPN?",
        'support_q2_text': "2. Did you already create a cloud gaming profile?",
        'support_q3_text': "3. Did you receive the code from Epic Games to activate your cloud gaming account?",
        'support_q4_text': "4. Did you create your Epic Games profile?",
        'support_q5_text': "5. Did you create a shortcut of the cloud gaming to play it like an installed app?",
        'support_q6_text': "6. Have you launched the game?",
        'support_q7_text': "7. Have you searched and found the reward Island?",
        'support_q8_text': "8. Did you follow the full setup to play with friends and earn?",
        'support_q9_text': "9. Did you start the game and play 130 hours for free this week?",
        'support_q10_text': "10. Did you click the like button every time before your 1-hour session ended?",
        'support_q11_text': "11. Have you saved the reward Island to your favorites?",
        'support_q12_text': "12. Were you introduced to this game by an influencer?",
        'support_q13_text': "13. Did you complete every single step and play 130 hours this week?",
        
        # Common responses
        'vpn_reminder': "Please download and use a VPN in USA before going further.\nThen answer this question again.\nDid you finally use a VPN?",
        'cloud_gaming_reminder': "Please create a cloud gaming profile.\nDo you want our assistance?",
        'epic_code_reminder': "You have to receive the code.\nDo you want our guidance to help you with that?",
        'epic_profile_reminder': "You have to create your Epic Games profile.\nDo you want our guidance?",
        'shortcut_reminder': "You have to create a shortcut to play from your homescreen.\nDo you want our guidance with that?",
        'launch_game_reminder': "You have to launch the game.\nDo you need our guidance?",
        'reward_island_reminder': "You have to search the reward Island in the search bar.\nDo you want our guidance for that?",
        'full_setup_reminder': "You have to follow the exact setup.\nDo you need our guidance?",
        'play_hours_reminder': "You need to play before aiming for the reward.\nAre you able to play at least 130 hours a week?",
        'like_button_reminder': "You must click the like button every time.\nDo you want our guidance on that?",
        'favorites_reminder': "You have to save the reward Island to your favorites.\nDo you want our guidance on that?",
        'expert_review_text': "An expert will review all your screenshots and you will earn.",
        
        # Button texts
        'yes_btn': "✅ Yes",
        'no_btn': "❌ No",
        'want_assistance': "🆘 Yes, I need assistance",
        'already_done': "✅ Already done, next step",
        'see_guidance': "📖 See guidance",
        'provide_influencer': "👤 Provide influencer name",
        'no_influencer': "❌ No influencer",
        'completed_all': "🎉 Completed all steps",
        'need_help': "🆘 Need help",
        
        # Links and guidance
        'cloud_gaming_link': "🌐 Create cloud gaming profile:\nhttps://www.xbox.com/fr-FR/play/games/fortnite/BT5P2X999VH2",
        'epic_activate_link': "🔗 Activate Epic Games:\nhttp://epicgames.com/activate",
        'epic_create_link': "🎮 Create Epic Games profile:\nepicgames.com",
        'launch_game_link': "🚀 Launch game:\nhttps://www.xbox.com/fr-FR/play/games/fortnite/BT5P2X999VH2",
        'channel_guidance': "📺 Please check our channel for guidance and instructions.",
        
        # Code messages
        'codes_title': "🔢 Here are the reward island codes:\n\n",
        'congratulations': "🎉 Congratulations! Your submission has been received for review.",
        
        # Navigation
        'back_to_previous': "⬅️ Back",
        'main_menu': "🏠 Main Menu",
        
        # Username collection
        'username_prompt': "Please provide your @username for review:",
        'support_thanks': "Thank you! Your submission has been received for review.",
        
        # New player flow
        'new_player_intro': "👋 NEW PLAYER FLOW - Let's get you set up!\n\nNote: Cloud gaming sessions last 1 hour. You'll need to relaunch to keep playing.",
        'new_player_complete': "🎮 Setup complete! You're ready to start playing and earning!",
        
        # Existing player flow  
        'existing_player_intro': "🎯 EXISTING PLAYER FLOW - Welcome back!\n\nNote: You probably know this already - cloud sessions last 1 hour.",
    },
    'fr': {
        'disclaimer': "**Avertissement :** Ce bot est un guide non officiel et n'est pas affilié à Epic Games ou Fortnite. Nous ne vous demanderons *jamais* votre mot de passe.",
        'lang_prompt': "Veuillez sélectionner votre langue :",
        'welcome': "🎮 Bienvenue dans le Bot de Support Gaming ! 🎮\n\nChoisissez votre type d'utilisateur :",
        'support_btn': "💼 Support (Réclamation de récompense)",
        'new_player_btn': "👋 Nouveau joueur",
        'existing_player_btn': "🎯 Joueur existant", 
        'helpful_channel_btn': "Guide complet sur le canal",
        'lang_btn': "🌐 Changer de Langue",
        'helpful_channel_text': "Rejoignez notre canal Telegram pour le guide complet, les actualités et pour discuter avec la communauté !",
        'join_channel_btn': "Rejoindre le Canal",
        'back_btn': "⬅️ Retour au Menu Principal",
        
        # Support flow - French
        'support_flow_title': "💼 FLUX DE SUPPORT",
        'support_flow_intro': "Vérifions votre progression pour la réclamation de récompense",
        
        # Questions from GameSupportBot - French
        'support_q1_text': "1. Avez-vous utilisé un VPN ?",
        'support_q2_text': "2. Avez-vous déjà créé un profil de cloud gaming ?",
        'support_q3_text': "3. Avez-vous reçu le code d'Epic Games pour activer votre compte de cloud gaming ?",
        'support_q4_text': "4. Avez-vous créé votre profil Epic Games ?",
        'support_q5_text': "5. Avez-vous créé un raccourci du cloud gaming pour jouer comme une application installée ?",
        'support_q6_text': "6. Avez-vous lancé le jeu ?",
        'support_q7_text': "7. Avez-vous recherché et trouvé l'île de récompense ?",
        'support_q8_text': "8. Avez-vous suivi la configuration complète pour jouer avec des amis et gagner ?",
        'support_q9_text': "9. Avez-vous commencé le jeu et joué 130 heures gratuitement cette semaine ?",
        'support_q10_text': "10. Avez-vous cliqué sur le bouton like à chaque fois avant la fin de votre session d'1 heure ?",
        'support_q11_text': "11. Avez-vous enregistré l'île de récompense dans vos favoris ?",
        'support_q12_text': "12. Avez-vous été présenté à ce jeu par un influenceur ?",
        'support_q13_text': "13. Avez-vous terminé chaque étape et joué 130 heures cette semaine ?",
        
        # Common responses - French
        'vpn_reminder': "Veuillez télécharger et utiliser un VPN aux USA avant d'aller plus loin.\nPuis répondez à cette question à nouveau.\nAvez-vous finalement utilisé un VPN ?",
        'cloud_gaming_reminder': "Veuillez créer un profil de cloud gaming.\nVoulez-vous notre assistance ?",
        'epic_code_reminder': "Vous devez recevoir le code.\nVoulez-vous notre aide pour cela ?",
        'epic_profile_reminder': "Vous devez créer votre profil Epic Games.\nVoulez-vous notre aide ?",
        'shortcut_reminder': "Vous devez créer un raccourci pour jouer depuis votre écran d'accueil.\nVoulez-vous notre aide pour cela ?",
        'launch_game_reminder': "Vous devez lancer le jeu.\nAvez-vous besoin de notre aide ?",
        'reward_island_reminder': "Vous devez rechercher l'île de récompense dans la barre de recherche.\nVoulez-vous notre aide pour cela ?",
        'full_setup_reminder': "Vous devez suivre la configuration exacte.\nAvez-vous besoin de notre aide ?",
        'play_hours_reminder': "Vous devez jouer avant de viser la récompense.\nÊtes-vous capable de jouer au moins 130 heures par semaine ?",
        'like_button_reminder': "Vous devez cliquer sur le bouton like à chaque fois.\nVoulez-vous notre aide pour cela ?",
        'favorites_reminder': "Vous devez enregistrer l'île de récompense dans vos favoris.\nVoulez-vous notre aide pour cela ?",
        'expert_review_text': "Un expert examinera toutes vos captures d'écran et vous gagnerez.",
        
        # Button texts - French
        'yes_btn': "✅ Oui",
        'no_btn': "❌ Non",
        'want_assistance': "🆘 Oui, j'ai besoin d'aide",
        'already_done': "✅ Déjà fait, étape suivante",
        'see_guidance': "📖 Voir les instructions",
        'provide_influencer': "👤 Fournir le nom de l'influenceur",
        'no_influencer': "❌ Aucun influenceur",
        'completed_all': "🎉 Toutes les étapes terminées",
        'need_help': "🆘 Besoin d'aide",
        
        # Links and guidance - French
        'cloud_gaming_link': "🌐 Créer un profil de cloud gaming :\nhttps://www.xbox.com/fr-FR/play/games/fortnite/BT5P2X999VH2",
        'epic_activate_link': "🔗 Activer Epic Games :\nhttp://epicgames.com/activate",
        'epic_create_link': "🎮 Créer un profil Epic Games :\nepicgames.com",
        'launch_game_link': "🚀 Lancer le jeu :\nhttps://www.xbox.com/fr-FR/play/games/fortnite/BT5P2X999VH2",
        'channel_guidance': "📺 Veuillez consulter notre canal pour obtenir des conseils et des instructions.",
        
        # Code messages - French
        'codes_title': "🔢 Voici les codes de l'île de récompense :\n\n",
        'congratulations': "🎉 Félicitations ! Votre soumission a été reçue pour examen.",
        
        # Navigation - French
        'back_to_previous': "⬅️ Retour",
        'main_menu': "🏠 Menu Principal",
        
        # Username collection - French
        'username_prompt': "Veuillez fournir votre @nom d'utilisateur pour examen :",
        'support_thanks': "Merci ! Votre soumission a été reçue pour examen.",
        
        # New player flow - French
        'new_player_intro': "👋 FLUX NOUVEAU JOUEUR - Préparons votre configuration !\n\nNote : Les sessions de cloud gaming durent 1 heure. Vous devrez relancer pour continuer à jouer.",
        'new_player_complete': "🎮 Configuration terminée ! Vous êtes prêt à commencer à jouer et à gagner !",
        
        # Existing player flow - French
        'existing_player_intro': "🎯 FLUX JOUEUR EXISTANT - Bon retour !\n\nNote : Vous le savez probablement déjà - les sessions cloud durent 1 heure.",
    }
}

# --- Helper Functions ---
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str = None):
    """Helper function to show the main menu in the user's language."""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    keyboard = [
        [InlineKeyboardButton(s['support_btn'], callback_data="support_start")],
        [InlineKeyboardButton(s['new_player_btn'], callback_data="new_player_start")],
        [InlineKeyboardButton(s['existing_player_btn'], callback_data="existing_player_start")],
        [InlineKeyboardButton(s['helpful_channel_btn'], callback_data="helpful_channel")],
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

def get_yes_no_keyboard(lang: str, back_callback: str):
    """Helper to create yes/no keyboard"""
    s = STRINGS[lang]
    return [
        [InlineKeyboardButton(s['yes_btn'], callback_data="yes")],
        [InlineKeyboardButton(s['no_btn'], callback_data="no")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data=back_callback)]
    ]

def print_codes(lang: str) -> str:
    """Helper to format codes for display"""
    s = STRINGS[lang]
    codes_text = s['codes_title']
    for code in GAME_CODES:
        codes_text += f"   {code}\n"
    return codes_text

# --- SUPPORT FLOW (from GameSupportBot) ---

async def support_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Flow - Start"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    context.user_data['support_qa'] = []  # Initialize Q&A storage
    context.user_data['current_question'] = 1
    
    text = f"💼 {s['support_flow_title']} 💼\n\n{s['support_flow_intro']}\n\n{s['support_q1_text']}"
    
    keyboard = get_yes_no_keyboard(lang, "back_to_main")
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_question_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, question_num: int) -> int:
    """Generic handler for support questions"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    user_answer = query.data
    current_q = context.user_data.get('current_question', 1)
    
    # Store the answer
    question_text = getattr(s, f'support_q{current_q}_text', f"Question {current_q}")
    context.user_data['support_qa'].append((question_text, "Yes" if user_answer == "yes" else "No"))
    
    # Handle specific question logic
    if user_answer == "no":
        return await handle_no_answer(update, context, current_q)
    
    # Move to next question
    next_question = current_q + 1
    context.user_data['current_question'] = next_question
    
    if next_question <= 13:
        question_text = getattr(s, f'support_q{next_question}_text', f"Question {next_question}")
        
        keyboard = get_yes_no_keyboard(lang, f"support_q{current_q}")
        
        await query.edit_message_text(text=question_text, reply_markup=InlineKeyboardMarkup(keyboard))
        return SUPPORT_FLOW
    else:
        # All questions completed
        return await support_complete(update, context)

async def handle_no_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, question_num: int) -> int:
    """Handle 'no' answers with specific guidance"""
    query = update.callback_query
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    current_q = context.user_data.get('current_question', 1)
    
    if question_num == 1:  # VPN question
        text = s['vpn_reminder']
        keyboard = [
            [InlineKeyboardButton(s['yes_btn'], callback_data="vpn_fixed")],
            [InlineKeyboardButton(s['no_btn'], callback_data="channel_forward")],
            [InlineKeyboardButton(s['back_to_previous'], callback_data="support_start")]
        ]
    
    elif question_num == 2:  # Cloud gaming profile
        text = s['cloud_gaming_reminder']
        keyboard = [
            [InlineKeyboardButton(s['want_assistance'], callback_data="cloud_gaming_assistance")],
            [InlineKeyboardButton(s['already_done'], callback_data="yes")],
            [InlineKeyboardButton(s['back_to_previous'], callback_data="support_start")]
        ]
    
    elif question_num == 3:  # Epic Games code
        text = s['epic_code_reminder']
        keyboard = [
            [InlineKeyboardButton(s['see_guidance'], callback_data="epic_activate_help")],
            [InlineKeyboardButton(s['already_done'], callback_data="yes")],
            [InlineKeyboardButton(s['back_to_previous'], callback_data="support_q2")]
        ]
    
    elif question_num == 4:  # Epic Games profile
        text = s['epic_profile_reminder']
        keyboard = [
            [InlineKeyboardButton(s['see_guidance'], callback_data="epic_create_help")],
            [InlineKeyboardButton(s['already_done'], callback_data="yes")],
            [InlineKeyboardButton(s['back_to_previous'], callback_data="support_q3")]
        ]
    
    elif question_num == 5:  # Shortcut
        text = s['shortcut_reminder']
        keyboard = [
            [InlineKeyboardButton(s['see_guidance'], callback_data="channel_forward")],
            [InlineKeyboardButton(s['already_done'], callback_data="yes")],
            [InlineKeyboardButton(s['back_to_previous'], callback_data="support_q4")]
        ]
    
    elif question_num == 6:  # Launch game
        text = s['launch_game_reminder']
        keyboard = [
            [InlineKeyboardButton(s['see_guidance'], callback_data="launch_game_help")],
            [InlineKeyboardButton(s['already_done'], callback_data="yes")],
            [InlineKeyboardButton(s['back_to_previous'], callback_data="support_q5")]
        ]
    
    elif question_num == 7:  # Reward island
        text = s['reward_island_reminder']
        keyboard = [
            [InlineKeyboardButton(s['see_guidance'], callback_data="show_codes")],
            [InlineKeyboardButton(s['already_done'], callback_data="yes")],
            [InlineKeyboardButton(s['back_to_previous'], callback_data="support_q6")]
        ]
    
    elif question_num == 8:  # Full setup
        text = s['full_setup_reminder']
        keyboard = [
            [InlineKeyboardButton(s['see_guidance'], callback_data="channel_forward")],
            [InlineKeyboardButton(s['already_done'], callback_data="yes")],
            [InlineKeyboardButton(s['back_to_previous'], callback_data="support_q7")]
        ]
    
    elif question_num == 9:  # Play hours
        text = s['play_hours_reminder']
        keyboard = [
            [InlineKeyboardButton(s['yes_btn'], callback_data="yes")],
            [InlineKeyboardButton(s['no_btn'], callback_data="channel_forward")],
            [InlineKeyboardButton(s['back_to_previous'], callback_data="support_q8")]
        ]
    
    elif question_num == 10:  # Like button
        text = s['like_button_reminder']
        keyboard = [
            [InlineKeyboardButton(s['see_guidance'], callback_data="channel_forward")],
            [InlineKeyboardButton(s['already_done'], callback_data="yes")],
            [InlineKeyboardButton(s['back_to_previous'], callback_data="support_q9")]
        ]
    
    elif question_num == 11:  # Favorites
        text = s['favorites_reminder']
        keyboard = [
            [InlineKeyboardButton(s['see_guidance'], callback_data="channel_forward")],
            [InlineKeyboardButton(s['already_done'], callback_data="yes")],
            [InlineKeyboardButton(s['back_to_previous'], callback_data="support_q10")]
        ]
    
    elif question_num == 12:  # Influencer
        text = s['support_q12_text']
        keyboard = [
            [InlineKeyboardButton(s['provide_influencer'], callback_data="influencer_yes")],
            [InlineKeyboardButton(s['no_influencer'], callback_data="influencer_no")],
            [InlineKeyboardButton(s['back_to_previous'], callback_data="support_q11")]
        ]
    
    else:  # Default case
        return await support_question_handler(update, context, question_num)
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, help_type: str) -> int:
    """Handle help requests during support flow"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    current_q = context.user_data.get('current_question', 1)
    
    if help_type == "cloud_gaming_assistance":
        text = s['cloud_gaming_link']
    elif help_type == "epic_activate_help":
        text = s['epic_activate_link']
    elif help_type == "epic_create_help":
        text = s['epic_create_link']
    elif help_type == "launch_game_help":
        text = s['launch_game_link']
    elif help_type == "show_codes":
        text = print_codes(lang)
    elif help_type == "channel_forward":
        text = s['channel_guidance']
        keyboard = [[InlineKeyboardButton(s['join_channel_btn'], url=HELPFUL_CHANNEL_LINK)]]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
        return SUPPORT_FLOW
    else:
        text = s['channel_guidance']
    
    keyboard = [
        [InlineKeyboardButton(s['already_done'], callback_data="yes")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data=f"support_q{current_q}")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_influencer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, choice: str) -> int:
    """Handle influencer question"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    if choice == "influencer_yes":
        context.user_data['support_influencer'] = "Yes - will provide name"
        text = "Please provide the influencer name when you submit your username."
    else:
        context.user_data['support_influencer'] = "No influencer"
        text = s['expert_review_text']
    
    # Move to next question (Q13)
    context.user_data['current_question'] = 13
    question_text = s['support_q13_text']
    
    keyboard = [
        [InlineKeyboardButton(s['completed_all'], callback_data="yes")],
        [InlineKeyboardButton(s['need_help'], callback_data="channel_forward")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="support_q11")]
    ]
    
    await query.edit_message_text(text=f"{text}\n\n{question_text}", reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_complete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support flow completed - ask for username"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    context.user_data['flow_type'] = 'support'
    
    await query.edit_message_text(text=s['username_prompt'])
    return USERNAME_COLLECTION

# --- NEW PLAYER FLOW ---

async def new_player_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Flow - Start"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    context.user_data['new_player_qa'] = []
    context.user_data['current_question'] = 1
    
    text = f"{s['new_player_intro']}\n\n{s['support_q1_text']}"
    
    keyboard = get_yes_no_keyboard(lang, "back_to_main")
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_player_question_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, question_num: int) -> int:
    """Handler for new player questions"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    user_answer = query.data
    current_q = context.user_data.get('current_question', 1)
    
    # Store the answer
    question_text = getattr(s, f'support_q{current_q}_text', f"Question {current_q}")
    context.user_data['new_player_qa'].append((question_text, "Yes" if user_answer == "yes" else "No"))
    
    # For new players, we use future tense for some questions
    if current_q >= 9:  # Questions 9-11 use future tense for new players
        if user_answer == "no":
            return await handle_new_player_no_answer(update, context, current_q)
    
    # Move to next question
    next_question = current_q + 1
    context.user_data['current_question'] = next_question
    
    if next_question <= 12:  # New player flow has 12 questions
        if next_question <= 8:
            question_text = getattr(s, f'support_q{next_question}_text', f"Question {next_question}")
        else:
            # Use future tense for questions 9-12
            future_questions = {
                9: "9. Will you start the game and play 130 hours for free this week?",
                10: "10. Will you click the like button every time before your 1-hour session ended?",
                11: "11. Will you save the reward Island to your favorites?",
                12: "12. Were you introduced to this game by an influencer?"
            }
            question_text = future_questions.get(next_question, f"Question {next_question}")
        
        keyboard = get_yes_no_keyboard(lang, f"new_player_q{current_q}")
        
        await query.edit_message_text(text=question_text, reply_markup=InlineKeyboardMarkup(keyboard))
        return NEW_PLAYER_FLOW
    else:
        # All questions completed
        return await new_player_complete(update, context)

async def handle_new_player_no_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, question_num: int) -> int:
    """Handle 'no' answers for new player flow"""
    query = update.callback_query
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    current_q = context.user_data.get('current_question', 1)
    
    if question_num == 12:  # Influencer question for new players
        text = s['support_q12_text']
        keyboard = [
            [InlineKeyboardButton(s['provide_influencer'], callback_data="new_influencer_yes")],
            [InlineKeyboardButton(s['no_influencer'], callback_data="new_influencer_no")],
            [InlineKeyboardButton(s['back_to_previous'], callback_data=f"new_player_q{current_q-1}")]
        ]
    else:
        # For other questions, use similar logic as support flow but with future tense
        return await new_player_question_handler(update, context, question_num)
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_player_complete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New player flow completed"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    text = s['new_player_complete']
    
    keyboard = [[InlineKeyboardButton(s['main_menu'], callback_data="back_to_main")]]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return MAIN_MENU

# --- EXISTING PLAYER FLOW ---

async def existing_player_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Flow - Start"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    context.user_data['existing_player_qa'] = []
    
    text = f"{s['existing_player_intro']}\n\n1. Have you searched and found the reward Island?"
    
    keyboard = get_yes_no_keyboard(lang, "back_to_main")
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return EXISTING_PLAYER_FLOW

async def existing_player_question_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler for existing player questions"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    user_answer = query.data
    
    # Simplified flow for existing players - just a few key questions
    if user_answer == "no" and "reward" in query.message.text.lower():
        # First question - reward island
        text = s['reward_island_reminder']
        keyboard = [
            [InlineKeyboardButton(s['see_guidance'], callback_data="show_codes")],
            [InlineKeyboardButton(s['already_done'], callback_data="existing_next")],
            [InlineKeyboardButton(s['back_to_previous'], callback_data="existing_player_start")]
        ]
    elif user_answer == "yes" or user_answer == "existing_next":
        # Move through simplified questions
        current_state = context.user_data.get('existing_player_state', 1)
        
        questions = [
            "2. Did you follow the full setup to play with friends and earn?",
            "3. Did you start the game and play 130 hours for free this week?",
            "4. Will you click the like button every time before your 1-hour session ended?",
            "5. Did you save the reward Island to your favorites?",
            "6. Were you introduced to this game by an influencer?"
        ]
        
        if current_state < len(questions):
            text = questions[current_state - 1]
            context.user_data['existing_player_state'] = current_state + 1
            keyboard = get_yes_no_keyboard(lang, "existing_player_start")
        else:
            # Flow completed
            text = "🎯 Existing player setup verified! You're all set to continue playing and earning."
            keyboard = [[InlineKeyboardButton(s['main_menu'], callback_data="back_to_main")]]
    else:
        # Channel forward for other no answers
        text = s['channel_guidance']
        keyboard = [[InlineKeyboardButton(s['join_channel_btn'], url=HELPFUL_CHANNEL_LINK)]]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return EXISTING_PLAYER_FLOW

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

# --- USERNAME COLLECTION ---

async def collect_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Collect username and send Q&A to support team"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    username = update.message.text
    
    logger.info(f"*** USERNAME COLLECTION from user {update.message.from_user.id}: {username} ***")
    
    if not SUPPORT_CHAT_ID:
        logger.error("SUPPORT_CHAT_ID is not set in environment variables")
        await update.message.reply_text("❌ Support feature is currently unavailable. Please try again later.")
        return await show_main_menu(update, context)
    
    try:
        user = update.effective_user
        user_username = user.username if user.username else "No username"
        first_name = user.first_name if user.first_name else "No first name"
        last_name = user.last_name if user.last_name else "No last name"
        
        flow_type = context.user_data.get('flow_type', 'unknown')
        qa_data = []
        
        if flow_type == 'support':
            qa_data = context.user_data.get('support_qa', [])
            flow_title = "💼 SUPPORT QUESTIONNAIRE"
            # Add influencer info
            influencer_info = context.user_data.get('support_influencer', 'Not specified')
            if influencer_info:
                qa_data.append(("Influencer information", influencer_info))
        elif flow_type == 'new_player':
            qa_data = context.user_data.get('new_player_qa', [])
            flow_title = "👋 NEW PLAYER QUESTIONNAIRE"
        elif flow_type == 'existing_player':
            qa_data = context.user_data.get('existing_player_qa', [])
            flow_title = "🎯 EXISTING PLAYER QUESTIONNAIRE"
        else:
            qa_data = []
            flow_title = "❓ UNKNOWN FLOW"
        
        support_message = (
            f"🚨 **{flow_title}** 🚨\n"
            f"👤 User: {first_name} {last_name}\n"
            f"📛 User's Telegram: @{user_username}\n"
            f"💬 Provided Username: {username}\n"
            f"🆔 User ID: `{user.id}`\n"
            f"⏰ Time: {update.message.date.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"🌐 Language: {lang.upper()}\n\n"
        )
        
        if qa_data:
            support_message += "**Questions & Answers:**\n"
            for i, (question, answer) in enumerate(qa_data, 1):
                support_message += f"{i}. {question}\n   ➤ {answer}\n\n"
        else:
            support_message += "**No Q&A data collected.**\n\n"
        
        support_message += f"**Flow Type:** {flow_type.replace('_', ' ').title()}"
        
        await context.bot.send_message(
            chat_id=SUPPORT_CHAT_ID,
            text=support_message,
            parse_mode='Markdown'
        )
        
        await update.message.reply_text(text=s['support_thanks'], reply_markup=ReplyKeyboardRemove())
        return await show_main_menu(update, context)
        
    except Exception as e:
        logger.error(f"Error sending support message to group: {e}")
        await update.message.reply_text("❌ There was an error sending your information. Please try again later.")
        return await show_main_menu(update, context)

async def cancel_support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User types /cancel during the support flow."""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    await update.message.reply_text(text=s['support_cancel'], reply_markup=ReplyKeyboardRemove())
    return await show_main_menu(update, context)

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
                CallbackQueryHandler(support_start, pattern="^support_start$"),
                CallbackQueryHandler(new_player_start, pattern="^new_player_start$"),
                CallbackQueryHandler(existing_player_start, pattern="^existing_player_start$"),
                CallbackQueryHandler(show_helpful_channel, pattern="^helpful_channel$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
            SUPPORT_FLOW: [
                # Support question handlers
                CallbackQueryHandler(lambda u, c: support_question_handler(u, c, 1), pattern="^yes$"),
                CallbackQueryHandler(lambda u, c: support_question_handler(u, c, 1), pattern="^no$"),
                CallbackQueryHandler(lambda u, c: support_question_handler(u, c, 2), pattern="^vpn_fixed$"),
                
                # Help handlers
                CallbackQueryHandler(lambda u, c: support_help_handler(u, c, "cloud_gaming_assistance"), pattern="^cloud_gaming_assistance$"),
                CallbackQueryHandler(lambda u, c: support_help_handler(u, c, "epic_activate_help"), pattern="^epic_activate_help$"),
                CallbackQueryHandler(lambda u, c: support_help_handler(u, c, "epic_create_help"), pattern="^epic_create_help$"),
                CallbackQueryHandler(lambda u, c: support_help_handler(u, c, "launch_game_help"), pattern="^launch_game_help$"),
                CallbackQueryHandler(lambda u, c: support_help_handler(u, c, "show_codes"), pattern="^show_codes$"),
                CallbackQueryHandler(lambda u, c: support_help_handler(u, c, "channel_forward"), pattern="^channel_forward$"),
                
                # Influencer handler
                CallbackQueryHandler(lambda u, c: support_influencer_handler(u, c, "influencer_yes"), pattern="^influencer_yes$"),
                CallbackQueryHandler(lambda u, c: support_influencer_handler(u, c, "influencer_no"), pattern="^influencer_no$"),
                
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
            NEW_PLAYER_FLOW: [
                CallbackQueryHandler(lambda u, c: new_player_question_handler(u, c, 1), pattern="^yes$"),
                CallbackQueryHandler(lambda u, c: new_player_question_handler(u, c, 1), pattern="^no$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
            EXISTING_PLAYER_FLOW: [
                CallbackQueryHandler(existing_player_question_handler, pattern="^yes$"),
                CallbackQueryHandler(existing_player_question_handler, pattern="^no$"),
                CallbackQueryHandler(existing_player_question_handler, pattern="^existing_next$"),
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

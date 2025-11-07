import logging
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
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

# Codes for the game
GAME_CODES = [
    "6086-7221-0564",
    "2753-4695-7191", 
    "9689-1352-5966",
    "4563-6624-9460",
    "4828-9033-2281"]

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
        'back_btn': "⬅️ Back to Main Menu",
        'support_q1': "Have you already read the 'New player' guide and the 'Full guide in channel'?",
        'yes_btn': "Yes, I still have a question",
        'no_btn': "No, I will check them now",
        'support_q1_no': "Please review those guides first. They answer most questions! 🙏\n\nReturning you to the main menu.",
        'support_q2': "Okay. By providing your @username, you consent to our support team contacting you directly on Telegram. We will *only* use this to help with your question.\n\nPlease type your @username (like @myusername) to proceed.\n\nType /cancel to go back.",
        'support_thanks': "Thank you! Your @username has been noted. We will get in touch with you as soon as possible.\n\nReturning you to the main menu.",
        'support_cancel': "Support request cancelled. Returning to main menu.",
        'invalid_username': "That doesn't look like a valid @username. Please start with '@' and try again, or type /cancel.",
        'username_prompt': "Okay. By providing your @username, you consent to our support team contacting you directly on Telegram. We will *only* use this to help with your question.\n\nPlease type your @username (like @myusername) to proceed.\n\nType /cancel to go back.",
        
        # Support flow
        'support_flow_title': "Support",
        'support_flow_intro': "In order to get in touch with us, you need to answer these questions so we can determine which stage of the process you're at. If everything has been done correctly, you'll be able to claim your reward 💰💰",
        'support_q1_text': "1 Did you use a VPN?",
        'support_q2_text': "2 - Did you already create a cloud gaming profile?",
        'support_q3_text': "3 - Did you receive the code from epic games to activate your cloud gaming account?",
        'support_q4_text': "4 Did you create your epic games profile?",
        'support_q5_text': "5 Did you create a shortcut of the cloud gaming to play it like an installed app directly from your Homescreen?",
        'support_q6_text': "6 Have you launched the game?",
        'support_q7_text': "7 Have you searched and found the reward Island?",
        'support_q8_text': "8 Did you follow the full setup to be able to play with friends and earn a lot together without any worries?",
        'support_q9_text': "9 Did you start the game and play 130 hours for free this week?",
        'support_q10_text': "10 Did you click on the like button every single time before your 1 hour play session ended during your 130 hours of play this week?",
        'support_q11_text': "11 Have you saved the reward Island to your favorites?",
        'support_q12_text': "12 Were you introduced to this game by an influencer?",
        'support_q13_text': "13 Make sure you completed every single step before sending us your @, did you completed every single step and play at least 130 hours this week?",
        
        # Common responses
        'vpn_reminder': "Please download and use a VPN in USA before going any further to create all your authentic profiles but to play you don't use it.\n\nDid you finally use a VPN?",
        'cloud_gaming_reminder': "Please create a cloud gaming profile. Do you want our assistance?",
        'epic_code_reminder': "Please you have to receive the code, do you want our guidance to help you with that?",
        'epic_profile_reminder': "No please you have to create your epic games profile, do you want our guidance?",
        'shortcut_reminder': "No. You have to create a shortcut to play fortnite from your homescreen, do you want our guidance with that?",
        'launch_game_reminder': "No you have to launch the game, do you need our guidance?",
        'reward_island_reminder': "No, you have to search the reward Island in the search bar and just choose it , do you want our guidance for that?",
        'full_setup_reminder': "No, you have to follow the exact setup , do you need our guidance?",
        'play_hours_reminder': "No, you have to start the game and play every single day for free before aiming for the reward, are you able to play at least 130 hours a week?",
        'like_button_reminder': "No, You have to click on the like button every single time before your 1 hour play session ended during your 130 hours a week , do you want our guidance on that?",
        'favorites_reminder': "No , you have to save the reward Island to your favorites and play , do you want our guidance on that?",
        'expert_review_text': "One of the expert will review all the screenshots of the game and you will earn",
        
        # Button texts
        'a_yes': "A Yes",
        'b_no': "B No",
        'a_if_yes': "A If yes",
        'b_if_no': "B If no",
        'yes_i_received': "A Yes I received the code , I want the next step",
        'yes_im_ready': "A Yes, I'm ready for the next step",
        'yes_i_did': "A Yes , I did it and I will send you all the necessary screenshots",
        'want_codes': "Yes I want the best codes to play",
        'already_chose': "No , I already choosed one code",
        'want_assistance': "Yes",
        'already_have': "No I already have one, I want the next step",
        'finally_fixed': "No I finally fix everything, I want to move to the next step",
        'will_play': "No, I will play and let you know in the support session later on",
        'have_proof': "No , I have proof I saved the reward Island to my favorites and I actually play on it",
        'have_proof_played': "No, I have proof that I played 130 hours this week and I liked every single time , and I am wishing to share it with you guys",
        'see_channel': "yes I want to see it in the channel",
        'completed': "Completed",
        'next_question': "Next Question",
        'join_channel_only': "Join Channel",
        
        # Navigation
        'back_to_previous': "⬅️ Back",
        'back_to_support': "⬅️ Back to Support",
        'back_to_existing': "⬅️ Back to Existing Player", 
        'back_to_new': "⬅️ Back to New Player",
        'main_menu': "🏠 Main Menu",
        
        # Influencer question
        'provide_name': "Provide the name please:",
        
        # Existing player flow
        'existing_player_intro': "Because you are playing on the cloud, your session will last for 1 hour. The game will close, and you will have to launch it again to keep playing.\nYou probably know it cause you already follow all the instructions\n\n1 Have you searched and found the reward Island?",
        'existing_q2_text': "2 Did you follow the full setup to be able to play with friends and earn a lot together without any worries?",
        'existing_q3_text': "3 Did you start the game and play 130 hours for free this week?",
        'existing_q4_text': "4 With your existing account ,  will you click on the like button every single time before your 1 hour play session ended during your 130 hours of play this week?",
        'existing_q5_text': "5 Did you save the reward Island to your favorites?",
        'existing_q6_text': "6 Were you introduced to this game by an influencer?",
        
        # New player flow
        'new_player_intro': "New player:\n\nYou're diving into an immersive gaming adventure.This bot will help you set up your account, join the game, start playing and earning\nBecause you are playing on the cloud, your session will last for 1 hour. The game will close, and you will have to launch it again to keep playing.\n\n1 Did you use a VPN?",
        'new_q2_text': "2 - Did you already create a cloud gaming profile?",
        'new_q3_text': "3 - Did you receive the code from epic games to activate your cloud gaming account?",
        'new_q4_text': "4 Did you create your epic games profile?",
        'new_q5_text': "5 Did you create a shortcut of the cloud gaming to play it like an installed app directly from your Homescreen?",
        'new_q6_text': "6 Have you launched the game?",
        'new_q7_text': "7 Have you searched and found the reward Island?",
        'new_q8_text': "8 Did you follow the full setup to be able to play with friends and earn a lot together without any worries?",
        'new_q9_text': "9 Will you start the game and play 130 hours for free this week?",
        'new_q10_text': "10 With your new account , will you click on the like button every single time before your 1 hour play session ended during your 130 hours of play this week?",
        'new_q11_text': "11 Will you save the reward Island to your favorites?",
        'new_q12_text': "12 Were you introduced to this game by an influencer?",
        
        # Links and guidance
        'cloud_gaming_link': "Here's the link to create your cloud gaming profile:\nhttps://www.xbox.com/fr-FR/play/games/fortnite/BT5P2X999VH2",
        'epic_activate_link': "Here's the activation link:\nhttp://epicgames.com/activate",
        'epic_create_link': "Create your Epic Games profile here:\nepicgames.com",
        'launch_game_link': "Launch the game here:\nhttps://www.xbox.com/fr-FR/play/games/fortnite/BT5P2X999VH2",
        'channel_guidance': "Please check our channel for guidance:",
        'channel_instruction_9': "Please check our channel and look for instruction 9:",
        'channel_instruction_10': "Please check our channel and look for instruction 10:",
        'channel_instruction_11': "Please check our channel and look for instruction 11:",
        'channel_instruction_12': "Please check our channel and look for instruction 12:",
        'channel_instruction_13': "Please check our channel and look for instruction 13:",
    },
    'fr': {
        'disclaimer': "**Avertissement :** Ce bot est un guide non officiel et n'est pas affilié à Epic Games ou Fortnite. Nous ne vous demanderons *jamais* votre mot de passe.",
        'lang_prompt': "Veuillez sélectionner votre langue :",
        'welcome': "Bienvenue ! Tu plonges dans une aventure de jeu immersive. Ce bot t'aidera à configurer ton compte, à rejoindre la partie et à commencer à jouer.",
        'new_player_btn': "Nouveau joueur",
        'existing_player_btn': "Joueur existant",
        'helpful_channel_btn': "Guide complet sur le canal",
        'support_btn': "Support",
        'lang_btn': "🌐 Changer de Langue",
        'helpful_channel_text': "Rejoignez notre canal Telegram pour le guide complet, les actualités et pour discuter avec la communauté !",
        'join_channel_btn': "Rejoindre le Canal",
        'back_btn': "⬅️ Retour au Menu Principal",
        'support_q1': "Avez-vous déjà lu le guide 'Nouveau joueur' et le 'Guide complet sur le canal' ?",
        'yes_btn': "Oui, j'ai encore une question",
        'no_btn': "Non, je vais les voir maintenant",
        'support_q1_no': "Veuillez d'abord consulter ces guides. Ils répondent à la plupart des questions ! 🙏\n\nRetour au menu principal.",
        'support_q2': "D'accord. En fournissant votre @nomdutilisateur, vous acceptez que notre équipe d'assistance vous contacte directement sur Telegram. Nous l'utiliserons *uniquement* pour répondre à votre question.\n\nVeuillez taper votre @nomdutilisateur (comme @monpseudo) pour continuer.\n\nTapez /cancel pour revenir.",
        'support_thanks': "Merci ! Votre @nomdutilisateur a été noté. Nous vous contacterons dès que possible.\n\nRetour au menu principal.",
        'support_cancel': "Demande d'aide annulée. Retour au menu principal.",
        'invalid_username': "Cela ne ressemble pas à un @nomdutilisateur valide. Veuillez commencer par '@' et réessayer, ou tapez /cancel.",
        'username_prompt': "D'accord. En fournissant votre @nomdutilisateur, vous acceptez que notre équipe d'assistance vous contacte directement sur Telegram. Nous l'utiliserons *uniquement* pour répondre à votre question.\n\nVeuillez taper votre @nomdutilisateur (comme @monpseudo) pour continuer.\n\nTapez /cancel pour revenir.",
        
        # Support flow - French
        'support_flow_title': "Support",
        'support_flow_intro': "Afin de nous contacter, vous devez répondre à ces questions afin que nous puissions déterminer à quelle étape du processus vous vous trouvez. Si tout a été fait correctement, vous pourrez réclamer votre récompense 💰💰",
        'support_q1_text': "1 Avez-vous utilisé un VPN ?",
        'support_q2_text': "2 - Avez-vous déjà créé un profil de cloud gaming ?",
        'support_q3_text': "3 - Avez-vous reçu le code d'Epic Games pour activer votre compte de cloud gaming ?",
        'support_q4_text': "4 Avez-vous créé votre profil Epic Games ?",
        'support_q5_text': "5 Avez-vous créé un raccourci du cloud gaming pour jouer comme une application installée directement depuis votre écran d'accueil ?",
        'support_q6_text': "6 Avez-vous lancé le jeu ?",
        'support_q7_text': "7 Avez-vous recherché et trouvé l'île de récompense ?",
        'support_q8_text': "8 Avez-vous suivi la configuration complète pour pouvoir jouer avec des amis et gagner beaucoup ensemble sans aucun souci ?",
        'support_q9_text': "9 Avez-vous commencé le jeu et joué 130 heures gratuitement cette semaine ?",
        'support_q10_text': "10 Avez-vous cliqué sur le bouton like à chaque fois avant que votre session de jeu d'1 heure ne se termine pendant vos 130 heures de jeu cette semaine ?",
        'support_q11_text': "11 Avez-vous enregistré l'île de récompense dans vos favoris ?",
        'support_q12_text': "12 Avez-vous été présenté à ce jeu par un influenceur ?",
        'support_q13_text': "13 Assurez-vous d'avoir terminé chaque étape avant de nous envoyer votre @, avez-vous terminé chaque étape et joué au moins 130 heures cette semaine ?",
        
        # Common responses - French
        'vpn_reminder': "Veuillez télécharger et utiliser un VPN aux USA avant d'aller plus loin pour créer tous vos profils authentiques mais pour jouer vous ne l'utilisez pas.\n\nAvez-vous finalement utilisé un VPN ?",
        'cloud_gaming_reminder': "Veuillez créer un profil de cloud gaming. Voulez-vous notre assistance ?",
        'epic_code_reminder': "Veuillez, vous devez recevoir le code, voulez-vous notre aide pour cela ?",
        'epic_profile_reminder': "Non, veuillez, vous devez créer votre profil Epic Games, voulez-vous notre aide ?",
        'shortcut_reminder': "Non. Vous devez créer un raccourci pour jouer à Fortnite depuis votre écran d'accueil, voulez-vous notre aide pour cela ?",
        'launch_game_reminder': "Non, vous devez lancer le jeu, avez-vous besoin de notre aide ?",
        'reward_island_reminder': "Non, vous devez rechercher l'île de récompense dans la barre de recherche et la choisir, voulez-vous notre aide pour cela ?",
        'full_setup_reminder': "Non, vous devez suivre la configuration exacte, avez-vous besoin de notre aide ?",
        'play_hours_reminder': "Non, vous devez commencer le jeu et jouer chaque jour gratuitement avant de viser la récompense, êtes-vous capable de jouer au moins 130 heures par semaine ?",
        'like_button_reminder': "Non, vous devez cliquer sur le bouton like à chaque fois avant que votre session de jeu d'1 heure ne se termine pendant vos 130 heures par semaine, voulez-vous notre aide pour cela ?",
        'favorites_reminder': "Non, vous devez enregistrer l'île de récompense dans vos favoris et jouer, voulez-vous notre aide pour cela ?",
        'expert_review_text': "Un expert examinera toutes les captures d'écran du jeu et vous gagnerez",
        
        # Button texts - French
        'a_yes': "A Oui",
        'b_no': "B Non",
        'a_if_yes': "A Si oui",
        'b_if_no': "B Si non",
        'yes_i_received': "A Oui j'ai reçu le code, je veux l'étape suivante",
        'yes_im_ready': "A Oui, je suis prêt pour l'étape suivante",
        'yes_i_did': "A Oui, je l'ai fait et je vous enverrai toutes les captures d'écran nécessaires",
        'want_codes': "Oui je veux les meilleurs codes pour jouer",
        'already_chose': "Non, j'ai déjà choisi un code",
        'want_assistance': "Oui",
        'already_have': "Non j'en ai déjà un, je veux l'étape suivante",
        'finally_fixed': "Non j'ai finalement tout réparé, je veux passer à l'étape suivante",
        'will_play': "Non, je vais jouer et vous tiens au courant lors de la session de support",
        'have_proof': "Non, j'ai la preuve que je l'ai sauvegardé et que j'y joue réellement",
        'have_proof_played': "Non, j'ai la preuve que j'ai joué 130 heures cette semaine et que j'ai aimé à chaque fois, et je souhaite le partager avec vous",
        'see_channel': "oui je veux le voir dans le canal",
        'completed': "Terminé",
        'next_question': "Question Suivante",
        'join_channel_only': "Rejoindre le Canal",
        
        # Navigation - French
        'back_to_previous': "⬅️ Retour",
        'back_to_support': "⬅️ Retour au Support",
        'back_to_existing': "⬅️ Retour au Joueur Existant", 
        'back_to_new': "⬅️ Retour au Nouveau Joueur",
        'main_menu': "🏠 Menu Principal",
        
        # Influencer question - French
        'provide_name': "Fournissez le nom s'il vous plaît :",
        
        # Existing player flow - French
        'existing_player_intro': "Parce que vous jouez sur le cloud, votre session durera 1 heure. Le jeu se fermera et vous devrez le relancer pour continuer à jouer.\nVous le savez probablement car vous suivez déjà toutes les instructions\n\n1 Avez-vous recherché et trouvé l'île de récompense ?",
        'existing_q2_text': "2 Avez-vous suivi la configuration complète pour pouvoir jouer avec des amis et gagner beaucoup ensemble sans aucun souci ?",
        'existing_q3_text': "3 Avez-vous commencé le jeu et joué 130 heures gratuitement cette semaine ?",
        'existing_q4_text': "4 Avec votre compte existant, cliquerez-vous sur le bouton like à chaque fois avant que votre session de jeu d'1 heure ne se termine pendant vos 130 heures de jeu cette semaine ?",
        'existing_q5_text': "5 Avez-vous enregistré l'île de récompense dans vos favoris ?",
        'existing_q6_text': "6 Avez-vous été présenté à ce jeu par un influenceur ?",
        
        # New player flow - French
        'new_player_intro': "Nouveau joueur :\n\nVous plongez dans une aventure de jeu immersive. Ce bot vous aidera à configurer votre compte, à rejoindre le jeu, à commencer à jouer et à gagner.\nParce que vous jouez sur le cloud, votre session durera 1 heure. Le jeu se fermera et vous devrez le relancer pour continuer à jouer.\n\n1 Avez-vous utilisé un VPN ?",
        'new_q2_text': "2 - Avez-vous déjà créé un profil de cloud gaming ?",
        'new_q3_text': "3 - Avez-vous reçu le code d'Epic Games pour activer votre compte de cloud gaming ?",
        'new_q4_text': "4 Avez-vous créé votre profil Epic Games ?",
        'new_q5_text': "5 Avez-vous créé un raccourci du cloud gaming pour jouer comme une application installée directement depuis votre écran d'accueil ?",
        'new_q6_text': "6 Avez-vous lancé le jeu ?",
        'new_q7_text': "7 Avez-vous recherché et trouvé l'île de récompense ?",
        'new_q8_text': "8 Avez-vous suivi la configuration complète pour pouvoir jouer avec des amis et gagner beaucoup ensemble sans aucun souci ?",
        'new_q9_text': "9 Allez-vous commencer le jeu et jouer 130 heures gratuitement cette semaine ?",
        'new_q10_text': "10 Avec votre nouveau compte, cliquerez-vous sur le bouton like à chaque fois avant que votre session de jeu d'1 heure ne se termine pendant vos 130 heures de jeu cette semaine ?",
        'new_q11_text': "11 Allez-vous enregistrer l'île de récompense dans vos favoris ?",
        'new_q12_text': "12 Avez-vous été présenté à ce jeu par un influenceur ?",
        
        # Links and guidance - French
        'cloud_gaming_link': "Voici le lien pour créer votre profil de cloud gaming :\nhttps://www.xbox.com/fr-FR/play/games/fortnite/BT5P2X999VH2",
        'epic_activate_link': "Voici le lien d'activation :\nhttp://epicgames.com/activate",
        'epic_create_link': "Créez votre profil Epic Games ici :\nepicgames.com",
        'launch_game_link': "Lancez le jeu ici :\nhttps://www.xbox.com/fr-FR/play/games/fortnite/BT5P2X999VH2",
        'channel_guidance': "Veuillez consulter notre canal pour obtenir des conseils :",
        'channel_instruction_9': "Veuillez consulter notre canal et chercher l'instruction 9 :",
        'channel_instruction_10': "Veuillez consulter notre canal et chercher l'instruction 10 :",
        'channel_instruction_11': "Veuillez consulter notre canal et chercher l'instruction 11 :",
        'channel_instruction_12': "Veuillez consulter notre canal et chercher l'instruction 12 :",
        'channel_instruction_13': "Veuillez consulter notre canal et chercher l'instruction 13 :",
    }}

# --- Helper Functions ---
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str = None):
    """Helper function to show the main menu in the user's language."""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    keyboard = [
        [InlineKeyboardButton(s['new_player_btn'], callback_data="new_player_start")],
        [InlineKeyboardButton(s['existing_player_btn'], callback_data="existing_player_start")],
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

async def safe_edit_message(query, text, reply_markup=None, parse_mode=None):
    """Safely edit message with error handling and delay."""
    try:
        await asyncio.sleep(0.5)  # Add delay to prevent rapid updates
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
    except Exception as e:
        logger.warning(f"Failed to edit message: {e}")
        # Try to send a new message if editing fails
        try:
            await query.message.reply_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        except Exception as e2:
            logger.error(f"Failed to send new message: {e2}")

# --- NEW PLAYER FLOW ---
async def new_player_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Flow - Start"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    context.user_data['new_player_qa'] = []  # Initialize Q&A storage
    
    # Store Q1 text to use in subsequent handlers
    context.user_data['new_q1_text'] = s['new_player_intro'].split('\n')[-1]

    text = s['new_player_intro']
    
    keyboard = [
        [InlineKeyboardButton(s['a_yes'], callback_data="new_q1_yes")],
        [InlineKeyboardButton(s['b_no'], callback_data="new_q1_no")],
        [InlineKeyboardButton(s['back_btn'], callback_data="back_to_main")]
    ]
    
    await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q1_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q1 - Yes -> Q2"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store Q&A
    if not context.user_data['new_player_qa'] or context.user_data['new_player_qa'][-1][0] != context.user_data.get('new_q1_text'):
        context.user_data['new_player_qa'].append((context.user_data.get('new_q1_text', s['new_player_intro'].split('\n')[-1]), "Yes"))
    
    context.user_data['new_q2_text_key'] = 'new_q2_text'

    text = s['new_q2_text']
    
    keyboard = [
        [InlineKeyboardButton(s['a_yes'], callback_data="new_q2_yes")],
        [InlineKeyboardButton(s['b_no'], callback_data="new_q2_no")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="new_player_start")]
    ]
    
    await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q1_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q1 - No -> Ask if they finally used VPN"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store Q&A
    if not context.user_data['new_player_qa'] or context.user_data['new_player_qa'][-1][0] != context.user_data.get('new_q1_text'):
        context.user_data['new_player_qa'].append((context.user_data.get('new_q1_text', s['new_player_intro'].split('\n')[-1]), "No"))
    
    text = s['vpn_reminder']
    
    keyboard = [
        [InlineKeyboardButton(s['a_if_yes'], callback_data="new_q1_no_yes")],
        [InlineKeyboardButton(s['b_if_no'], callback_data="new_channel_forward")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="new_player_start")]
    ]
    
    await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q1_no_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q1 No -> Yes (after VPN reminder) -> Q2"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store that they fixed the VPN issue
    context.user_data['new_player_qa'].append(("VPN Reminder - Did you finally use VPN?", "Yes"))
    
    # Now proceed to Q2
    context.user_data['new_q2_text_key'] = 'new_q2_text'
    text = s['new_q2_text']
    
    keyboard = [
        [InlineKeyboardButton(s['a_yes'], callback_data="new_q2_yes")],
        [InlineKeyboardButton(s['b_no'], callback_data="new_q2_no")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="new_q1_no")]
    ]
    
    await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q2_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q2 - Yes -> Q3"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store Q&A
    context.user_data['new_player_qa'].append((s[context.user_data.get('new_q2_text_key', 'new_q2_text')], "Yes"))

    context.user_data['new_q3_text_key'] = 'new_q3_text'
    text = s['new_q3_text']
    
    keyboard = [
        [InlineKeyboardButton(s['yes_i_received'], callback_data="new_q3_yes")],
        [InlineKeyboardButton(s['b_no'], callback_data="new_q3_no")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="new_q1_yes")]
    ]
    
    await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q2_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q2 - No -> Ask if they want assistance"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store Q&A
    context.user_data['new_player_qa'].append((s['new_q2_text'], "No"))
    
    text = s['cloud_gaming_reminder']
    
    keyboard = [
        [InlineKeyboardButton(s['want_assistance'], callback_data="new_cloud_gaming_link")],
        [InlineKeyboardButton(s['already_have'], callback_data="new_q2_no_already_have")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="new_q1_yes")]
    ]
    
    await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q2_no_already_have(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q2 No -> Already have -> Q3"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store that they already have cloud gaming
    context.user_data['new_player_qa'].append(("Cloud Gaming Reminder", "Already have profile"))
    
    # Now proceed to Q3
    context.user_data['new_q3_text_key'] = 'new_q3_text'
    text = s['new_q3_text']
    
    keyboard = [
        [InlineKeyboardButton(s['yes_i_received'], callback_data="new_q3_yes")],
        [InlineKeyboardButton(s['b_no'], callback_data="new_q3_no")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="new_q2_no")]
    ]
    
    await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_cloud_gaming_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player - Cloud Gaming Link -> Q3"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    text = s['cloud_gaming_link']
    
    keyboard = [
        [InlineKeyboardButton(s['next_question'], callback_data="new_q3_yes")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="new_q2_no")]
    ]
    
    await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q3_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q3 - Yes -> Q4"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store Q&A
    context.user_data['new_player_qa'].append((s[context.user_data.get('new_q3_text_key', 'new_q3_text')], "Yes"))

    context.user_data['new_q4_text_key'] = 'new_q4_text'
    text = s['new_q4_text']
    
    keyboard = [
        [InlineKeyboardButton(s['a_yes'], callback_data="new_q4_yes")],
        [InlineKeyboardButton(s['b_no'], callback_data="new_q4_no")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="new_q2_yes")]
    ]
    
    await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_q3_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Q3 - No -> Ask if they want guidance"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store Q&A
    context.user_data['new_player_qa'].append((s['new_q3_text'], "No"))
    
    text = s['epic_code_reminder']
    
    keyboard = [
        [InlineKeyboardButton(s['want_assistance'], callback_data="new_epic_activate")],
        [InlineKeyboardButton(s['b_no'], callback_data="new_channel_forward")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="new_q2_yes")]
    ]
    
    await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

async def new_epic_activate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player - Epic Games Activate -> Q4"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    text = s['epic_activate_link']
    
    keyboard = [
        [InlineKeyboardButton(s['next_question'], callback_data="new_q4_yes")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="new_q3_no")]
    ]
    
    await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

# Continue with the rest of the new player flow following the same pattern...
# [The rest of the new player flow handlers would follow the same structure]

# --- EXISTING PLAYER FLOW ---
async def existing_player_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Flow - Start"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    context.user_data['existing_player_qa'] = []  # Initialize Q&A storage
    
    context.user_data['existing_q1_text'] = s['existing_player_intro'].split('\n')[-1]
    text = s['existing_player_intro']
    
    keyboard = [
        [InlineKeyboardButton(s['a_yes'], callback_data="existing_q1_yes")],
        [InlineKeyboardButton(s['b_no'], callback_data="existing_q1_no")],
        [InlineKeyboardButton(s['back_btn'], callback_data="back_to_main")]
    ]
    
    await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
    return EXISTING_PLAYER_FLOW

async def existing_q1_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Q1 - Yes -> Q2"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store Q&A
    context.user_data['existing_player_qa'].append((context.user_data.get('existing_q1_text'), "Yes"))

    context.user_data['existing_q2_text_key'] = 'existing_q2_text'
    text = s['existing_q2_text']
    
    keyboard = [
        [InlineKeyboardButton(s['yes_im_ready'], callback_data="existing_q2_yes")],
        [InlineKeyboardButton(s['b_no'], callback_data="existing_q2_no")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="existing_player_start")]
    ]
    
    await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
    return EXISTING_PLAYER_FLOW

async def existing_q1_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Q1 - No -> Show codes"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store Q&A
    context.user_data['existing_player_qa'].append((context.user_data.get('existing_q1_text'), "No"))
    
    codes_text = "Here are the codes for the reward Island:\n\n" + "\n".join(GAME_CODES)
    
    keyboard = [
        [InlineKeyboardButton(s['already_chose'], callback_data="existing_q2_yes")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="existing_player_start")]
    ]
    
    await safe_edit_message(query, codes_text, InlineKeyboardMarkup(keyboard))
    return EXISTING_PLAYER_FLOW

# Continue with the rest of the existing player flow following the same pattern...

# --- SUPPORT FLOW ---
async def support_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Flow - Start"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    context.user_data['support_qa'] = []  # Initialize Q&A storage
    
    context.user_data['support_q1_text'] = s['support_q1_text']
    text = (
        f"{s['support_flow_title']}:\n\n"
        f"{s['support_flow_intro']}\n\n"
        f"{s['support_q1_text']}"
    )
    
    keyboard = [
        [InlineKeyboardButton(s['a_yes'], callback_data="support_q1_yes")],
        [InlineKeyboardButton(s['b_no'], callback_data="support_q1_no")],
        [InlineKeyboardButton(s['back_btn'], callback_data="back_to_main")]
    ]
    
    await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_q1_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Q1 - Yes -> Q2"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store Q&A
    if not context.user_data['support_qa'] or context.user_data['support_qa'][-1][0] != context.user_data.get('support_q1_text'):
        context.user_data['support_qa'].append((context.user_data.get('support_q1_text'), "Yes"))

    context.user_data['support_q2_text_key'] = 'support_q2_text'
    text = s['support_q2_text']
    
    keyboard = [
        [InlineKeyboardButton(s['a_yes'], callback_data="support_q2_yes")],
        [InlineKeyboardButton(s['b_no'], callback_data="support_q2_no")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="support_start")]
    ]
    
    await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_q1_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Q1 - No -> Ask if they finally used VPN"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store Q&A
    context.user_data['support_qa'].append((s['support_q1_text'], "No"))
    
    text = s['vpn_reminder']
    
    keyboard = [
        [InlineKeyboardButton(s['a_if_yes'], callback_data="support_q1_no_yes")],
        [InlineKeyboardButton(s['b_if_no'], callback_data="support_channel_only")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="support_start")]
    ]
    
    await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

async def support_q1_no_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Q1 No -> Yes (after VPN reminder) -> Q2"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Store that they fixed the VPN issue
    context.user_data['support_qa'].append(("VPN Reminder - Did you finally use VPN?", "Yes"))
    
    # Now proceed to Q2
    context.user_data['support_q2_text_key'] = 'support_q2_text'
    text = s['support_q2_text']
    
    keyboard = [
        [InlineKeyboardButton(s['a_yes'], callback_data="support_q2_yes")],
        [InlineKeyboardButton(s['b_no'], callback_data="support_q2_no")],
        [InlineKeyboardButton(s['back_to_previous'], callback_data="support_q1_no")]
    ]
    
    await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

# Continue with the rest of the support flow following the same pattern...

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
        await safe_edit_message(
            query, text, 
            InlineKeyboardMarkup(keyboard), 
            'Markdown'
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
    await query.answer()
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
    await safe_edit_message(
        query, s['helpful_channel_text'],
        InlineKeyboardMarkup(keyboard)
    )
    
    return MAIN_MENU

# --- USERNAME COLLECTION ---
async def collect_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Collect username and send Q&A to support team"""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    username = update.message.text
    
    if username.startswith('@') and len(username) > 2:
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
            flow_title = "❓ UNKNOWN FLOW"
            
            if flow_type == 'existing_player':
                qa_data = context.user_data.get('existing_player_qa', [])
                flow_title = "🏆 EXISTING PLAYER QUESTIONNAIRE"
            elif flow_type == 'new_player':
                qa_data = context.user_data.get('new_player_qa', [])
                flow_title = "🎮 NEW PLAYER QUESTIONNAIRE"
            elif flow_type == 'support':
                qa_data = context.user_data.get('support_qa', [])
                flow_title = "🆘 SUPPORT REQUEST"
            
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
                    # Check if question is a full string or a key, display gracefully
                    q_text = STRINGS.get(lang, STRINGS['en']).get(question, question)
                    support_message += f"{i}. {q_text.split('\n')[-1].strip()}\n   ➤ **{answer}**\n\n"
            else:
                support_message += "**No Q&A data collected.**\n\n"
            
            support_message += f"**Flow Type:** {flow_type.replace('_', ' ').title()}"
            
            await context.bot.send_message(
                chat_id=SUPPORT_CHAT_ID,
                text=support_message,
                parse_mode='Markdown'
            )
            
            # Clear QA data after submission
            context.user_data.pop('existing_player_qa', None)
            context.user_data.pop('new_player_qa', None)
            context.user_data.pop('support_qa', None)
            
            await update.message.reply_text(text=s['support_thanks'], reply_markup=ReplyKeyboardRemove())
            return await show_main_menu(update, context)
            
        except Exception as e:
            logger.error(f"Error sending support message to group: {e}")
            await update.message.reply_text("❌ There was an error sending your information. Please try again later.")
            return await show_main_menu(update, context)
    else:
        await update.message.reply_text(text=s['invalid_username'])
        return USERNAME_COLLECTION

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
                CallbackQueryHandler(new_player_start, pattern="^new_player_start$"),
                CallbackQueryHandler(existing_player_start, pattern="^existing_player_start$"),
                CallbackQueryHandler(show_helpful_channel, pattern="^helpful_channel$"),
                CallbackQueryHandler(support_start, pattern="^contact_support$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
            EXISTING_PLAYER_FLOW: [
                CallbackQueryHandler(existing_q1_yes, pattern="^existing_q1_yes$"),
                CallbackQueryHandler(existing_q1_no, pattern="^existing_q1_no$"),
                CallbackQueryHandler(existing_q2_yes, pattern="^existing_q2_yes$"),
                CallbackQueryHandler(existing_q2_no, pattern="^existing_q2_no$"),
                # Add other existing player handlers...
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
            NEW_PLAYER_FLOW: [
                CallbackQueryHandler(new_q1_yes, pattern="^new_q1_yes$"),
                CallbackQueryHandler(new_q1_no, pattern="^new_q1_no$"),
                CallbackQueryHandler(new_q1_no_yes, pattern="^new_q1_no_yes$"),
                CallbackQueryHandler(new_q2_yes, pattern="^new_q2_yes$"),
                CallbackQueryHandler(new_q2_no, pattern="^new_q2_no$"),
                CallbackQueryHandler(new_q2_no_already_have, pattern="^new_q2_no_already_have$"),
                CallbackQueryHandler(new_cloud_gaming_link, pattern="^new_cloud_gaming_link$"),
                CallbackQueryHandler(new_q3_yes, pattern="^new_q3_yes$"),
                CallbackQueryHandler(new_q3_no, pattern="^new_q3_no$"),
                CallbackQueryHandler(new_epic_activate, pattern="^new_epic_activate$"),
                # Add other new player handlers...
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
            SUPPORT_FLOW: [
                CallbackQueryHandler(support_q1_yes, pattern="^support_q1_yes$"),
                CallbackQueryHandler(support_q1_no, pattern="^support_q1_no$"),
                CallbackQueryHandler(support_q1_no_yes, pattern="^support_q1_no_yes$"),
                CallbackQueryHandler(support_q2_yes, pattern="^support_q2_yes$"),
                CallbackQueryHandler(support_q2_no, pattern="^support_q2_no$"),
                # Add other support handlers...
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

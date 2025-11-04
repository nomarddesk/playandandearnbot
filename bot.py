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
        
        # Button texts - NEW KEYS ADDED FOR LOCALIZATION
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
        
        # Specific custom buttons that were hardcoded
        'b_1_if_yes': "B - 1 If yes",
        'b_2_if_no': "B - 2 if no",
        'b_1_yes': "B - 1 Yes",
        'b_2_no_already_have': "B - 2 No I already have one, I want the next step",
        'b_2_no': "B - 2 No",
        'b_1_see_channel': "B - 1 yes I want to see it in the channel",
        'b_2_no_shortcut': "B - 2 No I finally create a shortcut",
        'b_2_no_already_chose': "B - 2 No , I already choosed one code",
        'b_2_no_fix_everything': "B - 2 No I finally fix everything, I want to move to the next step",
        'b_2_no_will_play': "B - 2 No, I will play and let you know in the support session later on",
        'b_2_no_have_proof_saved': "B - 2 No , I have proof I saved the reward Island to my favorites and I actually play on it",
        'b_2_no_have_proof_played': "B - 2 No, I have proof that I played 130 hours this week and I liked every single time , and I am wishing to share it with you guys",
        'b_2_no_fix_next_step': "B - 2 No I finally fix everything, I want to move to the next step",
        
        # Code messages
        'codes_title': "Just copy one of them and enter it on the search bar:\n\n",
        'support_codes_title': "Here are the codes for the reward Island:\n\n",
        
        # Navigation
        'back_to_previous': "⬅️ Back",
        'back_to_support': "⬅️ Back to Support",
        'back_to_existing': "⬅️ Back to Existing Player", 
        'back_to_new': "⬅️ Back to New Player",
        'main_menu': "🏠 Main Menu",
        
        # Influencer question
        'provide_name': "Provide the name please:",
        
        # Existing player flow - UPDATED TEXT
        'existing_player_intro': "Because you are playing on the cloud, your session will last for 1 hour. The game will close, and you will have to launch it again to keep playing.\nYou probably know it cause you already follow all the instructions\n\n1 Have you searched and found the reward Island?",
        'existing_q2_text': "2 Did you follow the full setup to be able to play with friends and earn a lot together without any worries?",
        'existing_q3_text': "3 Did you start the game and play 130 hours for free this week?",
        'existing_q4_text': "4 With your existing account ,  will you click on the like button every single time before your 1 hour play session ended during your 130 hours of play this week?",
        'existing_q5_text': "5 Did you save the reward Island to your favorites?",
        'existing_q6_text': "6 Were you introduced to this game by an influencer?",
        
        # New player flow - UPDATED TEXT
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
        
        # AI Assistance
        'ai_assistance_btn': "🤖 AI Assistant",
        'ai_welcome': "🤖 **AI Assistant Activated**\n\nI'll help guide you through the process and answer any questions you have. You can type your responses freely or use the buttons when available.\n\nPlease tell me which category best describes you:",
        'ai_thinking': "🤔 Analyzing your response...",
        'ai_suggestion': "💡 **Suggestion:**",
        'ai_question': "❓ **Question:**",
        'ai_continue': "Continue with AI",
        'ai_go_back': "⬅️ Back to Menu",
        'ai_analyzing_flow': "🔍 Analyzing your progress and determining the best next step...",
        'ai_understanding': "I understand you're working on:",
        'ai_next_steps': "📋 **Recommended Next Steps:**",
        'ai_type_response': "💬 You can type your response or use the buttons below:",
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
        
        # Button texts - French - UPDATED
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
        
        # Specific custom buttons that were hardcoded
        'b_1_if_yes': "B - 1 Si oui",
        'b_2_if_no': "B - 2 Si non",
        'b_1_yes': "B - 1 Oui",
        'b_2_no_already_have': "B - 2 Non j'en ai déjà un, je veux l'étape suivante",
        'b_2_no': "B - 2 Non",
        'b_1_see_channel': "B - 1 oui je veux le voir dans le canal",
        'b_2_no_shortcut': "B - 2 Non j'ai finalement créé un raccourci",
        'b_2_no_already_chose': "B - 2 Non, j'ai déjà choisi un code",
        'b_2_no_fix_everything': "B - 2 Non j'ai finalement tout réparé, je veux passer à l'étape suivante",
        'b_2_no_will_play': "B - 2 Non, je vais jouer et vous tiens au courant lors de la session de support",
        'b_2_no_have_proof_saved': "B - 2 Non, j'ai la preuve que je l'ai sauvegardé et que j'y joue réellement",
        'b_2_no_have_proof_played': "B - 2 Non, j'ai la preuve que j'ai joué 130 heures cette semaine et que j'ai aimé à chaque fois, et je souhaite le partager avec vous",
        'b_2_no_fix_next_step': "B - 2 Non j'ai finalement tout réparé, je veux passer à l'étape suivante",
        
        # Code messages - French
        'codes_title': "Copiez simplement l'un d'entre eux et entrez-le dans la barre de recherche :\n\n",
        'support_codes_title': "Voici les codes pour l'île de récompense :\n\n",
        
        # Navigation - French
        'back_to_previous': "⬅️ Retour",
        'back_to_support': "⬅️ Retour au Support",
        'back_to_existing': "⬅️ Retour au Joueur Existant", 
        'back_to_new': "⬅️ Retour au Nouveau Joueur",
        'main_menu': "🏠 Menu Principal",
        
        # Influencer question - French
        'provide_name': "Fournissez le nom s'il vous plaît :",
        
        # Existing player flow - French - UPDATED
        'existing_player_intro': "Parce que vous jouez sur le cloud, votre session durera 1 heure. Le jeu se fermera et vous devrez le relancer pour continuer à jouer.\nVous le savez probablement car vous suivez déjà toutes les instructions\n\n1 Avez-vous recherché et trouvé l'île de récompense ?",
        'existing_q2_text': "2 Avez-vous suivi la configuration complète pour pouvoir jouer avec des amis et gagner beaucoup ensemble sans aucun souci ?",
        'existing_q3_text': "3 Avez-vous commencé le jeu et joué 130 heures gratuitement cette semaine ?",
        'existing_q4_text': "4 Avec votre compte existant, cliquerez-vous sur le bouton like à chaque fois avant que votre session de jeu d'1 heure ne se termine pendant vos 130 heures de jeu cette semaine ?",
        'existing_q5_text': "5 Avez-vous enregistré l'île de récompense dans vos favoris ?",
        'existing_q6_text': "6 Avez-vous été présenté à ce jeu par un influenceur ?",
        
        # New player flow - French - UPDATED
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
        
        # AI Assistance - French
        'ai_assistance_btn': "🤖 Assistant IA",
        'ai_welcome': "🤖 **Assistant IA Activé**\n\nJe vais vous guider à travers le processus et répondre à toutes vos questions. Vous pouvez taper vos réponses librement ou utiliser les boutons lorsqu'ils sont disponibles.\n\nVeuillez me dire quelle catégorie vous décrit le mieux :",
        'ai_thinking': "🤔 Analyse de votre réponse...",
        'ai_suggestion': "💡 **Suggestion :**",
        'ai_question': "❓ **Question :**",
        'ai_continue': "Continuer avec l'IA",
        'ai_go_back': "⬅️ Retour au Menu",
        'ai_analyzing_flow': "🔍 Analyse de votre progression et détermination de la meilleure prochaine étape...",
        'ai_understanding': "Je comprends que vous travaillez sur :",
        'ai_next_steps': "📋 **Prochaines Étapes Recommandées :**",
        'ai_type_response': "💬 Vous pouvez taper votre réponse ou utiliser les boutons ci-dessous :",
    }}

# --- AI AGENT CORE FUNCTIONS ---
async def generate_ai_response(user_context: dict, current_question: str, user_response: str, lang: str) -> dict:
    """
    Generate AI-powered response based on user context and conversation flow
    """
    if not openai_client:
        logger.warning("OpenAI client not available - returning default response")
        return {
            "response": "I'm currently unavailable. Please use the button options or try again later." if lang == 'en' else "Je suis actuellement indisponible. Veuillez utiliser les options de bouton ou réessayer plus tard.",
            "next_question": None,
            "buttons": [],
            "should_redirect": False
        }
    
    try:
        # Build comprehensive context for the AI
        conversation_history = user_context.get('conversation_history', [])
        flow_type = user_context.get('flow_type', 'general')
        current_state = user_context.get('current_state', 'main_menu')
        qa_data = user_context.get('qa_data', [])
        
        # Prepare system prompt
        system_prompt = f"""You are an AI gaming assistant for Fortnite and cloud gaming. The user is communicating in {lang.upper()}.

CONTEXT:
- Current Flow: {flow_type}
- Current State: {current_state}
- Current Question: "{current_question}"
- User's Response: "{user_response}"

USER'S PROGRESS:
{chr(10).join([f"Q: {q} | A: {a}" for q, a in qa_data]) if qa_data else "No progress data yet"}

RESPONSE REQUIREMENTS:
1. Analyze the user's response and progress
2. Provide helpful, accurate guidance about Fortnite cloud gaming
3. Determine the most logical next question from the predefined flow
4. Suggest appropriate buttons when relevant
5. If user seems stuck or confused, offer alternative guidance
6. Always maintain a helpful, encouraging tone

BUTTON OPTIONS REFERENCE:
- "A Yes" / "A Oui" - For affirmative answers
- "B No" / "B Non" - For negative answers  
- "Next Question" / "Question Suivante" - To continue flow
- Channel links for additional help

RESPONSE FORMAT (JSON):
{{
    "response": "Your main response text with guidance",
    "next_question": "The next question to ask from predefined flow",
    "buttons": ["Button text 1", "Button text 2", ...],
    "should_redirect": true/false,
    "analysis": "Brief analysis of user's situation"
}}

Keep responses concise but helpful. Always guide users toward completing the setup process."""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history for context
        for msg in conversation_history[-8:]:  # Last 8 messages for context
            messages.append(msg)
        
        messages.append({"role": "user", "content": f"Current question: {current_question}\nMy response: {user_response}"})
        
        response = openai_client.chat.completions.create(
            model="gpt-4",  # Using GPT-4 as requested
            messages=messages,
            temperature=0.7,
            max_tokens=800
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Parse JSON response
        try:
            parsed_response = json.loads(ai_response)
            return parsed_response
        except json.JSONDecodeError:
            logger.warning("Failed to parse AI response as JSON, using fallback")
            # Extract structured information from text response
            return {
                "response": ai_response,
                "next_question": "Would you like to continue with the next step?" if lang == 'en' else "Souhaitez-vous continuer avec l'étape suivante ?",
                "buttons": ["Next Question" if lang == 'en' else "Question Suivante", "Back to Menu" if lang == 'en' else "Retour au Menu"],
                "should_redirect": False,
                "analysis": "User provided free-text response requiring AI interpretation"
            }
            
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        return {
            "response": "I'm having trouble processing your request. Please try using the button options or try again later." if lang == 'en' else "Je rencontre des difficultés à traiter votre demande. Veuillez utiliser les options de bouton ou réessayer plus tard.",
            "next_question": None,
            "buttons": [],
            "should_redirect": True
        }

async def determine_user_category(user_message: str, lang: str) -> str:
    """
    Use AI to determine if user is new player, existing player, or needs support
    """
    if not openai_client:
        return "general"
    
    try:
        system_prompt = f"""Analyze the user's message and determine which category they belong to:
- "new_player": User is new to Fortnite cloud gaming and needs setup help
- "existing_player": User already has an account and needs advanced help
- "support": User has specific issues or needs technical support
- "general": Can't determine or general inquiry

User message: "{user_message}"
Language: {lang}

Respond with ONLY the category name, nothing else."""
        
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": system_prompt}],
            temperature=0.3,
            max_tokens=50
        )
        
        category = response.choices[0].message.content.strip().lower()
        return category if category in ["new_player", "existing_player", "support", "general"] else "general"
        
    except Exception as e:
        logger.error(f"Error determining user category: {e}")
        return "general"

async def analyze_comprehensive_progress(user_context: dict, lang: str) -> dict:
    """
    Comprehensive analysis of user's progress across all flows
    """
    if not openai_client:
        return {"analysis": "Progress analysis unavailable", "recommendations": ["Continue with current flow"]}
    
    try:
        qa_data = user_context.get('qa_data', [])
        flow_type = user_context.get('flow_type', 'general')
        
        system_prompt = f"""Comprehensively analyze the user's progress in the {flow_type} flow and provide detailed recommendations.

USER'S Q&A HISTORY:
{chr(10).join([f"Q: {q} | A: {a}" for q, a in qa_data]) if qa_data else "No data yet"}

Provide a JSON response with:
1. "analysis": Summary of current progress and status
2. "completed_steps": List of completed steps
3. "pending_steps": List of remaining steps
4. "blockers": Any identified issues or blockers
5. "recommendations": Specific next actions
6. "confidence": Confidence in analysis (0-1)

Be specific and actionable. Focus on Fortnite cloud gaming setup and rewards."""
        
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": system_prompt}],
            temperature=0.7,
            max_tokens=600
        )
        
        analysis_text = response.choices[0].message.content.strip()
        
        try:
            return json.loads(analysis_text)
        except json.JSONDecodeError:
            return {
                "analysis": analysis_text,
                "completed_steps": ["Analysis completed"],
                "pending_steps": ["Continue with flow"],
                "blockers": ["None identified"],
                "recommendations": ["Proceed with next question in flow"],
                "confidence": 0.7
            }
        
    except Exception as e:
        logger.error(f"Error analyzing comprehensive progress: {e}")
        return {
            "analysis": "Unable to analyze progress at this time",
            "recommendations": ["Please continue with the guided flow"]
        }

# --- ENHANCED HELPER FUNCTIONS WITH AI ---
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str = None):
    """Helper function to show the main menu in the user's language."""
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    keyboard = [
        [InlineKeyboardButton(s['new_player_btn'], callback_data="new_player_start")],
        [InlineKeyboardButton(s['existing_player_btn'], callback_data="existing_player_start")],
        [InlineKeyboardButton(s['helpful_channel_btn'], callback_data="helpful_channel")],
        [InlineKeyboardButton(s['support_btn'], callback_data="contact_support")],
        [InlineKeyboardButton(s['ai_assistance_btn'], callback_data="ai_assistance_start")],  # AI Assistant button
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
    
    # Update context for AI
    context.user_data['current_state'] = 'main_menu'
    return MAIN_MENU

async def handle_free_text_response(update: Update, context: ContextTypes.DEFAULT_TYPE, current_question: str, current_state: int) -> int:
    """
    Handle free-text user responses using AI analysis
    """
    user_message = update.message.text
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Show thinking message
    thinking_msg = await update.message.reply_text(s['ai_thinking'])
    
    # Prepare user context for AI
    user_context = {
        'conversation_history': context.user_data.get('conversation_history', []),
        'flow_type': context.user_data.get('flow_type', 'general'),
        'current_state': context.user_data.get('current_state', 'unknown'),
        'qa_data': context.user_data.get(f"{context.user_data.get('flow_type', 'general')}_qa", [])
    }
    
    # Generate AI response
    ai_response = await generate_ai_response(user_context, current_question, user_message, lang)
    
    # Build response message
    response_text = f"{ai_response.get('response', '')}"
    
    if ai_response.get('analysis'):
        response_text += f"\n\n🔍 {ai_response['analysis']}"
    
    if ai_response.get('next_question'):
        response_text += f"\n\n{s['ai_question']} {ai_response['next_question']}"
        # Store the next question for context
        context.user_data['current_question'] = ai_response['next_question']
    
    # Create keyboard from AI-suggested buttons
    keyboard = []
    buttons = ai_response.get('buttons', [])
    
    if buttons:
        for button_text in buttons:
            # Map common button texts to callbacks
            if button_text in [s['a_yes'], "Yes", "Oui"]:
                keyboard.append([InlineKeyboardButton(s['a_yes'], callback_data=f"{context.user_data.get('flow_type', 'general')}_q_yes")])
            elif button_text in [s['b_no'], "No", "Non"]:
                keyboard.append([InlineKeyboardButton(s['b_no'], callback_data=f"{context.user_data.get('flow_type', 'general')}_q_no")])
            elif button_text in [s['next_question'], "Next Question", "Question Suivante"]:
                keyboard.append([InlineKeyboardButton(s['next_question'], callback_data=f"{context.user_data.get('flow_type', 'general')}_next")])
            else:
                # Generic button
                keyboard.append([InlineKeyboardButton(button_text, callback_data="ai_continue")])
    
    # Add navigation buttons
    if context.user_data.get('flow_type') == 'new_player':
        keyboard.append([InlineKeyboardButton(s['back_to_new'], callback_data="new_player_start")])
    elif context.user_data.get('flow_type') == 'existing_player':
        keyboard.append([InlineKeyboardButton(s['back_to_existing'], callback_data="existing_player_start")])
    elif context.user_data.get('flow_type') == 'support':
        keyboard.append([InlineKeyboardButton(s['back_to_support'], callback_data="support_start")])
    
    keyboard.append([InlineKeyboardButton(s['main_menu'], callback_data="back_to_main")])
    
    # Add channel redirect if suggested
    if ai_response.get('should_redirect'):
        keyboard.append([InlineKeyboardButton(s['join_channel_btn'], url=HELPFUL_CHANNEL_LINK)])
    
    # Update thinking message with actual response
    await thinking_msg.edit_text(
        text=response_text,
        reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
        parse_mode='Markdown'
    )
    
    # Store conversation history
    if 'conversation_history' not in context.user_data:
        context.user_data['conversation_history'] = []
    
    context.user_data['conversation_history'].extend([
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": response_text}
    ])
    
    return current_state

# --- AI ASSISTANCE FLOW ---
async def ai_assistance_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start AI assistance flow"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Initialize AI conversation context
    context.user_data['ai_context'] = {
        'conversation_history': [],
        'flow_type': 'ai_assistance',
        'qa_data': []
    }
    
    context.user_data['current_state'] = 'ai_assistance'
    
    # Store initial message
    context.user_data['ai_context']['conversation_history'].append({
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
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    return AI_ASSISTED_FLOW

async def handle_ai_category_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle AI category choice and provide initial guidance"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    choice = query.data
    ai_context = context.user_data.get('ai_context', {})
    
    # Map choices to flow types
    flow_map = {
        'ai_new_player': ('new_player', s['new_player_btn']),
        'ai_existing_player': ('existing_player', s['existing_player_btn']), 
        'ai_support': ('support', s['support_btn'])
    }
    
    flow_type, flow_name = flow_map.get(choice, ('general', 'General'))
    
    ai_context['flow_type'] = flow_type
    context.user_data['flow_type'] = flow_type
    
    ai_context['conversation_history'].append({
        "role": "user",
        "content": f"User selected: {flow_name}"
    })
    
    # Show analysis message
    analysis_msg = await query.edit_message_text(text=s['ai_analyzing_flow'])
    
    # Get comprehensive analysis and guidance
    progress_analysis = await analyze_comprehensive_progress(ai_context, lang)
    
    # Build response
    response_text = f"🎯 **{s['ai_understanding']} {flow_name}**\n\n"
    response_text += f"📊 {progress_analysis.get('analysis', 'Starting analysis...')}\n\n"
    
    if progress_analysis.get('recommendations'):
        response_text += f"{s['ai_next_steps']}\n"
        for rec in progress_analysis.get('recommendations', []):
            response_text += f"• {rec}\n"
    
    response_text += f"\n{s['ai_type_response']}"
    
    # Create appropriate keyboard based on flow type
    keyboard = []
    if flow_type == 'new_player':
        keyboard.append([InlineKeyboardButton(s['new_player_intro'].split('\n')[-1], callback_data="new_player_start")])
    elif flow_type == 'existing_player':
        keyboard.append([InlineKeyboardButton(s['existing_player_intro'].split('\n')[-1], callback_data="existing_player_start")])
    elif flow_type == 'support':
        keyboard.append([InlineKeyboardButton(s['support_q1_text'], callback_data="support_start")])
    
    keyboard.append([InlineKeyboardButton(s['ai_continue'], callback_data="ai_continue_chat")])
    keyboard.append([InlineKeyboardButton(s['ai_go_back'], callback_data="ai_assistance_start")])
    
    await analysis_msg.edit_text(
        text=response_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    # Store AI response in history
    ai_context['conversation_history'].append({
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
    
    flow_type = context.user_data.get('flow_type', 'general')
    
    # Get appropriate first question based on flow type
    first_question = ""
    if flow_type == 'new_player':
        first_question = s['new_player_intro'].split('\n')[-1]
    elif flow_type == 'existing_player':
        first_question = s['existing_player_intro'].split('\n')[-1]
    elif flow_type == 'support':
        first_question = s['support_q1_text']
    else:
        first_question = "How can I help you today?"
    
    await query.edit_message_text(
        text=f"💬 **{first_question}**\n\n{s['ai_type_response']}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(s['ai_go_back'], callback_data="ai_assistance_start")],
            [InlineKeyboardButton(s['main_menu'], callback_data="back_to_main")]
        ])
    )
    
    context.user_data['awaiting_ai_input'] = True
    context.user_data['current_question'] = first_question
    return AI_ASSISTED_FLOW

async def handle_ai_free_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle free-text input in AI assistance flow"""
    if not context.user_data.get('awaiting_ai_input'):
        return AI_ASSISTED_FLOW
        
    return await handle_free_text_response(update, context, 
                                        context.user_data.get('current_question', 'General assistance'), 
                                        AI_ASSISTED_FLOW)

# --- ENHANCED EXISTING FLOWS WITH AI INTEGRATION ---
# Modified existing handlers to work with AI
async def enhanced_flow_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                              next_question: str, next_state: int, response: str = "Yes") -> int:
    """
    Enhanced flow handler that integrates AI analysis
    """
    query = update.callback_query
    if query:
        await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    flow_type = context.user_data.get('flow_type', 'general')
    
    # Store Q&A
    qa_key = f"{flow_type}_qa"
    if qa_key not in context.user_data:
        context.user_data[qa_key] = []
    
    current_question = context.user_data.get('current_question', 'Unknown question')
    context.user_data[qa_key].append((current_question, response))
    
    # Update conversation history
    if 'conversation_history' not in context.user_data:
        context.user_data['conversation_history'] = []
    
    context.user_data['conversation_history'].append({
        "role": "user", 
        "content": f"Q: {current_question} | A: {response}"
    })
    
    # Get AI analysis of progress
    progress_analysis = await analyze_comprehensive_progress({
        'flow_type': flow_type,
        'qa_data': context.user_data[qa_key]
    }, lang)
    
    # Show next question with AI insights
    if query:
        await query.edit_message_text(
            text=f"**{next_question}**\n\n{s['ai_suggestion']} {progress_analysis.get('analysis', 'Continuing...')}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            text=f"**{next_question}**\n\n{s['ai_suggestion']} {progress_analysis.get('analysis', 'Continuing...')}",
            parse_mode='Markdown'
        )
    
    context.user_data['current_question'] = next_question
    context.user_data['current_state'] = f"{flow_type}_flow"
    
    return next_state

# Example modified handler (apply similar pattern to all handlers)
async def new_player_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New Player Flow - Start with AI integration"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    context.user_data['new_player_qa'] = []  # Initialize Q&A storage
    context.user_data['flow_type'] = 'new_player'
    
    # Store Q1 text
    context.user_data['new_q1_text'] = s['new_player_intro'].split('\n')[-1]
    context.user_data['current_question'] = context.user_data['new_q1_text']

    text = s['new_player_intro']
    
    keyboard = [
        [InlineKeyboardButton(s['a_yes'], callback_data="new_q1_yes")],
        [InlineKeyboardButton(s['b_no'], callback_data="new_q1_no")],
        [InlineKeyboardButton(s['ai_assistance_btn'], callback_data="ai_assistance_start")],
        [InlineKeyboardButton(s['back_btn'], callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return NEW_PLAYER_FLOW

# Apply similar AI integration to other flow starters
async def existing_player_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Existing Player Flow - Start with AI integration"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    context.user_data['existing_player_qa'] = []
    context.user_data['flow_type'] = 'existing_player'
    
    context.user_data['existing_q1_text'] = s['existing_player_intro'].split('\n')[-1]
    context.user_data['current_question'] = context.user_data['existing_q1_text']
    
    text = s['existing_player_intro']
    
    keyboard = [
        [InlineKeyboardButton(s['a_yes'], callback_data="existing_q1_yes")],
        [InlineKeyboardButton(s['b_no'], callback_data="existing_q1_no")],
        [InlineKeyboardButton(s['ai_assistance_btn'], callback_data="ai_assistance_start")],
        [InlineKeyboardButton(s['back_btn'], callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return EXISTING_PLAYER_FLOW

async def support_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Support Flow - Start with AI integration"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    context.user_data['support_qa'] = []
    context.user_data['flow_type'] = 'support'
    
    context.user_data['support_q1_text'] = s['support_q1_text']
    context.user_data['current_question'] = context.user_data['support_q1_text']
    
    text = (
        f"{s['support_flow_title']}:\n\n"
        f"{s['support_flow_intro']}\n\n"
        f"{s['support_q1_text']}"
    )
    
    keyboard = [
        [InlineKeyboardButton(s['a_yes'], callback_data="support_q1_yes")],
        [InlineKeyboardButton(s['b_no'], callback_data="support_q1_no")],
        [InlineKeyboardButton(s['ai_assistance_btn'], callback_data="ai_assistance_start")],
        [InlineKeyboardButton(s['back_btn'], callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SUPPORT_FLOW

# --- FREE TEXT HANDLERS FOR ALL FLOWS ---
async def handle_new_player_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle free-text responses in new player flow"""
    return await handle_free_text_response(update, context, 
                                         context.user_data.get('current_question', 'New player question'), 
                                         NEW_PLAYER_FLOW)

async def handle_existing_player_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle free-text responses in existing player flow"""
    return await handle_free_text_response(update, context, 
                                         context.user_data.get('current_question', 'Existing player question'), 
                                         EXISTING_PLAYER_FLOW)

async def handle_support_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle free-text responses in support flow"""
    return await handle_free_text_response(update, context, 
                                         context.user_data.get('current_question', 'Support question'), 
                                         SUPPORT_FLOW)

# --- KEEP ALL EXISTING FLOW HANDLERS (they will work alongside AI) ---
# [All the existing new_q1_yes, new_q1_no, existing_q1_yes, etc. handlers remain the same]
# ... (include all the existing flow handlers from the original code) ...

# --- UPDATED MAIN FUNCTION WITH AI INTEGRATION ---
def main() -> None:
    """Run the bot with AI integration."""
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
                CallbackQueryHandler(ai_assistance_start, pattern="^ai_assistance_start$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
            AI_ASSISTED_FLOW: [
                CallbackQueryHandler(handle_ai_category_choice, pattern="^ai_(new_player|existing_player|support)$"),
                CallbackQueryHandler(ai_continue_chat, pattern="^ai_continue_chat$"),
                CallbackQueryHandler(ai_assistance_start, pattern="^ai_assistance_start$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_free_text),
            ],
            EXISTING_PLAYER_FLOW: [
                # All existing existing player callback handlers
                CallbackQueryHandler(existing_q1_yes, pattern="^existing_q1_yes$"),
                CallbackQueryHandler(existing_q1_no, pattern="^existing_q1_no$"),
                CallbackQueryHandler(existing_q2_yes, pattern="^existing_q2_yes$"),
                CallbackQueryHandler(existing_q2_no, pattern="^existing_q2_no$"),
                CallbackQueryHandler(existing_q3_yes, pattern="^existing_q3_yes$"),
                CallbackQueryHandler(existing_q3_no, pattern="^existing_q3_no$"),
                CallbackQueryHandler(existing_q4_yes, pattern="^existing_q4_yes$"),
                CallbackQueryHandler(existing_q4_no, pattern="^existing_q4_no$"),
                CallbackQueryHandler(existing_q5_yes, pattern="^existing_q5_yes$"),
                CallbackQueryHandler(existing_q5_no, pattern="^existing_q5_no$"),
                CallbackQueryHandler(existing_influencer_yes, pattern="^existing_influencer_yes$"),
                CallbackQueryHandler(existing_influencer_no, pattern="^existing_influencer_no$"),
                CallbackQueryHandler(existing_ask_username, pattern="^existing_ask_username$"),
                CallbackQueryHandler(existing_channel_instruction_11, pattern="^existing_channel_instruction_11$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
                # Free text handler for existing player flow
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_existing_player_text),
            ],
            NEW_PLAYER_FLOW: [
                # All existing new player callback handlers  
                CallbackQueryHandler(new_q1_yes, pattern="^new_q1_yes$"),
                CallbackQueryHandler(new_q1_no, pattern="^new_q1_no$"),
                CallbackQueryHandler(new_q2_yes, pattern="^new_q2_yes$"),
                CallbackQueryHandler(new_q2_yes, pattern="^new_q2_yes_from_q1_no$"),
                CallbackQueryHandler(new_q2_no, pattern="^new_q2_no$"),
                CallbackQueryHandler(new_cloud_gaming_link, pattern="^new_cloud_gaming_link$"),
                CallbackQueryHandler(new_q3_yes, pattern="^new_q3_yes$"),
                CallbackQueryHandler(new_q3_no, pattern="^new_q3_no$"),
                CallbackQueryHandler(new_epic_activate, pattern="^new_epic_activate$"),
                CallbackQueryHandler(new_q4_yes, pattern="^new_q4_yes$"),
                CallbackQueryHandler(new_q4_no, pattern="^new_q4_no$"),
                CallbackQueryHandler(new_epic_create, pattern="^new_epic_create$"),
                CallbackQueryHandler(new_q5_yes, pattern="^new_q5_yes$"),
                CallbackQueryHandler(new_q5_no, pattern="^new_q5_no$"),
                CallbackQueryHandler(new_q6_yes, pattern="^new_q6_yes$"),
                CallbackQueryHandler(new_q6_no, pattern="^new_q6_no$"),
                CallbackQueryHandler(new_launch_game, pattern="^new_launch_game$"),
                CallbackQueryHandler(new_q7_yes, pattern="^new_q7_yes$"),
                CallbackQueryHandler(new_q7_no, pattern="^new_q7_no$"),
                CallbackQueryHandler(new_q8_yes, pattern="^new_q8_yes$"),
                CallbackQueryHandler(new_q8_no, pattern="^new_q8_no$"),
                CallbackQueryHandler(new_q9_yes, pattern="^new_q9_yes$"),
                CallbackQueryHandler(new_q9_no, pattern="^new_q9_no$"),
                CallbackQueryHandler(new_q10_yes, pattern="^new_q10_yes$"),
                CallbackQueryHandler(new_q10_no, pattern="^new_q10_no$"),
                CallbackQueryHandler(new_q11_yes, pattern="^new_q11_yes$"),
                CallbackQueryHandler(new_q11_no, pattern="^new_q11_no$"),
                CallbackQueryHandler(new_q12_yes, pattern="^new_q12_yes$"),
                CallbackQueryHandler(new_q12_no, pattern="^new_q12_no$"),
                CallbackQueryHandler(new_ask_username, pattern="^new_ask_username$"),
                CallbackQueryHandler(new_channel_forward, pattern="^new_channel_forward$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
                # Free text handler for new player flow
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_player_text),
            ],
            SUPPORT_FLOW: [
                # All existing support callback handlers
                CallbackQueryHandler(support_q1_yes, pattern="^support_q1_yes$"),
                CallbackQueryHandler(support_q1_no, pattern="^support_q1_no$"),
                CallbackQueryHandler(support_q2_yes, pattern="^support_q2_yes$"),
                CallbackQueryHandler(support_q2_yes, pattern="^support_q2_yes_from_q1_no$"),
                CallbackQueryHandler(support_q2_no, pattern="^support_q2_no$"),
                CallbackQueryHandler(support_cloud_gaming_link, pattern="^support_cloud_gaming_link$"),
                CallbackQueryHandler(support_q3_yes, pattern="^support_q3_yes$"),
                CallbackQueryHandler(support_q3_no, pattern="^support_q3_no$"),
                CallbackQueryHandler(support_epic_activate, pattern="^support_epic_activate$"),
                CallbackQueryHandler(support_q4_yes, pattern="^support_q4_yes$"),
                CallbackQueryHandler(support_q4_no, pattern="^support_q4_no$"),
                CallbackQueryHandler(support_epic_create, pattern="^support_epic_create$"),
                CallbackQueryHandler(support_q5_yes, pattern="^support_q5_yes$"),
                CallbackQueryHandler(support_q5_no, pattern="^support_q5_no$"),
                CallbackQueryHandler(support_q6_yes, pattern="^support_q6_yes$"),
                CallbackQueryHandler(support_q6_no, pattern="^support_q6_no$"),
                CallbackQueryHandler(support_launch_game, pattern="^support_launch_game$"),
                CallbackQueryHandler(support_q7_yes, pattern="^support_q7_yes$"),
                CallbackQueryHandler(support_q7_no, pattern="^support_q7_no$"),
                CallbackQueryHandler(support_q8_yes, pattern="^support_q8_yes$"),
                CallbackQueryHandler(support_q8_no, pattern="^support_q8_no$"),
                CallbackQueryHandler(support_q9_yes, pattern="^support_q9_yes$"),
                CallbackQueryHandler(support_q9_no, pattern="^support_q9_no$"),
                CallbackQueryHandler(support_q10_yes, pattern="^support_q10_yes$"),
                CallbackQueryHandler(support_q10_no, pattern="^support_q10_no$"),
                CallbackQueryHandler(support_q11_yes, pattern="^support_q11_yes$"),
                CallbackQueryHandler(support_q11_no, pattern="^support_q11_no$"),
                CallbackQueryHandler(support_q12_yes, pattern="^support_q12_yes$"),
                CallbackQueryHandler(support_q12_no, pattern="^support_q12_no$"),
                CallbackQueryHandler(support_q13, pattern="^support_q13$"),
                CallbackQueryHandler(support_get_username_start, pattern="^support_get_username_start$"),
                CallbackQueryHandler(support_channel_only, pattern="^support_channel_only$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
                # Free text handler for support flow
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_support_text),
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

    logger.info("Bot is running with AI integration...")
    print("🤖 Bot is starting with AI Agent...")
    print(f"✅ TELEGRAM_TOKEN: {'Set' if TELEGRAM_TOKEN else 'Not Set'}")
    print(f"✅ SUPPORT_CHAT_ID: {'Set' if SUPPORT_CHAT_ID else 'Not Set'}")
    print(f"✅ OPENAI_API_KEY: {'Set' if OPENAI_API_KEY else 'Not Set'}")
    if SUPPORT_CHAT_ID:
        print(f"📋 SUPPORT_CHAT_ID Value: {SUPPORT_CHAT_ID}")
    print("🚀 Bot is running with GPT-4 AI Agent...")
    
    application.run_polling()

if __name__ == "__main__":
    main()

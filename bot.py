import logging
import os
import json
import sqlite3
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
from telegram.error import Conflict

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
print("ENHANCED GAMING BOT - ENVIRONMENT CHECK:")
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

# Database file path
DB_FILE = "/tmp/gaming_bot.db" if os.path.exists("/tmp") else "gaming_bot.db"

# Initialize Database
def init_database():
    """Initialize SQLite database for user progress tracking"""
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_progress (
                user_id INTEGER PRIMARY KEY,
                player_type TEXT DEFAULT 'new',
                current_step INTEGER DEFAULT 1,
                completed_steps TEXT DEFAULT '[]',
                vpn_used BOOLEAN DEFAULT FALSE,
                profile_created BOOLEAN DEFAULT FALSE,
                epic_activated BOOLEAN DEFAULT FALSE,
                game_launched BOOLEAN DEFAULT FALSE,
                reward_island_found BOOLEAN DEFAULT FALSE,
                full_setup_complete BOOLEAN DEFAULT FALSE,
                playtime_hours INTEGER DEFAULT 0,
                like_clicks INTEGER DEFAULT 0,
                favorites_saved BOOLEAN DEFAULT FALSE,
                influencer_name TEXT,
                language TEXT DEFAULT 'en',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS support_cases (
                case_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                case_type TEXT,
                issue_description TEXT,
                steps_completed TEXT,
                status TEXT DEFAULT 'open',
                assigned_to TEXT,
                resolution_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES player_progress (user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_conversations (
                conversation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                user_message TEXT,
                ai_response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ Database initialized successfully at {DB_FILE}")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print("⚠️ Using in-memory storage as fallback")

init_database()

HELPFUL_CHANNEL_LINK = "https://t.me/rejoinsnousetgagne"

# Define conversation states
SELECT_LANGUAGE, MAIN_MENU, NEW_PLAYER_FLOW, EXISTING_PLAYER_FLOW, SUPPORT_FLOW, USERNAME_COLLECTION, AI_CHAT = range(7)

# Game codes for reward island
REWARD_ISLAND_CODES = [
    "6086-7221-0564",
    "2753-4695-7191", 
    "9689-1352-5966",
    "4563-6624-9460",
    "4828-9033-2281"
]

# --- ENHANCED LANGUAGE STRINGS ---
BOT_TEXTS = {
    'en': {
        # Welcome and Main Menu
        'welcome_title': "🎮 **Ultimate Gaming Assistant**",
        'welcome_subtitle': "Your gateway to immersive gaming and exclusive rewards!",
        'disclaimer': "🔒 *Unofficial Guide: Not affiliated with Epic Games or Fortnite. We never ask for passwords.*",
        
        # Main Menu Options
        'new_player_option': "🚀 New Player Setup",
        'existing_player_option': "⚡ Player Check-In", 
        'support_option': "🆘 Support & Rewards",
        'ai_chat_option': "🤖 AI Assistant Chat",
        'channel_option': "📚 Game Guides",
        'language_option': "🌐 Language",
        
        # New Player Flow
        'new_player_welcome': "🎮 **New Player Setup Guide**\n\nWelcome to your gaming adventure! I'll guide you through setup so you can start playing and earning rewards immediately.",
        'cloud_session_note': "💡 *Cloud Gaming Note: Sessions last 1 hour. Relaunch to continue playing.*",
        
        # Steps with improved wording
        'step_1_vpn': "🔒 **Step 1: VPN Setup**\nDid you use a USA VPN for profile creation?",
        'vpn_guidance': "📱 **VPN Required**\n\nUse a USA VPN *only during profile setup* (not for playing). This ensures proper regional configuration.\n\nHave you configured your VPN?",
        
        'step_2_profile': "☁️ **Step 2: Gaming Profile**\nHave you created your cloud gaming profile?",
        'profile_guidance': "🎯 **Profile Setup**\n\nLet's create your gaming profile for optimal performance and rewards tracking.",
        
        'step_3_activation': "⚡ **Step 3: Account Activation**\nDid you activate with Epic Games?",
        'activation_guidance': "🔗 **Activation Required**\n\nConnect your cloud gaming to Epic Games to save progress and enable rewards.",
        
        'step_4_epic': "👤 **Step 4: Epic Profile**\nIs your Epic Games profile complete?",
        'epic_guidance': "🎮 **Profile Completion**\n\nFinalize your Epic profile for full feature access and reward eligibility.",
        
        'step_5_shortcut': "📱 **Step 5: Quick Access**\nDid you add the game to your home screen?",
        'shortcut_guidance': "🚀 **Instant Access**\n\nHome screen shortcuts provide fastest game launch and better experience.",
        
        'step_6_launch': "🎯 **Step 6: Game Launch**\nHave you successfully launched the game?",
        'launch_guidance': "🕹️ **Game Ready**\n\nLet's ensure the game launches properly for seamless gameplay.",
        
        'step_7_reward_island': "🏝️ **Step 7: Reward Access**\nAre you on the Reward Island?",
        'reward_guidance': "💰 **Earning Zone**\n\nThe Reward Island is where you accumulate points and unlock exclusive rewards.",
        'code_display': "🔑 **Access Codes:**\n{}\n\nCopy any code → Game search bar → Start earning!",
        
        'step_8_full_setup': "⚙️ **Step 8: Complete Setup**\nIs your full configuration complete?",
        'setup_guidance': "🎪 **Optimal Configuration**\n\nComplete setup ensures maximum earnings with friends and smooth gameplay.",
        
        'step_9_commitment': "⏰ **Step 9: Weekly Goals**\nCan you commit to 130 hours weekly?",
        'commitment_guidance': "🏆 **Reward Requirements**\n\nConsistent playtime is key to unlocking the best rewards and bonuses.",
        
        'step_10_engagement': "👍 **Step 10: Engagement**\nWill you click 'Like' before each session ends?",
        'engagement_guidance': "📊 **Activity Tracking**\n\nThe 'Like' button helps us track your engagement for reward calculations.",
        
        'step_11_favorites': "⭐ **Step 11: Quick Access**\nIs Reward Island saved in favorites?",
        'favorites_guidance': "🚀 **Efficient Gaming**\n\nFavorites save time and ensure you're always in the earning zone.",
        
        'step_12_influencer': "📢 **Step 12: Community**\nDid an influencer bring you here?",
        'influencer_prompt': "👥 **Community Recognition**\n\nPlease share the influencer's name for proper attribution:",
        
        # Existing Player Flow
        'existing_welcome': "⚡ **Player Check-In**\n\nWelcome back! Let's verify your setup and maximize your rewards.",
        'existing_cloud_note': "💡 *You know the routine: 1-hour sessions, relaunch to continue.*",
        
        # Support Flow
        'support_welcome': "🆘 **Support & Reward Verification**\n\nLet's identify any issues and verify your reward eligibility! 💰",
        'support_success': "✅ **Verification Complete!**\n\nOur team will review your case and contact you within 24 hours.",
        
        # AI Chat
        'ai_welcome': "🤖 **AI Gaming Assistant**\n\nHello! I'm your AI gaming assistant. Ask me anything about:\n\n• Game setup & configuration\n• Reward system & earning tips\n• Troubleshooting issues\n• Best practices for maximum rewards\n\n*Type your question below or use the menu to return:*",
        'ai_thinking': "💭 Thinking...",
        'ai_support_suggestion': "\n\n🔔 *If you need personalized support, consider using the Support option in the main menu.*",
        
        # Common Responses
        'yes_option': "✅ Yes",
        'no_option': "❌ No", 
        'need_help': "🆘 I need help",
        'already_done': "✅ Already done",
        'skip_step': "⏭️ Skip",
        'continue_next': "➡️ Continue",
        'back_previous': "⬅️ Back",
        'main_menu': "🏠 Main Menu",
        'join_channel': "📚 Join Channel",
        'back_to_chat': "💬 Back to Chat",
        
        # Channel and Links
        'channel_invite': "Join our community for guides, tips, and support:",
        'channel_instructions': "Check our channel for detailed instructions:",
        
        # Support Specific
        'provide_username': "👤 **Contact Setup**\n\nPlease provide your Telegram username (starting with @) for support:",
        'username_saved': "✅ **Info Received!**\n\nSupport team will contact you soon. Keep playing!",
        'invalid_username': "❌ Please provide a valid @username",
    },
    'fr': {
        # Welcome and Main Menu
        'welcome_title': "🎮 **Assistant de Jeu Ultime**",
        'welcome_subtitle': "Votre passerelle vers le gaming immersif et les récompenses exclusives!",
        'disclaimer': "🔒 *Guide Non Officiel: Non affilié à Epic Games ou Fortnite. Nous ne demandons jamais de mots de passe.*",
        
        # Main Menu Options
        'new_player_option': "🚀 Configuration Nouveau Joueur",
        'existing_player_option': "⚡ Vérification Joueur", 
        'support_option': "🆘 Support & Récompenses",
        'ai_chat_option': "🤖 Assistant IA Chat",
        'channel_option': "📚 Guides de Jeu",
        'language_option': "🌐 Langue",
        
        # New Player Flow
        'new_player_welcome': "🎮 **Guide de Configuration Nouveau Joueur**\n\nBienvenue dans votre aventure de jeu! Je vais vous guider à travers la configuration pour que vous puissiez commencer à jouer et gagner des récompenses immédiatement.",
        'cloud_session_note': "💡 *Note Cloud Gaming: Les sessions durent 1 heure. Relancez pour continuer à jouer.*",
        
        # Steps with improved wording
        'step_1_vpn': "🔒 **Étape 1: Configuration VPN**\nAvez-vous utilisé un VPN USA pour la création de profil?",
        'vpn_guidance': "📱 **VPN Requis**\n\nUtilisez un VPN USA *uniquement pendant la configuration du profil* (pas pour jouer). Cela assure une configuration régionale correcte.\n\nAvez-vous configuré votre VPN?",
        
        'step_2_profile': "☁️ **Étape 2: Profil de Jeu**\nAvez-vous créé votre profil cloud gaming?",
        'profile_guidance': "🎯 **Configuration Profil**\n\nCréons votre profil de jeu pour des performances optimales et le suivi des récompenses.",
        
        'step_3_activation': "⚡ **Étape 3: Activation Compte**\nAvez-vous activé avec Epic Games?",
        'activation_guidance': "🔗 **Activation Requise**\n\nConnectez votre cloud gaming à Epic Games pour sauvegarder la progression et activer les récompenses.",
        
        'step_4_epic': "👤 **Étape 4: Profil Epic**\nVotre profil Epic Games est-il complet?",
        'epic_guidance': "🎮 **Finalisation Profil**\n\nFinalisez votre profil Epic pour un accès complet aux fonctionnalités et l'éligibilité aux récompenses.",
        
        'step_5_shortcut': "📱 **Étape 5: Accès Rapide**\nAvez-vous ajouté le jeu à votre écran d'accueil?",
        'shortcut_guidance': "🚀 **Accès Instantané**\n\nLes raccourcis écran d'accueil offrent le lancement le plus rapide et une meilleure expérience.",
        
        'step_6_launch': "🎯 **Étape 6: Lancement Jeu**\nAvez-vous lancé le jeu avec succès?",
        'launch_guidance': "🕹️ **Jeu Prêt**\n\nAssurons-nous que le jeu se lance correctement pour un gameplay fluide.",
        
        'step_7_reward_island': "🏝️ **Étape 7: Accès Récompenses**\nÊtes-vous sur l'Île des Récompenses?",
        'reward_guidance': "💰 **Zone de Gains**\n\nL'Île des Récompenses est l'endroit où vous accumulez des points et débloquez des récompenses exclusives.",
        'code_display': "🔑 **Codes d'Accès:**\n{}\n\nCopiez n'importe quel code → Barre de recherche jeu → Commencez à gagner!",
        
        'step_8_full_setup': "⚙️ **Étape 8: Configuration Complète**\nVotre configuration complète est-elle terminée?",
        'setup_guidance': "🎪 **Configuration Optimale**\n\nLa configuration complète assure des gains maximum avec des amis et un gameplay fluide.",
        
        'step_9_commitment': "⏰ **Étape 9: Objectifs Hebdomadaires**\nPouvez-vous vous engager à 130 heures par semaine?",
        'commitment_guidance': "🏆 **Exigences Récompenses**\n\nUn temps de jeu constant est essentiel pour débloquer les meilleures récompenses et bonus.",
        
        'step_10_engagement': "👍 **Étape 10: Engagement**\nCliquerez-vous sur 'J'aime' avant la fin de chaque session?",
        'engagement_guidance': "📊 **Suivi Activité**\n\nLe bouton 'J'aime' nous aide à suivre votre engagement pour le calcul des récompenses.",
        
        'step_11_favorites': "⭐ **Étape 11: Accès Rapide**\nL'Île des Récompenses est-elle sauvegardée dans les favoris?",
        'favorites_guidance': "🚀 **Gaming Efficace**\n\nLes favoris économisent du temps et assurent que vous êtes toujours dans la zone de gains.",
        
        'step_12_influencer': "📢 **Étape 12: Communauté**\nUn influenceur vous a-t-il amené ici?",
        'influencer_prompt': "👥 **Reconnaissance Communauté**\n\nVeuillez partager le nom de l'influenceur pour attribution correcte:",
        
        # Existing Player Flow
        'existing_welcome': "⚡ **Vérification Joueur**\n\nBon retour! Vérifions votre configuration et maximisons vos récompenses.",
        'existing_cloud_note': "💡 *Vous connaissez la routine: sessions de 1 heure, relancez pour continuer.*",
        
        # Support Flow
        'support_welcome': "🆘 **Support & Vérification Récompenses**\n\nIdentifions les problèmes et vérifions votre éligibilité aux récompenses! 💰",
        'support_success': "✅ **Vérification Terminée!**\n\nNotre équipe examinera votre cas et vous contactera dans les 24 heures.",
        
        # AI Chat
        'ai_welcome': "🤖 **Assistant IA Gaming**\n\nBonjour! Je suis votre assistant IA gaming. Demandez-moi n'importe quoi sur:\n\n• Configuration jeu & paramètres\n• Système de récompenses & conseils de gains\n• Résolution de problèmes\n• Meilleures pratiques pour des récompenses maximum\n\n*Tapez votre question ci-dessous ou utilisez le menu pour revenir:*",
        'ai_thinking': "💭 Réflexion...",
        'ai_support_suggestion': "\n\n🔔 *Si vous avez besoin d'un support personnalisé, envisagez d'utiliser l'option Support dans le menu principal.*",
        
        # Common Responses
        'yes_option': "✅ Oui",
        'no_option': "❌ Non", 
        'need_help': "🆘 J'ai besoin d'aide",
        'already_done': "✅ Déjà fait",
        'skip_step': "⏭️ Passer",
        'continue_next': "➡️ Continuer",
        'back_previous': "⬅️ Retour",
        'main_menu': "🏠 Menu Principal",
        'join_channel': "📚 Rejoindre Chaîne",
        'back_to_chat': "💬 Retour au Chat",
        
        # Channel and Links
        'channel_invite': "Rejoignez notre communauté pour des guides, astuces et support:",
        'channel_instructions': "Consultez notre chaîne pour des instructions détaillées:",
        
        # Support Specific
        'provide_username': "👤 **Configuration Contact**\n\nVeuillez fournir votre nom d'utilisateur Telegram (commençant par @) pour le support:",
        'username_saved': "✅ **Informations Reçues!**\n\nL'équipe de support vous contactera bientôt. Continuez à jouer!",
        'invalid_username': "❌ Veuillez fournir un @username valide",
    }
}

# --- DATABASE FUNCTIONS ---
def get_player_progress(user_id):
    """Get player progress from database"""
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM player_progress WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'user_id': result[0],
                'player_type': result[1],
                'current_step': result[2],
                'completed_steps': json.loads(result[3]),
                'vpn_used': bool(result[4]),
                'profile_created': bool(result[5]),
                'epic_activated': bool(result[6]),
                'game_launched': bool(result[7]),
                'reward_island_found': bool(result[8]),
                'full_setup_complete': bool(result[9]),
                'playtime_hours': result[10],
                'like_clicks': result[11],
                'favorites_saved': bool(result[12]),
                'influencer_name': result[13],
                'language': result[14]
            }
        return None
    except Exception as e:
        logger.error(f"Database error in get_player_progress: {e}")
        return None

def update_player_progress(user_id, updates):
    """Update player progress in database"""
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = conn.cursor()
        
        # Build update query dynamically
        set_clause = []
        values = []
        
        for key, value in updates.items():
            if key == 'completed_steps' and isinstance(value, list):
                value = json.dumps(value)
            set_clause.append(f"{key} = ?")
            values.append(value)
        
        values.append(user_id)
        
        query = f'''
            INSERT OR REPLACE INTO player_progress 
            (user_id, {', '.join(updates.keys())}, updated_at)
            VALUES (?, {', '.join(['?' for _ in updates])}, CURRENT_TIMESTAMP)
        '''
        
        cursor.execute(query, [user_id] + values[:-1])
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Database error in update_player_progress: {e}")
        return False

def create_support_case(user_id, username, case_type, issue_desc, steps_completed):
    """Create a support case in database"""
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO support_cases 
            (user_id, username, case_type, issue_description, steps_completed)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, case_type, issue_desc, json.dumps(steps_completed)))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Database error in create_support_case: {e}")
        return False

def save_chat_conversation(user_id, user_message, ai_response):
    """Save chat conversation to database"""
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO chat_conversations 
            (user_id, user_message, ai_response)
            VALUES (?, ?, ?)
        ''', (user_id, user_message, ai_response))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Database error in save_chat_conversation: {e}")
        return False

# --- ENHANCED AI ASSISTANT FUNCTION ---
async def gaming_assistant_response(user_message, user_context, lang):
    """AI assistant for gaming-related queries with enhanced support suggestion"""
    if not openai_client:
        return "I'm currently learning more about gaming setups. For now, please use the structured menus for assistance."
    
    try:
        # Enhanced system prompt for gaming focus with support suggestion
        system_prompt = f"""You are a gaming assistant specialist helping users with Fortnite cloud gaming setup and rewards.

Key Knowledge:
- Cloud gaming sessions: 1-hour duration
- VPN requirement: USA VPN for profile creation only
- Reward system: Based on playtime and engagement
- Weekly target: 130 hours for optimal rewards
- Key steps: Profile setup, activation, reward island access
- Support process: Users can contact support via menu

User Context: {user_context}

Respond helpfully and concisely in {lang.upper()} language. 
If the user seems to have complex issues that require personal assistance, gently suggest using the Support option.
Keep responses conversational and engaging."""

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Add support suggestion for complex issues
        support_keywords = ['problem', 'issue', 'error', 'not working', 'help', 'support', 'trouble', 'fix', 'broken']
        if any(keyword in user_message.lower() for keyword in support_keywords):
            texts = BOT_TEXTS[lang]
            ai_response += texts['ai_support_suggestion']
        
        return ai_response
    except Exception as e:
        logger.error(f"AI assistant error: {e}")
        return "I'm having trouble processing your request. Please try the menu options for specific help."

# --- ENHANCED FLOW MANAGEMENT ---
class FlowManager:
    """Manages different user flows with improved state handling"""
    
    def __init__(self):
        self.flows = {
            'new_player': self.new_player_flow,
            'existing_player': self.existing_player_flow,
            'support': self.support_flow
        }
    
    async def new_player_flow(self, update, context, step_number):
        """Enhanced new player flow with better step management"""
        user_id = update.effective_user.id
        lang = context.user_data.get('lang', 'en')
        texts = BOT_TEXTS[lang]
        
        flow_steps = {
            1: {
                'text': texts['step_1_vpn'],
                'keyboard': [
                    [InlineKeyboardButton(texts['yes_option'], callback_data='new_q1_yes')],
                    [InlineKeyboardButton(texts['no_option'], callback_data='new_q1_no')],
                    [InlineKeyboardButton(texts['back_previous'], callback_data='back_to_main')]
                ]
            },
            2: {
                'text': texts['step_2_profile'],
                'keyboard': [
                    [InlineKeyboardButton(texts['yes_option'], callback_data='new_q2_yes')],
                    [InlineKeyboardButton(texts['no_option'], callback_data='new_q2_no')],
                    [InlineKeyboardButton(texts['back_previous'], callback_data='new_back_1')]
                ]
            },
            # Add more steps as needed
        }
        
        current_step = flow_steps.get(step_number)
        if not current_step:
            return await self.complete_flow(update, context, 'new_player')
        
        query = update.callback_query
        if query:
            await query.edit_message_text(
                text=current_step['text'],
                reply_markup=InlineKeyboardMarkup(current_step['keyboard']),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                text=current_step['text'],
                reply_markup=InlineKeyboardMarkup(current_step['keyboard']),
                parse_mode='Markdown'
            )
        
        return NEW_PLAYER_FLOW
    
    async def existing_player_flow(self, update, context, step_number):
        """Enhanced existing player verification flow"""
        user_id = update.effective_user.id
        lang = context.user_data.get('lang', 'en')
        texts = BOT_TEXTS[lang]
        
        welcome_text = f"{texts['existing_welcome']}\n\n{texts['existing_cloud_note']}"
        
        keyboard = [
            [InlineKeyboardButton(texts['continue_next'], callback_data='existing_continue')],
            [InlineKeyboardButton(texts['back_previous'], callback_data='back_to_main')]
        ]
        
        query = update.callback_query
        if query:
            await query.edit_message_text(
                text=welcome_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                text=welcome_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        
        return EXISTING_PLAYER_FLOW
    
    async def support_flow(self, update, context, step_number):
        """Enhanced support and verification flow"""
        user_id = update.effective_user.id
        lang = context.user_data.get('lang', 'en')
        texts = BOT_TEXTS[lang]
        
        if step_number == 1:
            welcome_text = texts['support_welcome']
            keyboard = [
                [InlineKeyboardButton(texts['continue_next'], callback_data='support_continue')],
                [InlineKeyboardButton(texts['back_previous'], callback_data='back_to_main')]
            ]
            
            query = update.callback_query
            if query:
                await query.edit_message_text(
                    text=welcome_text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
            return SUPPORT_FLOW
        
        elif step_number == 2:
            username_text = texts['provide_username']
            keyboard = [
                [InlineKeyboardButton(texts['back_previous'], callback_data='support_back_1')]
            ]
            
            query = update.callback_query
            if query:
                await query.edit_message_text(
                    text=username_text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
            return USERNAME_COLLECTION
    
    async def complete_flow(self, update, context, flow_type):
        """Handle flow completion with reward tracking"""
        user_id = update.effective_user.id
        lang = context.user_data.get('lang', 'en')
        texts = BOT_TEXTS[lang]
        
        completion_message = {
            'new_player': "🎉 **Setup Complete!** You're ready to start earning rewards!",
            'existing_player': "✅ **Check-In Complete!** Your setup is optimized for maximum rewards!",
            'support': "🆗 **Case Logged!** Our team will contact you within 24 hours."
        }
        
        keyboard = [
            [InlineKeyboardButton(texts['main_menu'], callback_data="back_to_main")],
            [InlineKeyboardButton(texts['join_channel'], url=HELPFUL_CHANNEL_LINK)]
        ]
        
        query = update.callback_query
        if query:
            await query.edit_message_text(
                text=completion_message[flow_type],
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                text=completion_message[flow_type],
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        
        return MAIN_MENU

# Initialize flow manager
flow_manager = FlowManager()

# --- ENHANCED MESSAGE HANDLER ---
async def handle_intelligent_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Enhanced message handler with AI assistance"""
    user_message = update.message.text
    user_id = update.message.from_user.id
    lang = context.user_data.get('lang', 'en')
    
    # Get user context from database
    user_progress = get_player_progress(user_id)
    user_context = {
        'progress': user_progress,
        'current_flow': context.user_data.get('current_flow', 'general'),
        'language': lang
    }
    
    # Show typing action
    await update.message.chat.send_action(action="typing")
    
    # Get AI response
    ai_response = await gaming_assistant_response(user_message, user_context, lang)
    
    # Save conversation to database
    save_chat_conversation(user_id, user_message, ai_response)
    
    # Create response with menu options
    texts = BOT_TEXTS[lang]
    keyboard = [
        [InlineKeyboardButton(texts['back_to_chat'], callback_data="continue_ai_chat")],
        [InlineKeyboardButton(texts['support_option'], callback_data="start_support")],
        [InlineKeyboardButton(texts['main_menu'], callback_data="back_to_main")]
    ]
    
    await update.message.reply_text(
        text=ai_response,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return AI_CHAT

# --- AI CHAT FLOW ---
async def start_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start AI chat conversation"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    texts = BOT_TEXTS[lang]
    
    context.user_data['current_flow'] = 'ai_chat'
    context.user_data['current_state'] = AI_CHAT
    
    keyboard = [
        [InlineKeyboardButton(texts['main_menu'], callback_data="back_to_main")],
        [InlineKeyboardButton(texts['support_option'], callback_data="start_support")]
    ]
    
    await query.edit_message_text(
        text=texts['ai_welcome'],
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return AI_CHAT

async def continue_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Continue AI chat conversation"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    texts = BOT_TEXTS[lang]
    
    keyboard = [
        [InlineKeyboardButton(texts['main_menu'], callback_data="back_to_main")],
        [InlineKeyboardButton(texts['support_option'], callback_data="start_support")]
    ]
    
    await query.edit_message_text(
        text=texts['ai_welcome'],
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return AI_CHAT

# --- ENHANCED MAIN MENU ---
async def show_enhanced_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str = None):
    """Show enhanced main menu with better organization"""
    lang = context.user_data.get('lang', 'en')
    texts = BOT_TEXTS[lang]
    
    context.user_data['current_flow'] = 'general'
    context.user_data['current_state'] = MAIN_MENU
    
    welcome_text = message or f"{texts['welcome_title']}\n\n{texts['welcome_subtitle']}\n\n{texts['disclaimer']}"
    
    keyboard = [
        [InlineKeyboardButton(texts['new_player_option'], callback_data="start_new_player")],
        [InlineKeyboardButton(texts['existing_player_option'], callback_data="start_existing_player")],
        [InlineKeyboardButton(texts['support_option'], callback_data="start_support")],
        [InlineKeyboardButton(texts['ai_chat_option'], callback_data="start_ai_chat")],
        [
            InlineKeyboardButton(texts['channel_option'], callback_data="show_channel"),
            InlineKeyboardButton(texts['language_option'], callback_data="change_language")
        ]
    ]
    
    query = update.callback_query
    if query:
        await query.answer()
        try:
            await query.edit_message_text(
                text=welcome_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.warning(f"Menu edit failed: {e}")
    else:
        await update.message.reply_text(
            text=welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    return MAIN_MENU

# --- FLOW START HANDLERS ---
async def start_new_player_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start enhanced new player flow"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = context.user_data.get('lang', 'en')
    
    # Initialize player progress
    update_player_progress(user_id, {
        'player_type': 'new',
        'current_step': 1,
        'completed_steps': [],
        'language': lang
    })
    
    context.user_data['current_flow'] = 'new_player'
    context.user_data['current_state'] = NEW_PLAYER_FLOW
    context.user_data['current_step'] = 1
    
    return await flow_manager.new_player_flow(update, context, 1)

async def start_existing_player_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start enhanced existing player flow"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = context.user_data.get('lang', 'en')
    
    # Update player progress
    update_player_progress(user_id, {
        'player_type': 'existing',
        'current_step': 1,
        'language': lang
    })
    
    context.user_data['current_flow'] = 'existing_player'
    context.user_data['current_state'] = EXISTING_PLAYER_FLOW
    context.user_data['current_step'] = 1
    
    return await flow_manager.existing_player_flow(update, context, 1)

async def start_support_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start enhanced support flow"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = context.user_data.get('lang', 'en')
    
    context.user_data['current_flow'] = 'support'
    context.user_data['current_state'] = SUPPORT_FLOW
    context.user_data['current_step'] = 1
    context.user_data['support_answers'] = []
    
    return await flow_manager.support_flow(update, context, 1)

# --- SUPPORT USERNAME HANDLER ---
async def handle_support_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle support username collection"""
    user_message = update.message.text
    user_id = update.message.from_user.id
    lang = context.user_data.get('lang', 'en')
    texts = BOT_TEXTS[lang]
    
    # Validate username format
    if not user_message.startswith('@') or len(user_message) < 2:
        await update.message.reply_text(texts['invalid_username'])
        return USERNAME_COLLECTION
    
    # Create support case
    user_progress = get_player_progress(user_id)
    steps_completed = user_progress['completed_steps'] if user_progress else []
    
    create_support_case(
        user_id=user_id,
        username=user_message,
        case_type='general_support',
        issue_description='User requested support via AI chat suggestion',
        steps_completed=steps_completed
    )
    
    # Send confirmation
    keyboard = [
        [InlineKeyboardButton(texts['main_menu'], callback_data="back_to_main")]
    ]
    
    await update.message.reply_text(
        text=texts['username_saved'],
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return MAIN_MENU

# --- CHANNEL AND LANGUAGE HANDLERS ---
async def show_channel_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show channel information"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    texts = BOT_TEXTS[lang]
    
    keyboard = [
        [InlineKeyboardButton(texts['join_channel'], url=HELPFUL_CHANNEL_LINK)],
        [InlineKeyboardButton(texts['main_menu'], callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        text=texts['channel_invite'],
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )
    
    return MAIN_MENU

async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Change language preference"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [
            InlineKeyboardButton("English 🇬🇧", callback_data="set_lang_en"),
            InlineKeyboardButton("Français 🇫🇷", callback_data="set_lang_fr")
        ],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        text="🌐 **Select your language / Choisissez votre langue:**",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return MAIN_MENU

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Set user language preference"""
    query = update.callback_query
    lang = query.data.replace('set_lang_', '')
    context.user_data['lang'] = lang
    
    # Update in database if user exists
    user_id = update.effective_user.id
    update_player_progress(user_id, {'language': lang})
    
    await query.answer(f"Language set to {lang.upper()}")
    return await show_enhanced_menu(update, context)

# --- BUTTON HANDLERS ---
async def handle_new_player_answers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle new player flow answers"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == 'new_q1_yes':
        # Handle VPN yes answer
        user_id = update.effective_user.id
        update_player_progress(user_id, {'vpn_used': True})
        return await flow_manager.new_player_flow(update, context, 2)
    
    elif data == 'new_q1_no':
        # Handle VPN no answer
        return await flow_manager.new_player_flow(update, context, 1)
    
    elif data == 'new_back_1':
        return await flow_manager.new_player_flow(update, context, 1)
    
    return NEW_PLAYER_FLOW

async def handle_existing_player_answers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle existing player flow answers"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == 'existing_continue':
        return await flow_manager.complete_flow(update, context, 'existing_player')
    
    return EXISTING_PLAYER_FLOW

async def handle_support_answers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle support flow answers"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == 'support_continue':
        return await flow_manager.support_flow(update, context, 2)
    
    elif data == 'support_back_1':
        return await flow_manager.support_flow(update, context, 1)
    
    return SUPPORT_FLOW

# --- ERROR HANDLER ---
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors gracefully"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    if isinstance(context.error, Conflict):
        logger.warning("Bot conflict detected - another instance might be running")
        return
    
    try:
        if update and update.effective_message:
            lang = context.user_data.get('lang', 'en')
            texts = BOT_TEXTS[lang]
            await update.effective_message.reply_text(
                "⚠️ Sorry, I encountered an error. Please try again or use the menu options."
            )
    except Exception as e:
        logger.error(f"Error while sending error message: {e}")

# --- START COMMAND ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Enhanced start command with better presentation"""
    user = update.effective_user
    welcome_text = (
        "🎮 **Welcome to the Ultimate Gaming Assistant!**\n\n"
        "I'm here to help you:\n"
        "• Set up your gaming account 🚀\n"
        "• Maximize your rewards 💰\n"
        "• Resolve any issues 🛠️\n"
        "• Connect with our community 👥\n\n"
        "🔒 *Unofficial Guide - Not affiliated with Epic Games/Fortnite*\n\n"
        "Choose your language below:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("English 🇬🇧", callback_data="set_lang_en"),
            InlineKeyboardButton("Français 🇫🇷", callback_data="set_lang_fr")
        ]
    ]
    
    await update.message.reply_text(
        text=welcome_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return SELECT_LANGUAGE

# --- MAIN APPLICATION SETUP ---
def main() -> None:
    """Run the enhanced gaming bot"""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN environment variable not set!")
        print("❌ ERROR: TELEGRAM_TOKEN is required!")
        return

    # Create application with enhanced settings
    application = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .read_timeout(30)
        .write_timeout(30)
        .connect_timeout(30)
        .pool_timeout(30)
        .build()
    )

    # Add error handler
    application.add_error_handler(error_handler)

    # Enhanced conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_LANGUAGE: [
                CallbackQueryHandler(set_language, pattern="^set_lang_(en|fr)$")
            ],
            MAIN_MENU: [
                CallbackQueryHandler(start_new_player_flow, pattern="^start_new_player$"),
                CallbackQueryHandler(start_existing_player_flow, pattern="^start_existing_player$"),
                CallbackQueryHandler(start_support_flow, pattern="^start_support$"),
                CallbackQueryHandler(start_ai_chat, pattern="^start_ai_chat$"),
                CallbackQueryHandler(show_channel_info, pattern="^show_channel$"),
                CallbackQueryHandler(change_language, pattern="^change_language$"),
                CallbackQueryHandler(show_enhanced_menu, pattern="^back_to_main$"),
            ],
            NEW_PLAYER_FLOW: [
                CallbackQueryHandler(handle_new_player_answers, pattern="^new_"),
                CallbackQueryHandler(show_enhanced_menu, pattern="^back_to_main$"),
            ],
            EXISTING_PLAYER_FLOW: [
                CallbackQueryHandler(handle_existing_player_answers, pattern="^existing_"),
                CallbackQueryHandler(show_enhanced_menu, pattern="^back_to_main$"),
            ],
            SUPPORT_FLOW: [
                CallbackQueryHandler(handle_support_answers, pattern="^support_"),
                CallbackQueryHandler(show_enhanced_menu, pattern="^back_to_main$"),
            ],
            USERNAME_COLLECTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_support_username),
                CallbackQueryHandler(show_enhanced_menu, pattern="^back_to_main$"),
            ],
            AI_CHAT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_intelligent_message),
                CallbackQueryHandler(continue_ai_chat, pattern="^continue_ai_chat$"),
                CallbackQueryHandler(start_support_flow, pattern="^start_support$"),
                CallbackQueryHandler(show_enhanced_menu, pattern="^back_to_main$"),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
        per_message=False,
    )

    application.add_handler(conv_handler)

    # Enhanced startup message
    logger.info("Enhanced Gaming Bot starting...")
    print("🎮 ENHANCED GAMING BOT STARTING...")
    print("=" * 50)
    print(f"✅ TELEGRAM_TOKEN: {'Set' if TELEGRAM_TOKEN else 'Not Set'}")
    print(f"✅ SUPPORT_CHAT_ID: {'Set' if SUPPORT_CHAT_ID else 'Not Set'}")
    print(f"✅ OPENAI_API_KEY: {'Set' if OPENAI_API_KEY else 'Not Set'}")
    print(f"✅ OPENAI_CLIENT: {'Available' if openai_client else 'Not Available'}")
    print(f"✅ DATABASE: Enhanced schema at {DB_FILE}")
    print("🚀 FEATURES: AI Assistant, Progress Tracking, Multi-Language")
    print("🎯 FLOWS: New Player, Existing Player, Support, AI Chat")
    print("🛡️ ERROR HANDLING: Enhanced with conflict resolution")
    print("=" * 50)
    
    # Start the bot with enhanced configuration
    try:
        application.run_polling(
            poll_interval=1.0,
            timeout=30,
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
    except Conflict as e:
        logger.warning(f"Bot conflict on startup: {e}")
        print("⚠️ Another instance detected - normal in deployment")
    except Exception as e:
        logger.error(f"Failed to start enhanced bot: {e}")
        print(f"❌ Enhanced bot failed: {e}")

if __name__ == "__main__":
    main()

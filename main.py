import logging
import os
import asyncio
import datetime
import json
import re
import time
import random
from typing import Dict, List, Set

try:
    from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        ApplicationBuilder,
        ContextTypes,
        CommandHandler,
        MessageHandler,
        CallbackQueryHandler,
        filters,
    )
except ImportError:
    print("تم تثبيت python-telegram-bot بنجاح!")

# إعداد نظام تسجيل الأخطاء
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# الحصول على رمز البوت من متغيرات البيئة مع قيمة احتياطية
BOT_TOKEN = os.getenv("BOT_TOKEN", "5550839700:AAF2aVMPHDZE4kRhmrj_fIBYkaD5uSH019o")

# معرفات المطورين - يمكن الإضافة عليها
DEVELOPER_IDS = {123456789, 599637471}  # معرفات المطورين بالأرقام
DEVELOPER_USERNAMES = {"pps_s", "ppx_s"}  # أسماء المستخدمين للمطورين

# قوائم وقواعد بيانات عامة
global_banned_users = set()
user_warnings = {}  # تحذيرات المستخدمين
chat_settings = {}  # إعدادات المجموعات
user_stats = {}  # إحصائيات المستخدمين
welcome_messages = {}  # رسائل الترحيب المخصصة
auto_delete_timer = {}  # مؤقت الحذف التلقائي
flood_control = {}  # مراقبة السبام
muted_users = {}  # المستخدمون المكتومون مؤقتاً
link_whitelist = {}  # الروابط المسموحة
bad_words = {}  # الكلمات المحظورة

# الأنظمة الجديدة
auto_replies = {}  # نظام الردود التلقائية
chat_notes = {}  # نظام النوتات
quizzes = {}  # نظام المسابقات
user_activity = {}  # تتبع نشاط المستخدمين
welcome_media = {}  # صور الترحيب

bot_stats = {
    'total_commands': 0,
    'groups_count': 0,
    'messages_deleted': 0,
    'users_banned': 0,
    'warnings_given': 0,
    'start_time': datetime.datetime.now(),
    'messages_processed': 0,
    'groups_managed': set(),
    'active_users': set(),
    'auto_replies_triggered': 0,
    'notes_saved': 0,
    'quizzes_created': 0
}

# -------------------- وظائف المطور --------------------
async def is_developer(update: Update) -> bool:
    """التحقق من أن المستخدم هو أحد المطورين"""
    user = update.effective_user
    if user.id in DEVELOPER_IDS:
        return True
    if user.username and user.username in DEVELOPER_USERNAMES:
        return True
    return False

async def update_stats(stat_name: str, increment: int = 1):
    """تحديث الإحصائيات"""
    if stat_name in bot_stats:
        bot_stats[stat_name] += increment

# -------------------- التحقق من صلاحيات الإدارة --------------------
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """التحقق من أن المستخدم مدير في المجموعة"""
    try:
        # إذا كان المستخدم مطور، فهو مدير تلقائياً
        if await is_developer(update):
            return True

        chat_member = await context.bot.get_chat_member(
            update.effective_chat.id, 
            update.effective_user.id
        )
        return chat_member.status in ['creator', 'administrator']
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False

async def is_bot_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """التحقق من أن البوت مدير في المجموعة"""
    try:
        bot_member = await context.bot.get_chat_member(
            update.effective_chat.id, 
            context.bot.id
        )
        return bot_member.status in ['administrator']
    except Exception as e:
        logger.error(f"Error checking bot admin status: {e}")
        return False

# -------------------- دوال مساعدة متقدمة --------------------
def init_chat_settings(chat_id: int):
    """تهيئة إعدادات المجموعة"""
    if chat_id not in chat_settings:
        chat_settings[chat_id] = {
            'lock_photos': False,
            'lock_videos': False,
            'lock_audio': False,
            'lock_stickers': False,
            'lock_gifs': False,
            'lock_files': False,
            'lock_links': False,
            'lock_bots': False,
            'lock_voice': False,
            'lock_forwarded': False,
            'welcome_enabled': True,
            'auto_delete_enabled': False,
            'auto_delete_time': 0,
            'flood_limit': 5,
            'flood_time': 10,
            'warn_limit': 3,
            'anti_spam': True,
            'link_filter': False,
            'word_filter': False,
            'auto_ban_bots': False,
            'delete_service_messages': True,
            'report_mode': False,
            'auto_reply_enabled': True,
            'quiz_enabled': True
        }

def init_chat_data(chat_id: int):
    """تهيئة بيانات المجموعة الجديدة"""
    if chat_id not in auto_replies:
        auto_replies[chat_id] = {}
    if chat_id not in chat_notes:
        chat_notes[chat_id] = {}
    if chat_id not in quizzes:
        quizzes[chat_id] = {}
    if chat_id not in user_activity:
        user_activity[chat_id] = {}
    if chat_id not in welcome_media:
        welcome_media[chat_id] = None

def check_flood(user_id: int, chat_id: int) -> bool:
    """فحص السبام"""
    current_time = time.time()
    key = f"{chat_id}_{user_id}"

    if key not in flood_control:
        flood_control[key] = []

    # إزالة الرسائل القديمة
    flood_control[key] = [t for t in flood_control[key] if current_time - t < chat_settings.get(chat_id, {}).get('flood_time', 10)]

    # إضافة الرسالة الحالية
    flood_control[key].append(current_time)

    # فحص الحد الأقصى
    return len(flood_control[key]) > chat_settings.get(chat_id, {}).get('flood_limit', 5)

async def add_warning(user_id: int, chat_id: int, reason: str = "مخالفة القوانين"):
    """إضافة تحذير للمستخدم"""
    key = f"{chat_id}_{user_id}"
    if key not in user_warnings:
        user_warnings[key] = []

    warning = {
        'reason': reason,
        'time': datetime.datetime.now(),
        'count': len(user_warnings[key]) + 1
    }

    user_warnings[key].append(warning)
    await update_stats('warnings_given')

    return len(user_warnings[key])

def update_user_activity(chat_id: int, user_id: int):
    """تحديث نشاط المستخدم"""
    if chat_id not in user_activity:
        user_activity[chat_id] = {}
    
    if user_id not in user_activity[chat_id]:
        user_activity[chat_id][user_id] = {
            'messages': 0,
            'last_activity': datetime.datetime.now(),
            'join_date': datetime.datetime.now(),
            'warnings': 0
        }
    
    user_activity[chat_id][user_id]['messages'] += 1
    user_activity[chat_id][user_id]['last_activity'] = datetime.datetime.now()

# -------------------- أوامر عامة --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة الترحيب وعرض الأوامر المتوفرة"""
    welcome_message = (
        "🚀 **أهلاً بك! أنا بوت الحماية المتقدم للمجموعات**\n\n"
        "🔰 **الأوامر الأساسية:**\n"
        "🔹 **طرد** (بالرد) → طرد عضو\n"
        "🔹 **حظر** (بالرد) → حظر عضو نهائياً\n"
        "🔹 **تقييد** (بالرد) → منع العضو من الكتابة\n"
        "🔹 **رفع التقييد** (بالرد) → إلغاء التقييد\n"
        "🔹 **كتم** (بالرد) [المدة] → كتم مؤقت (مثال: كتم 1h)\n"
        "🔹 **إلغاء الكتم** (بالرد) → إلغاء الكتم\n\n"

        "⚠️ **نظام التحذيرات:**\n"
        "🔹 **تحذير** (بالرد) [السبب] → إعطاء تحذير\n"
        "🔹 **حذف التحذيرات** (بالرد) → مسح تحذيرات العضو\n"
        "🔹 **عرض التحذيرات** (بالرد) → عرض تحذيرات العضو\n\n"

        "🔒 **أوامر القفل والحماية:**\n"
        "🔹 **قفل الصور** / **فتح الصور**\n"
        "🔹 **قفل الفيديو** / **فتح الفيديو**\n"
        "🔹 **قفل الصوت** / **فتح الصوت**\n"
        "🔹 **قفل الملصقات** / **فتح الملصقات**\n"
        "🔹 **قفل المتحركات** / **فتح المتحركات**\n"
        "🔹 **قفل الملفات** / **فتح الملفات**\n"
        "🔹 **قفل الروابط** / **فتح الروابط**\n"
        "🔹 **قفل الصوتيات** / **فتح الصوتيات**\n"
        "🔹 **قفل البوتات** / **فتح البوتات**\n"
        "🔹 **قفل المحول** / **فتح المحول**\n"
        "🔹 **قفل الكل** / **فتح الكل**\n\n"

        "📊 **أوامر المعلومات:**\n"
        "🔹 **معلومات العضو** (بالرد) → تفاصيل العضو\n"
        "🔹 **معلومات المجموعة** → إحصائيات المجموعة\n"
        "🔹 **قائمة المدراء** → عرض المدراء\n"
        "🔹 **الإعدادات** → عرض إعدادات المجموعة\n\n"

        "🧹 **أوامر التنظيف:**\n"
        "🔹 **حذف** [العدد] → حذف رسائل (مثال: حذف 50)\n"
        "🔹 **تنظيف الصور** → حذف جميع الصور\n"
        "🔹 **تنظيف الملصقات** → حذف جميع الملصقات\n"
        "🔹 **تنظيف البوتات** → حذف رسائل البوتات\n\n"

        "🤖 **الميزات الجديدة:**\n"
        "🔹 **اضافة رد** [الكلمة] [الرد] → إضافة رد تلقائي\n"
        "🔹 **حذف رد** [الكلمة] → حذف رد تلقائي\n"
        "🔹 **قائمة الردود** → عرض جميع الردود\n"
        "🔹 **حفظ** [اسم] [النص] → حفظ نوتة\n"
        "🔹 **جلب** [اسم] → جلب نوتة\n"
        "🔹 **النوتات** → عرض جميع النوتات\n"
        "🔹 **مسابقة** [السؤال] [الإجابة] → إنشاء مسابقة\n"
        "🔹 **ترحيب** [النص] → تعديل رسالة الترحيب\n"
        "🔹 **نشاط** (بالرد) → عرض نشاط العضو\n\n"

        "👨‍💻 **أوامر المطور:**\n"
        "🔹 **لوحة المطور** → لوحة التحكم\n"
        "🔹 **إحصائيات شاملة** → تقرير مفصل\n"

        "⚠️ **ملاحظة:** الأوامر الإدارية متاحة للمدراء فقط\n"
        f"🆔 **معرفك:** `{update.effective_user.id}`"
    )

    try:
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        await update_stats('total_commands')

        # تسجيل المجموعة الجديدة
        if update.effective_chat.type in ['group', 'supergroup']:
            bot_stats['groups_managed'].add(update.effective_chat.id)
            init_chat_settings(update.effective_chat.id)
            init_chat_data(update.effective_chat.id)

        bot_stats['active_users'].add(update.effective_user.id)

    except Exception as e:
        logger.error(f"Error in start command: {e}")

# -------------------- نظام الردود التلقائية --------------------
async def add_auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إضافة رد تلقائي جديد"""
    if not await is_admin(update, context):
        await update.message.reply_text("❌ هذا الأمر للمدراء فقط.")
        return

    try:
        # استخراج الكلمة والرد من النص
        text_parts = update.message.text.split(maxsplit=2)
        if len(text_parts) < 3:
            await update.message.reply_text(
                "❌ الصيغة الصحيحة:\n"
                "**اضافة رد** [الكلمة] [الرد]\n\n"
                "مثال: **اضافة رد** مرحبا أهلاً وسهلاً بك!",
                parse_mode='Markdown'
            )
            return

        trigger_word = text_parts[1].lower()
        reply_text = text_parts[2]
        chat_id = update.effective_chat.id

        init_chat_data(chat_id)
        auto_replies[chat_id][trigger_word] = {
            'reply': reply_text,
            'created_by': update.effective_user.id,
            'created_at': datetime.datetime.now(),
            'usage_count': 0
        }

        await update.message.reply_text(
            f"✅ تم إضافة رد تلقائي جديد!\n\n"
            f"🔤 **الكلمة:** {trigger_word}\n"
            f"💬 **الرد:** {reply_text}",
            parse_mode='Markdown'
        )
        await update_stats('total_commands')

    except Exception as e:
        logger.error(f"Error in add_auto_reply: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء إضافة الرد.")

async def delete_auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف رد تلقائي"""
    if not await is_admin(update, context):
        await update.message.reply_text("❌ هذا الأمر للمدراء فقط.")
        return

    try:
        text_parts = update.message.text.split(maxsplit=1)
        if len(text_parts) < 2:
            await update.message.reply_text(
                "❌ الصيغة الصحيحة:\n"
                "**حذف رد** [الكلمة]",
                parse_mode='Markdown'
            )
            return

        trigger_word = text_parts[1].lower()
        chat_id = update.effective_chat.id

        if chat_id not in auto_replies or trigger_word not in auto_replies[chat_id]:
            await update.message.reply_text("❌ لا يوجد رد لهذه الكلمة.")
            return

        del auto_replies[chat_id][trigger_word]
        await update.message.reply_text(f"✅ تم حذف الرد التلقائي للكلمة: **{trigger_word}**", parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error in delete_auto_reply: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء حذف الرد.")

async def list_auto_replies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض جميع الردود التلقائية"""
    try:
        chat_id = update.effective_chat.id
        
        if chat_id not in auto_replies or not auto_replies[chat_id]:
            await update.message.reply_text("📝 لا توجد ردود تلقائية في هذه المجموعة.")
            return

        reply_list = "📋 **قائمة الردود التلقائية:**\n\n"
        for i, (trigger, data) in enumerate(auto_replies[chat_id].items(), 1):
            reply_list += f"🔹 **{i}.** {trigger} → {data['reply'][:50]}{'...' if len(data['reply']) > 50 else ''}\n"
            reply_list += f"   📊 استُخدم {data['usage_count']} مرة\n\n"

        await update.message.reply_text(reply_list, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error in list_auto_replies: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء عرض الردود.")

# -------------------- نظام النوتات --------------------
async def save_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حفظ نوتة جديدة"""
    if not await is_admin(update, context):
        await update.message.reply_text("❌ هذا الأمر للمدراء فقط.")
        return

    try:
        text_parts = update.message.text.split(maxsplit=2)
        if len(text_parts) < 3:
            await update.message.reply_text(
                "❌ الصيغة الصحيحة:\n"
                "**حفظ** [الاسم] [المحتوى]",
                parse_mode='Markdown'
            )
            return

        note_name = text_parts[1].lower()
        note_content = text_parts[2]
        chat_id = update.effective_chat.id

        init_chat_data(chat_id)
        chat_notes[chat_id][note_name] = {
            'content': note_content,
            'created_by': update.effective_user.id,
            'created_at': datetime.datetime.now(),
            'access_count': 0
        }

        await update.message.reply_text(
            f"✅ تم حفظ النوتة بنجاح!\n\n"
            f"📝 **الاسم:** {note_name}\n"
            f"📄 **المحتوى:** {note_content[:100]}{'...' if len(note_content) > 100 else ''}",
            parse_mode='Markdown'
        )
        await update_stats('notes_saved')

    except Exception as e:
        logger.error(f"Error in save_note: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء حفظ النوتة.")

async def get_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """جلب نوتة محفوظة"""
    try:
        text_parts = update.message.text.split(maxsplit=1)
        if len(text_parts) < 2:
            await update.message.reply_text(
                "❌ الصيغة الصحيحة:\n"
                "**جلب** [الاسم]",
                parse_mode='Markdown'
            )
            return

        note_name = text_parts[1].lower()
        chat_id = update.effective_chat.id

        if chat_id not in chat_notes or note_name not in chat_notes[chat_id]:
            await update.message.reply_text("❌ لا توجد نوتة بهذا الاسم.")
            return

        note_data = chat_notes[chat_id][note_name]
        note_data['access_count'] += 1

        await update.message.reply_text(
            f"📝 **{note_name}**\n\n{note_data['content']}",
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"Error in get_note: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء جلب النوتة.")

async def list_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض جميع النوتات"""
    try:
        chat_id = update.effective_chat.id
        
        if chat_id not in chat_notes or not chat_notes[chat_id]:
            await update.message.reply_text("📝 لا توجد نوتات محفوظة في هذه المجموعة.")
            return

        notes_list = "📋 **النوتات المحفوظة:**\n\n"
        for i, (name, data) in enumerate(chat_notes[chat_id].items(), 1):
            notes_list += f"🔹 **{i}.** {name} (استُخدمت {data['access_count']} مرة)\n"

        notes_list += f"\n💡 استخدم **جلب** [الاسم] لعرض أي نوتة"

        await update.message.reply_text(notes_list, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error in list_notes: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء عرض النوتات.")

# -------------------- نظام المسابقات --------------------
async def create_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إنشاء مسابقة جديدة"""
    if not await is_admin(update, context):
        await update.message.reply_text("❌ هذا الأمر للمدراء فقط.")
        return

    try:
        text_parts = update.message.text.split(maxsplit=2)
        if len(text_parts) < 3:
            await update.message.reply_text(
                "❌ الصيغة الصحيحة:\n"
                "**مسابقة** [السؤال] [الإجابة]",
                parse_mode='Markdown'
            )
            return

        question = text_parts[1]
        answer = text_parts[2].lower()
        chat_id = update.effective_chat.id

        quiz_id = f"quiz_{int(time.time())}"
        init_chat_data(chat_id)
        
        quizzes[chat_id][quiz_id] = {
            'question': question,
            'answer': answer,
            'created_by': update.effective_user.id,
            'created_at': datetime.datetime.now(),
            'participants': {},
            'solved': False,
            'solver': None
        }

        keyboard = [[InlineKeyboardButton("🏆 شارك في المسابقة", callback_data=f"join_quiz_{quiz_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"🎯 **مسابقة جديدة!**\n\n"
            f"❓ **السؤال:** {question}\n\n"
            f"💡 **كيفية المشاركة:** أرسل إجابتك في المجموعة\n"
            f"🏆 **الجائزة:** شرف الإجابة الصحيحة!",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        await update_stats('quizzes_created')

    except Exception as e:
        logger.error(f"Error in create_quiz: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء إنشاء المسابقة.")

# -------------------- نظام الترحيب المتقدم --------------------
async def set_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تعديل رسالة الترحيب"""
    if not await is_admin(update, context):
        await update.message.reply_text("❌ هذا الأمر للمدراء فقط.")
        return

    try:
        text_parts = update.message.text.split(maxsplit=1)
        if len(text_parts) < 2:
            await update.message.reply_text(
                "❌ الصيغة الصحيحة:\n"
                "**ترحيب** [نص الترحيب]\n\n"
                "💡 يمكنك استخدام:\n"
                "- {name} للاسم\n"
                "- {mention} للإشارة\n"
                "- {group} لاسم المجموعة",
                parse_mode='Markdown'
            )
            return

        welcome_text = text_parts[1]
        chat_id = update.effective_chat.id

        welcome_messages[chat_id] = {
            'text': welcome_text,
            'created_by': update.effective_user.id,
            'created_at': datetime.datetime.now()
        }

        await update.message.reply_text(
            f"✅ تم تعديل رسالة الترحيب بنجاح!\n\n"
            f"📝 **الرسالة الجديدة:**\n{welcome_text}",
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"Error in set_welcome_message: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء تعديل رسالة الترحيب.")

async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع العضو الجديد"""
    try:
        chat_id = update.effective_chat.id
        new_members = update.message.new_chat_members

        if not new_members:
            return

        for new_member in new_members:
            if new_member.is_bot:
                continue

            # تحديث بيانات النشاط
            update_user_activity(chat_id, new_member.id)

            # رسالة الترحيب
            if chat_id in welcome_messages:
                welcome_text = welcome_messages[chat_id]['text']
                welcome_text = welcome_text.replace('{name}', new_member.first_name)
                welcome_text = welcome_text.replace('{mention}', f"@{new_member.username}" if new_member.username else new_member.first_name)
                welcome_text = welcome_text.replace('{group}', update.effective_chat.title)
            else:
                welcome_text = f"🎉 أهلاً وسهلاً {new_member.first_name}!\n\nمرحباً بك في {update.effective_chat.title}"

            await update.message.reply_text(welcome_text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error in handle_new_member: {e}")

# -------------------- عرض نشاط المستخدم --------------------
async def show_user_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض نشاط المستخدم"""
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ لازم ترد على رسالة العضو.")
        return

    try:
        user = update.message.reply_to_message.from_user
        chat_id = update.effective_chat.id
        user_id = user.id

        if chat_id not in user_activity or user_id not in user_activity[chat_id]:
            await update.message.reply_text("❌ لا توجد بيانات نشاط لهذا العضو.")
            return

        activity_data = user_activity[chat_id][user_id]
        join_date = activity_data['join_date'].strftime("%Y-%m-%d")
        last_activity = activity_data['last_activity'].strftime("%Y-%m-%d %H:%M")

        activity_text = (
            f"📊 **نشاط العضو:** {user.first_name}\n\n"
            f"💬 **عدد الرسائل:** {activity_data['messages']:,}\n"
            f"📅 **تاريخ الانضمام:** {join_date}\n"
            f"🕐 **آخر نشاط:** {last_activity}\n"
            f"⚠️ **التحذيرات:** {activity_data['warnings']}"
        )

        await update.message.reply_text(activity_text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error in show_user_activity: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء عرض النشاط.")

# -------------------- أوامر إدارية متقدمة --------------------
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """طرد عضو من المجموعة"""
    if not await is_admin(update, context):
        await update.message.reply_text("❌ هذا الأمر للمدراء فقط.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("❌ لازم ترد على رسالة العضو.")
        return

    try:
        user_id = update.message.reply_to_message.from_user.id
        user_name = update.message.reply_to_message.from_user.first_name

        # التحقق من أن المستخدم المراد طرده ليس مديراً
        target_member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        if target_member.status in ['creator', 'administrator']:
            await update.message.reply_text("❌ لا يمكن طرد المدراء.")
            return

        await context.bot.ban_chat_member(update.effective_chat.id, user_id)

        # إضافة إلى قائمة المحظورين
        global_banned_users.add(user_id)

        keyboard = [[InlineKeyboardButton("إلغاء الحظر", callback_data=f"unban_{user_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"✅ تم طرد العضو **{user_name}** من المجموعة.\n"
            f"🆔 المعرف: `{user_id}`",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        await update_stats('users_banned')

    except Exception as e:
        logger.error(f"Error in ban command: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء طرد العضو.")

async def permanent_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حظر نهائي للعضو"""
    if not await is_admin(update, context):
        await update.message.reply_text("❌ هذا الأمر للمدراء فقط.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("❌ لازم ترد على رسالة العضو.")
        return

    try:
        user_id = update.message.reply_to_message.from_user.id
        user_name = update.message.reply_to_message.from_user.first_name

        target_member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        if target_member.status in ['creator', 'administrator']:
            await update.message.reply_text("❌ لا يمكن حظر المدراء.")
            return

        await context.bot.ban_chat_member(update.effective_chat.id, user_id)
        global_banned_users.add(user_id)

        await update.message.reply_text(
            f"🚫 تم حظر العضو **{user_name}** نهائياً من المجموعة.\n"
            f"🆔 المعرف: `{user_id}`\n"
            f"⚠️ لن يتمكن من الانضمام مرة أخرى.",
            parse_mode='Markdown'
        )
        await update_stats('users_banned')

    except Exception as e:
        logger.error(f"Error in permanent ban: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء الحظر.")

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تقييد عضو (منعه من الكتابة)"""
    if not await is_admin(update, context):
        await update.message.reply_text("❌ هذا الأمر للمدراء فقط.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("❌ لازم ترد على رسالة العضو.")
        return

    try:
        user_id = update.message.reply_to_message.from_user.id
        user_name = update.message.reply_to_message.from_user.first_name

        target_member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        if target_member.status in ['creator', 'administrator']:
            await update.message.reply_text("❌ لا يمكن تقييد المدراء.")
            return

        await context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=user_id,
            permissions=ChatPermissions(can_send_messages=False)
        )

        keyboard = [[InlineKeyboardButton("رفع التقييد", callback_data=f"unmute_{user_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"🔇 تم تقييد العضو **{user_name}**.\n"
            f"🆔 المعرف: `{user_id}`",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    except Exception as e:
        logger.error(f"Error in mute command: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء تقييد العضو.")

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رفع التقييد عن العضو"""
    if not await is_admin(update, context):
        await update.message.reply_text("❌ هذا الأمر للمدراء فقط.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("❌ لازم ترد على رسالة العضو.")
        return

    try:
        user_id = update.message.reply_to_message.from_user.id
        user_name = update.message.reply_to_message.from_user.first_name

        await context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_send_polls=True,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False
            )
        )

        await update.message.reply_text(f"🔓 تم رفع التقييد عن العضو **{user_name}**.", parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error in unmute command: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء رفع التقييد.")

# -------------------- نظام التحذيرات --------------------
async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إعطاء تحذير للعضو"""
    if not await is_admin(update, context):
        await update.message.reply_text("❌ هذا الأمر للمدراء فقط.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("❌ لازم ترد على رسالة العضو.")
        return

    try:
        user_id = update.message.reply_to_message.from_user.id
        user_name = update.message.reply_to_message.from_user.first_name
        chat_id = update.effective_chat.id

        # استخراج سبب التحذير
        text_parts = update.message.text.split(maxsplit=1)
        reason = text_parts[1] if len(text_parts) > 1 else "مخالفة القوانين"

        # إضافة التحذير
        warn_count = await add_warning(user_id, chat_id, reason)

        # الحد الأقصى للتحذيرات
        max_warnings = chat_settings.get(chat_id, {}).get('warn_limit', 3)

        if warn_count >= max_warnings:
            # طرد العضو عند الوصول للحد الأقصى
            await context.bot.ban_chat_member(chat_id, user_id)
            await update.message.reply_text(
                f"🚫 تم طرد العضو **{user_name}** لتجاوز الحد الأقصى من التحذيرات ({max_warnings}).\n"
                f"⚠️ آخر تحذير: {reason}",
                parse_mode='Markdown'
            )
        else:
            remaining = max_warnings - warn_count
            keyboard = [[InlineKeyboardButton("حذف التحذير", callback_data=f"delwarn_{user_id}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"⚠️ تم إعطاء تحذير للعضو **{user_name}**\n"
                f"📝 السبب: {reason}\n"
                f"📊 التحذيرات: {warn_count}/{max_warnings}\n"
                f"🔔 باقي {remaining} تحذيرات قبل الطرد",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )

    except Exception as e:
        logger.error(f"Error in warn command: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء إعطاء التحذير.")

# -------------------- أوامر القفل والفتح --------------------
async def lock_content(update: Update, context: ContextTypes.DEFAULT_TYPE, content_type: str):
    """قفل نوع محتوى محدد"""
    if not await is_admin(update, context):
        await update.message.reply_text("❌ هذا الأمر للمدراء فقط.")
        return

    chat_id = update.effective_chat.id
    init_chat_settings(chat_id)

    content_names = {
        'photos': 'الصور',
        'videos': 'الفيديوهات', 
        'audio': 'الصوتيات',
        'stickers': 'الملصقات',
        'gifs': 'المتحركات',
        'files': 'الملفات',
        'links': 'الروابط',
        'voice': 'الرسائل الصوتية',
        'bots': 'البوتات',
        'forwarded': 'الرسائل المحولة'
    }

    chat_settings[chat_id][f'lock_{content_type}'] = True
    content_name = content_names.get(content_type, content_type)
    await update.message.reply_text(f"🔒 تم قفل {content_name}.")

async def unlock_content(update: Update, context: ContextTypes.DEFAULT_TYPE, content_type: str):
    """فتح نوع محتوى محدد"""
    if not await is_admin(update, context):
        await update.message.reply_text("❌ هذا الأمر للمدراء فقط.")
        return

    chat_id = update.effective_chat.id
    init_chat_settings(chat_id)

    content_names = {
        'photos': 'الصور',
        'videos': 'الفيديوهات',
        'audio': 'الصوتيات', 
        'stickers': 'الملصقات',
        'gifs': 'المتحركات',
        'files': 'الملفات',
        'links': 'الروابط',
        'voice': 'الرسائل الصوتية',
        'bots': 'البوتات',
        'forwarded': 'الرسائل المحولة'
    }

    chat_settings[chat_id][f'lock_{content_type}'] = False
    content_name = content_names.get(content_type, content_type)
    await update.message.reply_text(f"🔓 تم فتح {content_name}.")

async def lock_all_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قفل جميع أنواع المحتوى"""
    if not await is_admin(update, context):
        await update.message.reply_text("❌ هذا الأمر للمدراء فقط.")
        return

    chat_id = update.effective_chat.id
    init_chat_settings(chat_id)

    # قفل جميع أنواع المحتوى
    content_types = ['photos', 'videos', 'audio', 'stickers', 'gifs', 'files', 'links', 'voice', 'bots', 'forwarded']
    for content_type in content_types:
        chat_settings[chat_id][f'lock_{content_type}'] = True

    await update.message.reply_text("🔒 تم قفل جميع أنواع المحتوى.")

async def unlock_all_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فتح جميع أنواع المحتوى"""
    if not await is_admin(update, context):
        await update.message.reply_text("❌ هذا الأمر للمدراء فقط.")
        return

    chat_id = update.effective_chat.id
    init_chat_settings(chat_id)

    # فتح جميع أنواع المحتوى
    content_types = ['photos', 'videos', 'audio', 'stickers', 'gifs', 'files', 'links', 'voice', 'bots', 'forwarded']
    for content_type in content_types:
        chat_settings[chat_id][f'lock_{content_type}'] = False

    await update.message.reply_text("🔓 تم فتح جميع أنواع المحتوى.")

# -------------------- أوامر الحذف --------------------
async def delete_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف عدد معين من الرسائل"""
    if not await is_admin(update, context):
        await update.message.reply_text("❌ هذا الأمر للمدراء فقط.")
        return

    try:
        # استخراج العدد من النص
        text_parts = update.message.text.split()
        count = 10  # افتراضي
        if len(text_parts) > 1:
            try:
                count = int(text_parts[1])
                if count > 100:
                    count = 100
                elif count < 1:
                    count = 1
            except ValueError:
                await update.message.reply_text("❌ يجب أن يكون العدد رقماً صحيحاً.")
                return

        # حذف الرسائل
        deleted_count = 0
        chat_id = update.effective_chat.id
        message_id = update.message.message_id

        for i in range(1, count + 1):
            try:
                await context.bot.delete_message(chat_id, message_id - i)
                deleted_count += 1
            except Exception:
                continue

        await update_stats('messages_deleted', deleted_count)

        # رسالة التأكيد (ستحذف تلقائياً بعد 5 ثوانِ)
        confirmation = await update.message.reply_text(f"🗑️ تم حذف {deleted_count} رسالة.")

        # حذف رسالة التأكيد والأمر بعد 5 ثوانِ
        await asyncio.sleep(5)
        try:
            await confirmation.delete()
            await update.message.delete()
        except:
            pass

    except Exception as e:
        logger.error(f"Error in delete messages: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء حذف الرسائل.")

# -------------------- أوامر المعلومات --------------------
async def user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض معلومات مفصلة عن العضو"""
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ لازم ترد على رسالة العضو.")
        return

    try:
        user = update.message.reply_to_message.from_user
        user_id = user.id
        chat_id = update.effective_chat.id

        # معلومات أساسية
        user_name = user.first_name
        last_name = user.last_name or "غير محدد"
        username = f"@{user.username}" if user.username else "لا يوجد"

        # حالة العضو
        chat_member = await context.bot.get_chat_member(chat_id, user_id)
        status = chat_member.status

        status_ar = {
            'creator': '👑 منشئ المجموعة',
            'administrator': '👮‍♂️ مدير',
            'member': '👤 عضو',
            'restricted': '🔒 مقيد',
            'left': '🚪 غادر المجموعة',
            'kicked': '🚫 مطرود'
        }.get(status, status)

        # التحذيرات
        warn_key = f"{chat_id}_{user_id}"
        warnings_count = len(user_warnings.get(warn_key, []))
        max_warnings = chat_settings.get(chat_id, {}).get('warn_limit', 3)

        # حالة الحظر
        ban_status = "🟢 غير محظور" if user_id not in global_banned_users else "🔴 محظور عالمياً"

        info_text = (
            f"👤 **معلومات العضو المفصلة**\n\n"
            f"🆔 **المعرف:** `{user_id}`\n"
            f"📛 **الاسم الأول:** {user_name}\n"
            f"📛 **الاسم الأخير:** {last_name}\n"
            f"🔗 **اسم المستخدم:** {username}\n"
            f"📊 **الحالة:** {status_ar}\n"
            f"⚠️ **التحذيرات:** {warnings_count}/{max_warnings}\n"
            f"🚫 **حالة الحظر:** {ban_status}\n"
            f"🤖 **نوع الحساب:** {'بوت' if user.is_bot else 'مستخدم عادي'}\n"
        )

        await update.message.reply_text(info_text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error in user_info: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء جلب معلومات العضو.")

# -------------------- أوامر المطور --------------------
async def developer_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لوحة تحكم المطور"""
    if not await is_developer(update):
        await update.message.reply_text("❌ هذا الأمر مخصص للمطورين فقط.")
        return

    try:
        uptime = datetime.datetime.now() - bot_stats['start_time']
        uptime_str = str(uptime).split('.')[0]

        # حساب الإحصائيات
        active_groups = len(bot_stats['groups_managed'])
        active_users_count = len(bot_stats['active_users'])
        total_warnings = sum(len(warnings) for warnings in user_warnings.values())
        total_replies = sum(len(replies) for replies in auto_replies.values())
        total_notes = sum(len(notes) for notes in chat_notes.values())
        total_quizzes = sum(len(quizzes_data) for quizzes_data in quizzes.values())

        panel_text = (
            "🔧 **لوحة تحكم المطور المحدثة**\n\n"
            f"📊 **إحصائيات النظام:**\n"
            f"⏰ مدة التشغيل: {uptime_str}\n"
            f"📝 الأوامر المنفذة: {bot_stats['total_commands']:,}\n"
            f"📨 الرسائل المعالجة: {bot_stats['messages_processed']:,}\n"
            f"🗑️الرسائل المحذوفة: {bot_stats['messages_deleted']:,}\n\n"

            f"👥 **إحصائيات المستخدمين:**\n"
            f"🏢 المجموعات النشطة: {active_groups:,}\n"
            f"👤 المستخدمون النشطون: {active_users_count:,}\n"
            f"🚫 المحظورون عالمياً: {len(global_banned_users):,}\n\n"

            f"⚠️ **إحصائيات المخالفات:**\n"
            f"⚠️ إجمالي التحذيرات: {total_warnings:,}\n"
            f"👮‍♂️ الطرد/الحظر: {bot_stats['users_banned']:,}\n\n"

            f"🤖 **الميزات الجديدة:**\n"
            f"💬 الردود التلقائية: {total_replies:,}\n"
            f"📝 النوتات المحفوظة: {total_notes:,}\n"
            f"🎯 المسابقات: {total_quizzes:,}\n"
            f"🔄 الردود المفعلة: {bot_stats['auto_replies_triggered']:,}\n\n"

            f"💾 **معلومات تقنية:**\n"
            f"🆔 معرف هذه المحادثة: `{update.effective_chat.id}`\n"
            f"👤 معرفك: `{update.effective_user.id}`\n"
            f"🤖 معرف البوت: `{context.bot.id}`\n"
        )

        await update.message.reply_text(panel_text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error in developer_panel: {e}")
        await update.message.reply_text("❌ حدث خطأ في لوحة المطور.")

async def comprehensive_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إحصائيات شاملة للبوت"""
    if not await is_developer(update):
        await update.message.reply_text("❌ هذا الأمر مخصص للمطورين فقط.")
        return

    try:
        stats_text = (
            "📈 **الإحصائيات الشاملة المحدثة**\n\n"
            f"📊 إجمالي الأوامر: {bot_stats['total_commands']}\n"
            f"📨 الرسائل المعالجة: {bot_stats['messages_processed']}\n"
            f"🗑️الرسائل المحذوفة: {bot_stats['messages_deleted']}\n"
            f"🚫 المستخدمون المحظورون: {bot_stats['users_banned']}\n"
            f"⚠️ التحذيرات المعطاة: {bot_stats['warnings_given']}\n"
            f"🤖 الردود التلقائية: {bot_stats['auto_replies_triggered']}\n"
            f"📝 النوتات المحفوظة: {bot_stats['notes_saved']}\n"
            f"🎯 المسابقات المنشأة: {bot_stats['quizzes_created']}"
        )

        await update.message.reply_text(stats_text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error in comprehensive_stats: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء جلب الإحصائيات.")

# -------------------- معالج الأوامر النصية --------------------
async def handle_text_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأوامر النصية العربية"""
    try:
        if not update.effective_chat or update.effective_chat.type not in ['group', 'supergroup']:
            return

        text = update.message.text.strip()
        
        # التحقق من أن النص يبدأ بأمر وليس مجرد محادثة عادية
        command_keywords = [
            'طرد', 'حظر', 'تقييد', 'رفع التقييد', 'إلغاء الكتم', 'تحذير',
            'قفل', 'فتح', 'حذف', 'معلومات العضو', 'لوحة المطور', 'إحصائيات شاملة',
            'اضافة رد', 'حذف رد', 'قائمة الردود', 'حفظ', 'جلب', 'النوتات',
            'مسابقة', 'ترحيب', 'نشاط'
        ]
        
        if not any(text.startswith(cmd) for cmd in command_keywords):
            return

        # قاموس الأوامر العربية
        commands_map = {
            # الأوامر الأساسية
            'طرد': ban_user,
            'حظر': permanent_ban,
            'تقييد': mute_user,
            'رفع التقييد': unmute_user,
            'إلغاء الكتم': unmute_user,

            # التحذيرات
            'تحذير': warn_user,

            # القفل والفتح
            'قفل الصور': lambda u, c: lock_content(u, c, 'photos'),
            'فتح الصور': lambda u, c: unlock_content(u, c, 'photos'),
            'قفل الفيديو': lambda u, c: lock_content(u, c, 'videos'),
            'فتح الفيديو': lambda u, c: unlock_content(u, c, 'videos'),
            'قفل الصوت': lambda u, c: lock_content(u, c, 'audio'),
            'فتح الصوت': lambda u, c: unlock_content(u, c, 'audio'),
            'قفل الملصقات': lambda u, c: lock_content(u, c, 'stickers'),
            'فتح الملصقات': lambda u, c: unlock_content(u, c, 'stickers'),
            'قفل المتحركات': lambda u, c: lock_content(u, c, 'gifs'),
            'فتح المتحركات': lambda u, c: unlock_content(u, c, 'gifs'),
            'قفل الملفات': lambda u, c: lock_content(u, c, 'files'),
            'فتح الملفات': lambda u, c: unlock_content(u, c, 'files'),
            'قفل الروابط': lambda u, c: lock_content(u, c, 'links'),
            'فتح الروابط': lambda u, c: unlock_content(u, c, 'links'),
            'قفل الصوتيات': lambda u, c: lock_content(u, c, 'voice'),
            'فتح الصوتيات': lambda u, c: unlock_content(u, c, 'voice'),
            'قفل البوتات': lambda u, c: lock_content(u, c, 'bots'),
            'فتح البوتات': lambda u, c: unlock_content(u, c, 'bots'),
            'قفل المحول': lambda u, c: lock_content(u, c, 'forwarded'),
            'فتح المحول': lambda u, c: unlock_content(u, c, 'forwarded'),
            'قفل الكل': lambda u, c: lock_all_content(u, c),
            'فتح الكل': lambda u, c: unlock_all_content(u, c),

            # الحذف
            'حذف': delete_messages,

            # المعلومات
            'معلومات العضو': user_info,
            'نشاط': show_user_activity,

            # الميزات الجديدة
            'اضافة رد': add_auto_reply,
            'حذف رد': delete_auto_reply,
            'قائمة الردود': list_auto_replies,
            'حفظ': save_note,
            'جلب': get_note,
            'النوتات': list_notes,
            'مسابقة': create_quiz,
            'ترحيب': set_welcome_message,

            # المطور
            'لوحة المطور': developer_panel,
            'إحصائيات شاملة': comprehensive_stats,
        }

        # البحث عن الأمر المطابق
        command_found = False
        for command_text, command_function in commands_map.items():
            if text.startswith(command_text):
                await command_function(update, context)
                await update_stats('total_commands')
                command_found = True
                break
        
        # إذا لم يتم العثور على أمر مطابق، لا تفعل شيئاً
        if not command_found:
            return

    except Exception as e:
        logger.error(f"Error in handle_text_commands: {e}")

# -------------------- فلترة الرسائل --------------------
async def message_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فلترة الرسائل حسب إعدادات المجموعة"""
    try:
        if not update.effective_chat or update.effective_chat.type not in ['group', 'supergroup']:
            return

        chat_id = update.effective_chat.id
        user_id = update.effective_user.id

        init_chat_settings(chat_id)
        init_chat_data(chat_id)
        settings = chat_settings[chat_id]

        # تحديث الإحصائيات والنشاط
        bot_stats['messages_processed'] += 1
        bot_stats['active_users'].add(user_id)
        update_user_activity(chat_id, user_id)

        # معالجة عضو جديد
        if update.message.new_chat_members:
            await handle_new_member(update, context)
            return

        # فحص الحظر العالمي
        if user_id in global_banned_users:
            await update.message.delete()
            return

        # فحص الردود التلقائية
        if settings.get('auto_reply_enabled', True) and update.message.text:
            message_text = update.message.text.lower()
            for trigger, reply_data in auto_replies.get(chat_id, {}).items():
                if trigger in message_text:
                    await update.message.reply_text(reply_data['reply'])
                    reply_data['usage_count'] += 1
                    await update_stats('auto_replies_triggered')
                    break

        # فحص المسابقات النشطة
        if update.message.text and chat_id in quizzes:
            message_text = update.message.text.lower().strip()
            for quiz_id, quiz_data in quizzes[chat_id].items():
                if not quiz_data['solved'] and message_text == quiz_data['answer']:
                    quiz_data['solved'] = True
                    quiz_data['solver'] = user_id
                    await update.message.reply_text(
                        f"🎉 **مبروك!** {update.effective_user.first_name}\n\n"
                        f"✅ إجابة صحيحة! لقد حللت المسابقة بنجاح!\n"
                        f"❓ **السؤال كان:** {quiz_data['question']}\n"
                        f"💡 **الإجابة:** {quiz_data['answer']}",
                        parse_mode='Markdown'
                    )
                    break

        # فلترة المحتوى
        should_delete = False
        delete_reason = ""

        if settings['lock_photos'] and update.message.photo:
            should_delete = True
            delete_reason = "الصور محظورة"
        elif settings['lock_videos'] and update.message.video:
            should_delete = True
            delete_reason = "الفيديوهات محظورة"
        elif settings['lock_audio'] and update.message.audio:
            should_delete = True
            delete_reason = "الصوتيات محظورة"
        elif settings['lock_stickers'] and update.message.sticker:
            should_delete = True
            delete_reason = "الملصقات محظورة"
        elif settings['lock_gifs'] and update.message.animation:
            should_delete = True
            delete_reason = "المتحركات محظورة"
        elif settings['lock_files'] and update.message.document:
            should_delete = True
            delete_reason = "الملفات محظورة"
        elif settings['lock_voice'] and (update.message.voice or update.message.video_note):
            should_delete = True
            delete_reason = "الرسائل الصوتية محظورة"
        elif settings['lock_forwarded'] and hasattr(update.message, 'forward_from'):
            should_delete = True
            delete_reason = "الرسائل المحولة محظورة"
        elif settings['lock_bots'] and update.message.from_user.is_bot:
            should_delete = True
            delete_reason = "البوتات محظورة"
        elif settings['lock_links'] and update.message.entities:
            for entity in update.message.entities:
                if entity.type in ["url", "text_link"]:
                    should_delete = True
                    delete_reason = "الروابط محظورة"
                    break

        if should_delete and not await is_admin(update, context):
            await update.message.delete()
            await update_stats('messages_deleted')

    except Exception as e:
        logger.error(f"Error in message_filter: {e}")

# -------------------- تشغيل البوت --------------------
def main():
    """الدالة الرئيسية لتشغيل البوت"""
    try:
        # إنشاء التطبيق
        app = ApplicationBuilder().token(BOT_TOKEN).build()

        # إضافة معالجات الأوامر
        app.add_handler(CommandHandler("start", start))

        # إضافة معالجات الأوامر النصية المباشرة
        app.add_handler(MessageHandler(filters.Regex(r'^طرد$'), ban_user))
        app.add_handler(MessageHandler(filters.Regex(r'^حظر$'), permanent_ban))
        app.add_handler(MessageHandler(filters.Regex(r'^تقييد$'), mute_user))
        app.add_handler(MessageHandler(filters.Regex(r'^رفع التقييد$'), unmute_user))
        app.add_handler(MessageHandler(filters.Regex(r'^إلغاء الكتم$'), unmute_user))
        app.add_handler(MessageHandler(filters.Regex(r'^تحذير'), warn_user))
        app.add_handler(MessageHandler(filters.Regex(r'^حذف'), delete_messages))
        app.add_handler(MessageHandler(filters.Regex(r'^معلومات العضو$'), user_info))
        app.add_handler(MessageHandler(filters.Regex(r'^نشاط$'), show_user_activity))
        app.add_handler(MessageHandler(filters.Regex(r'^لوحة المطور$'), developer_panel))
        app.add_handler(MessageHandler(filters.Regex(r'^إحصائيات شاملة$'), comprehensive_stats))
        
        # الميزات الجديدة
        app.add_handler(MessageHandler(filters.Regex(r'^اضافة رد'), add_auto_reply))
        app.add_handler(MessageHandler(filters.Regex(r'^حذف رد'), delete_auto_reply))
        app.add_handler(MessageHandler(filters.Regex(r'^قائمة الردود$'), list_auto_replies))
        app.add_handler(MessageHandler(filters.Regex(r'^حفظ'), save_note))
        app.add_handler(MessageHandler(filters.Regex(r'^جلب'), get_note))
        app.add_handler(MessageHandler(filters.Regex(r'^النوتات$'), list_notes))
        app.add_handler(MessageHandler(filters.Regex(r'^مسابقة'), create_quiz))
        app.add_handler(MessageHandler(filters.Regex(r'^ترحيب'), set_welcome_message))
        
        # أوامر القفل والفتح
        app.add_handler(MessageHandler(filters.Regex(r'^قفل الصور$'), lambda u, c: lock_content(u, c, 'photos')))
        app.add_handler(MessageHandler(filters.Regex(r'^فتح الصور$'), lambda u, c: unlock_content(u, c, 'photos')))
        app.add_handler(MessageHandler(filters.Regex(r'^قفل الفيديو$'), lambda u, c: lock_content(u, c, 'videos')))
        app.add_handler(MessageHandler(filters.Regex(r'^فتح الفيديو$'), lambda u, c: unlock_content(u, c, 'videos')))
        app.add_handler(MessageHandler(filters.Regex(r'^قفل الصوت$'), lambda u, c: lock_content(u, c, 'audio')))
        app.add_handler(MessageHandler(filters.Regex(r'^فتح الصوت$'), lambda u, c: unlock_content(u, c, 'audio')))
        app.add_handler(MessageHandler(filters.Regex(r'^قفل الملصقات$'), lambda u, c: lock_content(u, c, 'stickers')))
        app.add_handler(MessageHandler(filters.Regex(r'^فتح الملصقات$'), lambda u, c: unlock_content(u, c, 'stickers')))
        app.add_handler(MessageHandler(filters.Regex(r'^قفل المتحركات$'), lambda u, c: lock_content(u, c, 'gifs')))
        app.add_handler(MessageHandler(filters.Regex(r'^فتح المتحركات$'), lambda u, c: unlock_content(u, c, 'gifs')))
        app.add_handler(MessageHandler(filters.Regex(r'^قفل الملفات$'), lambda u, c: lock_content(u, c, 'files')))
        app.add_handler(MessageHandler(filters.Regex(r'^فتح الملفات$'), lambda u, c: unlock_content(u, c, 'files')))
        app.add_handler(MessageHandler(filters.Regex(r'^قفل الروابط$'), lambda u, c: lock_content(u, c, 'links')))
        app.add_handler(MessageHandler(filters.Regex(r'^فتح الروابط$'), lambda u, c: unlock_content(u, c, 'links')))
        app.add_handler(MessageHandler(filters.Regex(r'^قفل الصوتيات$'), lambda u, c: lock_content(u, c, 'voice')))
        app.add_handler(MessageHandler(filters.Regex(r'^فتح الصوتيات$'), lambda u, c: unlock_content(u, c, 'voice')))
        app.add_handler(MessageHandler(filters.Regex(r'^قفل البوتات$'), lambda u, c: lock_content(u, c, 'bots')))
        app.add_handler(MessageHandler(filters.Regex(r'^فتح البوتات$'), lambda u, c: unlock_content(u, c, 'bots')))
        app.add_handler(MessageHandler(filters.Regex(r'^قفل المحول$'), lambda u, c: lock_content(u, c, 'forwarded')))
        app.add_handler(MessageHandler(filters.Regex(r'^فتح المحول$'), lambda u, c: unlock_content(u, c, 'forwarded')))
        app.add_handler(MessageHandler(filters.Regex(r'^قفل الكل$'), lock_all_content))
        app.add_handler(MessageHandler(filters.Regex(r'^فتح الكل$'), unlock_all_content))

        # معالج فلترة الرسائل (يجب أن يكون الأخير)
        app.add_handler(MessageHandler(filters.ALL, message_filter))

        logger.info("🚀 تم تشغيل البوت بنجاح مع الميزات الجديدة!")
        print("🚀 البوت يعمل الآن مع الميزات المحدثة...")
        print("✅ الميزات الجديدة:")
        print("   🤖 نظام الردود التلقائية")
        print("   📝 نظام النوتات")
        print("   🎯 نظام المسابقات")
        print("   👋 رسائل ترحيب مخصصة")
        print("   📊 تتبع نشاط المستخدمين")

        # بدء البوت
        app.run_polling(drop_pending_updates=True)

    except Exception as e:
        logger.error(f"خطأ في تشغيل البوت: {e}")
        print(f"❌ خطأ في تشغيل البوت: {e}")

if __name__ == "__main__":
    main()

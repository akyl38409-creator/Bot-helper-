"""
GroupHelpBot — бот для Telegram-группы
Платформа: Render.com (Background Worker)
Библиотека: python-telegram-bot v21

Функции:
  1. Постит правила комментарием под каждым сообщением в группе
  2. Приветствует новых участников и отправляет правила
"""

import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ChatMemberHandler,
    CommandHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ParseMode

# ─────────────────────────────────────────────
#  НАСТРОЙКИ — задаются через переменные окружения на Render
#  (Environment Variables → BOT_TOKEN и GROUP_ID)
# ─────────────────────────────────────────────

BOT_TOKEN = os.environ["BOT_TOKEN"]
GROUP_ID  = int(os.environ["GROUP_ID"])

# ─────────────────────────────────────────────
#  ТЕКСТ ПРАВИЛ
# ─────────────────────────────────────────────

RULES_TEXT = """📋 <b>ПРАВИЛА ГРУППЫ</b>

1️⃣ Уважайте друг друга
2️⃣ Запрещён спам и флуд
3️⃣ Только тематические сообщения
4️⃣ Реклама без разрешения администрации — бан
5️⃣ Соблюдайте законодательство

⚠️ Нарушение правил = предупреждение или бан."""

WELCOME_TEXT = "👋 Добро пожаловать, {name}!\n\nПожалуйста, ознакомьтесь с правилами группы ниже ↓"

# ─────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)


# ─── /id — узнать ID чата ────────────────────────────────────────────────────

async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"Chat ID: <code>{update.effective_chat.id}</code>",
        parse_mode=ParseMode.HTML,
    )


# ─── /rules — показать правила вручную ──────────────────────────────────────

async def cmd_rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(RULES_TEXT, parse_mode=ParseMode.HTML)


# ─── Новое сообщение в группе ────────────────────────────────────────────────

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user

    if user and user.is_bot:
        return

    try:
        await message.reply_text(RULES_TEXT, parse_mode=ParseMode.HTML)
        log.info("Правила отправлены под сообщением %s от %s",
                 message.message_id, user.full_name if user else "?")
    except Exception as e:
        log.error("Ошибка при отправке правил: %s", e)


# ─── Новый участник ──────────────────────────────────────────────────────────

async def on_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = update.chat_member

    old_status = result.old_chat_member.status
    new_status = result.new_chat_member.status

    joined = (
        old_status in ("left", "kicked", "restricted")
        and new_status in ("member", "administrator", "creator")
    )
    if not joined:
        return

    user = result.new_chat_member.user
    if user.is_bot:
        return

    try:
        welcome_msg = await context.bot.send_message(
            chat_id=result.chat.id,
            text=WELCOME_TEXT.format(name=user.full_name),
            parse_mode=ParseMode.HTML,
        )
        await welcome_msg.reply_text(RULES_TEXT, parse_mode=ParseMode.HTML)
        log.info("Поприветствовали: %s (id=%s)", user.full_name, user.id)
    except Exception as e:
        log.error("Ошибка при приветствии: %s", e)


# ─── Запуск ──────────────────────────────────────────────────────────────────

def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("id", cmd_id))
    app.add_handler(CommandHandler("rules", cmd_rules))

    app.add_handler(MessageHandler(
        filters.Chat(GROUP_ID) & filters.TEXT & ~filters.COMMAND,
        on_message,
    ))

    app.add_handler(ChatMemberHandler(on_new_member, ChatMemberHandler.CHAT_MEMBER))

    log.info("Бот запущен на Render. GROUP_ID=%s", GROUP_ID)
    app.run_polling(allowed_updates=["message", "chat_member"])


if __name__ == "__main__":
    main()

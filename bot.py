#!/usr/bin/env python3
"""
Telegram bot for Microsoft Office help via GigaChat API.

Uses:
- TELEGRAM_TOKEN (бот в Telegram)
- GIGACHAT_CLIENT, GIGACHAT_CLIENT_SECRET (для получения токена)
- CGIGA_CHAT_TOKEN (опционально, можно оставить пустым)
- GIGACHAT_AUTH_URL, GIGACHAT_API_URL (адреса API)

Файл prompt.txt содержит системный промпт (ограничивает ответы областью Office).
"""

import os
import logging
import uuid
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ========================================
# Загрузка окружения
# ========================================
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

CLIENT_ID = os.getenv("GIGACHAT_CLIENT")
CLIENT_SECRET = os.getenv("GIGACHAT_CLIENT_SECRET")
ACCESS_TOKEN = os.getenv("CGIGA_CHAT_TOKEN")  # может быть пустым
AUTH_URL = os.getenv("GIGACHAT_AUTH_URL")
API_URL = os.getenv("GIGACHAT_API_URL")

PROMPT_FILE = os.getenv("PROMPT_FILE", "prompt.txt")
try:
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read().strip()
except FileNotFoundError:
    SYSTEM_PROMPT = "You are an assistant specialized in Microsoft Office (Word, Excel, PowerPoint, Outlook)."

# ========================================
# Логирование
# ========================================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ========================================
# Авторизация в GigaChat
# ========================================
def get_gigachat_token() -> str:
    """
    Получить access_token. Если в .env уже указан CGIGA_CHAT_TOKEN — используем его.
    Если он пустой или устарел — запрашиваем новый по client/secret.
    """
    global ACCESS_TOKEN
    if ACCESS_TOKEN:
        return ACCESS_TOKEN

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),  # уникальный ID запроса
    }
    data = {
        "scope": "GIGACHAT_API_PERS",  # может отличаться (ORG/TEAM), уточните у себя
    }

    resp = requests.post(
        AUTH_URL,
        headers=headers,
        auth=(CLIENT_ID, CLIENT_SECRET),
        data=data,
        verify=False,  # при самоподписанном сертификате, если есть корневой CA — уберите
        timeout=30,
    )

    if resp.status_code != 200:
        raise RuntimeError(f"GigaChat auth failed: {resp.status_code} {resp.text}")

    token = resp.json().get("access_token")
    if not token:
        raise RuntimeError("Не удалось получить access_token от GigaChat")

    ACCESS_TOKEN = token
    return token


# ========================================
# Вызов GigaChat API
# ========================================
def call_gigachat(system_prompt: str, user_message: str) -> str:
    token = get_gigachat_token()

    payload = {
        "model": "GigaChat:latest",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.2,
        "max_tokens": 800,
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    resp = requests.post(API_URL, json=payload, headers=headers, verify=False, timeout=30)

    if resp.status_code == 401:
        # токен истёк → сбрасываем и пробуем снова
        global ACCESS_TOKEN
        ACCESS_TOKEN = None
        return call_gigachat(system_prompt, user_message)

    if resp.status_code != 200:
        return f"Ошибка от GigaChat API: {resp.status_code} {resp.text}"

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return str(data)


# ========================================
# Ограничение области (Microsoft Office)
# ========================================
OFFICE_KEYWORDS = [
    "word", "excel", "powerpoint", "outlook", "office", "макрос", "формула", "таблица",
    "ppt", "docx", "xlsx", "presentation", "mail merge", "слайды", "формулы", "vba", "макросы"
]

def seems_outside_office(user_text: str) -> bool:
    low = user_text.lower()
    for k in OFFICE_KEYWORDS:
        if k in low:
            return False
    return True


# ========================================
# Telegram handlers
# ========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Привет! Я бот-помощник по Microsoft Office (Word, Excel, PowerPoint, Outlook).\n"
        "Задайте вопрос, например: «Как сделать сводную таблицу в Excel?»"
    )
    await update.message.reply_text(text)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Я отвечаю только на вопросы по Microsoft Office (Word, Excel, PowerPoint, Outlook).")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text or ""
    user_id = update.effective_user.id
    logger.info("Message from %s: %s", user_id, user_text[:200])

    if seems_outside_office(user_text):
        await update.message.reply_text(
            "Извините, я работаю только с вопросами по Microsoft Office. "
            "Задайте вопрос про Word, Excel, PowerPoint или Outlook."
        )
        return

    await update.message.reply_text("Обрабатываю запрос…")
    reply = call_gigachat(SYSTEM_PROMPT, user_text)

    MAX_LEN = 4000
    if len(reply) <= MAX_LEN:
        await update.message.reply_text(reply)
    else:
        for i in range(0, len(reply), MAX_LEN):
            await update.message.reply_text(reply[i:i+MAX_LEN])


# ========================================
# Main
# ========================================
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()

# bot.py
import os
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
from io import BytesIO


from PIL import Image
import pytesseract
import fitz # PyMuPDF
from pdf2image import convert_from_path
from docx import Document
import openpyxl


from gigachat import GigaChat
from prompt import MICROSOFT_OFFICE_PROMPT


from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters


# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Load env
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GIGA_CHAT_TOKEN = os.getenv('GIGA_CHAT_TOKEN')
DOWNLOAD_DIR = Path(os.getenv('DOWNLOAD_DIR', './downloads'))
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


# Инициализация GigaChat клиента
giga = GigaChat(credentials=GIGA_CHAT_TOKEN)


# Simple wrapper
def send_to_gigachat(user_message: str, system_prompt: str = MICROSOFT_OFFICE_PROMPT) -> str:
try:
response = giga.chat(
f"{system_prompt}\n\nUser: {user_message}"
)
return str(response)
except Exception as e:
logger.exception('GigaChat request failed')
return f"Ошибка при обращении к GigaChat: {e}"




async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(
"Привет! Я бот, использующий GigaChat. Отправь вопрос или прикрепи изображение/PDF/DOCX/XLSX для распознавания текста."
)




async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_text = update.message.text
reply = send_to_gigachat(user_text)
await update.message.reply_text(reply)




async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
photos = update.message.photo
file = await context.bot.get_file(photos[-1].file_id)
local_path = DOWNLOAD_DIR / f"img_{file.file_id}.jpg"
await file.download_to_drive(custom_path=str(local_path))
await update.message.reply_text("Изображение получено — выполняю OCR...")
try:
text = ocr_image(local_path)
prompt = f"Пользователь прислал изображение. Распознанный текст:\n\n{text}\n\nВопрос: {update.message.caption or 'Нет явного вопроса — прокомментируй содержимое.'}"
reply = send_to_gigachat(prompt)
await update.message.reply_text(reply)
except Exception as e:
logger.exception('OCR failed')
await update.message.reply_text(f"Ошибка при OCR: {e}")




async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
doc = update.message.document
file = await context.bot.get_file(doc.file_id)
local_path = DOWNLOAD_DIR / f"{doc.file_name}"
await file.download_to_drive(custom_path=str(local_path))
main()

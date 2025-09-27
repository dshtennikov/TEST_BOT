# bot.py

import os
import logging
import requests
from io import BytesIO
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes
from prompts import MICROSOFT_OFFICE_PROMPT

# Загрузка переменных окружения
load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GIGA_CHAT_TOKEN = os.getenv("GIGA_CHAT_TOKEN")

if not TELEGRAM_BOT_TOKEN or not GIGA_CHAT_TOKEN:
    raise ValueError("Отсутствуют TELEGRAM_BOT_TOKEN или GIGA_CHAT_TOKEN в .env")

GIGACHAT_API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

# Поддерживаемые форматы
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
PDF_EXTENSION = '.pdf'

def extract_text_from_image_pil(image: Image.Image) -> str:
    """Извлекает текст из объекта PIL Image."""
    try:
        return pytesseract.image_to_string(image, lang='rus+eng').strip()
    except Exception as e:
        logger.error(f"Ошибка OCR: {e}")
        return ""

def extract_text_from_document(file_bytes: bytes, filename: str) -> str:
    """Извлекает текст из документа (изображение или PDF)."""
    ext = os.path.splitext(filename.lower())[1]

    if ext in IMAGE_EXTENSIONS:
        try:
            image = Image.open(BytesIO(file_bytes))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            return extract_text_from_image_pil(image)
        except Exception as e:
            logger.error(f"Ошибка открытия изображения {filename}: {e}")
            return ""

    elif ext == PDF_EXTENSION:
        try:
            # Конвертируем первую страницу PDF в изображение
            images = convert_from_bytes(file_bytes, first_page=1, last_page=1, fmt='jpeg')
            if not images:
                return ""
            return extract_text_from_image_pil(images[0])
        except Exception as e:
            logger.error(f"Ошибка обработки PDF {filename}: {e}")
            return ""

    else:
        return ""  # Неподдерживаемый формат

def ask_gigachat(user_input: str) -> str:
    prompt = MICROSOFT_OFFICE_PROMPT.format(user_input=user_input)
    headers = {
        "Authorization": f"Bearer {GIGA_CHAT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "GigaChat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 1000
    }

    try:
        response = requests.post(
            GIGACHAT_API_URL,
            json=payload,
            headers=headers,
            verify=False,
            timeout=30
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"GigaChat ошибка: {e}")
        return "Не удалось обработать запрос. Проверьте токен или попробуйте позже."

# Обработчики
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! 📎\n"
        "Вы можете прислать:\n"
        "• Текстовый вопрос по Microsoft Office\n"
        "• Фото (скриншот)\n"
        "• Файл-изображение (JPG, PNG и др.)\n"
        "• PDF (обработается первая страница)\n"
        "Я помогу разобраться!"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    logger.info(f"Текст: {text}")
    answer = ask_gigachat(text)
    await update.message.reply_text(answer)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Обрабатываю фото...")
    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        file_bytes = await file.download_as_bytearray()
        image = Image.open(BytesIO(file_bytes))
        if image.mode != 'RGB':
            image = image.convert('RGB')
        extracted_text = extract_text_from_image_pil(image)
        if not extracted_text:
            await update.message.reply_text("Не удалось распознать текст. Попробуйте чёткий скриншот.")
            return
        logger.info(f"OCR из фото: {extracted_text}")
        answer = ask_gigachat(extracted_text)
        await update.message.reply_text(
            f"Распознано:\n```\n{extracted_text[:300]}{'...' if len(extracted_text) > 300 else ''}\n```\n\nОтвет:\n{answer}",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка фото: {e}")
        await update.message.reply_text("Ошибка обработки изображения.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    file_name = document.file_name or "unknown"
    mime_type = document.mime_type or ""

    # Проверка: изображение или PDF
    ext = os.path.splitext(file_name.lower())[1]
    if ext not in IMAGE_EXTENSIONS and ext != PDF_EXTENSION:
        await update.message.reply_text("Поддерживаются только изображения (JPG, PNG и др.) и PDF-файлы.")
        return

    await update.message.reply_text(f"📎 Обрабатываю файл: {file_name}...")

    try:
        file = await context.bot.get_file(document.file_id)
        file_bytes = await file.download_as_bytearray()
        extracted_text = extract_text_from_document(bytes(file_bytes), file_name)

        if not extracted_text:
            await update.message.reply_text("Не удалось извлечь текст. Убедитесь, что файл содержит читаемый текст.")
            return

        logger.info(f"OCR из документа {file_name}: {extracted_text}")
        answer = ask_gigachat(extracted_text)
        await update.message.reply_text(
            f"Файл: `{file_name}`\nРаспознано:\n```\n{extracted_text[:300]}{'...' if len(extracted_text) > 300 else ''}\n```\n\nОтвет:\n{answer}",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка документа {file_name}: {e}")
        await update.message.reply_text("Ошибка при обработке файла.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Произошла ошибка", exc_info=context.error)

# Запуск
def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_error_handler(error_handler)

    logger.info("Бот запущен с поддержкой фото и документов (включая PDF)!")
    application.run_polling()

if __name__ == "__main__":
    main()
import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from prompts import MICROSOFT_OFFICE_PROMPT

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получение токена бота
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GIGACHAT_CLIENT_ID = os.getenv("GIGACHAT_CLIENT_ID")
GIGACHAT_CLIENT_SECRET = os.getenv("GIGACHAT_CLIENT_SECRET")

# URL для получения токена и отправки запросов
AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
GIGACHAT_API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

# Кэширование access_token (в реальном проекте лучше использовать более надёжное хранилище)
_cached_access_token = None

def get_gigachat_access_token():
    global _cached_access_token
    if _cached_access_token:
        return _cached_access_token

    auth_response = requests.post(
        AUTH_URL,
        data={"scope": "GIGACHAT_API_PUB"},
        auth=(GIGACHAT_CLIENT_ID, GIGACHAT_CLIENT_SECRET),
        verify=False  # ⚠️ В продакшене лучше использовать сертификаты!
    )
    if auth_response.status_code != 200:
        raise Exception(f"Не удалось получить токен: {auth_response.text}")

    token_data = auth_response.json()
    _cached_access_token = token_data["access_token"]
    return _cached_access_token

def ask_gigachat(question: str) -> str:
    prompt = MICROSOFT_OFFICE_PROMPT.format(user_question=question)
    token = get_gigachat_access_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "GigaChat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }

    response = requests.post(GIGACHAT_API_URL, json=payload, headers=headers, verify=False)
    
    if response.status_code == 401:
        # Токен мог истечь — очищаем кэш и пробуем снова
        global _cached_access_token
        _cached_access_token = None
        token = get_gigachat_access_token()
        headers["Authorization"] = f"Bearer {token}"
        response = requests.post(GIGACHAT_API_URL, json=payload, headers=headers, verify=False)

    if response.status_code != 200:
        logger.error(f"GigaChat error: {response.status_code} - {response.text}")
        return "Извините, произошла ошибка при обращении к GigaChat."

    try:
        answer = response.json()["choices"][0]["message"]["content"]
        return answer.strip()
    except (KeyError, IndexError):
        return "Не удалось получить ответ от GigaChat."

# Обработчики Telegram
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот-помощник по Microsoft Office (Word, Excel, PowerPoint, Outlook). "
        "Задайте ваш вопрос — и я постараюсь помочь!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    logger.info(f"Получен вопрос: {user_text}")

    try:
        answer = ask_gigachat(user_text)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        answer = "Произошла ошибка при обработке запроса. Попробуйте позже."

    await update.message.reply_text(answer)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Произошла ошибка при обработке обновления", exc_info=context.error)

# Запуск бота
def main():
    if not TELEGRAM_TOKEN or not GIGACHAT_CLIENT_ID or not GIGACHAT_CLIENT_SECRET:
        raise ValueError("Отсутствуют обязательные переменные окружения в .env")

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    logger.info("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()
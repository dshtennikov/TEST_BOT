import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, 
    ContextTypes, 
    CommandHandler, 
    MessageHandler, 
    filters
)
from pathlib import Path

from config import Config
from file_processor import FileProcessor
from gigachat_client import GigaChatClient

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class OfficeAssistantBot:
    def __init__(self):
        self.config = Config()
        self.file_processor = FileProcessor()
        self.gigachat_client = GigaChatClient()
        self.application = None
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        welcome_text = """
👋 Привет! Я - Ассистент Преподавателя по Цифровым технологиям для менеджеров!

🤖 Я помогу тебе с вопросами по Microsoft Office:
• Word, Excel, PowerPoint
• Формулы, макросы, автоматизация
• Проблемы совместимости версий
• Пошаговые инструкции

📎 Можешь присылать мне:
• Текстовые вопросы
• Изображения с текстом
• PDF, DOCX, XLSX файлы

Просто задай вопрос или загрузи файл! 🚀
        """
        await update.message.reply_text(welcome_text)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = """
📖 Доступные команды:
/start - Начать работу
/help - Показать эту справку
/clear - Очистить историю диалога

📋 Примеры вопросов:
• "Как сделать оглавление в Word?"
• "Почему не работает функция XLOOKUP?"
• "Как посчитать сумму в столбце Excel?"

🖼️ Поддерживаемые файлы:
• Изображения (JPG, PNG) - распознаем текст
• PDF, DOCX, XLSX - извлекаем содержимое
        """
        await update.message.reply_text(help_text)
    
    async def clear_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Очистка истории диалога"""
        self.gigachat_client.clear_history()
        await update.message.reply_text("🗑️ История диалога очищена!")
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        user_message = update.message.text
        
        # Показываем статус обработки
        await update.message.reply_chat_action("typing")
        
        try:
            # Отправляем в GigaChat
            response = self.gigachat_client.send_message(user_message)
            await update.message.reply_text(response)
            
        except Exception as e:
            logger.error(f"Text processing error: {e}")
            await update.message.reply_text("❌ Произошла ошибка при обработке запроса. Попробуйте еще раз.")
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка фотографий"""
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        local_path = Path(Config.DOWNLOAD_DIR) / f"photo_{photo.file_id}.jpg"
        
        try:
            await update.message.reply_text("🖼️ Обрабатываю изображение...")
            
            # Скачиваем файл
            await file.download_to_drive(custom_path=str(local_path))
            
            # OCR обработка
            extracted_text = self.file_processor.process_image(local_path)
            user_question = update.message.caption or "Что на этом изображении?"
            
            # Отправляем в GigaChat
            response = self.gigachat_client.send_message(
                user_question, 
                extracted_text, 
                "image"
            )
            await update.message.reply_text(response)
            
        except Exception as e:
            logger.exception('Photo processing failed')
            await update.message.reply_text(f"❌ Ошибка при обработке изображения: {e}")
        finally:
            # Удаляем временный файл
            if local_path.exists():
                local_path.unlink()
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка документов"""
        doc = update.message.document
        file = await context.bot.get_file(doc.file_id)
        local_path = Path(Config.DOWNLOAD_DIR) / f"{doc.file_id}_{doc.file_name}"
        
        try:
            # Проверка размера файла
            if doc.file_size and doc.file_size > Config.MAX_FILE_SIZE:
                await update.message.reply_text("❌ Файл слишком большой. Максимальный размер: 20MB")
                return
            
            # Определяем тип файла
            file_type = self.file_processor.get_file_type(doc.file_name, doc.mime_type)
            
            if file_type == 'unknown':
                await update.message.reply_text("❌ Поддерживаются только PDF, DOCX, XLSX файлы и изображения")
                return
            
            # Скачиваем файл
            await file.download_to_drive(custom_path=str(local_path))
            await update.message.reply_text(f"📎 Обрабатываю {file_type.upper()} файл...")
            
            # Обработка в зависимости от типа файла
            extracted_text = ""
            if file_type == 'pdf':
                extracted_text = self.file_processor.process_pdf(local_path)
            elif file_type == 'docx':
                extracted_text = self.file_processor.process_docx(local_path)
            elif file_type == 'xlsx':
                extracted_text = self.file_processor.process_xlsx(local_path)
            
            # Обрезаем текст если слишком длинный
            if len(extracted_text) > Config.MAX_TEXT_LENGTH:
                extracted_text = extracted_text[:Config.MAX_TEXT_LENGTH] + "\n\n... (текст обрезан)"
            
            user_question = update.message.caption or f"Проанализируй этот {file_type} файл"
            
            # Отправляем в GigaChat
            response = self.gigachat_client.send_message(
                user_question, 
                extracted_text, 
                file_type
            )
            await update.message.reply_text(response)
            
        except Exception as e:
            logger.exception('Document processing failed')
            await update.message.reply_text(f"❌ Ошибка при обработке документа: {e}")
        finally:
            # Удаляем временный файл
            if local_path.exists():
                local_path.unlink()
    
    def setup_handlers(self):
        """Настройка обработчиков"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("clear", self.clear_history))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        self.application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
    
    def run(self):
        """Запуск бота"""
        try:
            Config.validate()
            
            self.application = ApplicationBuilder().token(Config.TELEGRAM_TOKEN).build()
            self.setup_handlers()
            
            logger.info('🤖 Бот запущен!')
            self.application.run_polling()
            
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            print(f"Ошибка запуска: {e}")

def main():
    bot = OfficeAssistantBot()
    bot.run()

if __name__ == '__main__':
    main()

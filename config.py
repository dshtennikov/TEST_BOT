import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    GIGA_CHAT_TOKEN = os.getenv("GIGA_CHAT_TOKEN")
    DOWNLOAD_DIR = "downloads"
    
    # Настройки OCR
    TESSERACT_LANG = "rus+eng"
    
    # Ограничения
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
    MAX_TEXT_LENGTH = 4000
    
    @classmethod
    def validate(cls):
        if not cls.TELEGRAM_TOKEN:
            raise ValueError("TELEGRAM_TOKEN not set in environment")
        if not cls.GIGA_CHAT_TOKEN:
            raise ValueError("GIGA_CHAT_TOKEN not set in environment")

# 🤖 Office Assistant Bot for Microsoft Office

Бот-ассистент преподавателя для помощи студентам-менеджерам в работе с Microsoft Office. Поддерживает обработку документов, изображений и предоставляет интеллектуальные ответы через GigaChat API.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)
![OCR](https://img.shields.io/badge/OCR-Tesseract-green.svg)

## ✨ Возможности

- **📝 Интеллектуальные ответы** на вопросы по Microsoft Office через GigaChat
- **🖼️ OCR обработка** изображений (русский и английский языки)
- **📄 Обработка документов**: PDF, DOCX, XLSX
- **🔍 Извлечение текста** из сканов и изображений
- **💬 Контекстный диалог** с сохранением истории
- **🛡️ Безопасность** - блокировка вредоносных запросов

## 🏗️ Архитектура
office-assistant-bot/
├── bot.py # Основной файл бота
├── config.py # Конфигурация приложения
├── file_processor.py # Обработчик файлов
├── gigachat_client.py # Клиент GigaChat API
├── prompts.py # Промпты и шаблоны
├── requirements.txt # Зависимости Python
├── install_tesseract.sh # Установка Tesseract OCR
└── .devcontainer/ # Конфигурация GitHub Codespaces

text

## 🚀 Быстрый старт

### 1. Клонирование репозитория

'''bash
git clone https://github.com/yourusername/office-assistant-bot.git
cd office-assistant-bot'''
### 2. Настройка в GitHub Codespaces
Откройте проект в GitHub Codespaces

Система автоматически установит Tesseract OCR и зависимости

Создайте .env файл:

'''bash
# Автоматическое создание тестового .env
bash create_temp_env.sh

# Или интерактивное создание
bash interactive_env_setup.sh'''
### 3. Ручная установка (локально)
Установка Tesseract OCR
Ubuntu/Debian:

'''bash
sudo apt update
sudo apt install -y tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng
Windows:

Скачайте установщик с GitHub Tesseract

Добавьте в PATH: C:\Program Files\Tesseract-OCR\

macOS:

bash
brew install tesseract tesseract-lang
Установка Python зависимостей
bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или venv\Scripts\activate  # Windows

pip install -r requirements.txt'''
### 4. Настройка окружения
Создайте файл .env:

env
TELEGRAM_TOKEN=your_telegram_bot_token_here
GIGA_CHAT_TOKEN=your_gigachat_token_here
DEBUG=true
LOG_LEVEL=INFO
MAX_FILE_SIZE=20971520
Получение токенов:
Telegram Bot Token:

Напишите @BotFather в Telegram

Команда: /newbot

Получите токен вида: 1234567890:AAFakeTokenForTesting123456789

GigaChat Token:

Зарегистрируйтесь на GigaChat

Создайте API ключ в личном кабинете

### 5. Запуск бота
bash
python bot.py
📋 Команды бота
/start - Начать работу с ботом

/help - Получить справку по командам

/clear - Очистить историю диалога

##📁 Поддерживаемые файлы
Тип файла	Форматы	Возможности
Изображения	JPG, PNG, BMP	OCR распознавание текста
Документы	PDF, DOCX	Извлечение текста и структуры
Таблицы	XLSX	Чтение данных с листов
Текст	Любые вопросы	Интеллектуальный анализ
##🎯 Примеры использования
Вопросы по Microsoft Office:
text
• "Как сделать оглавление в Word?"
• "Почему не работает функция XLOOKUP в Excel?"
• "Как создать макрос в PowerPoint?"
• "Как посчитать сумму в столбце Excel?"
Обработка файлов:
📷 Фотография с текстом ошибки → анализ и решение

📄 PDF документ с инструкцией → извлечение ключевой информации

📊 Excel файл с данными → анализ и рекомендации

📝 Word документ → проверка структуры и форматирования

##🔧 Технические детали
Модули проекта
bot.py - Основной модуль Telegram бота

file_processor.py - Обработка и анализ файлов

gigachat_client.py - Интеграция с GigaChat API

config.py - Управление конфигурацией

prompts.py - Промпты для AI-модели

Обработка файлов
python
# Пример обработки PDF
processor = FileProcessor()
text = processor.process_pdf("document.pdf")

# OCR для изображений
text = processor.process_image("screenshot.png")
Безопасность
✅ Проверка размера файлов (макс. 20MB)

✅ Валидация типов файлов

✅ Блокировка вредоносных запросов

✅ Очистка временных файлов

🐛 Решение проблем
Common Issues
Tesseract не установлен:

bash
# Проверка установки
tesseract --version
tesseract --list-langs
Ошибки зависимостей:

bash
pip install --upgrade -r requirements.txt
Проблемы с токенами:

Проверьте правильность токенов в .env

Убедитесь, что бот активирован в @BotFather

Ошибки OCR:

bash
# Тестирование OCR
python test_ocr.py
Логирование
Уровни логирования настраиваются в .env:

env
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
📚 API Документация
GigaChat Integration
python
from gigachat_client import GigaChatClient

client = GigaChatClient()
response = client.send_message("Как сделать оглавление в Word?")
File Processing
python
from file_processor import FileProcessor

processor = FileProcessor()
pdf_text = processor.process_pdf("document.pdf")
docx_text = processor.process_docx("document.docx")
🤝 Разработка
Установка для разработки
bash
git clone https://github.com/yourusername/office-assistant-bot.git
cd office-assistant-bot

# Установка dev-зависимостей
pip install -r requirements.txt
pip install pytest pylint black

# Запуск тестов
python test_ocr.py
python -m pytest tests/
Структура проекта
text
tests/
├── test_ocr.py          # Тесты OCR функциональности
├── test_file_processor.py # Тесты обработки файлов
└── test_bot.py          # Тесты бота
Code Style
bash
# Форматирование кода
black bot.py file_processor.py gigachat_client.py

# Проверка стиля
pylint bot.py
📄 Лицензия
Этот проект распространяется под лицензией MIT. Подробнее см. в файле LICENSE.

👥 Авторы
Ваше Имя

🙏 Благодарности
SberAI за GigaChat API

Tesseract OCR за OCR движок

python-telegram-bot за отличную библиотеку

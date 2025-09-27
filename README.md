# Telegram GigaChat Bot


Простой бот, который передаёт запросы в GigaChat и умеет распознавать текст из изображений, PDF, а также извлекать данные из DOCX и XLSX.


## Быстрый старт
1. Скопируйте файлы в папку проекта.
2. Переименуйте `.env.example` в `.env` и заполните переменные `TELEGRAM_TOKEN` и `GIGA_CHAT_TOKEN`.
3. Установите системные зависимости:
- `tesseract-ocr` (для OCR): `sudo apt install tesseract-ocr` или brew/choco.
- `poppler` (для pdf2image): `sudo apt install poppler-utils` или brew/choco.
4. Установите Python зависимости: `pip install -r requirements.txt`.
5. Запустите: `python bot.py`.


## Особенности и замечания
- `prompt.py` содержит системный prompt, оптимизированный для ответов по Microsoft Office с учётом версий и платформ.
- Используется официальный клиент `gigachat` для взаимодействия с API.
- OCR может давать ошибк

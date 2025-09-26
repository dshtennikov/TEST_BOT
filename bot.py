import os
import logging
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CLIENT_ID = os.getenv("GIGACHAT_CLIENT")
CLIENT_SECRET = os.getenv("GIGACHAT_CLIENT_SECRET")
ACCESS_TOKEN = os.getenv("CGIGA_CHAT_TOKEN")  # может быть пустым
AUTH_URL = os.getenv("GIGACHAT_AUTH_URL")
API_URL = os.getenv("GIGACHAT_API_URL")

# ======================================================
# Авторизация в GigaChat
# ======================================================
def get_gigachat_token() -> str:
    global ACCESS_TOKEN
    if ACCESS_TOKEN:
        return ACCESS_TOKEN

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": "123e4567-e89b-12d3-a456-426614174000",  # можно сгенерировать uuid4
    }
    data = {
        "scope": "GIGACHAT_API_PERS",  # может быть другой (ORG/TEAM), уточните у себя
    }

    resp = requests.post(
        AUTH_URL,
        headers=headers,
        auth=(CLIENT_ID, CLIENT_SECRET),
        data=data,
        verify=False,  # у них бывает self-signed TLS, если есть корневой сертификат — лучше убрать
        timeout=30,
    )

    if resp.status_code != 200:
        raise RuntimeError(f"GigaChat auth failed: {resp.status_code} {resp.text}")

    token = resp.json().get("access_token")
    if not token:
        raise RuntimeError("Не удалось получить access_token от GigaChat")

    ACCESS_TOKEN = token
    return token

# ======================================================
# Вызов GigaChat API
# ======================================================
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
        # токен протух → сбрасываем и пробуем снова
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
import logging
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from config import Config
from prompts import MICROSOFT_OFFICE_PROMPT, format_user_prompt

logger = logging.getLogger(__name__)

class GigaChatClient:
    def __init__(self):
        self.client = GigaChat(
            credentials=Config.GIGA_CHAT_TOKEN,
            verify_ssl_certs=False
        )
        self.conversation_history = []
    
    def send_message(self, user_message: str, extracted_text: str = None, file_type: str = None) -> str:
        """Отправка сообщения в GigaChat"""
        try:
            # Форматируем пользовательский промпт
            user_prompt = format_user_prompt(user_message, extracted_text, file_type)
            
            # Создаем список сообщений
            messages = [
                Messages(role=MessagesRole.SYSTEM, content=MICROSOFT_OFFICE_PROMPT)
            ]
            
            # Добавляем историю диалога
            messages.extend(self.conversation_history)
            
            # Добавляем текущее сообщение
            messages.append(Messages(role=MessagesRole.USER, content=user_prompt))
            
            # Отправляем запрос
            response = self.client.chat(Chat(messages=messages))
            assistant_response = response.choices[0].message.content
            
            # Обновляем историю (ограничиваем размер)
            self.conversation_history.append(Messages(role=MessagesRole.USER, content=user_prompt))
            self.conversation_history.append(Messages(role=MessagesRole.ASSISTANT, content=assistant_response))
            
            # Ограничиваем историю последними 10 сообщениями
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
            
            return assistant_response
            
        except Exception as e:
            logger.error(f"GigaChat error: {e}")
            return "🤖 Извините, произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте еще раз."
    
    def clear_history(self):
        """Очистка истории диалога"""
        self.conversation_history = []

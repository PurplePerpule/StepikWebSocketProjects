from pydantic import BaseModel


class Message(BaseModel):
    text: str  # Текст сообщения
    author: str  # Автор сообщения
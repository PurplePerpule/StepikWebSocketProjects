from pydantic import BaseModel
from typing import List, Optional


class User(BaseModel):
    sid: str               # Уникальный идентификатор пользователя (Socket.IO ID)
    room: Optional[str]    # Название комнаты
    name: Optional[str]    # Имя пользователя
    messages: List[str] = []  # Список сообщений пользователя


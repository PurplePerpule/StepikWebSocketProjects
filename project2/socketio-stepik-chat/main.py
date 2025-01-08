import eventlet
from eventlet import wsgi
import socketio
from loguru import logger

from src.models.user import User
from src.models.message import Message

ROOMS = ["lobby", "general", "random"]

# Заставляем работать пути к статике
static_files = {'/': 'static/index.html', '/static': './static'}
sio = socketio.Server(cors_allowed_origins='*', async_mode='eventlet')
app = socketio.WSGIApp(sio, static_files=static_files)

# Хранилище пользователей
users = {}

def add_user(sid, user):
    """Добавляет пользователя в хранилище."""
    users[sid] = user
    logger.debug(f"Пользователь добавлен: {user} (SID={sid})")

def get_user(sid):
    """Возвращает пользователя по SID."""
    return users.get(sid)

def remove_user(sid):
    """Удаляет пользователя из хранилища."""
    user = users.pop(sid, None)
    if user:
        logger.debug(f"Пользователь удалён: {user} (SID={sid})")
    return user

# Обрабатываем подключение пользователя
@sio.event
def connect(sid, environ):
    logger.info(f"Пользователь {sid} подключился")

@sio.on('get_rooms')
def on_get_rooms(sid, data):
    sio.emit('rooms', ROOMS, to=sid)
    logger.info(f"Список комнат отправлен пользователю {sid}")

@sio.on('join')
def on_join(sid, data):
    room = data.get('room')
    name = data.get('name')

    # Валидация данных
    if not room or room not in ROOMS:
        sio.emit('error', {'message': 'Invalid room'}, to=sid)
        logger.warning(f"Некорректная комната: room={room}, sid={sid}")
        return
    if not name:
        sio.emit('error', {'message': 'Invalid name'}, to=sid)
        logger.warning(f"Некорректное имя: name={name}, sid={sid}")
        return

    # Создаем пользователя и добавляем его в хранилище
    user = User(sid=sid, room=room, name=name)
    add_user(sid, user)

    # Присоединяем пользователя к комнате
    sio.enter_room(sid, room)
    sio.emit('move', {'room': room}, to=sid)
    logger.info(f"Пользователь {name} (sid={sid}) присоединился к комнате {room}")

@sio.on('leave')
def on_leave(sid, data):
    user = remove_user(sid)
    if user and user.room:
        sio.leave_room(sid, user.room)
        logger.info(f"Пользователь {user.name} (sid={sid}) покинул комнату {user.room}")

@sio.on('send_message')
def on_message(sid, data):
    text = data.get('text')
    user = get_user(sid)

    # Валидация данных
    if not user:
        sio.emit('error', {'message': 'User not found'}, to=sid)
        logger.error(f"Пользователь с sid={sid} не найден")
        return
    if not text:
        sio.emit('error', {'message': 'Message text is required'}, to=sid)
        logger.warning(f"Пустое сообщение от пользователя {user.name} (sid={sid})")
        return

    # Создаём сообщение и добавляем его к пользователю
    message = Message(text=text, author=user.name)
    user.messages.append(message)

    # Рассылаем сообщение в комнате
    sio.emit('message', {'name': user.name, 'text': text}, to=user.room)
    logger.info(f"Сообщение от {user.name} в комнате {user.room}: {text}")

@sio.event
def disconnect(sid):
    user = remove_user(sid)
    if user:
        logger.info(f"Пользователь {user.name} (sid={sid}) отключился")

if __name__ == '__main__':
    wsgi.server(eventlet.listen(("127.0.0.1", 8000)), app)

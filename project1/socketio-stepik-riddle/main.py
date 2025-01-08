import eventlet
import socketio
from eventlet import wsgi
from loguru import logger

from src.all_riddles import riddles

# Заставляем работать пути к статике
static_files = {'/': 'static/index.html', '/static': './static'}
sio = socketio.Server(cors_allowed_origins='*', async_mode='eventlet')
app = socketio.WSGIApp(sio, static_files=static_files)

# Храним состояние игроков
players = {}

# Обрабатываем подключение пользователя
@sio.event
def connect(sid, environ):
    logger.info(f"Пользователь {sid} подключился")
    players[sid] = {"current_riddle_index": 0, "score": 0}

# Обрабатываем запрос очередного вопроса
@sio.on('next')
def next_event(sid, data):
    player = players.get(sid)
    
    if player:
        current_index = player["current_riddle_index"]
        
        if current_index < len(riddles):
            riddle = riddles[current_index]
            player["current_riddle_index"] += 1  # Увеличиваем индекс для следующей загадки
            sio.emit('riddle', {'text': riddle['text']}, room=sid)
        else:
            sio.emit('over', {}, room=sid)

# Обрабатываем отправку ответа
@sio.on('answer')
def receive_answer(sid, data):
    answer = data.get('text', '').strip().lower()
    player = players.get(sid)
    
    if player and player["current_riddle_index"] > 0:
        current_index = player["current_riddle_index"] - 1  # Индекс текущей загадки
        correct_answer = riddles[current_index]["answer"].lower()
        is_correct = correct_answer == answer
        
        if is_correct:
            player["score"] += 1
        
        sio.emit('result', {
            'riddle': riddles[current_index]["text"],
            'is_correct': is_correct,
            'answer': riddles[current_index]["answer"]
        }, room=sid)
        
        sio.emit('score', {'value': player["score"]}, room=sid)

# Обрабатываем отключение пользователя
@sio.event
def disconnect(sid):
    logger.info(f"Пользователь {sid} отключился")
    if sid in players:
        del players[sid]

if __name__ == '__main__':
    wsgi.server(eventlet.listen(("127.0.0.1", 8000)), app)
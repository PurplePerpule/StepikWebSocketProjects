import eventlet
from eventlet import wsgi
import socketio
from loguru import logger
from src.models import Player, Game, Question
from src.topics import topics
from src.questions import questions
from typing import List

# Статика
static_files = {'/': 'static/index.html', '/static': './static'}
sio = socketio.Server(cors_allowed_origins='*', async_mode='eventlet')
app = socketio.WSGIApp(sio, static_files=static_files)

# Глобальные переменные
waiting_players = {}  # Зал ожидания {topic_pk: [player1, player2, ...]}
games = {}  # Текущие игры {game_uid: Game}

def get_questions_by_topic(topic_pk: int) -> List[Question]:
    logger.debug(f"Запрос вопросов для темы с pk={topic_pk}")
    
    # Проверка на наличие вопросов по теме
    filtered_questions = [Question(**q) for q in questions if q['topic'] == topic_pk]
    if not filtered_questions:
        logger.warning(f"Для темы {topic_pk} нет вопросов.")
    
    return filtered_questions

@sio.event
def connect(sid, environ):
    logger.info(f"Пользователь {sid} подключился с окружением {environ}")
    
    # Проверка на корректность окружения
    if not environ:
        logger.warning(f"У окружения для пользователя {sid} нет данных.")
        
@sio.on("get_topics")
def get_topics(sid, *args):
    logger.debug(f"Получен запрос на темы от пользователя {sid}")
    
    # Проверка на наличие доступных тем
    if not topics:
        logger.warning("Список тем пуст!")
    
    topics_list = [{"pk": topic['pk'], "name": topic['name'], "has_players": bool(waiting_players.get(topic['pk']))}
                   for topic in topics]
    sio.emit("topics", topics_list, to=sid)
    logger.info(f"Отправлены темы пользователю {sid}: {topics_list}")

@sio.on("join_game")
def join_game(sid, data):
    logger.debug(f"Получен запрос от пользователя {sid} на присоединение к игре с данными: {data}")
    
    # Проверка на наличие данных в запросе
    if not data.get("topic_pk") or not data.get("name"):
        logger.error(f"Недостаточно данных для присоединения к игре от пользователя {sid}")
        sio.emit("error", {"message": "Missing required data"}, to=sid)
        return
    
    topic_pk = data.get("topic_pk")
    name = data.get("name")
    topic = next((t for t in topics if t['pk'] == topic_pk), None)

    if not topic:
        logger.error(f"Тема с pk={topic_pk} не найдена для пользователя {sid}")
        sio.emit("error", {"message": "Invalid topic"}, to=sid)
        return

    if topic_pk not in waiting_players:
        waiting_players[topic_pk] = []
        logger.debug(f"Создан новый список игроков для темы с pk={topic_pk}")

    player = Player(sid=sid, name=name)
    waiting_players[topic_pk].append(player)
    logger.info(f"Игрок {name} ({sid}) присоединился к теме {topic['name']}")

    # Проверка, достаточно ли игроков для старта игры
    if len(waiting_players[topic_pk]) == 2:
        player1, player2 = waiting_players[topic_pk]
        del waiting_players[topic_pk]

        topic_questions = get_questions_by_topic(topic_pk)
        if not topic_questions:
            logger.error(f"Не удалось получить вопросы для темы {topic_pk}")
            return
        
        game_uid = f"game_{sid}"
        game = Game(players=[player1, player2], questions=topic_questions)
        games[game_uid] = game
        logger.info(f"Запущена новая игра {game_uid} с игроками {player1.name} и {player2.name}")

        for p in [player1, player2]:
            sio.emit("game", {
                "uid": game_uid,
                "players": [{"name": p.name, "score": p.score}],
                "current_question": topic_questions[0].dict(),
                "question_count": len(topic_questions)
            }, to=p.sid)
            logger.debug(f"Отправлена информация о игре {game_uid} игроку {p.sid}")

@sio.on("answer")
def answer(sid, data):
    logger.debug(f"Получен ответ от пользователя {sid} с данными: {data}")
    
    # Проверка на корректность данных ответа
    if not data.get("game_uid") or data.get("index") is None:
        logger.error(f"Отсутствуют необходимые данные для ответа от пользователя {sid}")
        sio.emit("error", {"message": "Missing required data"}, to=sid)
        return
    
    game_uid = data.get("game_uid")
    index = data.get("index")
    game = games.get(game_uid)

    if not game:
        logger.error(f"Игра с uid={game_uid} не найдена для пользователя {sid}")
        sio.emit("error", {"message": "Game not found"}, to=sid)
        return

    current_question = game.get_current_question()
    correct_index = current_question.answer

    player = next((p for p in game.players if p.sid == sid), None)
    if not player:
        logger.error(f"Игрок с sid={sid} не найден в игре {game_uid}")
        sio.emit("error", {"message": "Player not in game"}, to=sid)
        return

    feedback = {"correct": index == correct_index, "answer": correct_index + 1}
    if index == correct_index:
        player.score += 1
        logger.info(f"Игрок {player.name} правильно ответил на вопрос, увеличен счет до {player.score}")

    if game.next_question():
        next_question = game.get_current_question()
        for p in game.players:
            sio.emit("game", {
                "uid": game_uid,
                "players": [{"name": pl.name, "score": pl.score} for pl in game.players],
                "current_question": next_question.dict(),
                "question_count": len(game.questions) - game.current_question_index,
                "feedback": feedback
            }, to=p.sid)
        logger.debug(f"Отправлены обновления по игре {game_uid} игрокам")
    else:
        results = [{"name": p.name, "score": p.score} for p in game.players]
        logger.info(f"Игра {game_uid} завершена, результаты: {results}")
        for p in game.players:
            sio.emit("over", {"results": results}, to=p.sid)

@sio.event
def disconnect(sid):
    logger.info(f"Пользователь {sid} отключился")
    
    # Проверка на удаление игрока из всех тем и игр
    for topic_pk, players in waiting_players.items():
        waiting_players[topic_pk] = [p for p in players if p.sid != sid]
    
    for game_uid, game in games.items():
        game.players = [p for p in game.players if p.sid != sid]
        if not game.players:
            del games[game_uid]
    
    logger.debug(f"Игрок с sid={sid} был удален из всех игр и тем")

if __name__ == '__main__':
    logger.info("Запуск сервера на http://127.0.0.1:8000")
    wsgi.server(eventlet.listen(("127.0.0.1", 8000)), app)
    logger.debug("Сервер успешно запущен и слушает 127.0.0.1:8000")

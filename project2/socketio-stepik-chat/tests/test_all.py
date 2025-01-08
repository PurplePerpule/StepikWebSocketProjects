import time
import requests

URL = 'http://127.0.0.1:8000/'


def test_assets():
    """
    Тест проверяет что сервер отдаёт index.html и все необходимые статические файлы подгружаются
    """
    response = requests.get(URL)
    assert response.status_code == 200, "Не удалось загрузить страницу index.html"

    page_content = response.content.decode('utf-8')
    assert '<script src="/static/lariska.js"></script>' in page_content
    assert '<script src="/static/script.js"></script>' in page_content
    assert '<link rel="stylesheet" type="text/css" href="/static/style.css"/>' in page_content

    # check that all static files are loaded
    response_lariska = requests.get(URL + 'static/lariska.js')
    assert response_lariska.status_code == 200, "Не удалось подгрузить lariska.js"

    response_script = requests.get(URL + 'static/script.js')
    assert response_script.status_code == 200, "Не удалось подгрузить script.js"

    response_style = requests.get(URL + 'static/style.css')
    assert response_style.status_code == 200, "Не удалось подгрузить style.css"


def test_logic_full(client, events):
    """
    Тест проверяет всю логику работы чата
    """
    client.connect(URL)
    assert client.connected, "Клиент не смог подключиться к серверу"

    client.emit('get_rooms', {})
    time.sleep(0.1)

    rooms = events.get('rooms')
    assert rooms, "Не пришёл эвент 'rooms' в ответ на эвент 'get_rooms'"
    assert rooms == ['lobby', 'general', 'random'], (f"Вернулись неправильные комнаты, ожидались: "
                                                     f"['lobby', 'general', 'random'], получены: "
                                                     f"{rooms['rooms']}")

    client.emit('join', {'room': 'general', 'name': 'Jason Statman'})
    time.sleep(0.1)

    move = events.get('move')
    assert move, "Не пришёл эвент 'move' после подключения в ответ на эвент 'join'"
    assert move['room'] == 'general', (f"Вернулись неправильная комната после подключения, ожидалась: general, "
                                       f"получена: {move['room']}")

    client.emit('send_message', {'text': 'Hello!'})
    time.sleep(0.1)

    message = events.get('message')
    assert message, "Не пришёл эвент 'message' после отправки сообщения эвентом 'send_message'"
    assert message['text'] == 'Hello!', (f"Вернулся неправильный текст сообщения, ожидался: 'Hello!', "
                                         f"получен: {message['text']}")
    assert message['name'] == 'Jason Statman', (f"Вернулось неправильное имя отправителя, ожидалось: 'Jason Statman', "
                                                f"получено: {message['name']}")

    client.emit('leave')
    time.sleep(0.1)

    client.emit('join', {'room': 'lobby', 'name': 'Michael'})
    time.sleep(0.1)

    move = events.get('move')
    assert move, "Не пришёл эвент 'move' после подключения в ответ на эвент 'join'"
    assert move['room'] == 'lobby', (f"Вернулись неправильная комната после подключения, ожидалась: lobby, "
                                     f"получена: {move['room']}")

    client.emit('send_message', {'text': 'Python'})
    time.sleep(0.1)

    message = events.get('message')
    assert message, "Не пришёл эвент 'message' после отправки сообщения эвентом 'send_message'"
    assert message['text'] == 'Python', (f"Вернулся неправильный текст сообщения, ожидался: 'Python', "
                                         f"получен: {message['text']}")
    assert message['name'] == 'Michael', (f"Вернулось неправильное имя отправителя, ожидалось: 'Michael', "
                                          f"получено: {message['name']}")

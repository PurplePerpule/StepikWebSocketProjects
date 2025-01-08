import time
import requests

URL = 'http://127.0.0.1:8000/'


def test_assets(client):
    """
    Тест проверяет что сервер отдаёт index.html и все необходимые статические файлы подгружаются
    """
    response = requests.get(URL)
    assert response.status_code == 200, "Не удалось загрузить страницу index.html"

    page_content = response.content.decode('utf-8')
    assert '<script src="static/lariska.js"></script>' in page_content
    assert '<script src="static/script.js"></script>' in page_content
    assert '<link rel="stylesheet" type="text/css" href="static/style.css"/>' in page_content

    # check that all static files are loaded
    response_lariska = requests.get(URL + 'static/lariska.js')
    assert response_lariska.status_code == 200, "Не удалось подгрузить lariska.js"

    response_script = requests.get(URL + 'static/script.js')
    assert response_script.status_code == 200, "Не удалось подгрузить script.js"

    response_style = requests.get(URL + 'static/style.css')
    assert response_style.status_code == 200, "Не удалось подгрузить style.css"


def test_logic_full(client, events, riddles):
    """
    Тест проверяет всю логику игры
    (все вопросы, правильные и неверные ответы, подсчёт очков и окончание игры)
    """
    client.connect(URL)
    assert client.connected, "Клиент не смог подключиться к серверу"

    # Отвечаем верно на первые 4 вопроса из 5
    for i in range(1, 5):
        client.emit('next', {})
        time.sleep(0.1)

        response = events.get('riddle')
        assert response, "Не пришёл эвент 'riddle' после начала игры" if i == 1 \
            else "Не пришёл эвент 'riddle' после нажатия кнопки 'Следующий вопрос'"
        assert 'text' in response, "Не найден текст загадки в эвенте 'riddle'"

        answer = riddles(response['text'])

        client.emit('answer', {'text': answer})
        time.sleep(0.1)

        score = events.get('score')
        assert score, "Не пришёл эвент 'score' после ответа на вопрос!"
        assert score['value'] == i, f"Количество очков должно быть {i}, получено значение {score['value']}!"

        result = events.get('result')
        assert result, "Не пришёл эвент 'result' после ответа на вопрос!"
        assert result['is_correct'] == True, "Ответ на вопрос должен быть верным!"

        # очищаем предыдущие данные, полученные в эвентах
        for event in ('riddle', 'score', 'result'):
            if event in events:
                del events[event]

    # Отвечаем на последнюю 5ю задачу неверным ответом
    client.emit('next', {})
    time.sleep(0.1)
    client.emit('answer', {'text': 'wrong answer'})
    time.sleep(0.1)
    result = events.get('result')
    assert result, "Не пришёл эвент 'result' после неверного ответа на вопрос!"
    assert result['is_correct'] == False, ("Ответ на вопрос должен быть неверным, "
                                           "так как тест передаёт в 'answer': {'text': 'wrong answer'}")

    # Очищаем данные предыдущего score, далее будет проверка придёт ли score с 0 очков в конце игры.
    if 'score' in events:
        del events['score']

    client.emit('next', {})
    time.sleep(0.1)

    # Проверяем пришёл ли эвент 'over' после окончания игры
    assert 'over' in events, "Эвент 'over' не пришёл после окончания игры!"

    score = events.get('score')
    assert score, "Не пришёл эвент 'score' после окончания игры!"
    # Проверяем что очки сбросились в 0 после окончания игры
    assert score['value'] == 0, (f"После окончания игры количество очков должно быть 0, "
                                 f"получено значение {score['value']}!")

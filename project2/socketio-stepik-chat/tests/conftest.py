import pytest
from socketio import Client


@pytest.fixture
def client():
    sio = Client()
    yield sio
    sio.disconnect()


@pytest.fixture
def events(client):
    """ Фикстура для отлова всех эвентов которые приходят от бэка клиенту """
    all_events = {}

    def event_handler(event, data):
        all_events[event] = data

    client.on('*', event_handler)
    yield all_events

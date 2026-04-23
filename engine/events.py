class Subject:
    def __init__(self):
        self._observers = []

    def attach(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer):
        try:
            self._observers.remove(observer)
        except ValueError:
            pass

    def notify(self, event_type: str, data: dict = None):
        for observer in self._observers:
            observer.update(event_type, data)


class Observer:
    def update(self, event_type: str, data: dict):
        pass

class GameEventLogger(Observer):
    def update(self, event_type: str, data: dict):
        # Useful for debugging. In a full game, events trigger logic here.
        # print(f"[DEBUG] Event: {event_type} - {data}")
        pass

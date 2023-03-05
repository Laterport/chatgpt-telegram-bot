import json, time

class Chat:
    def __init__(self):
        self.__last_updated = 0
        self.__messages = []
        with open("config.json") as f:
            config = json.load(f)
            self.__wait_time = config["wait_time"]

    def __repr__(self):
        return str(self.__messages) + '\n'

    @property
    def history(self):
        return self.__messages

    def add_message(self, message, source):
        now = time.time()
        # if last conversation ended more than __wait_time ago (default: 300s), forget it
        if (source == "user") and (now - self.__last_updated > self.__wait_time):
            self.__messages.clear()

        self.__last_updated = now
        self.__messages.append({"role": source, "content": message})

    def clear(self):
        self.__last_updated = time.time()
        self.__messages.clear()

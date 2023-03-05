import os, time, json

class UsageStats:
    USAGE_UPDATE_PERIOD = 300 # seconds

    def __init__(self):
        if not os.path.exists("./usage"):
            os.makedirs("./usage")

        self.__last_usage_dump = 0
        self.__file_path = None
        self.__token_stats = {}
        self.__load(time.time())


    def update(self, user_id, used_tokens):
        now = time.time()
        filepath = self.__usage_file_path(now)
        if filepath != self.__file_path:
            self.__load(now) # switch to the file with next month's stats

        today = self.__format_time(now, "%Y-%m-%d")
        if today not in self.__token_stats:
            self.__token_stats[today] = {}
        today_stats = self.__token_stats[today]

        if user_id not in today_stats:
            today_stats[user_id] = {"tokens": used_tokens, "requests": 1}
        else:
            user_stats = today_stats[user_id]
            user_stats["tokens"] += used_tokens
            user_stats["requests"] += 1

        if now - self.__last_usage_dump >= self.USAGE_UPDATE_PERIOD:
            self.__dump(now)


    def __format_time(self, now, fmt_string):
        return time.strftime(fmt_string, time.gmtime(now))

    def __usage_file_path(self, now):
        name = self.__format_time(now, "%Y%m") + "_usage.json"
        return os.path.join('.', "usage", name)

    def __load(self, now):
        filepath = self.__usage_file_path(now)
        if self.__file_path is not None and filepath != self.__file_path:
             # save previously used file
             self.__dump(now)

        self.__token_stats = {}
        self.__file_path = filepath
        self.__last_usage_dump = now
        if os.path.exists(filepath):
            with open(filepath) as f:
                self.__token_stats = json.load(f)

    def __dump(self, now):
        with open(self.__file_path, "w") as f:
            json.dump(self.__token_stats, f)
        self.__last_usage_dump = now

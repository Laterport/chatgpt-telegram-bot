#!/usr/bin/python3
# -*- coding: utf-8 -*-
import openai, json
from usage import UsageStats

class ChatGPT:
    MODEL_NAME = "gpt-3.5-turbo"
    BEHAVIOUR = {"role": "system", "content": "You are a helpful assistant"}

    def __init__(self):
        with open("config.json") as f:
            cfg = json.load(f)
            openai.api_key = cfg["openai_api_key"]
        self.__usage = UsageStats()

    def get_response(self, user_id, chat_messages, update_usage=True):
        try:
            response = openai.ChatCompletion.create(
                model=self.MODEL_NAME,
                messages=[self.BEHAVIOUR].extend(chat_messages)
            )
            if update_usage:
                self.__usage.update(user_id, response["usage"]["total_tokens"])
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            return str(e) + "\nSorry, I am not feeling well. Please try again."

if __name__=="__main__":
    bot = ChatGPT()
    print(bot.get_response(123, [{"role": "user", "content": "Tell me a joke."}], False))

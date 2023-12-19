# chatbot.py

from chat import Chat
import json
from openai_api import ChatGPT

class ChatBot:
    def __init__(self):
        self.__chats = {}
        # Load API key from config file
        with open("config.json") as config_file:
            config_data = json.load(config_file)
            api_key = config_data.get("openai_api_key")
            self.__bot = ChatGPT(api_key)

    # returns ChatGPT response
    def talk(self, chat_id, user_id, message):
        if chat_id not in self.__chats:
            self.__chats[chat_id] = Chat()
        chat = self.__chats[chat_id]
        chat.add_message(message, "user")

        openai_response = self.__bot.get_response(user_id, chat.history)
        chat.add_message(openai_response, "assistant")
        return openai_response

    def clear(self, chat_id):
        try:
            self.__chats[chat_id].clear()
        except Exception as e:
            print(e)

if __name__ == "__main__":
    bot = ChatBot()

    try:
        chat_id = 1
        user_id = "some_user_id"
        message = "Tell me a joke."
        response = bot.talk(chat_id, user_id, message)
        print(response)
    except Exception as e:
        print(str(e) + "\nSorry, I am not feeling well. Please try again.")

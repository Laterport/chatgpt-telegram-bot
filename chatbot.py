from chat import Chat
from openai_api import ChatGPT

class ChatBot:
    def __init__(self):
        self.__chats = {}
        self.__bot = ChatGPT()

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
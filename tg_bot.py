#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""TelegramMessageParser
Enter description of this module
__author__ = Zhiquan Wang
__copyright__ = Copyright 2022
__version__ = 1.0
__maintainer__ = Zhiquan Wang
__email__ = i@flynnoct.com
__status__ = Dev
"""
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import json, random
from chatbot import ChatBot

class TelegramBot:
    def __init__(self):
        with open("config.json") as f:
            config = json.load(f)
            self.__allowed_users = config["allowed_users"]
            self.bot = ApplicationBuilder().token(config["telegram_bot_token"]).build()
        self.add_handlers()
        self.__chat_bot = ChatBot()

        # start
        self.bot.run_polling()

    def add_handlers(self):
        self.bot.add_handler(CommandHandler("start", self.start))
        self.bot.add_handler(CommandHandler("clear", self.clear_context))
        self.bot.add_handler(CommandHandler("getid", self.get_user_id))
        self.bot.add_handler(MessageHandler(filters.PHOTO | filters.AUDIO | filters.VIDEO, self.chat_file))
        self.bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.chat))
        self.bot.add_handler(MessageHandler(filters.COMMAND, self.unknown))


    async def chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.effective_message

        # Check if the message is an explicit mention to the bot
        if f"@{context.bot.username}" in msg.text or msg.chat.type=="private":
            # Bot is explicitly mentioned or it's a private chat, respond to the message
            await context.bot.send_chat_action(chat_id=msg.chat.id, action="typing")

            # Check if the user is allowed to use the bot
            if not self.check_user_allowed(str(update.effective_user.id)):
                await context.bot.send_message(
                    chat_id=msg.chat.id,
                    text="Sorry, you are not allowed to use this bot. Contact the bot owner for more information."
                )
                return

            # Directly pass the user's message to OpenAI for processing
            response = self.__chat_bot.talk(msg.chat.id, update.effective_user.id, msg.text)
            await msg.reply_text(response)
            return  # Exit the function to avoid further processing

        # If not explicitly mentioned, check if the message contains any keywords
        with open('all_unique_words.txt', 'r', encoding='utf-8') as file:
            keywords = [line.strip().lower() for line in file.readlines()]

        lower_text = msg.text.lower()

        # Check if any keyword is present in the message
        if any(keyword in lower_text for keyword in keywords):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            msg_text = msg.text.replace(f"@{context.bot.username}", "")

            # Randomly select a phrase template
            phrase_templates = [
                "Не задачай лишних вопросов, а просто расскажи мне про {word}",
                "Не задачай лишних вопросов, а просто скажи, ты думаешь про {word}",
                "Не задачай лишних вопросов, а просто поведай историю про {word}",
                "Не задачай лишних вопросов, а просто расскажи анекдот про {word}",
                "Не задачай лишних вопросов, а просто сочини стих про {word}",
                "Не задачай лишних вопросов, а просто придумай афоризм про {word}",
                "Не мучь свой мозг вопросами, а просто расскажи интересный факт о {word}.",
                "Не заморачивайся вопросами, а поделись своими впечатлениями от {word}.",
                "Забудь про вопросы, а расскажи, как ты относишься к {word}.",
                "Не усложняй, просто расскажи свою любимую историю, связанную с {word}.",
                "Не гони вопросы, а расскажи, что приходит тебе в голову, когда слышишь {word}."
            ]

            random_template = random.choice(phrase_templates)

            # Substitute the keyword into the selected template
            response = random_template.format(word=msg_text)

            # Send the generated phrase directly to OpenAI
            openai_response = self.__chat_bot.talk(update.effective_chat.id, update.effective_user.id, response)

            # Respond with the OpenAI-generated response
            await update.message.reply_text(openai_response)
            return  # Exit the function to avoid further processing

        # If no explicit mention or keyword is found, do not respond to general chat messages
        return


    # file and photo messages
    async def chat_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # get message
        message = update.effective_message.text
        if message is None:
            return
        # group chat without @username
        if (update.effective_chat.type in ["group", "supergroup"] and f"@{context.bot.username}" not in message):
            return
        # check if user is allowed to use this bot
        if not self.check_user_allowed(str(update.effective_user.id)):
            await context.bot.send_message(chat_id = update.effective_chat.id,
                text = "Sorry, you are not allowed to use this bot. Contact the bot owner for more information."
            )
            return
        await context.bot.send_message(chat_id = update.effective_chat.id,
            text = "Sorry, I can't handle files and photos yet."
        )

    # start command
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Hello, I'm a ChatGPT bot."
        )

    # clear context command
    async def clear_context(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.__chat_bot.clear(update.effective_chat.id)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Context cleared.")

    async def get_user_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id, text=str(update.effective_user.id))

    # unknown command
    async def unknown(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Sorry, I didn't understand that command."
        )

    # check if user is allowed to use this bot, add user to "allowed_users" in config.json
    def check_user_allowed(self, user_id):
        return user_id in self.__allowed_users


if __name__=="__main__":
    TelegramBot()
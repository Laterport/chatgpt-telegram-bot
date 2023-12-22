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
import json
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

    # chat messages
    async def chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.effective_message
        if update.effective_chat.type in ["group", "supergroup"]:
            isReplyToBot = msg.reply_to_message and msg.reply_to_message.from_user.id == context.bot.id
            isAddressedToBot = isReplyToBot or f"@{context.bot.username}" in msg.text
            if not isAddressedToBot:
                return

        # check if user is allowed to use this bot
        if not self.check_user_allowed(str(update.effective_user.id)):
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Sorry, you are not allowed to use this bot. Contact the bot owner for more information."
            )
            return

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        # remove bot @username from message
        msg_text = msg.text.replace(f"@{context.bot.username}", "")
        # send message to openai
        response = self.__chat_bot.talk(update.effective_chat.id, update.effective_user.id, msg_text)
        await update.message.reply_text(response) # send bot response to user

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
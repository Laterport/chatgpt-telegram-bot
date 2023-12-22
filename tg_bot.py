import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import json, random, re, sys
from chatbot import ChatBot


logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

        if not self.check_user_allowed(str(update.effective_user.id)):
            await context.bot.send_message(chat_id = update.effective_chat.id,
                text = "Sorry, you are not allowed to use this bot. Contact the bot owner for more information."
            )
            return

        # Check if the message is a reply to the bot in private messages
        if msg.reply_to_message and msg.reply_to_message.from_user.id == context.bot.id:
            # The message is a reply to the bot in a private chat, respond to the message
            await context.bot.send_chat_action(chat_id=msg.chat.id, action="typing")

            # Directly pass the user's reply to OpenAI for processing
            response = self.__chat_bot.talk(msg.chat.id, update.effective_user.id, msg.text)
            await msg.reply_text(response)
            return  # Exit the function to avoid further processing

        # If not explicitly mentioned, check if the message is in private chat
        if msg.chat.type == "private":
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

            # Directly pass the user's message to OpenAI for processing
            response = self.__chat_bot.talk(update.effective_chat.id, update.effective_user.id, msg.text)

            # Respond with the OpenAI-generated response
            await msg.reply_text(response)

            # If the message is not in private chat, do not respond
            return

            # If in a group chat and user is allowed
        if msg.chat.type == "supergroup" and context.bot.username in msg.text.lower():
            # Extract user's direct message
            direct_message = msg.text.split(context.bot.username)[1].strip()

            # Process the user's direct message using OpenAI
            response = self.__chat_bot.talk(update.effective_chat.id, update.effective_user.id, direct_message)

            # Respond with the OpenAI-generated response
            await context.bot.send_chat_action(chat_id=update.effective_chat.id,
                                               action="typing")  # Add typing status here
            await msg.reply_text(response)
            return  # Exit the function to avoid further processing

        # If not explicitly mentioned, check if the message contains any keywords
        with open('DICT.txt', 'r', encoding='utf-8') as file:
            patterns = [re.compile(line.strip(), re.IGNORECASE) for line in file.readlines()]

        lower_text = msg.text.lower()

        # Проверьте, есть ли какое-либо ключевое слово в сообщении
        if any(pattern.search(lower_text) for pattern in patterns):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            msg_text = msg.text.replace(f"@{context.bot.username}", "")

            # Randomly select a phrase template
            phrase_templates = [
                "Не задавай лишних вопросов, а просто сочини стих про {word}",
                "Не задачай лишних вопросов, а просто придумай афоризм про {word}",
                "Не мудри, а напиши краткую рассказ-миниатюру на тему {word}",
                "Не томи вопросами, а создай эпиграмму о {word}",
                "Не путай, а выдумай короткую историю с персонажем по имени {word}",
                "Не тяни, а составь диалог между двумя вымышленными персонажами, обсуждающими {word}",
                "Не заморачивайся, а напиши кроссворд с ключевым словом {word}",
                "Не спрашивай, а разверни идею в кратком сценарии, где главный момент связан с {word}",
                "Не гадай, а составь краткое описание загадочного предмета с именем {word}",
                "Не разглагольствуй, а напиши короткую сказку, в которой {word} играет важную роль",
                "Не тягай за ниточки, а создай короткую поэму с {word} в качестве основной темы",
                "Не мешкай, а напиши юмористический монолог на тему {word}",
                "Не затягивай, а придумай короткую пародию на известный текст с участием {word}"
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
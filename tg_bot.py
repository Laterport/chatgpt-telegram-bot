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
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="Sorry, you are not allowed to use this bot. Contact the bot owner for more information.")
            return

        bot_username = context.bot.username.lower()

        # Check if the message is a direct mention to the bot or a private message
        if msg.chat.type == "private" or bot_username in msg.text.lower():
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

            # Process the user's message directly without template
            response = self.__chat_bot.talk(update.effective_chat.id, update.effective_user.id, msg.text)
            await msg.reply_text(response)
            return

        # Check if the message is a reply to the bot
        if msg.reply_to_message and msg.reply_to_message.from_user.id == context.bot.id:
            await context.bot.send_chat_action(chat_id=msg.chat.id, action="typing")

            # Process the user's reply to the bot
            response = self.__chat_bot.talk(msg.chat.id, update.effective_user.id, msg.text)
            logging.info(f'Request: {msg.text}, Response: {response}')
            await msg.reply_text(response)
            return

        # Check for group/supergroup messages
        if update.effective_chat.type in ["group", "supergroup"]:
            with open('DICT.txt', 'r', encoding='utf-8') as file:
                dictionary_words = {line.strip().upper() for line in file.readlines()}

            upper_text = msg.text.upper()

            # Check if any whole word from DICT is present in the message and the word has at least 5 characters
            if (
            detected_word := next((word for word in upper_text.split() if word in dictionary_words and len(word) >= 5),
                                  None)):
                logging.info(f"Bot detected the word: {detected_word}")
                await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

                # Replace mentions using regular expression
                msg_text = re.sub(r'@\w+', '', msg.text)

                # Randomly select a phrase template
                phrase_templates = [
                    "Не задавай лишних вопросов, а придумай пословицу про {word}",
                    "Не задавай лишних вопросов, а придумай поговорку про {word}",
                    "Не задавай лишних вопросов, а придумай народную мудрость про {word}",
                    "Не задавай лишних вопросов, а придумай сплетню про {word}",
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
                await msg.reply_text(openai_response)
                return  # Exit the function to avoid further processing

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
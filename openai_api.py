import requests
import json
import logging
from retry import retry
from usage import UsageStats

class ChatGPT:
    ENDPOINT = "https://neuroapi.host/v1"  # Обновите с вашим адресом сервера
    MODEL_NAME = "gpt-4"
    BEHAVIOUR = {"role": "system", "content": "You are a helpful assistant"}

    def __init__(self, api_key):
        self.api_key = api_key
        self.__usage = UsageStats()
        self.logger = logging.getLogger(__name__)  # Создаем логгер

    @retry(tries=3, delay=3, backoff=1, max_delay=3)
    def get_response(self, user_id, chat_messages, update_usage=True):
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            payload = {
                "model": self.MODEL_NAME,
                "messages": [self.BEHAVIOUR] + chat_messages
            }

            # Обновленная строка URL с /gpt-3.5-turbo/chat/completions
            url = f"{self.ENDPOINT}/chat/completions"

            self.logger.info(f"Sending request to {url} with payload: {payload}")

            response = requests.post(url, headers=headers, data=json.dumps(payload))

            self.logger.info(f"Received response with status code: {response.status_code}, content: {response.content}")

            if response.status_code != 200:
                raise Exception(f"Request failed with status code: {response.status_code}")

            response_data = response.json()
            if update_usage:
                self.__usage.update(user_id, response_data.get("usage", {}).get("total_tokens", 0))
            return response_data["choices"][0]["message"]["content"]
        except Exception as e:
            self.logger.error(f"Error during request: {e}")
            raise e
# Настроим логирование
logging.basicConfig(level=logging.INFO)  # Уровень логирования INFO

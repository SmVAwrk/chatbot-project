
from settings import TOKEN, GROUP_ID

from random import randint

import vk_api

from vk_api import bot_longpoll

import logging

log = logging.getLogger('debug_logger')
log.setLevel(logging.DEBUG)


def log_function():

    file_handler = logging.FileHandler(filename='log/bot_debug.log', mode='a', encoding='utf-8')
    format_for_dbg = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s',
                                       datefmt='%d-%m-%Y %H:%M')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(format_for_dbg)
    log.addHandler(file_handler)

    strm_handler = logging.StreamHandler()
    format_for_info = logging.Formatter(fmt='%(levelname)s - %(message)s')
    strm_handler.setLevel(logging.DEBUG)
    strm_handler.setFormatter(format_for_info)
    log.addHandler(strm_handler)


class ChatBot:

    def __init__(self, group_id, token):
        """
        Создание чат-бота
        :param group_id: ID группы вк
        :param token: индивидуальный токен из группы
        """
        self.group_id = group_id
        self.token = token
        self.vk_api = vk_api.VkApi(token=self.token)
        self.bot_longpoll = vk_api.bot_longpoll.VkBotLongPoll(vk=self.vk_api, group_id=self.group_id)
        self.api = self.vk_api.get_api()

    def run(self):
        """
        Запуск чат-бота
        """
        for event in self.bot_longpoll.listen():
            log.debug("_______Произошло событие_______")
            try:
                self.in_action(event=event)
            except Exception as exc:
                log.exception('Произошла ошибка')

    def in_action(self, event):
        """
        Обработка события
        :param event: событие класса VkBotEvent(VkBotEventType)
        """
        if event.type is vk_api.bot_longpoll.VkBotEventType.MESSAGE_NEW:
            u_id = event.object.message['from_id']
            u_text = event.object.message['text']
            log.info(f"Пришло сообщение: {u_text}")
            self.api.messages.send(random_id=randint(0, 2 ** 20), user_id=u_id, message=f'Ваше сообщение: {u_text}')
        elif event.type is vk_api.bot_longpoll.VkBotEventType.MESSAGE_REPLY:
            log.info('Я ответил на сообщение')
        else:
            log.debug(f'Я не умею обрабатывать событие: {event.type}')


if __name__ == "__main__":
    log_function()
    chat_bot = ChatBot(group_id=GROUP_ID, token=TOKEN)
    chat_bot.run()





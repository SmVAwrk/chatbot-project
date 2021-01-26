#!/usr/bin/env python3

import requests
from pony.orm import db_session

import handlers
from models import UserState, UserRequest
from settings import TOKEN, GROUP_ID, SCENARIOS, INTENTS, DEFAULT_ANSWER
from random import randint
import vk_api
from vk_api import bot_longpoll
import logging

log = logging.getLogger('debug_logger')
log.setLevel(logging.DEBUG)


def log_function():
    """Функция для записи лога"""
    file_handler = logging.FileHandler(filename='log/bot_debug.log', mode='a', encoding='utf-8')
    format_for_file = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s',
                                        datefmt='%d-%m-%Y %H:%M')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(format_for_file)
    log.addHandler(file_handler)
    strm_handler = logging.StreamHandler()
    format_for_stream = logging.Formatter(fmt='%(levelname)s - %(message)s')
    strm_handler.setLevel(logging.DEBUG)
    strm_handler.setFormatter(format_for_stream)
    log.addHandler(strm_handler)


class ChatBot:
    """
    use Python 3.7
    Бот для регистрации на конференцию 'X' в ВК.
    Функционал бота:
    - может рассказать о том, что будет на конференции;
    - может рассказать, когда будет конференция;
    - может рассказать, где будет конференция;
    - может зарегистриовать на конференцию, сгенерировать билет и прислать его пользователю.
    """

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
        Запуск чат-бота.
        Ожидание события.
        """
        for event in self.bot_longpoll.listen():
            # log.debug("___Произошло событие___")
            try:
                self.in_action(event=event)
            except Exception as exc:
                log.exception(f'Произошла ошибка {exc}')

    @db_session
    def in_action(self, event):
        """
        Обработка события.
        :param event: событие класса VkBotEvent(VkBotEventType).
        db_session - Декоратор ORM для автоматических коммитов при работе с БД.
        """
        if event.type != vk_api.bot_longpoll.VkBotEventType.MESSAGE_NEW:
            # log.debug(f'Я не умею обрабатывать событие: {event.type}')
            return
        u_id = str(event.object.message['from_id'])
        u_text = event.object.message['text']
        log.info(f"Пришло сообщение: '{u_text}' от пользователя {u_id}.")

        state = UserState.get(user_id=u_id)

        if state is not None:
            log.debug(f"Продолжается сценарий {state.scenario_name}.")
            self.continue_scenario(text=u_text, state=state, user_id=u_id)
        else:
            for intent in INTENTS:
                log.debug("Поиск намерения...")
                if any(token in u_text.lower() for token in intent['token']):
                    log.debug("Найдено намерение.")
                    if intent['answer']:
                        self.send_text(user_id=u_id, text_to_send=intent['answer'])
                    else:
                        log.info("Начинается сценарий.")
                        self.start_scenario(scenario_name=intent['scenario'], u_id=u_id, text=u_text)
                    break
            else:
                log.info("Намерение не найдено.")
                self.send_text(user_id=u_id, text_to_send=DEFAULT_ANSWER)

    def send_text(self, user_id, text_to_send):
        """
        Отправка текста пользователю.
        :param user_id: ID пользователя для отправки сообщения
        :param text_to_send: текст отправляемого сообщения
        """
        self.api.messages.send(random_id=randint(0, 2 ** 20), user_id=user_id, message=text_to_send)
        log.info(f'Отправлено текстовое сообщение: {text_to_send}.')

    def send_image(self, user_id, image):
        """
        Отправка изображения пользователю.
        :param user_id: ID пользователя для отправки сообщения
        :param image: отправляемое изображение, объект класса BytesIO
        """
        upload_url = self.api.photos.getMessagesUploadServer()['upload_url']
        upload_data = requests.post(url=upload_url, files={'photo': ('image.png', image, 'image/png')}).json()
        image_data = self.api.photos.saveMessagesPhoto(**upload_data)

        owner_id = image_data[0]['owner_id']
        media_id = image_data[0]['id']
        attachment = f'photo{owner_id}_{media_id}'
        self.api.messages.send(random_id=randint(0, 2 ** 20), user_id=user_id, attachment=attachment)
        log.info('Отправлено изображение.')

    def send_step(self, user_id, step, text, context):
        """
        Отправка всех необходимых для данного шага юнитов.
        :param user_id: ID пользователя для отправки сообщения
        :param step: наименование шага
        :param text: текст пользователя
        :param context: словарь с данными, которые ввел пользователь
        """
        if 'text' in step:
            self.send_text(user_id=user_id, text_to_send=step['text'].format(**context))
        if 'image' in step:
            handler = getattr(handlers, step['image'])
            image = handler(text, context)
            self.send_image(user_id=user_id, image=image)

    def start_scenario(self, scenario_name, u_id, text):
        """
        Функция начала сценария
        :param scenario_name: название сценария
        :param u_id: ID пользователя начинающего сценарий
        :param text: текст пользователя
        """
        scenario = SCENARIOS[scenario_name]
        first_step = scenario['first_step']
        step = scenario['steps'][first_step]
        self.send_step(user_id=u_id, step=step, text=text, context={})
        UserState(user_id=u_id, scenario_name=scenario_name, step_name=first_step, context={})

    def continue_scenario(self, text, state, user_id):
        """
        Функция продолжения сценария
        :param text: текст пользователя
        :param state: состояние пользователя, объект класса UserState
        :param user_id: ID пользователя продолжающего сценарий
        """
        scenario_break_tokens = SCENARIOS[state.scenario_name]['scenario_break']['scenario_break_tokens']
        if any(token in text.lower() for token in scenario_break_tokens):
            log.info(f'Пользователь {user_id} прервал сценарий {state.scenario_name}.')
            text_to_send = SCENARIOS[state.scenario_name]['scenario_break']['break_text']
            self.send_text(user_id=user_id, text_to_send=text_to_send)
            state.delete()
            return
        steps = SCENARIOS[state.scenario_name]['steps']
        step = steps[state.step_name]
        handler = getattr(handlers, step['handler'])
        if handler(text=text, context=state.context):
            log.debug('Ответ пользователя прошел.')
            next_step = steps[step['next_step']]
            self.send_step(user_id=user_id, text=text, step=next_step, context=state.context)
            if next_step['next_step']:
                state.step_name = step['next_step']
            else:
                UserRequest(user_id=user_id, **state.context)
                log.info(f'Сценарий {state.scenario_name} закончен.')
                state.delete()
        else:
            log.debug('Ответ пользователя не прошел.')
            text_to_send = step['failure_text'].format(**state.context)
            self.send_text(user_id=user_id, text_to_send=text_to_send)


if __name__ == "__main__":
    log_function()
    chat_bot = ChatBot(group_id=GROUP_ID, token=TOKEN)
    chat_bot.run()





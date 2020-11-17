import json

import handlers
from settings import TOKEN, GROUP_ID, SCENARIOS, INTENTS, DEFAULT_ANSWER
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

# def dialogflow_func(message):
#     request = apiai.ApiAI(client_access_token=)
#     request.lang = 'ru'
#     request.session_id = randint(0, 2 ** 20)
#     request.query = message
#     responsejson = json.loads(request.getresponse().read().decode('utf-8'))


class UserState:
    """
    Cостояние пользователя внутри сценария
    """
    def __init__(self, scenario_name, step_name, context=None):
        self.scenario_name = scenario_name
        self.step_name = step_name
        self.context = context or {}


class ChatBot:
    """
    use Python 3.7
    Бот для регистрации на конференцию 'X' в ВК.
    Фнкционал бота:
    - может рассказать о том, что будет на конференции;
    - может рассказать когда будет конференция;
    - может рассказать где будет конференция;
    - может зарегистриовать на конференцию.
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
        self.user_states = {}

    def run(self):
        """
        Запуск чат-бота.
        Ожидание события.
        """
        for event in self.bot_longpoll.listen():
            log.debug("_______Произошло событие_______")
            try:
                self.in_action(event=event)
            except Exception as exc:
                log.exception(f'Произошла ошибка {exc}')

    def in_action(self, event):
        """
        Обработка события
        :param event: событие класса VkBotEvent(VkBotEventType)
        """
        if event.type != vk_api.bot_longpoll.VkBotEventType.MESSAGE_NEW:
            log.debug(f'Я не умею обрабатывать событие: {event.type}')
            return
        u_id = event.object.message['from_id']
        u_text = event.object.message['text']
        log.info(f"Пришло сообщение: {u_text}")
        if u_id in self.user_states:
            text_to_send = self.continue_scenario(u_id=u_id, text=u_text)
        else:
            for intent in INTENTS:
                if any(token in u_text.lower() for token in intent['token']):
                    if intent['answer']:
                        text_to_send = intent['answer']
                    else:
                        text_to_send = self.start_scenario(scenario_name=intent['scenario'], u_id=u_id)
                    break
            else:
                text_to_send = DEFAULT_ANSWER
        self.api.messages.send(random_id=randint(0, 2 ** 20), user_id=u_id, message=text_to_send)
        log.info('Я ответил на сообщение')

    def start_scenario(self, scenario_name, u_id):
        scenario = SCENARIOS[scenario_name]
        first_step = scenario['first_step']
        step = scenario['steps'][first_step]
        text_to_send = step['text']
        self.user_states[u_id] = UserState(scenario_name=scenario_name, step_name=first_step)
        return text_to_send

    def continue_scenario(self, u_id, text):
        state = self.user_states[u_id]
        steps = SCENARIOS[state.scenario_name]['steps']
        step = steps[state.step_name]
        handler = getattr(handlers, step['handler'])
        if handler(text=text, context=state.context):
            next_step = steps[step['next_step']]
            text_to_send = next_step['text'].format(**state.context)
            if next_step['next_step']:
                state.step_name = step['next_step']
            else:
                self.user_states.pop(u_id)
        else:
            text_to_send = step['failure_text'].format(**state.context)
        return text_to_send


if __name__ == "__main__":
    log_function()
    chat_bot = ChatBot(group_id=GROUP_ID, token=TOKEN)
    chat_bot.run()





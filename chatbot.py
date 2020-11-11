from pprint import pprint
from random import randint

import vk_api

from vk_api import bot_longpoll

from _token import token

group_id = 200224352


class ChatBot:

    def __init__(self, group_id, token):
        self.group_id = group_id
        self.token = token
        self.vk_api = vk_api.VkApi(token=self.token)
        self.bot_longpoll = vk_api.bot_longpoll.VkBotLongPoll(vk=self.vk_api, group_id=self.group_id)
        self.api = self.vk_api.get_api()

    def run(self):
        for event in self.bot_longpoll.listen():
            print(f"_______Произошло событие_______")
            try:
                self.in_action(event=event)
            except Exception as exc:
                print(exc)

    def in_action(self, event):
        if event.type is vk_api.bot_longpoll.VkBotEventType.MESSAGE_NEW:
            u_id = event.object.message['from_id']
            u_text = event.object.message['text']
            print(f"Пришло сообщение: {u_text}")
            self.api.messages.send(random_id=randint(0, 2 ** 20), user_id=u_id, message=f'Ваше сообщение: {u_text}')
        elif event.type is vk_api.bot_longpoll.VkBotEventType.MESSAGE_REPLY:
            print('Я ответил на сообщение')
        else:
            print(f'Я не умею обрабатывать событие: {event.type}')


if __name__ == "__main__":
    chat_bot = ChatBot(group_id=group_id, token=token)
    chat_bot.run()




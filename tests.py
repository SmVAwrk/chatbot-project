import unittest
from copy import deepcopy
from unittest.mock import patch, Mock

from pony.orm import rollback, db_session
from vk_api import bot_longpoll
import settings
from chatbot import ChatBot
from imagemaker import make_image


def isolate_db(func):

    def wrapper(*args, **kwargs):
        with db_session as session:
            func(*args, **kwargs)
            rollback()
    return wrapper


class ChatBotTest(unittest.TestCase):
    RAW_EVENT = {
        'type': 'message_new',
        'object': {
            'message': {
                'date': 1605360790, 'from_id': 123456789, 'id': 119, 'out': 0, 'peer_id': 123456789,
                'text': '', 'conversation_message_id': 117, 'fwd_messages': [], 'important': False,
                'random_id': 0, 'attachments': [], 'is_hidden': False},
            'client_info': {
                'button_actions': ['text', 'vkpay', 'open_app', 'location', 'open_link'],
                'keyboard': True, 'inline_keyboard': True, 'carousel': False, 'lang_id': 0}},
        'group_id': 200224352, 'event_id': 'b1a73afcbf05f1c28a8c3d7dca7c04cb6eb55848'}
    TEST_PHRASES = [
        'Ты не поймешь эту фразу',
        'Привет',
        'Что за конференция?',
        'Когда?',
        'Где?',
        'Зарегистрируй меня',
        'киборг12',
        'Тест',
        'fail@fail',
        'test@test.com',
        'Спасибо',
        'Зарегай',
        'Не хочу'
    ]
    EXPECTED_ANSWERS = [
        settings.DEFAULT_ANSWER,
        settings.INTENTS[2]['answer'],
        settings.INTENTS[5]['answer'],
        settings.INTENTS[0]['answer'],
        settings.INTENTS[1]['answer'],
        settings.SCENARIOS['registration']['steps']['step1']['text'],
        settings.SCENARIOS['registration']['steps']['step1']['failure_text'],
        settings.SCENARIOS['registration']['steps']['step2']['text'],
        settings.SCENARIOS['registration']['steps']['step2']['failure_text'],
        settings.SCENARIOS['registration']['steps']['step3']['text'].format(name='Тест', email='test@test.com'),
        settings.INTENTS[4]['answer'],
        settings.SCENARIOS['registration']['steps']['step1']['text'],
        settings.SCENARIOS['registration']['scenario_break']['break_text']
    ]

    def test_run(self):
        count = 5
        obj = {'1': 1}
        event = [obj] * count
        bot_longpoll_mock = Mock()
        bot_longpoll_mock.listen = Mock(return_value=event)
        with patch('chatbot.vk_api.VkApi'):
            with patch('chatbot.vk_api.bot_longpoll.VkBotLongPoll', return_value=bot_longpoll_mock):
                chatbot = ChatBot('a', 'b')
                chatbot.in_action = Mock()
                chatbot.run()
                chatbot.in_action.assert_called()
                self.assertEqual(chatbot.in_action.call_count, count)
                chatbot.in_action.assert_any_call(event=obj)

    @isolate_db
    def test_run_adv(self):
        send_mock = Mock()
        api_mock = Mock()
        api_mock.messages.send = send_mock
        events = []
        for test_phrase in self.TEST_PHRASES:
            event = deepcopy(self.RAW_EVENT)
            event['object']['message']['text'] = test_phrase
            events.append(bot_longpoll.VkBotMessageEvent(event))

        bot_longpoll_mock = Mock()
        bot_longpoll_mock.listen = Mock(return_value=events)
        with patch('chatbot.vk_api.bot_longpoll.VkBotLongPoll', return_value=bot_longpoll_mock):
            chatbot = ChatBot('a', 'b')
            chatbot.api = api_mock
            chatbot.send_image = Mock()
            chatbot.run()
        assert send_mock.call_count == len(self.TEST_PHRASES)

        real_answers = []
        for call in send_mock.call_args_list:
            args, kwargs = call
            real_answers.append(kwargs['message'])
        assert real_answers == self.EXPECTED_ANSWERS

    def test_make_image(self):
        with open('files/avatar_test.png', 'rb') as expected_avatar:
            avatar_mock = Mock()
            avatar_mock.content = expected_avatar.read()

        with patch('requests.get', return_value=avatar_mock):
            real_img = make_image('Тест', 'test@test.com')

        with open('files/ticket_test.png', 'rb') as expected_img:
            expected_bytes = expected_img.read()

        assert real_img.read() == expected_bytes


if __name__ == '__main__':
    unittest.main()

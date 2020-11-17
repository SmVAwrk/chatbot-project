import unittest
from random import randint
from unittest.mock import patch, Mock, ANY

from vk_api import bot_longpoll

from chatbot import ChatBot


class ChatBotTest(unittest.TestCase):
    RAW_EVENT_1 = {
        'type': 'message_typing_state',
        'object': {'state': 'typing', 'from_id': 2933937, 'to_id': -200224352},
        'group_id': 200224352, 'event_id': '9ecd131f552a41eba27f3eede9c52ce2b94e2341'}
    RAW_EVENT_2 = {
        'type': 'message_new',
        'object': {
            'message': {
                'date': 1605360790, 'from_id': 2933937, 'id': 119, 'out': 0, 'peer_id': 2933937,
                'text': 'sad', 'conversation_message_id': 117, 'fwd_messages': [], 'important': False,
                'random_id': 0, 'attachments': [], 'is_hidden': False},
            'client_info': {
                'button_actions': ['text', 'vkpay', 'open_app', 'location', 'open_link'],
                'keyboard': True, 'inline_keyboard': True, 'carousel': False, 'lang_id': 0}},
        'group_id': 200224352, 'event_id': 'b1a73afcbf05f1c28a8c3d7dca7c04cb6eb55848'}

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

    def test_in_action(self):
        event = bot_longpoll.VkBotEvent(raw=self.RAW_EVENT_2)
        with patch('chatbot.vk_api.VkApi'):
            with patch('chatbot.vk_api.bot_longpoll.VkBotLongPoll'):
                chatbot = ChatBot('a', 'b')
                chatbot.api = Mock()
                chatbot.api.messages.send = Mock()
                chatbot.in_action(event=event)
        chatbot.api.messages.send.assert_called_once_with(
            random_id=ANY,
            user_id=self.RAW_EVENT_2["object"]['message']['from_id'],
            message=f'Ваше сообщение: {self.RAW_EVENT_2["object"]["message"]["text"]}')


if __name__ == '__main__':
    unittest.main()


"""
Handler -  для обработки текста пользователя. Принимает text и context ({}), а возвращает bool
"""

import re

name_pattern = r'^[а-яА-Я]{2,15}$'
email_pattern = r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b'


def handle_name(text, context):
    match = re.match(name_pattern, text)
    if match:
        context['name'] = text.capitalize()
        return True
    else:
        return False


def handle_email(text, context):
    matches = re.findall(email_pattern, text)
    if len(matches) > 0:
        context['email'] = matches[0]
        return True
    else:
        return False

from io import BytesIO

import requests
from PIL import Image, ImageFont, ImageDraw

TEMPLATE_PATH = 'files/ticket_template.jpg'
FONT_PATH = 'files/Roboto-Regular.ttf'
FONT_SIZE = 30
BLACK_COLOR = (0, 0, 0)
NAME_OFFSET = (215, 183)
EMAIL_OFFSET = (215, 238)
AVATAR_X_SIZE = 100
AVATAR_Y_SIZE = 100
AVATAR_OFFSET = (472, 178)


def make_image(name, email):
    """
    Функция создания билета с данными пользователя.
    :param name: имя пользователя
    :param email: e-mail пользователя
    :return: объект класса BytesIO
    """
    ticket_template = Image.open(TEMPLATE_PATH)
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    write_ticket = ImageDraw.Draw(ticket_template)
    write_ticket.text(NAME_OFFSET, f"{name}", font=font, fill=BLACK_COLOR)
    write_ticket.text(EMAIL_OFFSET, f"{email}", font=font, fill=BLACK_COLOR)

    response = requests.get(url=f'https://robohash.org/{email}?size={AVATAR_X_SIZE}x{AVATAR_Y_SIZE}')
    avatar_file_like = BytesIO(response.content)
    avatar = Image.open(avatar_file_like)

    ticket_template.paste(avatar, AVATAR_OFFSET)

    temp_file = BytesIO()
    ticket_template.save(temp_file, 'png')
    temp_file.seek(0)

    return temp_file

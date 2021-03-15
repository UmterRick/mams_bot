import logging
import time
import asyncio
import calendar
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import executor, Dispatcher, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Update
from datetime import datetime, timedelta

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:85.0) Gecko/20100101 Firefox/85.0'}
URL = 'https://meandmyschool.org.ua/ru/'
TOKEN = '1485443475:AAEv-Xl15Xp9Z6sSFyH4tizumu4oeJ3ZtdY'
C_URL = 'https://meandmyschool.org.ua/detalnishe-pro-prohramy/'

DB_NAME = 'test1'
ADMIN_PASSWORD = '1111'
TRAINER_PASSWORD = '2222'

USER_TYPE = None
CHAT_ID = 0
msgID = None
DELAY = 100

weekdays = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС']
eng_weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

daytimes = []
coursesId = []
list_of_coursesID = []

start_text = 'Привіт! 👋\nЯ бот🤖, який допоможе тобі обрати собі курс у нашому освітньому центрі \n \
        ЯІМОЯШКОЛА🎓\nОбреріть хто ви?👇🏻'


admin_groups_start = "Вітаю, я Бот <i>ЯІМОЯШКОЛА</i>\n " \
                     "Ви додали мене до чату адміністраторів.\n" \
                     "Тут ви зможете отримувати нові заявки до груп\n\n"\
                     "Для доступу до функцій треба <b>ввести пароль</b> адміністраторів!"


def str_to_list(input_str):
    res = []
    if input_str == '[]':
        res = []
    else:
        for i in input_str[1:-1].split(','):
            i = int(i.strip())
            res.append(i)
    return res


def range_to_str_list(my_range_end):
    res = []
    for el in range(my_range_end):
        res.append(str(el))
    return res


def create_callback_data(*args):
    res_data = []
    for arg in args:
        res_data.append(str(arg))
    print(str(res_data))
    return str(res_data)


def test(arg1, arg2):
    return ";".join([arg1, arg2])

a = test('1','2')
print('a =', a)
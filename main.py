import asyncio
import os
import time

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

from dotenv import load_dotenv

import tasks
from users import UserState


load_dotenv()

bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher(bot)


HELP_MSG = '''
/new - Создать новую задачу
/tasks - Просмотреть список текущих задач
/closed_tasks - Посмотреть список закрытых задач
/close - Закрыть задачу из списка текущих
/help - Вывести это сообщение
'''


user_states = {}


@dp.message_handler(commands=['help'])
async def process_help_comand(msg: types.Message):
    await bot.send_message(msg.from_user.id, HELP_MSG)


@dp.message_handler(commands=['start'])
async def process_start_command(msg: types.Message):
    await bot.send_message(msg.from_user.id, 'Привет! Я TODO-бот', reply_markup=types.ReplyKeyboardRemove())
    await process_help_comand(msg)


@dp.message_handler()
async def process_text_message(msg: types.Message):
    user = msg.from_user.id
    
    if user not in user_states:
        user_states[user] = UserState(user, msg.text)
    user_states[user].process_state(msg.text)
    reply_msg = user_states[user].reply_text
    if reply_msg != '':
        await bot.send_message(msg.from_user.id, reply_msg)

    if user_states[user].is_terminated:
        del user_states[user]


async def send_actual_reminds():
    for row in tasks.get_actual_reminds():
        user = row['user_id']
        msg = row['title']
        msg += ('\n\n' + row['description']) if row['description'] else ''
        await bot.send_message(user, msg)


async def scheduled_events():
    t = time.strftime('%H:%M')
    while True:
        await asyncio.sleep(1)
        if t != time.strftime('%H:%M'):
            t = time.strftime('%H:%M')
            await send_actual_reminds()

    
if __name__ == '__main__':
    tasks.ensure_db_exists()
    loop = asyncio.get_event_loop()
    loop.create_task(scheduled_events())
    executor.start_polling(dp)
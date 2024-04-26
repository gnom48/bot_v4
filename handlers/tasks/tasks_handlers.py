from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from bot import *
from keybords import *
from models import *
from ..main_handlers import *
from datetime import timedelta
from datetime import datetime as dt
import re
import random
import asyncio


# ввод названия задачи
@dp.message_handler(state=WorkStates.task_name)
async def enter_task_name(msg: types.Message, state: FSMContext):
    Rielter.update(last_action=dumps((int(dt.now().timestamp()), True))).where(Rielter.rielter_id == msg.from_user.id).execute()
    async with state.proxy() as data:
        data["task_name"] = msg.text
    await msg.answer("Теперь напиши дату (в формате ДД-ММ-ГГГГ), когда тебе нужно об этом напомнить:")
    await WorkStates.task_date.set()


# ввод даты задачи
@dp.message_handler(state=WorkStates.task_date)
async def enter_task_date(msg: types.Message, state: FSMContext):
    Rielter.update(last_action=dumps((int(dt.now().timestamp()), True))).where(Rielter.rielter_id == msg.from_user.id).execute()
    if re.match(r'\d{2}\-\d{2}\-\d{4}', msg.text):
        date_obj = dt.strptime(msg.text, '%d-%m-%Y')
        if date_obj.date() < dt.now().date():
            await msg.answer("Напоминания можно задавать только на будущее, попробуй еще раз!", reply_markup=types.ReplyKeyboardRemove())
            return
        if dt.now().date().year - date_obj.date().year > 1:
            await msg.answer("Не стоит загадывать на такой большой срок, лучше сосредоточься на настоящем! Попробуй ввести дату еще раз!", reply_markup=types.ReplyKeyboardRemove())
            return
        async with state.proxy() as data:
            data["date_planed"] = msg.text
        await msg.answer("Теперь введи время в формате ЧЧ:ММ")
        await WorkStates.task_time.set()
    else:
        await msg.answer("Возможно что-то с форматом даты, попробуй еще раз", reply_markup=types.ReplyKeyboardRemove())
        await WorkStates.task_date.set()
        
        
# ввод времени задачи
@dp.message_handler(state=WorkStates.task_time)
async def enter_task_date(msg: types.Message, state: FSMContext):
    Rielter.update(last_action=dumps((int(dt.now().timestamp()), True))).where(Rielter.rielter_id == msg.from_user.id).execute()
    if re.match(r'\d{2}\:\d{2}', msg.text):
        time_obj: dt
        try:
            time_obj = dt.strptime(msg.text, '%H:%M').time()
        except:
            await msg.answer("Возможно что-то с форматом времени, попробуй еще раз", reply_markup=types.ReplyKeyboardRemove())
            await WorkStates.task_time.set()
            return
        async with state.proxy() as data:
            if dt.strptime(data["date_planed"], '%d-%m-%Y').date() == dt.now().date():
                dt_tmp = dt(year=dt.now().year, month=dt.now().month, day=dt.now().day, hour=time_obj.hour, minute=time_obj.minute, second=0)
                if (dt_tmp - dt.now()).seconds < 3500:
                    await msg.answer("Боюсь что я не могу поставить напоминание ранее, ранее чем через час! Попробуй еще раз")
                    return
                schedule_job(msg.from_user.id, bot, f"Напоминаю, что ты запланировал в {msg.text} заняться: {data['task_name']}", None, None, dt_tmp - timedelta(hours=3, minutes=30), " + 1 напоминание")
                await msg.answer("Принято! Я обязательно напомню тебе сегодня (за полчаса до)")
                await msg.answer(generate_main_menu_text(), reply_markup=get_inline_menu_markup())
                await WorkStates.ready.set()
                return
            Task.create(rielter_id=msg.from_user.id,
                task_name=data["task_name"],
                date_planed=data["date_planed"],
                time_planed=msg.text).save()
        await msg.answer("Принято! Я обязательно напомню тебе, когда придет время (за полчаса до)")
        await msg.answer(generate_main_menu_text(), reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()
    else:
        await msg.answer("Возможно что-то с форматом времени, попробуй еще раз", reply_markup=types.ReplyKeyboardRemove())
        await WorkStates.task_time.set()
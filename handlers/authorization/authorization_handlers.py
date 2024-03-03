from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from bot import *
from keybords import *
from ..main_handlers import *
from models import *
from apscheduler.triggers.cron import CronTrigger
from datetime import timedelta
from datetime import datetime as dt
import re
import random
import asyncio


# подтверждение начала регистрации
@dp.callback_query_handler(lambda callback: callback.data == "Старт регистрации", state=WorkStates.restart)
async def send_welcome(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("✓")
    async with state.proxy() as data:
        data["rielter_id"] = callback.from_user.id
    await bot.send_message(chat_id=callback.from_user.id, text="Введи ФИО:")
    await WorkStates.reg_enter_login.set()


# ввод ФИО
@dp.message_handler(state=WorkStates.reg_enter_login)
async def enter_fio(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now(), True)
    async with state.proxy() as data:
        data["fio"] = msg.text
    await msg.answer("Теперь введи дату рождения (в формате ДД-ММ-ГГГГ):")
    await WorkStates.reg_enter_brthday.set()


# ввод даты рождения
@dp.message_handler(state=WorkStates.reg_enter_brthday)
async def enter_brth(msg: types.Message, state: FSMContext):
    if re.match(r'\d{2}\-\d{2}\-\d{4}', msg.text):
        date_obj = dt.strptime(msg.text, '%d-%m-%Y')
        if date_obj > dt.now():
            await msg.answer("О, ты из будущего, попробуй ввести еще раз!", reply_markup=types.ReplyKeyboardRemove())
            return
        if dt.now().date().year - date_obj.date().year < 16:
            await msg.answer("Слишком юный возраст, попробуй ввести еще раз!", reply_markup=types.ReplyKeyboardRemove())
            return
        async with state.proxy() as data:
            data["birthday"] = msg.text
    else:
        await msg.answer("Возможно что-то с форматом даты, попробуй еще раз!", reply_markup=types.ReplyKeyboardRemove())
        return
    await msg.answer("Теперь укажи пол:", reply_markup=get_gender_kb())
    await WorkStates.reg_enter_gender.set()


# выбор пола
@dp.callback_query_handler(state=WorkStates.reg_enter_gender)
async def process_callback_gender(callback: types.CallbackQuery, state: FSMContext):
    if not (callback.data == "М" or callback.data == "Ж"):
        await bot.send_message(callback.from_user.id, "Ошибка, попробуй снова!")
        return
    await callback.answer("✓")
    async with state.proxy() as data:
        data["gender"] = callback.data
    await bot.send_message(callback.from_user.id, "Теперь выбери, направления вашей деятельности:", reply_markup=get_realtors_type_kb())
    await WorkStates.reg_enter_type.set()


# выбор направления работы и подведение итога регистрации
@dp.callback_query_handler(state=WorkStates.reg_enter_type)
async def process_callback_gender(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "residential":
        async with state.proxy() as data:
            data["rielter_type"] = 0
    elif callback.data == "commercial":
        async with state.proxy() as data:
            data["rielter_type"] = 1
    else:
        await bot.send_message(callback.from_user.id, "Ошибка, попробуй снова!")
        return
    await callback.answer("✓")
    async with state.proxy() as data:
        profile_tmp = Rielter.get_or_none(Rielter.rielter_id == callback.from_user.id)
        if profile_tmp != None:
            profile_tmp = Rielter.update(rielter_id=data["rielter_id"],
                                         fio=data["fio"],
                                         birthday=data["birthday"],
                                         gender=data["gender"],
                                         rielter_type=data["rielter_type"]).where(Rielter.rielter_id == data["rielter_id"]).execute()
        else:
            Rielter.create(rielter_id=data["rielter_id"],
                           fio=data["fio"],
                           birthday=data["birthday"],
                           gender=data["gender"],
                           rielter_type=data["rielter_type"]).save()
            Report.create(rielter_id=callback.from_user.id).save()
            WeekReport.create(rielter_id=callback.from_user.id).save()
            MonthReport.create(rielter_id=callback.from_user.id).save()

        profile = Rielter.get(Rielter.rielter_id == callback.from_user.id)

        await bot.send_message(callback.from_user.id, f"Профиль сформирован!\n\nID: {profile.rielter_id},\nФИО: {profile.fio},\nДата рождения: {profile.birthday},\nПол: {profile.gender},\nНаправление работы: {Rielter_type.get_by_id(pk=profile.rielter_type).rielter_type_name}")
        await bot.send_message(callback.from_user.id, generate_main_menu_text(), reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()

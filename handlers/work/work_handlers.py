from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from bot import *
from ..main_handlers import *
from keybords import *
from models import *
from apscheduler.triggers.cron import CronTrigger
from datetime import timedelta
from datetime import datetime as dt
import re
import random
import asyncio


# количество расклеенных листовок
@dp.message_handler(lambda msg: msg.text, state=WorkStates.enter_flyer_count)
async def enter_posting_adverts_count(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now(), True)
    count: int = 0
    try:
        count = int(msg.text)
        if count < 0:
            raise Exception()
    except Exception:
        await msg.reply("Ошибка, попробуй ввести еще раз!", reply_markup=types.ReplyKeyboardRemove())
        return
    await msg.answer("Расклейка объявлений играет важную роль в привлечении новых клиентов! Чем больше расклеишь, тем больше людей о нас узнают!", reply_markup=types.ReplyKeyboardRemove())
    tmp = Report.get_or_none(Report.rielter_id == msg.from_user.id)
    if tmp:
        count += tmp.posting_adverts
        Report.update(posting_adverts=count).where(Report.rielter_id == msg.from_user.id).execute()
    await msg.answer(generate_main_menu_text(), reply_markup=get_inline_menu_markup())
    await WorkStates.ready.set()


# количество звонков
@dp.message_handler(lambda msg: msg.text, state=WorkStates.enter_calls_count)
async def enter_posting_adverts_count(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now(), True)
    count: int = 0
    try:
        count = int(msg.text)
        if count < 0:
            raise Exception()
    except Exception:
        await msg.reply("Ошибка, попробуй ввести еще раз!", reply_markup=types.ReplyKeyboardRemove())
        return
    await msg.answer("Если клиенты не идут к нам, мы будем звонить им и звать сами!", reply_markup=types.ReplyKeyboardRemove())
    tmp = Report.get_or_none(Report.rielter_id == msg.from_user.id)
    if tmp:
        count += tmp.cold_call_count
        Report.update(cold_call_count=count).where(Report.rielter_id == msg.from_user.id).execute()
    await msg.answer(generate_main_menu_text(), reply_markup=get_inline_menu_markup())
    await WorkStates.ready.set()


# вид сделки
@dp.message_handler(lambda msg: msg.text in ["Квартира", "Земля", "Дом", "Офис", "Магазин", "Другое", "Назад"], state=WorkStates.deal_enter_deal_type)
async def enter_deal_type(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now(), True)
    if msg.text == "Назад":
        await msg.answer(text="Отмена!", reply_markup=types.ReplyKeyboardRemove())
        await msg.answer(text=generate_main_menu_text(), reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()
        return

    await WorkStates.ready.set()
    await msg.answer(text=f"Отлично! Вернусь через 2 часа и спрошу как у тебя дела!", reply_markup=types.ReplyKeyboardRemove())
    schedule_job(msg.from_user.id, bot, f"Как прошла сделка в категории: #{msg.text} ?", WorkStates.deal_retult, get_good_bed_result_markup(), dt.now() + SHIFT_TIMEDELTA, "Сделка")


# результат сделки
@dp.message_handler(lambda msg: msg.text in ["Хорошо", "Плохо"], state=WorkStates.deal_retult)
async def enter_deal_result(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now(), True)
    if msg.text == "Хорошо":
        tmp = Report.get_or_none(Report.rielter_id == msg.from_user.id)
        count = 0
        if tmp:
            count += tmp.deals_count
            Report.update(deals_count=count+1).where(Report.rielter_id == msg.from_user.id).execute()
        await msg.answer(generate_deal_related_compliment())
        await msg.answer(generate_main_menu_text(), reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()
    elif msg.text == "Плохо":
        await msg.answer(generate_bad_meeting_or_deal(), reply_markup=types.ReplyKeyboardRemove())
        await msg.answer(text="Давай разберемся, что могло пойти не так!", reply_markup=types.ReplyKeyboardRemove())
        await msg.answer(text="Выбери проблему:", reply_markup=get_bed_result(from_state=WorkStates.deal_retult))
        await WorkStates.deal_why_bad_result.set()
    

# результат аналитики и поиска
@dp.message_handler(lambda msg: msg.text in ["Хорошо", "Плохо"], state=WorkStates.analytics_result)
async def enter_analytics_result(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now(), True)
    if msg.text == "Хорошо":
        await msg.answer(f"Умение анализировать рынок и находить хорошие объекты - важные навыки для риелтора! Продолжай в том же духе!", reply_markup=types.ReplyKeyboardRemove())
        await msg.answer(f"{generate_main_menu_text()}", reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()

    elif msg.text == "Плохо":
        await msg.answer(generate_bad_meeting_or_deal(), reply_markup=types.ReplyKeyboardRemove())
        await msg.answer(text="Выбери проблему:", reply_markup=get_bed_result(from_state=WorkStates.analytics_result))
        await WorkStates.deal_why_bad_result.set()
        

# результат показа
@dp.message_handler(lambda msg: msg.text in ["Хорошо", "Плохо"], state=WorkStates.show_result)
async def enter_deal_result(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now(), True)
    if msg.text == "Хорошо":
        await msg.answer(text="В итоге вы подписали договор?", reply_markup=get_is_signed_markup())
        await WorkStates.is_signed.set()
    elif msg.text == "Плохо":
        await bot.send_message(chat_id=msg.from_user.id, text=generate_bad_meeting_or_deal(), reply_markup=types.ReplyKeyboardRemove())
        await bot.send_message(chat_id=msg.from_user.id, text="Выбери проблему:", reply_markup=get_bed_result(from_state=WorkStates.show_result))
        await WorkStates.deal_why_bad_result.set()
        

# результат задатка
@dp.message_handler(lambda msg: msg.text in ["Хорошо", "Плохо"], state=WorkStates.deposit_result)
async def enter_deal_result(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now(), True)
    if msg.text == "Хорошо":
        tmp = Report.get_or_none(Report.rielter_id == msg.from_user.id)
        count_deposits = 0
        count_contrects_signed = 0
        if tmp:
            count_deposits += tmp.take_deposit_count
            count_contrects_signed += tmp.contrects_signed
            Report.update(take_deposit_count=count_deposits+1, contrects_signed=count_contrects_signed+1).where(Report.rielter_id == msg.from_user.id).execute()
        await msg.answer(generate_deposit_compliment(), reply_markup=types.ReplyKeyboardRemove())
        await msg.answer(generate_main_menu_text(), reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()
    elif msg.text == "Плохо":
        await msg.answer(generate_bad_meeting_or_deal(), reply_markup=types.ReplyKeyboardRemove())
        await msg.answer(text="Что пошло не так?", reply_markup=get_bed_result(from_state=WorkStates.deposit_result))
        await WorkStates.deal_why_bad_result.set()
        

# результат встречи 
@dp.message_handler(lambda msg: msg.text in ["Хорошо", "Плохо"], state=WorkStates.meet_new_object_result)
async def enter_deal_result(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now(), True)
    if msg.text == "Хорошо":
        await msg.answer(text="В итоге вы подписали договор?", reply_markup=get_is_signed_markup())
        await WorkStates.is_signed.set()
    elif msg.text == "Плохо":
        await msg.answer(generate_bad_meeting_or_deal(), reply_markup=types.ReplyKeyboardRemove())
        await msg.answer(text="Выбери проблему:", reply_markup=get_bed_result(from_state=WorkStates.meet_new_object_result))
        await WorkStates.deal_why_bad_result.set()


# подписан ли договор
@dp.callback_query_handler(state=WorkStates.is_signed)
async def is_contract_signed(callback: types.Message, state: FSMContext):
    last_messages[callback.from_user.id] = (dt.now(), True)
    await callback.answer("✓")
    if callback.data == "signed":
        tmp = Report.get_or_none(Report.rielter_id == callback.from_user.id)
        count_shows = 0
        count_contrects_signed = 0
        if tmp:
            count_shows += tmp.show_objects
            count_contrects_signed += tmp.contrects_signed
            Report.update(show_objects=count_shows+1, contrects_signed=count_contrects_signed+1).where(Report.rielter_id == callback.from_user.id).execute()
        await bot.send_message(chat_id=callback.from_user.id, text="Это потрясающий успех, я в тебя всегда верил!", reply_markup=types.ReplyKeyboardRemove())
        await bot.send_message(chat_id=callback.from_user.id, text=generate_main_menu_text(), reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()

    elif callback.data == "unsigned":
        await bot.send_message(chat_id=callback.from_user.id, text="Значит в следующий раз точно подпишите!" , reply_markup=types.ReplyKeyboardRemove())
        await bot.send_message(chat_id=callback.from_user.id, text="А пока советую посмотреть материалы по этой теме, чтобы в следующий раз быть готовым на 100%", reply_markup=get_types_contracts_markup())
        schedule_job(callback.from_user.id, bot, "Изучил материал? Все понял, или нужно что-то еще?", WorkStates.is_all_materials_ok, get_is_all_materials_ok_markup(), dt.now() + SHIFT_SHORT_TIMEDELTA, "Изучение теоретических материалов")

    elif callback.data == "later":
        last_messages[callback.from_user.id] = (dt.now(), True)
        await bot.send_message(chat_id=callback.from_user.id, text = "Ладно, клиенту необходимо хорошенько подумать, давай запишем тебе напоминание!", reply_markup=types.ReplyKeyboardRemove())
        await bot.send_message(chat_id=callback.from_user.id, text = "Напиши краткое название задачи:")
        await WorkStates.task_name.set()
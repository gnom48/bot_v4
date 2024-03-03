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


# выбор раздела в базе знаний - корень
@dp.callback_query_handler(state=WorkStates.knowledge_base_root)
async def choose_what_bad(callback: types.CallbackQuery, state: FSMContext):
    last_messages[callback.from_user.id] = (dt.now(), True)
    await callback.answer("✓")

    if callback.data == "analytics" or callback.data == "shows" or callback.data == "commercial":
        kb = types.InlineKeyboardMarkup(row_width=1)
        vb = types.InlineKeyboardButton(text='Смотреть материал', url=why_bad_str_list[callback.data])
        kb.add(vb)
        await bot.send_message(callback.from_user.id, f"Вот ссылка на теоретическую информацию по твоей теме:", reply_markup=kb)
        await WorkStates.ready.set()
        schedule_job(callback.from_user.id, bot, "Изучил материал? Все понял, или нужно что-то еще?", WorkStates.is_all_materials_ok, get_is_all_materials_ok_markup(), dt.now() + SHIFT_SHORT_TIMEDELTA, "Изучение теоретических материалов")

    elif callback.data == "calls":
        kb = types.InlineKeyboardMarkup(row_width=1)
        vb1 = types.InlineKeyboardButton(text='Смотреть видео', url=why_bad_str_list[callback.data+"_video"])
        vb2 = types.InlineKeyboardButton(text='Читать матриалы', url=why_bad_str_list[callback.data])
        kb.add(vb1)
        kb.add(vb2)
        await bot.send_message(callback.from_user.id, f"Вот ссылки на теоретическую информацию по твоей теме:", reply_markup=kb)
        await WorkStates.ready.set()
        schedule_job(callback.from_user.id, bot, "Изучил материал? Все понял, или нужно что-то еще?", WorkStates.is_all_materials_ok, get_is_all_materials_ok_markup(), dt.now() + SHIFT_SHORT_TIMEDELTA, "Изучение теоретических материалов")

    elif callback.data == "bad_clients":
        await bot.send_message(chat_id=callback.from_user.id, text=f"Давай посмотрим, что я могу предложить тебе изучить, чтобы набраться теоретических знаний...", reply_markup=types.ReplyKeyboardRemove())
        await bot.send_message(chat_id=callback.from_user.id, text="Выбери какyю тему ты бы хотел просмотреть:", reply_markup=get_knowledge_base_bad_clients_markup())
        await WorkStates.knowledge_base_bad_clients.set()

    elif callback.data == "meets":
        await bot.send_message(chat_id=callback.from_user.id, text=f"Давай посмотрим, что я могу предложить тебе изучить, чтобы набраться теоретических знаний...", reply_markup=types.ReplyKeyboardRemove())
        await bot.send_message(chat_id=callback.from_user.id, text="Выбери какyю тему ты бы хотел просмотреть:", reply_markup=get_knowledge_base_bad_meets_markup())
        await WorkStates.knowledge_base_bad_meets.set()
    
    elif callback.data == "deals":
        await bot.send_message(chat_id=callback.from_user.id, text=f"Давай посмотрим, что я могу предложить тебе изучить, чтобы набраться теоретических знаний...", reply_markup=types.ReplyKeyboardRemove())
        await bot.send_message(chat_id=callback.from_user.id, text="Выбери какyю тему ты бы хотел просмотреть:", reply_markup=get_knowledge_base_deals_markup())
        await WorkStates.knowledge_base_base_deals.set()
        
        
# выбор раздела в базе знаний - раздел с возражениями клиентов
@dp.callback_query_handler(state=WorkStates.knowledge_base_bad_clients)
async def choose_what_bad_clients(callback: types.CallbackQuery, state: FSMContext):
    last_messages[callback.from_user.id] = (dt.now(), True)
    await callback.answer("✓")

    if callback.data in ["context", "general", "bad_calls", "anti_bad", "bad_meets"]:
        kb = types.InlineKeyboardMarkup(row_width=1)
        vb = types.InlineKeyboardButton(text='Смотреть материал', url=why_bad_str_list[callback.data])
        kb.add(vb)
        await bot.send_message(callback.from_user.id, f"Вот ссылка на теоретическую информацию по твоей теме:", reply_markup=kb)
        await WorkStates.ready.set()
        schedule_job(callback.from_user.id, bot, "Изучил материал? Все понял, или нужно что-то еще?", WorkStates.is_all_materials_ok, get_is_all_materials_ok_markup(), dt.now() + SHIFT_SHORT_TIMEDELTA, "Изучение теоретических материалов")
            
            
# выбор раздела в базе знаний - раздел с договорами
@dp.callback_query_handler(state=WorkStates.knowledge_base_base_deals)
async def choose_what_deals(callback: types.CallbackQuery, state: FSMContext):
    last_messages[callback.from_user.id] = (dt.now(), True)
    await callback.answer("✓")

    if callback.data in ["exclusive", "serching", "auction"]:
        kb = types.InlineKeyboardMarkup(row_width=1)
        vb = types.InlineKeyboardButton(text='Смотреть материал', url=why_bad_str_list[callback.data])
        kb.add(vb)
        await bot.send_message(callback.from_user.id, f"Вот ссылка на теоретическую информацию по твоей теме:", reply_markup=kb)
        await WorkStates.ready.set()
        schedule_job(callback.from_user.id, bot, "Изучил материал? Все понял, или нужно что-то еще?", WorkStates.is_all_materials_ok, get_is_all_materials_ok_markup(), dt.now() + SHIFT_SHORT_TIMEDELTA, "Изучение теоретических материалов")


# выбор раздела в базе знаний - раздел с встречами
@dp.callback_query_handler(state=WorkStates.knowledge_base_bad_meets)
async def choose_what_meets(callback: types.CallbackQuery, state: FSMContext):
    last_messages[callback.from_user.id] = (dt.now(), True)
    await callback.answer("✓")

    if callback.data in ["small-talk", "spin", "3yes"]:
        kb = types.InlineKeyboardMarkup(row_width=1)
        vb = types.InlineKeyboardButton(text='Смотреть материал', url=why_bad_str_list[callback.data])
        kb.add(vb)
        await bot.send_message(callback.from_user.id, f"Вот ссылка на теоретическую информацию по твоей теме:", reply_markup=kb)
        await WorkStates.ready.set()
        schedule_job(callback.from_user.id, bot, "Изучил материал? Все понял, или нужно что-то еще?", WorkStates.is_all_materials_ok, get_is_all_materials_ok_markup(), dt.now() + SHIFT_SHORT_TIMEDELTA, "Изучение теоретических материалов")

    elif callback.data == "all_able":
        await bot.send_message(chat_id=callback.from_user.id, text="Выбери далее:", reply_markup=get_knowledge_base_all_able_markup())
        await WorkStates.knowledge_base_all_able.set()
        
        
# выбор раздела в базе знаний - подраздел все можно продать
@dp.callback_query_handler(state=WorkStates.knowledge_base_all_able)
async def choose_what_all_able_to_sale(callback: types.CallbackQuery, state: FSMContext):
    last_messages[callback.from_user.id] = (dt.now(), True)
    await callback.answer("✓")

    if callback.data in ["price", "homestaging"]:
        kb = types.InlineKeyboardMarkup(row_width=1)
        vb = types.InlineKeyboardButton(text='Смотреть материал', url=why_bad_str_list[callback.data])
        kb.add(vb)
        await bot.send_message(callback.from_user.id, f"Вот ссылка на теоретическую информацию по твоей теме:", reply_markup=kb)
        await WorkStates.ready.set()
        schedule_job(callback.from_user.id, bot, "Изучил материал? Все понял, или нужно что-то еще?", WorkStates.is_all_materials_ok, get_is_all_materials_ok_markup(), dt.now() + SHIFT_SHORT_TIMEDELTA, "Изучение теоретических материалов")


# что конкретно не так (обработка кнопок и список) универсальная
@dp.callback_query_handler(state=WorkStates.deal_why_bad_result)
async def enter_why_deal_bad(callback: types.CallbackQuery, state: FSMContext):
    last_messages[callback.from_user.id] = (dt.now(), True)
    await callback.answer("✓")
    tmp = Report.get_or_none(Report.rielter_id == callback.from_user.id)
    if callback.data in ("Объект не понравился", "Задаток сорвался", "Продавец привередливый", "Покупатель привередливый", "Встреча не состоялась", "get_materials_analytics"):
        if callback.data == "Объект не понравился":
            count = 0
            if tmp:
                count += tmp.bad_object_count
                Report.update(bad_object_count=count+1).where(Report.rielter_id == callback.from_user.id).execute()
            await bot.send_message(chat_id=callback.from_user.id, text=f"Бывают и такие объекты, которые не стоили потраченного времени!\nИзучи этот материал, это позволит тебе в будущем избежать подобных ошибок:", 
                                reply_markup=get_video_link(why_bad_str_list["meets"]))
            await WorkStates.ready.set()
            
        elif callback.data == "Задаток сорвался":
            await bot.send_message(chat_id=callback.from_user.id, text = "Жаль, это был потенциальный клиент!")
            await bot.send_message(chat_id=callback.from_user.id, text=f"Выйти на задаток - самая сложная часть нашей работы, не!\nИзучи этот материал, это позволит тебе в будущем избежать подобных ошибок:", 
                                reply_markup=get_video_link(why_bad_str_list["anti_bad"]))
            await WorkStates.ready.set()

        elif callback.data == "Продавец привередливый":
            count = 0
            if tmp:
                count += tmp.bad_seller_count
                Report.update(bad_seller_count=count+1).where(Report.rielter_id == callback.from_user.id).execute()
            await bot.send_message(chat_id=callback.from_user.id, text=f"Порой на рынке встречаются крайне неприятные продавцы, что поделаешь!\nИзучи этот материал, это позволит тебе в будущем избежать подобных ошибок:", 
                                reply_markup=get_video_link(why_bad_str_list["bad_meets"]))
            await WorkStates.ready.set()
            
        elif callback.data == "Покупатель привередливый":
            count = 0
            if tmp:
                count += tmp.bad_seller_count
                Report.update(bad_seller_count=count+1).where(Report.rielter_id == callback.from_user.id).execute()
            await bot.send_message(chat_id=callback.from_user.id, text=f"Порой на рынке встречаются крайне неприятные покупатели, что поделаешь!\nИзучи этот материал, это позволит тебе в будущем избежать подобных ошибок:", 
                                reply_markup=get_video_link(why_bad_str_list["bad_meets"]))
            await WorkStates.ready.set()
            
        elif callback.data == "Встреча не состоялась":
            count = 0
            if tmp:
                count += tmp.bad_seller_count
                Report.update(bad_seller_count=count+1).where(Report.rielter_id == callback.from_user.id).execute()
            await bot.send_message(chat_id=callback.from_user.id, text=f"Иногда попадаются просто безответственные продавцы, не хочется иметь с ними дело!\nИзучи этот материал, это позволит тебе в будущем избежать подобных ошибок:", 
                                reply_markup=get_video_link(why_bad_str_list["bad_meets"]))
            await WorkStates.ready.set()

        elif callback.data == "get_materials_analytics":
            await bot.send_message(chat_id=callback.from_user.id, text=f"Всегда полезно самосовершенствование, особенно когда дело касается аналитики рынка или поиска новых объектов!:", 
                                reply_markup=get_video_link(why_bad_str_list["analytics"]))
            await WorkStates.ready.set()
            
        elif callback.data == "get_video_calls":
            await bot.send_message(chat_id=callback.from_user.id, text=f"Всегда полезно самосовершенствование, особенно когда дело касается аналитики рынка или поиска новых объектов!:", 
                                reply_markup=get_video_link("https://youtu.be/cATV_k5cqBc?si=n_cSPsPr1ZC6_vNs"))
            await WorkStates.ready.set()
        schedule_job(callback.from_user.id, bot, "Изучил материал? Все понял, или нужно что-то еще?", WorkStates.is_all_materials_ok, get_is_all_materials_ok_markup(), dt.now() + SHIFT_SHORT_TIMEDELTA, "Изучение теоретических материалов")

    elif callback.data == "Сделку перенесли" or callback.data == "Задаток перенесен":
        await bot.send_message(chat_id=callback.from_user.id, text = "Ладно, переносы имеют место в нашей работе, давай запишем тебе напоминание!", reply_markup=types.ReplyKeyboardRemove())
        await bot.send_message(chat_id=callback.from_user.id, text = "Напиши краткое название задачи:")
        await WorkStates.task_name.set()

    elif callback.data == "Клиент передумал":
        await bot.send_message(chat_id=callback.from_user.id, text = generate_bad_meeting_or_deal())
        await bot.send_message(chat_id=callback.from_user.id, text = generate_main_menu_text(), reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()
    
    elif callback.data == "other":
        await bot.send_message(chat_id=callback.from_user.id, text=f"Давай посмотрим, что я могу предложить тебе изучить, чтобы набраться теоретических знаний...", reply_markup=types.ReplyKeyboardRemove())
        await bot.send_message(chat_id=callback.from_user.id, text="Выбери какyю тему ты бы хотел просмотреть:", reply_markup=get_knowledge_base_root_markup())
        await WorkStates.knowledge_base_root.set()


# все понятно или повторить?
@dp.message_handler(lambda msg: msg.text in ["Спасибо, все понятно", "Нужна еще информация"], state=WorkStates.is_all_materials_ok)
async def is_all_materials_ok_handler(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now(), True)
    if msg.text == "Спасибо, все понятно":
        await msg.answer("Рад, что смог помочь тебе повысить уровень знаний в профессиональной сфере!", reply_markup=types.ReplyKeyboardRemove())
        await msg.answer(generate_main_menu_text(), reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()
    elif msg.text == "Нужна еще информация":
        await bot.send_message(chat_id=msg.from_user.id, text=f"Давай посмотрим, что я могу предложить тебе изучить, чтобы набраться теоретических знаний...", reply_markup=types.ReplyKeyboardRemove())
        await bot.send_message(chat_id=msg.from_user.id, text="Выбери какyю тему ты бы хотел просмотреть:", reply_markup=get_knowledge_base_root_markup())
        await WorkStates.knowledge_base_root.set()

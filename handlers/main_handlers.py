from aiogram import types
from aiogram.dispatcher import FSMContext
from bot import *
from keybords import *
from models import *
from .creation import *
from .notifications import *
from datetime import timedelta
from datetime import datetime as dt
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import asyncio, logging, json


# при старте бота
async def onStartBot(_):
    # запуск утреннего и вечернего оповещения
    main_scheduler.add_job(func=morning_notifications, trigger=CronTrigger(hour=10-3, minute=0), kwargs={"bot": bot, "dp": dp})
    main_scheduler.add_job(func=good_evening_notification, trigger=CronTrigger(hour=18-3, minute=30), kwargs={"bot": bot})

    # запуск ежемесячного и еженедельного отчета
    month_week_scheduler.add_job(func=get_month_statistics, trigger='cron', day='last', hour=10-3, minute=30, kwargs={"bot": bot})
    month_week_scheduler.add_job(func=get_week_statistics, trigger='cron', day_of_week='mon', hour=10-3, minute=50, kwargs={"bot": bot})

    # запуск слушателя игнора
    ignore_scheduler.add_job(func=ignore_listener, trigger=IntervalTrigger(minutes=1))

    main_scheduler.start()
    support_scheduler.start()
    month_week_scheduler.start()
    ignore_scheduler.start()

    create_db()

    logging.info("All was inited")


# команда помощь
@dp.message_handler(commands=['help'], state=WorkStates.ready)
async def del_task_cmd(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now(), True)
    await msg.answer(get_help_command_text())


# команда досрочно завершить задачу
@dp.message_handler(commands=['del_task'], state=WorkStates.ready)
async def del_task_cmd(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now(), True)
    res_str = ""
    c = 0
    if msg.from_user.id not in scheduler_list.keys():
        await bot.send_message(chat_id=msg.from_user.id, text="Вы еще не начинали никаких задач!")
        await msg.answer(generate_main_menu_text(), reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()
        return
    for job_id in scheduler_list[msg.from_user.id].keys():
        if support_scheduler.get_job(job_id):
            title = scheduler_list[msg.from_user.id][job_id]["title"]
            res_str += f"{c+1}) задача #{title} \n"
            c += 1

    if c > 0:
        res_str += "\n\nВведи порядковый номер задачи, которую хочешь завершить досрочно \n(Введи 0 чтобы выйти):"
        await bot.send_message(chat_id=msg.from_user.id, text=res_str)
        await WorkStates.enter_task_id.set()
    else:
        await bot.send_message(chat_id=msg.from_user.id, text="Вы еще не начинали никаких задач!")
        await msg.answer(generate_main_menu_text(), reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()


# ввод порядкового номера задачи, которую досрочно завершаем
@dp.message_handler(lambda msg: msg.text.isdigit(), state=WorkStates.enter_task_id)
async def enter_del_task_id(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now(), True)
    if msg.text == "0":
        await msg.answer(generate_main_menu_text(), reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()
        return
    c = 0
    if c > len(scheduler_list[msg.from_user.id].keys()) or c < 0:
        await msg.answer("Боюсь ты ввел неправильное число, попробуй еще раз!")
        return
    for job_id in scheduler_list[msg.from_user.id].keys():
        if c+1 == int(msg.text):
            support_scheduler.remove_job(job_id)
            await send_scheduled_message(**scheduler_list[msg.from_user.id][job_id])
            break
        c += 1


# инлайн режим бота
@dp.inline_handler(state="*")
async def inline_mode_query_handler(inline_query: types.InlineQuery, state: FSMContext):
    text = inline_query.query or "None"
    if text:
        items = []
        for rielter in Rielter.select():
            try:
                items.append(types.InlineQueryResultArticle(input_message_content=types.InputTextMessageContent(get_month_statistics_str(rielter.rielter_id)), id=str(rielter.rielter_id), title=f"Отчёт {rielter.fio}"))
            except:
                continue
        await bot.answer_inline_query(inline_query_id=inline_query.id, results=items, cache_time=1)


# команда меню
@dp.message_handler(commands=['menu'], state="*")
async def start_cmd(msg: types.Message):
    last_messages[msg.from_user.id] = (dt.now(), True)
    await msg.answer(generate_main_menu_text(), reply_markup=get_inline_menu_markup())
    await WorkStates.ready.set()
    

# служебная команда для отладки
@dp.message_handler(commands=['debug'], state="*")
async def start_cmd(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now(), False)
    await msg.answer(f"state = {state.__str__()}")
    await msg.answer(f"scheduler_list = {json.dumps(scheduler_list.__dict__)}")


# команда задача
@dp.message_handler(commands=['task'], state=WorkStates.ready)
async def start_cmd(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now(), True)
    await msg.answer("Отлично, давай запишем новое напоминание!", reply_markup=types.ReplyKeyboardRemove())
    await msg.answer("Напиши краткое название задачи:")
    await WorkStates.task_name.set()


# команда старт
@dp.message_handler(commands=['start'], state="*")
async def start_cmd(msg: types.Message):
    last_messages[msg.from_user.id] = (dt.now(), True)
    #scheduler_list[msg.from_user.id] = {} # сомнительно но ок
    oldRielter: any
    try:
        oldRielter = Rielter.get_by_id(pk=msg.from_user.id)
    except Exception:
        oldRielter = None
    if oldRielter:
        await msg.answer(f"С возвращением, {oldRielter.fio}!", reply_markup=types.ReplyKeyboardRemove())
        await msg.answer(generate_main_menu_text(), reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()
        return
    await msg.answer("Привет!\nДля начала работы нажми на кнопку 'Старт регистрации'", reply_markup=get_start_button())
    await WorkStates.restart.set()


# default хэндлер для клавиатуры, которая будет доступна всегда в состоянии ready
@dp.callback_query_handler(state=WorkStates.ready)
async def start_new_activity(callback: types.CallbackQuery, state: FSMContext):
    if callback.data not in ("analytics", "meeting", "call", "show", "search", "flyer", "deal", "deposit", "no_work", "d_base"):
        return
    await callback.answer("✓")
    last_messages[callback.from_user.id] = (dt.now(), True)
    if callback.data == "analytics":
        await bot.send_message(chat_id=callback.from_user.id, text="Хорошо, я вернусь через час, предложить новую работу!")
        tmp = Report.get_or_none(Report.rielter_id == callback.from_user.id)
        count = 0
        if tmp:
            count += tmp.analytics
            Report.update(analytics=count+1).where(Report.rielter_id == callback.from_user.id).execute()
        schedule_job(callback.from_user.id, bot, "Как прошло занятие аналитикой, уверен супер продуктивно?", WorkStates.analytics_result, get_good_bed_result_markup(), dt.now() + SHIFT_TIMEDELTA, "Аналитика")

    elif callback.data == "meeting":
        await bot.send_message(chat_id=callback.from_user.id, text="Хорошо, удачной поездки, скоро вернусь и спрошу как все прошло!")
        schedule_job(callback.from_user.id, bot, "Как прошла встреча?", WorkStates.meet_new_object_result, get_good_bed_result_markup(), dt.now() + SHIFT_TIMEDELTA, "Встреча")

    elif callback.data == "call":
        await bot.send_message(chat_id=callback.from_user.id, text="Хорошо, я вернусь через час, поитересоваться твоими успехами!")
        schedule_job(callback.from_user.id, bot, "Как твои успехи в прозвонах? Сколько рабочих звонков ты успел совершить?", WorkStates.enter_calls_count, None, dt.now() + SHIFT_TIMEDELTA, "Прозвон")

    elif callback.data == "show":
        await bot.send_message(chat_id=callback.from_user.id, text="Отлично, желаю удачного показа, скоро вернусь!")
        schedule_job(callback.from_user.id, bot, "Как прошел показ?", WorkStates.show_result, get_good_bed_result_markup(), dt.now() + SHIFT_TIMEDELTA, "Показ")

    elif callback.data == "search":
        await bot.send_message(chat_id=callback.from_user.id, text="Хорошо, я вернусь через час, предложить новую работу!")
        tmp = Report.get_or_none(Report.rielter_id == callback.from_user.id)
        if tmp:
            count = 0
            count += tmp.analytics
            Report.update(analytics=count+1).where(Report.rielter_id == callback.from_user.id).execute()
        schedule_job(callback.from_user.id, bot, "Как прошло занятие по поиску новых объектов, уверен супер продуктивно?", WorkStates.analytics_result, get_good_bed_result_markup(), dt.now() + SHIFT_TIMEDELTA, "Поиск")

    elif callback.data == "flyer":
        await bot.send_message(chat_id=callback.from_user.id, text="Хорошо, я вернусь через час, поитересоваться твоими успехами!")
        schedule_job(callback.from_user.id, bot, "Как твои успехи в расклейке? Прогулялся, отдохнул, готов к работе? Напиши сколько объявлений ты расклеил?", WorkStates.enter_flyer_count, None, dt.now() + SHIFT_TIMEDELTA, "Расклейка")

    elif callback.data == "deal":
        tmp = Rielter.get_or_none(Rielter.rielter_id == callback.from_user.id)
        if tmp.rielter_type_id == 0:
            await bot.send_message(chat_id=callback.from_user.id, text="Давай уточним:", reply_markup=get_meeting_private_markup())
        elif tmp.rielter_type_id == 1:
            await bot.send_message(chat_id=callback.from_user.id, text="Давай уточним:", reply_markup=get_meeting_commercial_markup())
        await WorkStates.deal_enter_deal_type.set()

    elif callback.data == "deposit":
        await bot.send_message(chat_id=callback.from_user.id, text="Хорошо, удачи. Скоро вернусь и спрошу как все прошло!")
        schedule_job(callback.from_user.id, bot, "Как прошло получение задатка?", WorkStates.deposit_result, get_good_bed_result_markup(), dt.now() + SHIFT_TIMEDELTA, "Задаток")

    elif callback.data == "no_work":
        await bot.send_message(chat_id=callback.from_user.id, text="Давай уточним:", reply_markup=get_rest_markup())
        await WorkStates.no_work_type.set()
        
    elif callback.data == "d_base":
        await bot.send_message(chat_id=callback.from_user.id, text=f"Давай посмотрим, что я могу предложить тебе изучить, чтобы набраться теоретических знаний...")
        await bot.send_message(chat_id=callback.from_user.id, text="Выбери какyю тему ты бы хотел просмотреть:", reply_markup=get_knowledge_base_root_markup())
        await WorkStates.knowledge_base_root.set()

    else:
        await bot.send_message(chat_id=callback.from_user.id, text="О нет, непредвиденная ситация!\nПросим вас сделать скриншот этой ситуации и направить разработчикам.")


# не могу работать
@dp.message_handler(lambda msg: msg.text in ["Устал", "Отпуск", "Больничный", "Назад"], state=WorkStates.no_work_type)
async def enter_no_work_type(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now(), True)
    if msg.text == "Назад":
        await msg.answer(generate_main_menu_text(), reply_markup=get_inline_menu_markup())
        await WorkStates.ready.set()
    elif msg.text == "Устал":
        await msg.answer("Конечно ты можешь отдохнуть, я напомню тебе про работу через час.", reply_markup=types.ReplyKeyboardRemove())
        schedule_job(msg.from_user.id, bot, generate_main_menu_text(), WorkStates.ready, get_inline_menu_markup(), dt.now() + SHIFT_TIMEDELTA, "Задаток")
        await WorkStates.ready.set()
    elif msg.text == "Отпуск":
        async with state.proxy() as data:
            data["rest_type"] = "отпуск"
        await msg.answer("Отпуск - лучшее время в году! Напиши, сколько дней планируешь отдыхать, а я сообщу руководителю:", reply_markup=types.ReplyKeyboardRemove())
        await WorkStates.enter_days_ill_or_rest.set()
    else:
        async with state.proxy() as data:
            data["rest_type"] = "больничный"
        await msg.answer("Болеть всегда неприятно, но ты поправляйся, а я сообщю руководителю.\nСколько дней тебя не тревожить?", reply_markup=types.ReplyKeyboardRemove())
        await WorkStates.enter_days_ill_or_rest.set()
        

# сколько дней болеть или отдыхать
@dp.message_handler(state=WorkStates.enter_days_ill_or_rest)
async def enter_no_work_type(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now(), False)
    try:
        days_count = int(msg.text)
        if days_count < 0:
            raise Exception()
    except Exception:
        await msg.reply("Ошибка, попробуй ввести еще раз!")
        return
    async with state.proxy() as data:
        await msg.answer(f"Я все понял. Не буду тревожить тебя дней: {days_count}. Можешь написать мне в любое время, когда сможешь продолжить работу", reply_markup=types.ReplyKeyboardRemove())
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Сотрудник  {Rielter.get_or_none(Rielter.rielter_id == msg.from_user.id).fio} #{msg.from_user.id} хочет взять #{data['rest_type']} на дней: {days_count}.")
        await WorkStates.ready.set()


# если поболтать
@dp.message_handler(state=WorkStates.ready)
async def talks(msg: types.Message, state: FSMContext):
    last_messages[msg.from_user.id] = (dt.now(), True)
    await msg.answer("Тебе стоит выбрать какое-нибудь действие, если ты потерялся - обратись к справке /help или своему руководителю!")

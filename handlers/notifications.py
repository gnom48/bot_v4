from aiogram import types, Bot
from datetime import time, date, timedelta
from datetime import datetime as dt
from models import *
from keybords import *
from aiogram.dispatcher.filters.state import State
from bot import *
from .creation import *
import holidays
import asyncio, logging
from aiogram.dispatcher import Dispatcher


# для правильной планировки отправки сообщения
def schedule_job(chat_id: int, bot: Bot, text: str, state: State, keyboard, send_at: dt, title: str) -> None:
    last_messages[chat_id] = (dt.now(), True)
    job_id = f"{chat_id}_{send_at}_{title}"
    kw = {"chat_id" : chat_id, "job_id" : job_id, "bot" : bot, "text" : text, "state" : state, "keyboard" : keyboard, "title" : title}
    support_scheduler.add_job(func=send_scheduled_message, trigger="date", run_date=send_at, kwargs=kw, id=job_id)
    if chat_id not in scheduler_list:
        scheduler_list[chat_id] = {}
    scheduler_list[chat_id][job_id] = kw


# отправка отложенного запланированного сообщения
async def send_scheduled_message(chat_id: int, job_id: str, bot: Bot, text: str, state: State, keyboard, title: str) -> None:
    await bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)
    if state:
        await state.set()
    if chat_id in scheduler_list:
        if job_id in scheduler_list[chat_id]:
            del scheduler_list[chat_id][job_id]
        else:
            logging.error(f"unable to delete task {job_id} user is not exists")
    else:
        logging.error(f"unable to delete task {job_id} job_id is not exists")
        scheduler_list[chat_id] = {}


# слушатель игнора - проверяет для пользователя последнее сообщение и ругается
async def ignore_listener() -> None:
    for chat_id in last_messages:
        time_point = dt.now()
        if time_point.time() > time(18-3, 0) or time_point.time() < time(10-3, 0):
            return
        if not last_messages[chat_id][1]:
            continue
        time_diff = time_point - last_messages[chat_id][0]
        if time_diff.seconds >= 3600 and time_diff.seconds < 3750 and len(last_messages[chat_id]) == 2:
            try:
                last_messages[chat_id] = (dt.now(), True, True)
                await bot.send_message(chat_id=chat_id, text="Я понимаю, что ты занят, расскажи, пожалуйста, как у тебя дела?")
            except:
                logging.error(f"unable to chat with [ignore] {chat_id}")
            continue
        # elif time_diff.seconds >= 7200 and time_diff.seconds < 10800 and len(last_messages[chat_id]) == 3:
        elif time_diff.seconds >= 3600 and time_diff.seconds < 3750 and len(last_messages[chat_id]) == 3:
            try:
                last_messages[chat_id] = (dt.now(), True, True, True)
                await bot.send_message(chat_id=chat_id, text="Я понимаю, что ты очень сильно занят, но напиши, пожалуйста, как у тебя с делом?")
            except:
                logging.error(f"unable to chat with [ignore] {chat_id}")
            continue
        # elif time_diff.seconds >= 10800:
        elif time_diff.seconds >= 3600 and time_diff.seconds < 3750 and len(last_messages[chat_id]) == 4:
            if not (dt.now().weekday() == 5 or dt.now().weekday() == 6 or dt.now() in holidays_ru["state_holidays"]):
                try:
                    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Сотрудник {Rielter.get_or_none(Rielter.rielter_id == chat_id).fio} (#{chat_id}) не отвечает на сообщения уже 3 часа!")
                    await bot.send_message(chat_id=chat_id, text=f"О нет, вы игнорируете меня уже 3 часа к ряду! Я был вынужден сообщить вашему руководителю.")
                    last_messages[chat_id] = (dt.now(), False)
                except:
                    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Сотрудник {Rielter.get_or_none(Rielter.rielter_id == chat_id).fio} (#{chat_id}) недоступен для отправки сообщений!")

        
# ежедневные утренние напоминания
async def morning_notifications(bot: Bot, dp: Dispatcher):
    # сброс счётчиков
    last_messages.clear()

    # др
    for rielter in Rielter.select():
        try:
            if rielter.birthday[:5] == dt.now().strftime('%d-%m'):
                await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Поздравляем с днем рождения сотрудника {rielter.fio}")
                await bot.send_message(chat_id=rielter.rielter_id, text=f"От наших коллег, руководителей и от себя, поздравляю тебя с днем рождения! 🎉 Желаю вам океан счастья, гору улыбок и сверкающих моментов в этот особенный день! 🎂❤️")
        except:
            logging.error(f"unable to chat with [morning] {rielter.rielter_id}")


    holidays_ru["state_holidays"] = holidays.Russia(years=dt.now().year)
    for rielter in Rielter.select():
        holidays_ru["birthdays"][rielter.birthday] = rielter.fio

    reports = Report.select()
    chats = []
    for tmp in reports:
        try:
            chats.append(tmp.rielter_id)
            
            # tmp.cold_call_count = 0
            # tmp.meet_new_objects = 0
            # tmp.take_in_work = 0
            # tmp.contrects_signed = 0
            # tmp.show_objects = 0
            # tmp.posting_adverts = 0
            # tmp.ready_deposit_count = 0
            # tmp.take_deposit_count = 0
            # tmp.deals_count = 0
            # tmp.analytics = 0
            # tmp.bad_seller_count = 0
            # tmp.bad_object_count = 0
            # tmp.save()

            # напоминания на день
            task_list: list = Task.select().where(Task.rielter_id == tmp.rielter_id)
            tasks_str = ""
            if len(task_list) != 0:
                tasks_str = f"Напоминаю, что на сегодня ты запланировал:\n\n"
                for task in task_list:
                    if tmp.rielter_id == task.rielter_id and dt.strptime(task.date_planed, '%d-%m-%Y').date() == dt.now().date():
                        tasks_str = tasks_str + f" - {task.task_name}\n\n"
                        time_obj: dt
                        try:
                            time_obj = dt.strptime(str(task.time_planed), '%H:%M:%S').time()
                        except:
                            continue
                        dt_tmp = dt(year=dt.now().year, month=dt.now().month, day=dt.now().day, hour=time_obj.hour, minute=time_obj.minute, second=0)
                        schedule_job(tmp.rielter_id, bot, f"Напоминаю, что ты запланировал в {task.time_planed} заняться: {task.task_name}", None, None, dt_tmp - timedelta(hours=3, seconds=10), " + 1 напоминание")
                        Task.delete().where(Task.id == task.id).execute()
                await bot.send_message(chat_id=tmp.rielter_id, text=tasks_str)

            if dt.now().weekday() == 5 or dt.now().weekday() == 6 or dt.now() in holidays_ru["state_holidays"]:
                if dt.now() in holidays_ru['state_holidays']:
                    await bot.send_message(chat_id=tmp.rielter_id, text=f"Поздравляю с праздником! Сегодня - {holidays_ru['state_holidays'][dt.now()]}")
                return

            last_messages[tmp.rielter_id] = (dt.now(), True)
            await bot.send_message(chat_id=tmp.rielter_id, text=get_day_plan(Rielter.get_by_id(pk=tmp.rielter_id).rielter_type_id))

            await bot.send_message(chat_id=tmp.rielter_id, text=generate_main_menu_text(), reply_markup=get_inline_menu_markup())
            await dp.storage.set_state(user=tmp.rielter_id, state=WorkStates.ready)

        except:
            logging.error(f"unable to chat with [morning] {tmp.rielter_id}")


# ежедневное вечернее подведение итогов
async def good_evening_notification(bot: Bot):
    holidays_ru["state_holidays"] = holidays.Russia(years=dt.now().year)
    # др
    for rielter in Rielter.select():
        try:
            if rielter.birthday[:5] == (dt.now() + timedelta(days=1)).strftime('%d-%m'):
                await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Напоминаю, что завтра день рождения у нашего коллеги - {rielter.fio}!\n")
        except:
            pass

    flag = False
    if dt.now().weekday() == 5 or dt.now().weekday() == 6 or dt.now() in holidays_ru["state_holidays"]:
        flag = True
    
    dayReport = Report.select()
    day_results_str = ""
    for day_results in dayReport:
        day_results_str = f"\nЗвонков: {day_results.cold_call_count} \nвыездов на осмотры: {day_results.meet_new_objects}" \
            + f"\nаналитика: {day_results.analytics} \nподписано контрактов: {day_results.contrects_signed}" \
            + f"\nпоказано объектов: {day_results.show_objects} \nрасклеено объявлений: {day_results.posting_adverts}" \
            + f"\nклиентов готовых подписать договор: {day_results.take_in_work} \nклиентов внесли залог: {day_results.take_deposit_count}" \
            + f"\nзавершено сделок: {day_results.deals_count}\n" \
            + f"\nнарвался на плохих продавцов / клиентов: {day_results.bad_seller_count}" \
            + f"\nнарвался на плохие объекты: {day_results.bad_object_count}"
        
        kb = InlineKeyboardMarkup(row_width=1)

        # Звонки
        if day_results.cold_call_count < 5:
            calls_praise = "Мало! 😔 Ты должен делать минимум 5 звонков в день. Но не переживай, изучи эти материалы, и сможешь стать еще продуктивнее."
            vb1 = InlineKeyboardButton(text='Видео про звонки 🎥', url=why_bad_str_list["calls_video"])
            vb2 = InlineKeyboardButton(text='Про звонки 📖', url=why_bad_str_list["calls"])
            kb.add(vb1)
            kb.add(vb2)
        elif 5 <= day_results.cold_call_count < 10:
            calls_praise = "Молодец! Продолжай в том же духе! 👍"
        else:
            calls_praise = "Ты просто супер! Ты крутой сотрудник! 🥳"

        # Расклейка
        if day_results.posting_adverts < 7:
            stickers_praise = "Плохо! Нужно больше расклеек! 😔 Давай посмотрим видео-материалы про правила расклейки, может быть ты подчерпнешь для себя что-то новое."
            # vb = InlineKeyboardButton(text='Про расклейки 📖', url=why_bad_str_list["commercial"])
            # kb.add(vb)
        elif 17 <= day_results.posting_adverts < 28:
            stickers_praise = "Молодец! Так держать! 👍"
        else:
            stickers_praise = "Супер молодец! Мега продуктивная работа! 🥳"

        # Связанное предложение
        praise_sentence = f"Что я могу сказать по поводу эффективности твоей работы:\n\nЗвонки: {calls_praise}\n\nРасклейка: {stickers_praise}"

        worker = Rielter.get_by_id(pk=day_results.rielter_id)

        if not flag:
            try:
                await bot.send_message(chat_id=day_results.rielter_id, text=f"Доброе вечер! Жаль, но пора заканчивать рабочий день. \n\nДавай посмотрим, как ты потрудился сегодня:") #\n{day_results_str}")
                await bot.send_message(chat_id=day_results.rielter_id, text=f"{praise_sentence}", reply_markup=kb)
                await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Сотрудник {worker.fio} (#{day_results.rielter_id}) завершил рабочий день. \nОтчет: \n{day_results_str}")
            except:
                logging.error(f"unable to chat with [evening] {day_results.rielter_id}")


        week_result = WeekReport.get_or_none(WeekReport.rielter_id == day_results.rielter_id)
        if week_result:
            week_result.cold_call_count += day_results.cold_call_count
            week_result.meet_new_objects += day_results.meet_new_objects
            week_result.take_in_work += day_results.take_in_work
            week_result.contrects_signed += day_results.contrects_signed
            week_result.show_objects += day_results.show_objects
            week_result.posting_adverts += day_results.posting_adverts
            week_result.take_deposit_count += day_results.take_deposit_count
            week_result.deals_count += day_results.deals_count
            week_result.analytics += day_results.analytics
            week_result.bad_seller_count += day_results.bad_seller_count
            week_result.bad_object_count += day_results.bad_object_count
            week_result.save()
            
        month_result = MonthReport.get_or_none(MonthReport.rielter_id == day_results.rielter_id)
        if month_result:
            month_result.cold_call_count += day_results.cold_call_count
            month_result.meet_new_objects += day_results.meet_new_objects
            month_result.take_in_work += day_results.take_in_work
            month_result.contrects_signed += day_results.contrects_signed
            month_result.show_objects += day_results.show_objects
            month_result.posting_adverts += day_results.posting_adverts
            month_result.take_deposit_count += day_results.take_deposit_count
            month_result.deals_count += day_results.deals_count
            month_result.analytics += day_results.analytics
            month_result.bad_seller_count += day_results.bad_seller_count
            month_result.bad_object_count += day_results.bad_object_count
            month_result.save()

        day_res = Report.get_or_none(Report.rielter_id == day_results.rielter_id)
        if day_res:
            day_res.cold_call_count = 0
            day_res.meet_new_objects = 0
            day_res.take_in_work = 0
            day_res.contrects_signed = 0
            day_res.show_objects = 0
            day_res.posting_adverts = 0
            day_res.ready_deposit_count = 0
            day_res.take_deposit_count = 0
            day_res.deals_count = 0
            day_res.analytics = 0
            day_res.bad_seller_count = 0
            day_res.bad_object_count = 0
            day_res.save()


# статистики еженедельная [отправить]
async def get_week_statistics(bot: Bot):
    weekResolts = WeekReport.select()
    for results in weekResolts:
        tmp = Rielter.get_or_none(Rielter.rielter_id == results.rielter_id)
        results_str = f"Статистика сотрудника {tmp.fio} (#{tmp.rielter_id}) за последнюю рабочую неделю:\n"
        results_str += f"\nзвонков: {results.cold_call_count} \nвыездов на осмотры: {results.meet_new_objects}" \
            + f"\nаналитика: {results.analytics} \nподписано контрактов: {results.contrects_signed}" \
            + f"\nпоказано объектов: {results.show_objects} \nрасклеено объявлений: {results.posting_adverts}" \
            + f"\nклиентов готовых подписать договор: {results.take_in_work} \nклиентов внесли залог: {results.take_deposit_count}" \
            + f"\nзавершено сделок: {results.deals_count}\n" \
            + f"\nнарвался на плохих продавцов / клиентов: {results.bad_seller_count}" \
            + f"\nнарвался на плохие объекты: {results.bad_object_count}"
        try:
            await bot.send_message(chat_id=ADMIN_CHAT_ID, text=results_str)
        except:
                logging.error(f"unable to chat with [stat week] {results.rielter_id}")

        results.cold_call_count = 0
        results.meet_new_objects = 0
        results.take_in_work = 0
        results.contrects_signed = 0
        results.show_objects = 0
        results.posting_adverts = 0
        results.ready_deposit_count = 0
        results.take_deposit_count = 0
        results.deals_count = 0
        results.analytics = 0
        results.bad_seller_count = 0
        results.bad_object_count = 0
        results.save()


# статистики ежемесячная [текст]
def get_month_statistics_str(rielter_id) -> str:
    results = Report.get_or_none(Report.rielter_id == rielter_id)
    tmp = Rielter.get_or_none(Rielter.rielter_id == rielter_id)
    results_str = f"Статистика сотрудника {tmp.fio} (#{tmp.rielter_id}) за последний месяц:\n"
    results_str += f"\nзвонков: {results.cold_call_count} \nвыездов на осмотры: {results.meet_new_objects}" \
        + f"\nаналитика: {results.analytics} \nподписано контрактов: {results.contrects_signed}" \
        + f"\nпоказано объектов: {results.show_objects} \nрасклеено объявлений: {results.posting_adverts}" \
        + f"\nклиентов готовых подписать договор: {results.take_in_work} \nклиентов внесли залог: {results.take_deposit_count}" \
        + f"\nзавершено сделок: {results.deals_count}\n" \
        + f"\nнарвался на плохих продавцов / клиентов: {results.bad_seller_count}" \
        + f"\nнарвался на плохие объекты: {results.bad_object_count}"
    return results_str


# статистики ежемесячная [отправить]
async def get_month_statistics(bot: Bot):
    monthResults = MonthReport.select()
    for results in monthResults:
        tmp = Rielter.get_or_none(Rielter.rielter_id == results.rielter_id)
        results_str = f"Статистика сотрудника {tmp.fio} (#{tmp.rielter_id}) за последний месяц:\n"
        results_str += f"\nзвонков: {results.cold_call_count} \nвыездов на осмотры: {results.meet_new_objects}" \
            + f"\nаналитика: {results.analytics} \nподписано контрактов: {results.contrects_signed}" \
            + f"\nпоказано объектов: {results.show_objects} \nрасклеено объявлений: {results.posting_adverts}" \
            + f"\nклиентов готовых подписать договор: {results.take_in_work} \nклиентов внесли залог: {results.take_deposit_count}" \
            + f"\nзавершено сделок: {results.deals_count}\n" \
            + f"\nнарвался на плохих продавцов / клиентов: {results.bad_seller_count}" \
            + f"\nнарвался на плохие объекты: {results.bad_object_count}"
        try:
            await bot.send_message(chat_id=ADMIN_CHAT_ID, text=results_str)
        except:
            logging.error(f"unable to chat with [morning] {results.rielter_id}")

        results.cold_call_count = 0
        results.meet_new_objects = 0
        results.take_in_work = 0
        results.contrects_signed = 0
        results.show_objects = 0
        results.posting_adverts = 0
        results.ready_deposit_count = 0
        results.take_deposit_count = 0
        results.deals_count = 0
        results.analytics = 0
        results.bad_seller_count = 0
        results.bad_object_count = 0
        results.save()

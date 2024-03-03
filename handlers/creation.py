from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime as dt
from models import *
from keybords import *
from aiogram.dispatcher.filters.state import State
from bot import *
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage


bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

holidays_ru = {"state_holidays": {}, "birthdays": {}}

main_scheduler = AsyncIOScheduler(timezone="UTC")
support_scheduler = AsyncIOScheduler(timezone="UTC")
month_week_scheduler = AsyncIOScheduler(timezone="UTC")
ignore_scheduler = AsyncIOScheduler(timezone="UTC")

scheduler_list = dict() # словарь структуры { chat_id : { task_id : (kwargs, "занятие") } }
last_messages = dict() # словарь структуры { chat_id : (last_message_time, bool) }
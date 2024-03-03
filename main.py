from aiogram.utils import executor
from handlers import *
from models import *


executor.start_polling(dp, skip_updates=True, on_startup=onStartBot)
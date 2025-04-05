# Телеграм бот - наставник и ментор для сотрудников риелторского агентства

### Стэк:
- Python
    - Aiogram2
    - Peewee
    - APScheduler
- Docker

### Запуск:
0. Заполнить переменные TOKEN и ADMIN_CHAT_ID
1. Выполнить команды:
    - `docker build -t miabox_bot .`
    - `docker run miabox_bot`
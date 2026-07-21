# FocusFlow

Мобильное приложение для техники Pomodoro с задачами и Premium-подпиской.

## Стек
- Python 3.14
- Flet 0.85.3
- SQLAlchemy + SQLite

## Запуск
```bash
pip install -r requirements.txt
python main.py

Структура
main.py — точка входа
db/ — модели и операции с БД
services/ — бизнес-логика (таймер, звук)
ui/ — экраны и тема
assets/sounds/ — звуковые файлы (не включены в репозиторий)

Звуки
Положите файл bell.wav в assets/sounds/. Без него будет системный звук Windows.
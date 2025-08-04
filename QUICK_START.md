# 🚀 Быстрый старт HR-бота

## Установка и запуск за 5 минут

### 1. Установка зависимостей
```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. Настройка конфигурации
```bash
cp env.example .env
# Отредактируйте .env файл, добавив свои токены
```

### 3. Запуск бота
```bash
python run.py
```

## Получение токенов

### Telegram Bot Token
1. Найдите @BotFather в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте полученный токен в `.env`

### OpenAI API Key
1. Зарегистрируйтесь на https://platform.openai.com/
2. Перейдите в раздел API Keys
3. Создайте новый ключ
4. Скопируйте ключ в `.env`

## Тестирование
```bash
python test_bot.py
```

## Структура проекта
- `bot.py` - основной файл бота
- `admin_panel.py` - административная панель
- `questions.py` - вопросы для интервью
- `ai_analyzer.py` - AI-анализ ответов
- `database.py` - работа с базой данных
- `models.py` - модели данных

## Поддержка
Подробная документация в `README.md` 
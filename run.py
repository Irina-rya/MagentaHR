#!/usr/bin/env python3
"""
Скрипт запуска HR-бота
Использование: python run.py
"""

import os
import sys
from pathlib import Path

def check_environment():
    """Проверка окружения и конфигурации"""
    print("🔍 Проверка окружения...")
    
    # Проверяем наличие .env файла
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ Файл .env не найден!")
        print("📝 Создайте файл .env со следующими переменными:")
        print("   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here")
        print("   OPENAI_API_KEY=your_openai_api_key_here")
        print("   LOG_LEVEL=INFO")
        return False
    
    # Загружаем переменные из .env файла
    from dotenv import load_dotenv
    load_dotenv()
    
    # Проверяем переменные окружения
    required_vars = ["TELEGRAM_BOT_TOKEN", "OPENAI_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Отсутствуют переменные окружения: {', '.join(missing_vars)}")
        return False
    
    print("✅ Окружение настроено корректно")
    return True

def check_dependencies():
    """Проверка зависимостей"""
    print("📦 Проверка зависимостей...")
    
    try:
        import telegram
        import openai
        import pydantic
        import dotenv
        print("✅ Все зависимости установлены")
        return True
    except ImportError as e:
        print(f"❌ Отсутствует зависимость: {e}")
        print("💡 Установите зависимости: pip install -r requirements.txt")
        return False

def main():
    """Основная функция"""
    print("🤖 Запуск HR-бота для компании Маджента")
    print("=" * 50)
    
    # Проверяем окружение
    if not check_environment():
        sys.exit(1)
    
    # Проверяем зависимости
    if not check_dependencies():
        sys.exit(1)
    
    print("\n🚀 Запуск бота...")
    print("💡 Для остановки нажмите Ctrl+C")
    print("=" * 50)
    
    try:
        # Импортируем и запускаем бота
        from bot import HRBot
        bot = HRBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        print(f"\n❌ Ошибка запуска: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
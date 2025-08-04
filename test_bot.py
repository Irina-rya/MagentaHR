#!/usr/bin/env python3
"""
Тестирование HR-бота
Запуск: python test_bot.py
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import Candidate, Interview, Answer, Position, InterviewStatus
from questions import get_questions_for_position, get_question_by_id
from database import Database
from ai_analyzer import AIAnalyzer
from config import Config

class TestHRBot(unittest.TestCase):
    """Тесты для HR-бота"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        # Используем тестовую базу данных
        self.test_db_path = "test_hrbot.db"
        self.db = Database(self.test_db_path)
        
        # Создаем тестового кандидата
        self.test_candidate = Candidate(
            user_id=123456789,
            username="test_user",
            first_name="Тест",
            last_name="Пользователь"
        )
    
    def tearDown(self):
        """Очистка после каждого теста"""
        # Удаляем тестовую базу данных
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def test_candidate_creation(self):
        """Тест создания кандидата"""
        self.assertEqual(self.test_candidate.user_id, 123456789)
        self.assertEqual(self.test_candidate.username, "test_user")
        self.assertEqual(self.test_candidate.first_name, "Тест")
        self.assertEqual(self.test_candidate.last_name, "Пользователь")
    
    def test_save_and_get_candidate(self):
        """Тест сохранения и получения кандидата из БД"""
        # Сохраняем кандидата
        success = self.db.save_candidate(self.test_candidate)
        self.assertTrue(success)
        
        # Получаем кандидата
        retrieved_candidate = self.db.get_candidate(123456789)
        self.assertIsNotNone(retrieved_candidate)
        self.assertEqual(retrieved_candidate.user_id, self.test_candidate.user_id)
        self.assertEqual(retrieved_candidate.username, self.test_candidate.username)
    
    def test_interview_creation(self):
        """Тест создания интервью"""
        interview = Interview(
            candidate_id=123456789,
            position=Position.SALES,
            status=InterviewStatus.STARTED
        )
        
        self.assertEqual(interview.candidate_id, 123456789)
        self.assertEqual(interview.position, Position.SALES)
        self.assertEqual(interview.status, InterviewStatus.STARTED)
        self.assertEqual(interview.current_question_index, 0)
    
    def test_save_and_get_interview(self):
        """Тест сохранения и получения интервью из БД"""
        interview = Interview(
            candidate_id=123456789,
            position=Position.SALES,
            status=InterviewStatus.STARTED
        )
        
        # Сохраняем интервью
        interview_id = self.db.save_interview(interview)
        self.assertGreater(interview_id, 0)
        
        # Получаем интервью
        retrieved_interview = self.db.get_interview(interview_id)
        self.assertIsNotNone(retrieved_interview)
        self.assertEqual(retrieved_interview.candidate_id, interview.candidate_id)
        self.assertEqual(retrieved_interview.position, interview.position)
    
    def test_questions_for_sales_position(self):
        """Тест получения вопросов для позиции продаж"""
        questions = get_questions_for_position(Position.SALES)
        self.assertGreater(len(questions), 0)
        
        # Проверяем, что все вопросы для продаж
        for question in questions:
            self.assertEqual(question.position, Position.SALES)
    
    def test_questions_for_qa_position(self):
        """Тест получения вопросов для позиции тестирования"""
        questions = get_questions_for_position(Position.QA)
        self.assertGreater(len(questions), 0)
        
        # Проверяем, что все вопросы для тестирования
        for question in questions:
            self.assertEqual(question.position, Position.QA)
    
    def test_get_question_by_id(self):
        """Тест получения вопроса по ID"""
        # Получаем первый вопрос для продаж
        sales_questions = get_questions_for_position(Position.SALES)
        if sales_questions:
            first_question = sales_questions[0]
            
            # Ищем вопрос по ID
            found_question = get_question_by_id(first_question.id)
            self.assertIsNotNone(found_question)
            self.assertEqual(found_question.id, first_question.id)
            self.assertEqual(found_question.text, first_question.text)
    
    def test_answer_creation(self):
        """Тест создания ответа"""
        answer = Answer(
            question_id="sales_1",
            answer_text="У меня есть опыт в продажах B2B продуктов"
        )
        
        self.assertEqual(answer.question_id, "sales_1")
        self.assertEqual(answer.answer_text, "У меня есть опыт в продажах B2B продуктов")
        self.assertEqual(len(answer.follow_up_answers), 0)
    
    def test_save_and_get_answers(self):
        """Тест сохранения и получения ответов"""
        # Создаем интервью
        interview = Interview(
            candidate_id=123456789,
            position=Position.SALES,
            status=InterviewStatus.STARTED
        )
        interview_id = self.db.save_interview(interview)
        
        # Создаем ответ
        answer = Answer(
            question_id="sales_1",
            answer_text="У меня есть опыт в продажах B2B продуктов"
        )
        
        # Сохраняем ответ
        success = self.db.save_answer(interview_id, answer)
        self.assertTrue(success)
        
        # Получаем ответы
        answers = self.db.get_interview_answers(interview_id)
        self.assertEqual(len(answers), 1)
        self.assertEqual(answers[0].question_id, answer.question_id)
        self.assertEqual(answers[0].answer_text, answer.answer_text)
    
    def test_interview_progress(self):
        """Тест прогресса интервью"""
        interview = Interview(
            candidate_id=123456789,
            position=Position.SALES,
            status=InterviewStatus.STARTED
        )
        
        # Добавляем ответ
        answer = Answer(
            question_id="sales_1",
            answer_text="Тестовый ответ"
        )
        
        initial_index = interview.current_question_index
        interview.add_answer(answer)
        
        # Проверяем, что индекс увеличился
        self.assertEqual(interview.current_question_index, initial_index + 1)
        self.assertEqual(len(interview.answers), 1)
    
    @patch('ai_analyzer.openai.OpenAI')
    def test_ai_analyzer_initialization(self, mock_openai):
        """Тест инициализации AI анализатора"""
        # Мокаем OpenAI клиент
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Создаем анализатор
        analyzer = AIAnalyzer()
        
        # Проверяем, что клиент создан
        mock_openai.assert_called_once()
    
    def test_config_validation(self):
        """Тест валидации конфигурации"""
        # Сохраняем оригинальные значения
        original_token = Config.TELEGRAM_BOT_TOKEN
        original_api_key = Config.OPENAI_API_KEY
        
        # Тестируем с пустыми значениями
        Config.TELEGRAM_BOT_TOKEN = None
        Config.OPENAI_API_KEY = None
        
        with self.assertRaises(ValueError):
            Config.validate()
        
        # Восстанавливаем значения
        Config.TELEGRAM_BOT_TOKEN = original_token
        Config.OPENAI_API_KEY = original_api_key
    
    def test_position_enum(self):
        """Тест enum позиций"""
        self.assertEqual(Position.SALES.value, "sales")
        self.assertEqual(Position.QA.value, "qa")
        
        # Тест создания из строки
        sales_position = Position("sales")
        qa_position = Position("qa")
        
        self.assertEqual(sales_position, Position.SALES)
        self.assertEqual(qa_position, Position.QA)
    
    def test_interview_status_enum(self):
        """Тест enum статусов интервью"""
        self.assertEqual(InterviewStatus.STARTED.value, "started")
        self.assertEqual(InterviewStatus.IN_PROGRESS.value, "in_progress")
        self.assertEqual(InterviewStatus.COMPLETED.value, "completed")
        self.assertEqual(InterviewStatus.TIMEOUT.value, "timeout")

class TestQuestionContent(unittest.TestCase):
    """Тесты содержания вопросов"""
    
    def test_sales_questions_content(self):
        """Тест содержания вопросов для продаж"""
        questions = get_questions_for_position(Position.SALES)
        
        # Проверяем, что есть вопросы по всем категориям
        categories = set()
        for question in questions:
            categories.add(question.category)
        
        expected_categories = {
            "Общая мотивация и опыт",
            "Навыки работы с клиентами", 
            "Процесс продаж",
            "Результаты"
        }
        
        self.assertEqual(categories, expected_categories)
    
    def test_qa_questions_content(self):
        """Тест содержания вопросов для тестирования"""
        questions = get_questions_for_position(Position.QA)
        
        # Проверяем, что есть вопросы по всем категориям
        categories = set()
        for question in questions:
            categories.add(question.category)
        
        expected_categories = {
            "Общая мотивация и опыт",
            "Технические навыки",
            "Инструменты",
            "Процессы и взаимодействие"
        }
        
        self.assertEqual(categories, expected_categories)
    
    def test_follow_up_questions(self):
        """Тест уточняющих вопросов"""
        questions = get_questions_for_position(Position.SALES)
        
        for question in questions:
            # Проверяем, что у каждого вопроса есть уточняющие вопросы
            self.assertIsInstance(question.follow_up_questions, list)
            self.assertLessEqual(len(question.follow_up_questions), 2)  # Максимум 2 уточняющих вопроса

def run_tests():
    """Запуск всех тестов"""
    print("🧪 Запуск тестов HR-бота...")
    
    # Создаем тестовый набор
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Добавляем тесты
    suite.addTests(loader.loadTestsFromTestCase(TestHRBot))
    suite.addTests(loader.loadTestsFromTestCase(TestQuestionContent))
    
    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Выводим результат
    if result.wasSuccessful():
        print("\n✅ Все тесты прошли успешно!")
        return True
    else:
        print(f"\n❌ Тесты не прошли. Ошибок: {len(result.failures)}")
        return False

if __name__ == "__main__":
    # Проверяем, что мы в правильной директории
    if not os.path.exists("bot.py"):
        print("❌ Ошибка: Запустите тесты из директории HRBot")
        sys.exit(1)
    
    # Запускаем тесты
    success = run_tests()
    sys.exit(0 if success else 1) 
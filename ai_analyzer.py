import openai
from typing import List, Dict, Any
from models import Interview, Answer, InterviewAnalysis, Position
from config import Config
import json

class AIAnalyzer:
    """AI analyzer for interview responses"""
    
    def __init__(self):
        openai.api_key = Config.OPENAI_API_KEY
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
    
    def analyze_resume(self, resume_text: str, position: Position) -> Dict[str, Any]:
        """Analyze candidate's resume"""
        prompt = f"""
        Проанализируйте резюме кандидата на позицию {position.value} и извлеките следующую информацию:
        
        Резюме:
        {resume_text}
        
        Пожалуйста, предоставьте анализ в формате JSON со следующими полями:
        {{
            "experience_years": "количество лет опыта",
            "key_skills": ["список ключевых навыков"],
            "experience_level": "junior/middle/senior",
            "relevant_experience": "релевантный опыт",
            "education": "образование",
            "summary": "краткое резюме профиля"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            print(f"Error analyzing resume: {e}")
            return {
                "experience_years": "неизвестно",
                "key_skills": [],
                "experience_level": "unknown",
                "relevant_experience": "не указано",
                "education": "не указано",
                "summary": "Ошибка анализа резюме"
            }
    
    def analyze_interview(self, interview: Interview, answers: List[Answer]) -> InterviewAnalysis:
        """Analyze complete interview"""
        
        # Prepare answers text for analysis
        answers_text = ""
        for i, answer in enumerate(answers, 1):
            answers_text += f"Вопрос {i}: {answer.answer_text}\n"
            if answer.follow_up_answers:
                for j, follow_up in enumerate(answer.follow_up_answers, 1):
                    answers_text += f"  Уточнение {j}: {follow_up}\n"
            answers_text += "\n"
        
        prompt = f"""
        Проанализируйте ответы кандидата на позицию {interview.position.value} и предоставьте детальную оценку.
        
        Ответы кандидата:
        {answers_text}
        
        Пожалуйста, проанализируйте:
        1. Глубину и релевантность ответов
        2. Логику и последовательность мышления
        3. Стиль речи и коммуникативные навыки
        4. Оригинальность ответов (нет ли шаблонных формулировок)
        5. Оценку по компетенциям
        
        Предоставьте результат в формате JSON:
        {{
            "overall_score": 0.85,
            "competency_scores": {{
                "experience": 0.8,
                "technical_skills": 0.7,
                "communication": 0.9,
                "problem_solving": 0.75
            }},
            "communication_skills": "описание стиля общения",
            "experience_level": "junior/middle/senior",
            "originality_score": 0.9,
            "recommendations": ["список рекомендаций"],
            "hr_recommendation": "recommended/needs_clarification/not_recommended",
            "summary": "краткое резюме интервью"
        }}
        
        Оценки должны быть от 0 до 1, где 1 - отлично.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return InterviewAnalysis(
                candidate_id=interview.candidate_id,
                position=interview.position,
                overall_score=result["overall_score"],
                competency_scores=result["competency_scores"],
                communication_skills=result["communication_skills"],
                experience_level=result["experience_level"],
                originality_score=result["originality_score"],
                recommendations=result["recommendations"],
                hr_recommendation=result["hr_recommendation"],
                summary=result["summary"]
            )
            
        except Exception as e:
            print(f"Error analyzing interview: {e}")
            return InterviewAnalysis(
                candidate_id=interview.candidate_id,
                position=interview.position,
                overall_score=0.5,
                competency_scores={"experience": 0.5, "technical_skills": 0.5, "communication": 0.5, "problem_solving": 0.5},
                communication_skills="Ошибка анализа",
                experience_level="unknown",
                originality_score=0.5,
                recommendations=["Ошибка анализа интервью"],
                hr_recommendation="needs_clarification",
                summary="Произошла ошибка при анализе интервью"
            )
    
    def check_answer_quality(self, answer: str, question: str) -> Dict[str, Any]:
        """Check if answer needs follow-up questions"""
        prompt = f"""
        Оцените качество ответа кандидата на вопрос и определите, нужны ли уточняющие вопросы.
        
        Вопрос: {question}
        Ответ: {answer}
        
        Проанализируйте:
        1. Полнота ответа (0-1)
        2. Конкретность (0-1)
        3. Релевантность (0-1)
        4. Нужны ли уточняющие вопросы (true/false)
        
        Ответ в формате JSON:
        {{
            "completeness": 0.7,
            "specificity": 0.6,
            "relevance": 0.8,
            "needs_follow_up": true,
            "reason": "причина для уточняющего вопроса"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error checking answer quality: {e}")
            return {
                "completeness": 0.5,
                "specificity": 0.5,
                "relevance": 0.5,
                "needs_follow_up": False,
                "reason": "Ошибка анализа"
            }
    
    def generate_follow_up_question(self, original_question: str, answer: str, available_follow_ups: List[str]) -> str:
        """Generate appropriate follow-up question"""
        prompt = f"""
        На основе ответа кандидата сгенерируйте подходящий уточняющий вопрос.
        
        Оригинальный вопрос: {original_question}
        Ответ кандидата: {answer}
        Доступные уточняющие вопросы: {available_follow_ups}
        
        Выберите наиболее подходящий уточняющий вопрос из списка или сгенерируйте новый, если ни один не подходит.
        Верните только текст вопроса.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating follow-up question: {e}")
            return available_follow_ups[0] if available_follow_ups else "Можете рассказать подробнее?" 
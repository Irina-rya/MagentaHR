import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from telegram.constants import ParseMode

from config import Config
from models import Candidate, Interview, Answer, Position, InterviewStatus, InterviewAnalysis
from database import Database
from questions import get_questions_for_position, Question, get_contact_questions_for_position, get_professional_questions_for_position
from ai_analyzer import AIAnalyzer

# Configure logging with more detailed format
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    level=getattr(logging, Config.LOG_LEVEL),
    handlers=[
        logging.FileHandler('hrbot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HRBot:
    """Main HR Bot class"""
    
    def __init__(self):
        self.db = Database()
        self.ai_analyzer = AIAnalyzer()
        self.active_interviews: Dict[int, Tuple[int, Interview]] = {}  # user_id -> (interview_id, interview)
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        # Create or get candidate
        candidate = Candidate(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        self.db.save_candidate(candidate)
        
        welcome_message = f"""
Здравствуйте! 👋  
Я — HR-бот компании **{Config.COMPANY_NAME}**.  
Готов провести короткое собеседование (5–7 минут), чтобы лучше узнать вас.

🔗 Прежде чем начнем:
- Ознакомьтесь с нами на сайте [{Config.COMPANY_WEBSITE}]({Config.COMPANY_WEBSITE})
- Подпишитесь на вакансии: [{Config.CAREERS_CHANNEL}](https://t.me/{Config.CAREERS_CHANNEL.replace('@', '')})

Готовы? Давайте начнем!
        """
        
        keyboard = [
            [InlineKeyboardButton("Да, готов начать! 🚀", callback_data="start_interview")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "start_interview":
            await self.choose_position(query, context)
        elif query.data.startswith("position_"):
            position = query.data.split("_")[1]
            await self.ask_for_resume(query, context, Position(position))
        elif query.data == "with_resume":
            await self.ask_for_resume_upload(query, context)
        elif query.data == "without_resume":
            await self.start_interview(query, context, context.user_data.get('selected_position'))
        elif query.data == "skip_resume":
            await self.start_interview(query, context, context.user_data.get('selected_position'))
        elif query.data == "upload_resume_again":
            await self.ask_for_resume_upload(query, context)
        elif query.data == "continue_without_resume":
            await self.start_interview(query, context, context.user_data.get('selected_position'))
        elif query.data == "start_interview_after_resume":
            await self.start_interview(query, context, context.user_data.get('selected_position'))
    
    async def ask_for_resume(self, query, context: ContextTypes.DEFAULT_TYPE, position: Position):
        """Ask if candidate wants to upload resume after position selection"""
        # Save selected position
        context.user_data['selected_position'] = position
        
        position_name = "Сотрудник отдела продаж" if position == Position.SALES else "Тестировщик ПО"
        
        message = f"""
🎯 **Выбрана позиция: {position_name}**

📋 Хотите загрузить резюме? Это поможет мне:
• Адаптировать вопросы под ваш опыт
• Отметить релевантные навыки для позиции
• Провести более персонализированное собеседование

(Можно пропустить — мы проведем стандартное собеседование)
        """
        
        keyboard = [
            [InlineKeyboardButton("Да, загружу резюме 📄", callback_data="with_resume")],
            [InlineKeyboardButton("Пропустить, начнем без резюме ⏭️", callback_data="without_resume")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
        logger.info(f"User {query.from_user.id} selected position {position.value}, asking for resume")
    
    async def ask_for_resume_upload(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Ask to upload resume"""
        message = """
Пожалуйста, отправьте ваше резюме в виде текста или файла.

Вы можете:
- Скопировать текст резюме в сообщение
- Отправить файл (PDF, DOC, DOCX)
- Или нажать "Пропустить" для продолжения без резюме
        """
        
        keyboard = [
            [InlineKeyboardButton("Пропустить резюме ⏭️", callback_data="skip_resume")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
        
        # Set state to wait for resume
        context.user_data['waiting_for_resume'] = True
    
    async def choose_position(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Show position selection"""
        message = """
Пожалуйста, выберите, на какую позицию вы проходите собеседование:
        """
        
        keyboard = [
            [InlineKeyboardButton("1️⃣ Сотрудник отдела продаж", callback_data="position_sales")],
            [InlineKeyboardButton("2️⃣ Тестировщик ПО", callback_data="position_qa")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    async def start_interview(self, query, context: ContextTypes.DEFAULT_TYPE, position: Position):
        """Start interview for selected position"""
        # Handle both Update and CallbackQuery objects
        if hasattr(query, 'from_user'):
            user_id = query.from_user.id
        elif hasattr(query, 'effective_user'):
            user_id = query.effective_user.id
        else:
            logger.error("Cannot determine user_id from query object")
            return
        
        # Update candidate with position
        candidate = self.db.get_candidate(user_id)
        if candidate:
            candidate.position = position
            self.db.save_candidate(candidate)
        
        # Create new interview
        interview = Interview(
            candidate_id=user_id,
            position=position,
            status=InterviewStatus.STARTED
        )
        
        interview_id = self.db.save_interview(interview)
        self.active_interviews[user_id] = (interview_id, interview)
        
        # Get all questions (contact + professional)
        questions = get_questions_for_position(position)
        if questions:
            first_question = questions[0]
            
            # Format first question (contact introduction)
            message = f"""
{first_question.text}
            """
            
            # Handle different types of query objects
            if hasattr(query, 'edit_message_text'):
                await query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN)
            elif hasattr(query, 'message'):
                await query.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            else:
                logger.error("Cannot send message - unknown query type")
                return
            
            # Set state to wait for answer
            context.user_data['waiting_for_answer'] = True
            context.user_data['current_question_id'] = first_question.id
        else:
            error_message = "Ошибка: вопросы для данной позиции не найдены."
            if hasattr(query, 'edit_message_text'):
                await query.edit_message_text(error_message)
            elif hasattr(query, 'message'):
                await query.message.reply_text(error_message)
    
    async def show_resume_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE, analysis: dict, position: Position):
        """Show resume analysis to user and start interview"""
        try:
            experience_level = analysis.get('experience_level', 'unknown')
            recommendations = analysis.get('recommendations', [])
            
            message = f"""
✅ **Резюме проанализировано!**

📊 **Уровень опыта:** {experience_level}
🎯 **Позиция:** {position.value.upper()}

💡 **Рекомендации:**
"""
            
            if recommendations:
                for i, rec in enumerate(recommendations[:3], 1):
                    message += f"{i}. {rec}\n"
            else:
                message += "• Готовы к собеседованию\n"
            
            message += f"""
🎯 **Готовы ли вы перейти к собеседованию?**

⏱️ **Время:** примерно 5-7 минут
📝 **Вопросов:** {len(get_questions_for_position(position)) - 5} профессиональных вопросов

🚀 **Удачи!** Мы верим в ваш успех! 💪
            """
            
            keyboard = [
                [InlineKeyboardButton("✅ Да, готов начать!", callback_data="start_interview_after_resume")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error showing resume analysis: {e}")
            # Fallback to simple start
            await update.message.reply_text(
                "✅ **Резюме сохранено!**\n\n"
                "🎯 **Готовы ли вы перейти к собеседованию?**\n\n"
                "🚀 **Удачи!** Мы верим в ваш успех! 💪",
                parse_mode=ParseMode.MARKDOWN
            )
            # Start interview after a short delay
            await asyncio.sleep(2)
            await self.start_interview(update, context, position)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        user_id = update.effective_user.id
        text = update.message.text
        
        # Check if waiting for resume
        if context.user_data.get('waiting_for_resume'):
            await self.handle_resume_upload(update, context, text)
            return
        
        # Check if waiting for follow-up answer
        if context.user_data.get('waiting_for_follow_up'):
            await self.handle_follow_up_answer(update, context, text)
            return
        
        # Check if waiting for answer
        if context.user_data.get('waiting_for_answer'):
            await self.handle_answer(update, context, text)
            return
        
        # Default response
        await update.message.reply_text(
            "Используйте /start для начала собеседования или /help для справки."
        )
    
    async def handle_resume_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Handle resume text upload"""
        user_id = update.effective_user.id
        position = context.user_data.get('selected_position')
        
        logger.info(f"User {user_id} uploaded resume: {len(text)} characters for position {position}")
        
        # Check if resume looks valid (not just random text)
        if len(text) < 50:
            keyboard = [
                [InlineKeyboardButton("📄 Загрузить резюме заново", callback_data="upload_resume_again")],
                [InlineKeyboardButton("🚀 Продолжить без резюме", callback_data="continue_without_resume")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "⚠️ **Похоже, что загруженный текст слишком короткий для резюме.**\n\n"
                "Пожалуйста, загрузите полное резюме или продолжите собеседование без него.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            return
        
        # Check for common resume keywords
        resume_keywords = ['опыт', 'образование', 'навыки', 'проекты', 'работа', 'компания', 'должность']
        text_lower = text.lower()
        keyword_count = sum(1 for keyword in resume_keywords if keyword in text_lower)
        
        if keyword_count < 2:
            keyboard = [
                [InlineKeyboardButton("📄 Загрузить резюме заново", callback_data="upload_resume_again")],
                [InlineKeyboardButton("🚀 Продолжить без резюме", callback_data="continue_without_resume")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "⚠️ **Загруженный текст не похож на резюме.**\n\n"
                "Пожалуйста, загрузите настоящее резюме или продолжите собеседование без него.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            return
        
        # Save resume to candidate
        candidate = self.db.get_candidate(user_id)
        if candidate:
            candidate.resume_text = text
            candidate.position = position
            self.db.save_candidate(candidate)
            logger.info(f"Resume saved for user {user_id}")
            
            # Analyze resume for selected position
            if position:
                try:
                    logger.info(f"Analyzing resume for position {position}")
                    analysis = self.ai_analyzer.analyze_resume(text, position)
                    candidate.experience_level = analysis.get('experience_level', 'unknown')
                    self.db.save_candidate(candidate)
                    
                    # Store analysis for interview adaptation
                    context.user_data['resume_analysis'] = analysis
                    
                    logger.info(f"Resume analysis completed for user {user_id}: {analysis.get('experience_level', 'unknown')}")
                    
                    # Show resume analysis to user
                    await self.show_resume_analysis(update, context, analysis, position)
                    
                except Exception as e:
                    logger.error(f"Error analyzing resume for user {user_id}: {e}")
                    # Continue with interview even if analysis fails
                    await update.message.reply_text(
                        "✅ **Резюме сохранено!**\n\n"
                        "⚠️ Не удалось проанализировать резюме, но собеседование будет проведено.\n\n"
                        "🚀 Начинаем собеседование...",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    # Clear resume waiting state before starting interview
                    context.user_data.pop('waiting_for_resume', None)
                    await self.start_interview(update, context, position)
            else:
                await update.message.reply_text("Ошибка: позиция не выбрана. Начните заново с /start")
        else:
            await update.message.reply_text("Ошибка: кандидат не найден. Начните заново с /start")
        
        # Clear resume waiting state
        context.user_data.pop('waiting_for_resume', None)
    
    async def handle_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Handle interview answer"""
        user_id = update.effective_user.id
        logger.info(f"User {user_id} provided answer: {len(text)} characters")
        
        if user_id not in self.active_interviews:
            logger.warning(f"User {user_id} tried to answer without active interview")
            await update.message.reply_text("Собеседование не найдено. Используйте /start для начала.")
            return
        
        interview_id, interview = self.active_interviews[user_id]
        questions = get_questions_for_position(interview.position)
        
        if interview.current_question_index >= len(questions):
            logger.info(f"Interview completed for user {user_id}")
            await self.complete_interview(update, context, user_id, interview)
            return
        
        current_question = questions[interview.current_question_index]
        logger.info(f"Processing answer for question {current_question.id} (user {user_id})")
        
        # Handle contact questions specifically (no follow-up questions)
        if current_question.category == "contact" or current_question.category == "introduction":
            await self.handle_contact_answer(update, context, text, current_question, user_id, interview_id, interview)
            return
        
        # Save answer for regular questions
        answer = Answer(
            question_id=current_question.id,
            answer_text=text
        )
        
        # Check if answer needs follow-up (simplified logic to avoid delays)
        needs_follow_up = len(text) < 50 or interview.follow_up_count < 1
        
        if needs_follow_up and interview.follow_up_count < Config.MAX_FOLLOW_UP_QUESTIONS:
            # Ask follow-up question
            follow_up_question = current_question.follow_up_questions[0] if current_question.follow_up_questions else "Можете рассказать подробнее?"
            
            message = f"""
**Уточняющий вопрос:**

{follow_up_question}
            """
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
            # Set state to wait for follow-up answer
            context.user_data['waiting_for_follow_up'] = True
            context.user_data['current_answer'] = answer
            context.user_data['follow_up_question'] = follow_up_question
            
            logger.info(f"Follow-up question sent to user {user_id}")
            
        else:
            # Save answer and move to next question
            self.db.save_answer(interview_id, answer)
            interview.add_answer(answer)
            self.db.update_interview(interview, interview_id)
            
            logger.info(f"Answer saved and moving to next question for user {user_id}")
            await self.ask_next_question(update, context, interview, questions)
    
    async def handle_contact_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, question: Question, user_id: int, interview_id: int, interview: Interview):
        """Handle contact information answers"""
        candidate = self.db.get_candidate(user_id)
        if not candidate:
            logger.error(f"Candidate not found for user {user_id}")
            await update.message.reply_text("Ошибка: кандидат не найден. Пожалуйста, начните заново.")
            return
        
        # Save contact information based on question type
        if question.id == "contact_intro":
            # Validate name and position
            text_lower = text.lower().strip()
            if len(text) < 10:
                await update.message.reply_text("Пожалуйста, представьтесь более подробно: укажите ваше имя, фамилию и желаемую позицию.")
                return
            
            # Extract name and position (simple validation)
            words = text.split()
            if len(words) < 2:
                await update.message.reply_text("Пожалуйста, укажите ваше имя, фамилию и желаемую позицию.")
                return
            
            # Save name to candidate
            candidate.first_name = words[0].title()
            if len(words) > 1:
                candidate.last_name = words[1].title()
            
        elif question.id == "contact_phone":
            # Basic phone validation
            phone = text.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
            if phone.startswith("8") and len(phone) == 11:
                phone = "+7" + phone[1:]
            elif phone.startswith("+7") and len(phone) == 12:
                pass  # Already in correct format
            else:
                await update.message.reply_text("Пожалуйста, укажите корректный номер телефона в формате +7XXXXXXXXXX или 8XXXXXXXXXX")
                return
            candidate.phone = phone
            
        elif question.id == "contact_email":
            # Basic email validation
            if "@" not in text or "." not in text:
                await update.message.reply_text("Пожалуйста, укажите корректный email адрес")
                return
            candidate.email = text.strip().lower()
            
        elif question.id == "contact_portfolio":
            if text.lower().strip() != "нет":
                candidate.portfolio = text.strip()
            else:
                candidate.portfolio = "не указан"
        
        # Save candidate with updated contact info
        self.db.save_candidate(candidate)
        
        # Save answer to interview
        answer = Answer(
            question_id=question.id,
            answer_text=text
        )
        self.db.save_answer(interview_id, answer)
        interview.add_answer(answer)
        self.db.update_interview(interview, interview_id)
        
        logger.info(f"Contact answer saved for user {user_id}, moving to next question")
        await self.ask_next_question(update, context, interview, get_questions_for_position(interview.position))
    
    async def handle_follow_up_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Handle follow-up answer"""
        user_id = update.effective_user.id
        logger.info(f"User {user_id} provided follow-up answer: {len(text)} characters")
        
        if user_id not in self.active_interviews:
            logger.warning(f"User {user_id} tried to provide follow-up without active interview")
            await update.message.reply_text("Собеседование не найдено.")
            return
        
        interview_id, interview = self.active_interviews[user_id]
        current_answer = context.user_data.get('current_answer')
        
        if current_answer:
            current_answer.follow_up_answers.append(text)
            interview.follow_up_count += 1
            
            # Save answer and move to next question
            self.db.save_answer(interview_id, current_answer)
            interview.add_answer(current_answer)
            self.db.update_interview(interview, interview_id)
            
            logger.info(f"Follow-up answer saved for user {user_id}, moving to next question")
            
            questions = get_questions_for_position(interview.position)
            await self.ask_next_question(update, context, interview, questions)
        else:
            logger.error(f"No current answer found for user {user_id} follow-up")
            await update.message.reply_text("Ошибка обработки ответа. Пожалуйста, начните собеседование заново.")
        
        # Clear follow-up state
        context.user_data.pop('waiting_for_follow_up', None)
        context.user_data.pop('current_answer', None)
        context.user_data.pop('follow_up_question', None)
    
    async def ask_next_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, interview: Interview, questions: list):
        """Ask next question in interview"""
        if interview.current_question_index >= len(questions):
            logger.info(f"All questions completed for user {interview.candidate_id}")
            await self.complete_interview(update, context, interview.candidate_id, interview)
            return
        
        next_question = questions[interview.current_question_index]
        
        # Check if this is the transition from contact to professional questions
        contact_questions = get_contact_questions_for_position(interview.position)
        professional_questions = get_professional_questions_for_position(interview.position)
        
        # If we're transitioning from contact to professional questions
        if (interview.current_question_index == len(contact_questions) and 
            next_question.id == professional_questions[0].id if professional_questions else None):
            
            # Show transition message
            transition_message = f"""
🎯 **Отлично! Контактные данные собраны.**

Теперь переходим к профессиональной части собеседования.

📋 **Позиция:** {interview.position.value.upper()}
⏱️ **Время:** примерно 5-7 минут
📝 **Вопросов:** {len(professional_questions)}

Готовы? Начинаем!
            """
            
            await update.message.reply_text(transition_message, parse_mode=ParseMode.MARKDOWN)
            
            # Wait a moment before asking the first professional question
            await asyncio.sleep(2)
        
        # Format message based on question category
        if next_question.category == "introduction":
            message = f"""
{next_question.text}
            """
        else:
            message = f"""
📝 **Вопрос {interview.current_question_index + 1} из {len(questions)}**

**{next_question.text}**

💡 Отвечайте подробно и по существу. Это поможет мне лучше понять ваш опыт и навыки.
            """
        
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
        
        # Set state to wait for answer
        context.user_data['waiting_for_answer'] = True
        context.user_data['current_question_id'] = next_question.id
        
        logger.info(f"Question {next_question.id} sent to user {interview.candidate_id}")
    
    async def send_interview_results_to_hr(self, candidate: Candidate, interview: Interview, analysis: dict):
        """Send interview results to HR specialist"""
        try:
            # Get all answers for the interview
            interview_id, _ = self.active_interviews.get(candidate.user_id, (None, None))
            if not interview_id:
                logger.error(f"Interview ID not found for user {candidate.user_id}")
                return
            
            answers = self.db.get_interview_answers(interview_id)
            
            # Format results message
            message = f"""
📊 **Новые результаты собеседования**

👤 **Кандидат:** {candidate.first_name} {candidate.last_name}
📱 **Телефон:** {candidate.phone or 'не указан'}
📧 **Email:** {candidate.email or 'не указан'}
💼 **Портфолио:** {candidate.portfolio or 'не указан'}
🎯 **Позиция:** {interview.position.value.upper()}
📅 **Дата:** {interview.started_at.strftime('%d.%m.%Y %H:%M')}

📈 **Результаты анализа:**
• Общий балл: {analysis.get('overall_score', 'N/A')}/10
• Рекомендация: {analysis.get('hr_recommendation', 'N/A')}
• Уровень опыта: {analysis.get('experience_level', 'N/A')}

💡 **Краткое резюме:**
{analysis.get('summary', 'Недоступно')}

🔗 **Действия:** Связаться с кандидатом для дальнейших шагов
            """
            
            # Send to HR specialist
            await self.application.bot.send_message(
                chat_id=Config.RESULTS_RECIPIENT,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.info(f"Interview results sent to HR for user {candidate.user_id}")
            
        except Exception as e:
            logger.error(f"Error sending interview results to HR: {e}")
    
    async def complete_interview(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, interview: Interview):
        """Complete interview and provide analysis"""
        # Get interview_id from active_interviews
        if user_id not in self.active_interviews:
            await update.message.reply_text("Ошибка: собеседование не найдено.")
            return
            
        interview_id, _ = self.active_interviews[user_id]
        
        # Mark interview as completed
        interview.status = InterviewStatus.COMPLETED
        interview.completed_at = datetime.now()
        self.db.update_interview(interview, interview_id)
        
        # Get all answers
        answers = self.db.get_interview_answers(interview_id)
        
        if not answers:
            await update.message.reply_text("Ошибка: ответы не найдены.")
            return
        
        # Prepare answers for analysis
        answers_text = "\n\n".join([f"Вопрос: {answer.question_id}\nОтвет: {answer.answer_text}" for answer in answers])
        
        try:
            # Analyze interview
            analysis = self.ai_analyzer.analyze_interview(answers_text, interview.position)
            
            # Save analysis
            interview_analysis = InterviewAnalysis(
                candidate_id=user_id,
                position=interview.position,
                overall_score=analysis.get('overall_score', 0.0),
                competency_scores=analysis.get('competency_scores', {}),
                communication_skills=analysis.get('communication_skills', 'unknown'),
                experience_level=analysis.get('experience_level', 'unknown'),
                originality_score=analysis.get('originality_score', 0.0),
                recommendations=analysis.get('recommendations', []),
                hr_recommendation=analysis.get('hr_recommendation', 'needs_clarification'),
                summary=analysis.get('summary', 'Анализ недоступен')
            )
            
            self.db.save_analysis(interview_analysis)
            
            # Send results to HR
            candidate = self.db.get_candidate(user_id)
            if candidate:
                await self.send_interview_results_to_hr(candidate, interview, analysis)
            
            # Show results to candidate
            overall_score = analysis.get('overall_score', 0.0)
            hr_recommendation = analysis.get('hr_recommendation', 'needs_clarification')
            
            recommendation_text = {
                'recommended': '✅ **Рекомендуем к найму**',
                'needs_clarification': '🤔 **Требует дополнительного рассмотрения**',
                'not_recommended': '❌ **Не рекомендуется к найму**'
            }.get(hr_recommendation, '🤔 **Требует дополнительного рассмотрения**')
            
            message = f"""
🎉 **Собеседование завершено!**

📊 **Ваш результат:** {overall_score:.1f}/10
{recommendation_text}

💡 **Что дальше:**
• Мы свяжемся с вами в ближайшее время
• Ожидайте звонка от HR-специалиста
• Спасибо за участие!

🚀 **Удачи в дальнейшем!** 💪
            """
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error(f"Error analyzing interview: {e}")
            await update.message.reply_text(
                "✅ **Собеседование завершено!**\n\n"
                "Мы свяжемся с вами в ближайшее время.\n\n"
                "🚀 **Удачи!** 💪",
                parse_mode=ParseMode.MARKDOWN
            )
        
        # Remove from active interviews
        self.active_interviews.pop(user_id, None)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🤖 **HR-бот компании Маджента**

**Команды:**
/start - Начать собеседование
/help - Показать эту справку

**О процессе:**
1. Выберите позицию (продажи или тестирование)
2. Ответьте на вопросы (5-7 минут)
3. Получите результат и ждите звонка от HR

**Поддержка:**
Если возникли проблемы, обратитесь к HR-специалисту.
        """
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    def run(self):
        """Run the bot"""
        # Validate configuration
        Config.validate()
        
        # Create application
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        self.application = application # Assign application to self
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CallbackQueryHandler(self.handle_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Start the bot
        logger.info("Starting HR Bot...")
        application.run_polling()

if __name__ == "__main__":
    bot = HRBot()
    bot.run() 
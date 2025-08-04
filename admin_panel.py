import asyncio
import logging
from datetime import datetime
from typing import List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from telegram.constants import ParseMode

from config import Config
from models import InterviewAnalysis, Position
from database import Database

logger = logging.getLogger(__name__)

class AdminPanel:
    """Admin panel for HR specialists"""
    
    def __init__(self):
        self.db = Database()
        self.admin_users = set()  # Set of admin user IDs
        
    def add_admin(self, user_id: int):
        """Add admin user"""
        self.admin_users.add(user_id)
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in self.admin_users
    
    async def admin_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin command"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("У вас нет доступа к административной панели.")
            return
        
        message = """
🔧 **Административная панель HR-бота**

Выберите действие:
        """
        
        keyboard = [
            [InlineKeyboardButton("📊 Посмотреть результаты", callback_data="admin_results")],
            [InlineKeyboardButton("👥 Кандидаты по позициям", callback_data="admin_candidates")],
            [InlineKeyboardButton("📈 Статистика", callback_data="admin_stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    
    async def handle_admin_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin panel callbacks"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        if not self.is_admin(user_id):
            await query.edit_message_text("У вас нет доступа к административной панели.")
            return
        
        if query.data == "admin_results":
            await self.show_recent_results(query, context)
        elif query.data == "admin_candidates":
            await self.show_candidates_by_position(query, context)
        elif query.data == "admin_stats":
            await self.show_statistics(query, context)
        elif query.data.startswith("result_"):
            analysis_id = query.data.split("_")[1]
            await self.show_detailed_result(query, context, analysis_id)
        elif query.data.startswith("position_filter_"):
            position = query.data.split("_")[2]
            await self.show_results_by_position(query, context, Position(position))
        elif query.data == "back_to_admin":
            await self.admin_start(update, context)
    
    async def show_recent_results(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Show recent interview results"""
        # Get recent analyses from database
        analyses = self.get_recent_analyses(limit=10)
        
        if not analyses:
            message = "Пока нет результатов интервью."
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_admin")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup)
            return
        
        message = "📊 **Последние результаты интервью:**\n\n"
        
        keyboard = []
        for analysis in analyses:
            candidate = self.db.get_candidate(analysis.candidate_id)
            candidate_name = f"{candidate.first_name} {candidate.last_name}" if candidate else f"ID: {analysis.candidate_id}"
            
            status_emoji = "✅" if analysis.hr_recommendation == "recommended" else "⚠️" if analysis.hr_recommendation == "needs_clarification" else "❌"
            
            message += f"{status_emoji} **{candidate_name}** ({analysis.position.value.upper()})\n"
            message += f"   Оценка: {analysis.overall_score:.2f}/1.0\n"
            message += f"   Рекомендация: {self.get_recommendation_text(analysis.hr_recommendation)}\n\n"
            
            keyboard.append([InlineKeyboardButton(
                f"Подробнее: {candidate_name}",
                callback_data=f"result_{analysis.candidate_id}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_admin")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    
    async def show_detailed_result(self, query, context: ContextTypes.DEFAULT_TYPE, candidate_id: int):
        """Show detailed interview result"""
        analysis = self.db.get_candidate_analysis(int(candidate_id))
        candidate = self.db.get_candidate(int(candidate_id))
        
        if not analysis or not candidate:
            await query.edit_message_text("Результат не найден.")
            return
        
        candidate_name = f"{candidate.first_name} {candidate.last_name}" if candidate else f"ID: {candidate_id}"
        
        message = f"""
📋 **Детальный результат интервью**

👤 **Кандидат:** {candidate_name}
📧 **Username:** @{candidate.username}
🎯 **Позиция:** {analysis.position.value.upper()}
📅 **Дата:** {analysis.created_at.strftime('%d.%m.%Y %H:%M')}

📊 **Общая оценка:** {analysis.overall_score:.2f}/1.0

🔍 **Оценка по компетенциям:**
"""
        
        for competency, score in analysis.competency_scores.items():
            message += f"   • {competency}: {score:.2f}/1.0\n"
        
        message += f"""
💬 **Коммуникативные навыки:** {analysis.communication_skills}
📈 **Уровень опыта:** {analysis.experience_level}
🎯 **Оригинальность ответов:** {analysis.originality_score:.2f}/1.0

📝 **Рекомендации:**
"""
        
        for rec in analysis.recommendations:
            message += f"   • {rec}\n"
        
        message += f"""
✅ **Итоговая рекомендация:** {self.get_recommendation_text(analysis.hr_recommendation)}

📄 **Резюме:**
{analysis.summary}
        """
        
        keyboard = [[InlineKeyboardButton("🔙 Назад к результатам", callback_data="admin_results")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    
    async def show_candidates_by_position(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Show candidates grouped by position"""
        message = "👥 **Кандидаты по позициям:**\n\n"
        
        keyboard = [
            [InlineKeyboardButton("💼 Продажи", callback_data="position_filter_sales")],
            [InlineKeyboardButton("🧪 Тестирование", callback_data="position_filter_qa")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_admin")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    
    async def show_results_by_position(self, query, context: ContextTypes.DEFAULT_TYPE, position: Position):
        """Show results filtered by position"""
        analyses = self.get_analyses_by_position(position)
        
        if not analyses:
            message = f"Нет результатов для позиции {position.value}."
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="admin_candidates")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup)
            return
        
        message = f"📊 **Результаты для позиции {position.value.upper()}:**\n\n"
        
        keyboard = []
        for analysis in analyses:
            candidate = self.db.get_candidate(analysis.candidate_id)
            candidate_name = f"{candidate.first_name} {candidate.last_name}" if candidate else f"ID: {analysis.candidate_id}"
            
            status_emoji = "✅" if analysis.hr_recommendation == "recommended" else "⚠️" if analysis.hr_recommendation == "needs_clarification" else "❌"
            
            message += f"{status_emoji} **{candidate_name}**\n"
            message += f"   Оценка: {analysis.overall_score:.2f}/1.0\n"
            message += f"   Дата: {analysis.created_at.strftime('%d.%m.%Y')}\n\n"
            
            keyboard.append([InlineKeyboardButton(
                f"Подробнее: {candidate_name}",
                callback_data=f"result_{analysis.candidate_id}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_candidates")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    
    async def show_statistics(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Show interview statistics"""
        stats = self.get_statistics()
        
        message = f"""
📈 **Статистика интервью**

📊 **Общая статистика:**
   • Всего интервью: {stats['total_interviews']}
   • За сегодня: {stats['today_interviews']}
   • За неделю: {stats['week_interviews']}

🎯 **По позициям:**
   • Продажи: {stats['sales_count']}
   • Тестирование: {stats['qa_count']}

✅ **Рекомендации:**
   • Рекомендовано: {stats['recommended_count']}
   • Требует уточнения: {stats['needs_clarification_count']}
   • Не рекомендовано: {stats['not_recommended_count']}

📊 **Средние оценки:**
   • Общая: {stats['avg_overall_score']:.2f}/1.0
   • Оригинальность: {stats['avg_originality_score']:.2f}/1.0
        """
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_admin")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    
    def get_recent_analyses(self, limit: int = 10) -> List[InterviewAnalysis]:
        """Get recent interview analyses"""
        # This would need to be implemented in Database class
        # For now, return empty list
        return []
    
    def get_analyses_by_position(self, position: Position) -> List[InterviewAnalysis]:
        """Get analyses filtered by position"""
        # This would need to be implemented in Database class
        # For now, return empty list
        return []
    
    def get_statistics(self) -> dict:
        """Get interview statistics"""
        # This would need to be implemented in Database class
        # For now, return mock data
        return {
            'total_interviews': 0,
            'today_interviews': 0,
            'week_interviews': 0,
            'sales_count': 0,
            'qa_count': 0,
            'recommended_count': 0,
            'needs_clarification_count': 0,
            'not_recommended_count': 0,
            'avg_overall_score': 0.0,
            'avg_originality_score': 0.0
        }
    
    def get_recommendation_text(self, recommendation: str) -> str:
        """Get human-readable recommendation text"""
        recommendations = {
            'recommended': '✅ Рекомендуется к следующему этапу',
            'needs_clarification': '⚠️ Требуется дополнительное уточнение',
            'not_recommended': '❌ Не рекомендован'
        }
        return recommendations.get(recommendation, recommendation)
    
    def run(self):
        """Run admin panel"""
        # Create application
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("admin", self.admin_start))
        application.add_handler(CallbackQueryHandler(self.handle_admin_callback))
        
        # Start the bot
        logger.info("Starting Admin Panel...")
        application.run_polling()

if __name__ == "__main__":
    # Add admin users here
    admin_panel = AdminPanel()
    # admin_panel.add_admin(123456789)  # Replace with actual admin user IDs
    
    admin_panel.run() 
from models import Question, Position
from config import Config

def get_contact_questions() -> list[Question]:
    """Get contact information questions"""
    return [
        Question(
            id="contact_intro",
            text=f"Здравствуйте! 👋\n\nЯ — HR-специалист компании **{Config.COMPANY_NAME}**. Очень приятно познакомиться!\n\nПрежде чем мы начнем собеседование, позвольте мне представиться и узнать немного о вас.\n\nМеня зовут {Config.HR_NAME}, я {Config.HR_POSITION} нашей компании. Мы ищем талантливых специалистов для развития нашей команды.\n\nТеперь, пожалуйста, представьтесь: как вас зовут и на какую позицию вы претендуете?",
            category="introduction",
            position=Position.SALES,  # Will be used for all positions
            is_required=True
        ),
        Question(
            id="contact_phone",
            text="Спасибо за представление! 🙏\n\nДля связи с вами мне понадобится ваш номер телефона. Пожалуйста, укажите его в формате:\n\n📱 +7 (XXX) XXX-XX-XX\n\nИли просто цифрами: 8XXXXXXXXXX",
            category="contact",
            position=Position.SALES,
            is_required=True
        ),
        Question(
            id="contact_email",
            text="Отлично! Теперь укажите, пожалуйста, ваш email для отправки результатов собеседования:\n\n📧 example@email.com",
            category="contact", 
            position=Position.SALES,
            is_required=True
        ),
        Question(
            id="contact_portfolio",
            text="И последний вопрос: есть ли у вас портфолио или примеры работ?\n\n💼 Ссылка на GitHub, Behance, или другие платформы\n\n(Если нет — просто напишите 'нет')",
            category="contact",
            position=Position.SALES,
            is_required=False
        ),
        Question(
            id="contact_ready",
            text="Отлично! Спасибо за предоставленную информацию. 📋\n\nТеперь у меня есть все необходимые контактные данные для связи с вами.\n\nГотовы начать собеседование? Оно займет примерно 5-7 минут и будет состоять из профессиональных вопросов.\n\n🚀 Начинаем!",
            category="introduction",
            position=Position.SALES,
            is_required=True
        )
    ] 
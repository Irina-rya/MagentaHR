import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for HR Bot"""
    
    # Telegram settings
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # OpenAI settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Database settings
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///hrbot.db")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Company info
    COMPANY_NAME = "Маджента"
    COMPANY_WEBSITE = "https://magenta.team"
    CAREERS_CHANNEL = "@magentacareers"
    
    # HR Specialist info
    HR_NAME = "Анна Петрова"
    HR_POSITION = "Ведущий HR-специалист"
    
    # Results notification
    RESULTS_RECIPIENT = "@iriska_rya"
    
    # Interview settings
    MAX_FOLLOW_UP_QUESTIONS = 2
    INTERVIEW_TIMEOUT_MINUTES = 30
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required") 
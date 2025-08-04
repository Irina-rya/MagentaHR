from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Position(str, Enum):
    """Available positions for interview"""
    SALES = "sales"
    QA = "qa"

class InterviewStatus(str, Enum):
    """Interview status"""
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    TIMEOUT = "timeout"

class Candidate(BaseModel):
    """Candidate model"""
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    position: Optional[Position] = None
    resume_text: Optional[str] = None
    experience_level: Optional[str] = None
    # Contact information
    phone: Optional[str] = None
    email: Optional[str] = None
    portfolio: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class Question(BaseModel):
    """Question model"""
    id: str
    text: str
    category: str
    position: Position
    follow_up_questions: List[str] = []
    is_required: bool = True

class Answer(BaseModel):
    """Answer model"""
    question_id: str
    answer_text: str
    follow_up_answers: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.now)

class Interview(BaseModel):
    """Interview session model"""
    candidate_id: int
    position: Position
    status: InterviewStatus = InterviewStatus.STARTED
    current_question_index: int = 0
    answers: List[Answer] = []
    follow_up_count: int = 0
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def add_answer(self, answer: Answer):
        """Add answer to interview"""
        self.answers.append(answer)
        self.current_question_index += 1
        
    def get_current_question(self, questions: List[Question]) -> Optional[Question]:
        """Get current question"""
        if self.current_question_index < len(questions):
            return questions[self.current_question_index]
        return None

class InterviewAnalysis(BaseModel):
    """Interview analysis result"""
    candidate_id: int
    position: Position
    overall_score: float
    competency_scores: Dict[str, float]
    communication_skills: str
    experience_level: str
    originality_score: float
    recommendations: List[str]
    hr_recommendation: str  # "recommended", "needs_clarification", "not_recommended"
    summary: str
    created_at: datetime = Field(default_factory=datetime.now) 
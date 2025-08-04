from models import Question, Position
from questions_sales import get_sales_questions
from questions_qa import get_qa_questions
from contact_questions import get_contact_questions

# Get questions from separate files
CONTACT_QUESTIONS = get_contact_questions()
SALES_QUESTIONS = get_sales_questions()
QA_QUESTIONS = get_qa_questions()

# Question sets by position
QUESTION_SETS = {
    Position.SALES: CONTACT_QUESTIONS + SALES_QUESTIONS,
    Position.QA: CONTACT_QUESTIONS + QA_QUESTIONS
}

def get_questions_for_position(position: Position) -> list[Question]:
    """Get questions for specific position"""
    return QUESTION_SETS.get(position, [])

def get_contact_questions_for_position(position: Position) -> list[Question]:
    """Get only contact questions for position"""
    return CONTACT_QUESTIONS

def get_professional_questions_for_position(position: Position) -> list[Question]:
    """Get only professional questions for position (without contact questions)"""
    if position == Position.SALES:
        return SALES_QUESTIONS
    elif position == Position.QA:
        return QA_QUESTIONS
    return []

def get_question_by_id(question_id: str) -> Question | None:
    """Get question by ID"""
    for questions in QUESTION_SETS.values():
        for question in questions:
            if question.id == question_id:
                return question
    return None 
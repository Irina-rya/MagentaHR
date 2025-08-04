import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from models import Candidate, Interview, Answer, InterviewAnalysis, Position, InterviewStatus
from config import Config

class Database:
    """Database manager for HR Bot"""
    
    def __init__(self, db_path: str = "hrbot.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if contact fields exist, if not add them
            cursor.execute("PRAGMA table_info(candidates)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Candidates table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS candidates (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    position TEXT,
                    resume_text TEXT,
                    experience_level TEXT,
                    phone TEXT,
                    email TEXT,
                    portfolio TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Add contact fields if they don't exist
            if 'phone' not in columns:
                cursor.execute('ALTER TABLE candidates ADD COLUMN phone TEXT')
            if 'email' not in columns:
                cursor.execute('ALTER TABLE candidates ADD COLUMN email TEXT')
            if 'portfolio' not in columns:
                cursor.execute('ALTER TABLE candidates ADD COLUMN portfolio TEXT')
            
            # Interviews table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS interviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_id INTEGER,
                    position TEXT,
                    status TEXT,
                    current_question_index INTEGER DEFAULT 0,
                    follow_up_count INTEGER DEFAULT 0,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (candidate_id) REFERENCES candidates (user_id)
                )
            ''')
            
            # Answers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    interview_id INTEGER,
                    question_id TEXT,
                    answer_text TEXT,
                    follow_up_answers TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (interview_id) REFERENCES interviews (id)
                )
            ''')
            
            # Analysis table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_id INTEGER,
                    position TEXT,
                    overall_score REAL,
                    competency_scores TEXT,
                    communication_skills TEXT,
                    experience_level TEXT,
                    originality_score REAL,
                    recommendations TEXT,
                    hr_recommendation TEXT,
                    summary TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (candidate_id) REFERENCES candidates (user_id)
                )
            ''')
            
            conn.commit()
    
    def save_candidate(self, candidate: Candidate) -> bool:
        """Save candidate to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO candidates 
                    (user_id, username, first_name, last_name, position, resume_text, experience_level, 
                     phone, email, portfolio, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    candidate.user_id,
                    candidate.username,
                    candidate.first_name,
                    candidate.last_name,
                    candidate.position.value if candidate.position else None,
                    candidate.resume_text,
                    candidate.experience_level,
                    candidate.phone,
                    candidate.email,
                    candidate.portfolio,
                    candidate.created_at.isoformat()
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving candidate: {e}")
            return False
    
    def get_candidate(self, user_id: int) -> Optional[Candidate]:
        """Get candidate by user_id"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_id, username, first_name, last_name, position, resume_text, experience_level,
                           phone, email, portfolio, created_at
                    FROM candidates WHERE user_id = ?
                ''', (user_id,))
                
                row = cursor.fetchone()
                if row:
                    return Candidate(
                        user_id=row[0],
                        username=row[1],
                        first_name=row[2],
                        last_name=row[3],
                        position=Position(row[4]) if row[4] else None,
                        resume_text=row[5],
                        experience_level=row[6],
                        phone=row[7],
                        email=row[8],
                        portfolio=row[9],
                        created_at=datetime.fromisoformat(row[10])
                    )
                return None
        except Exception as e:
            print(f"Error getting candidate: {e}")
            return None
    
    def save_interview(self, interview: Interview) -> int:
        """Save interview and return interview_id"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO interviews 
                    (candidate_id, position, status, current_question_index, follow_up_count, started_at, completed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    interview.candidate_id,
                    interview.position.value,
                    interview.status.value,
                    interview.current_question_index,
                    interview.follow_up_count,
                    interview.started_at.isoformat(),
                    interview.completed_at.isoformat() if interview.completed_at else None
                ))
                interview_id = cursor.lastrowid
                conn.commit()
                return interview_id
        except Exception as e:
            print(f"Error saving interview: {e}")
            return 0
    
    def update_interview(self, interview: Interview, interview_id: int) -> bool:
        """Update existing interview"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE interviews 
                    SET status = ?, current_question_index = ?, follow_up_count = ?, completed_at = ?
                    WHERE id = ?
                ''', (
                    interview.status.value,
                    interview.current_question_index,
                    interview.follow_up_count,
                    interview.completed_at.isoformat() if interview.completed_at else None,
                    interview_id
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error updating interview: {e}")
            return False
    
    def get_interview(self, interview_id: int) -> Optional[Interview]:
        """Get interview by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT candidate_id, position, status, current_question_index, follow_up_count, started_at, completed_at
                    FROM interviews WHERE id = ?
                ''', (interview_id,))
                
                row = cursor.fetchone()
                if row:
                    return Interview(
                        candidate_id=row[0],
                        position=Position(row[1]),
                        status=InterviewStatus(row[2]),
                        current_question_index=row[3],
                        follow_up_count=row[4],
                        started_at=datetime.fromisoformat(row[5]),
                        completed_at=datetime.fromisoformat(row[6]) if row[6] else None
                    )
                return None
        except Exception as e:
            print(f"Error getting interview: {e}")
            return None
    
    def get_active_interview(self, candidate_id: int) -> Optional[tuple[int, Interview]]:
        """Get active interview for candidate"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, candidate_id, position, status, current_question_index, follow_up_count, started_at, completed_at
                    FROM interviews 
                    WHERE candidate_id = ? AND status IN ('started', 'in_progress')
                    ORDER BY started_at DESC LIMIT 1
                ''', (candidate_id,))
                
                row = cursor.fetchone()
                if row:
                    interview = Interview(
                        candidate_id=row[1],
                        position=Position(row[2]),
                        status=InterviewStatus(row[3]),
                        current_question_index=row[4],
                        follow_up_count=row[5],
                        started_at=datetime.fromisoformat(row[6]),
                        completed_at=datetime.fromisoformat(row[7]) if row[7] else None
                    )
                    return row[0], interview
                return None
        except Exception as e:
            print(f"Error getting active interview: {e}")
            return None
    
    def save_answer(self, interview_id: int, answer: Answer) -> bool:
        """Save answer to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO answers 
                    (interview_id, question_id, answer_text, follow_up_answers, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    interview_id,
                    answer.question_id,
                    answer.answer_text,
                    json.dumps(answer.follow_up_answers),
                    answer.timestamp.isoformat()
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving answer: {e}")
            return False
    
    def get_interview_answers(self, interview_id: int) -> List[Answer]:
        """Get all answers for interview"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT question_id, answer_text, follow_up_answers, timestamp
                    FROM answers WHERE interview_id = ? ORDER BY timestamp
                ''', (interview_id,))
                
                answers = []
                for row in cursor.fetchall():
                    answers.append(Answer(
                        question_id=row[0],
                        answer_text=row[1],
                        follow_up_answers=json.loads(row[2]) if row[2] else [],
                        timestamp=datetime.fromisoformat(row[3])
                    ))
                return answers
        except Exception as e:
            print(f"Error getting interview answers: {e}")
            return []
    
    def save_analysis(self, analysis: InterviewAnalysis) -> bool:
        """Save interview analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO analysis 
                    (candidate_id, position, overall_score, competency_scores, communication_skills, 
                     experience_level, originality_score, recommendations, hr_recommendation, summary, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    analysis.candidate_id,
                    analysis.position.value,
                    analysis.overall_score,
                    json.dumps(analysis.competency_scores),
                    analysis.communication_skills,
                    analysis.experience_level,
                    analysis.originality_score,
                    json.dumps(analysis.recommendations),
                    analysis.hr_recommendation,
                    analysis.summary,
                    analysis.created_at.isoformat()
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving analysis: {e}")
            return False
    
    def get_candidate_analysis(self, candidate_id: int) -> Optional[InterviewAnalysis]:
        """Get latest analysis for candidate"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT candidate_id, position, overall_score, competency_scores, communication_skills,
                           experience_level, originality_score, recommendations, hr_recommendation, summary, created_at
                    FROM analysis 
                    WHERE candidate_id = ? 
                    ORDER BY created_at DESC LIMIT 1
                ''', (candidate_id,))
                
                row = cursor.fetchone()
                if row:
                    return InterviewAnalysis(
                        candidate_id=row[0],
                        position=Position(row[1]),
                        overall_score=row[2],
                        competency_scores=json.loads(row[3]),
                        communication_skills=row[4],
                        experience_level=row[5],
                        originality_score=row[6],
                        recommendations=json.loads(row[7]),
                        hr_recommendation=row[8],
                        summary=row[9],
                        created_at=datetime.fromisoformat(row[10])
                    )
                return None
        except Exception as e:
            print(f"Error getting candidate analysis: {e}")
            return None 
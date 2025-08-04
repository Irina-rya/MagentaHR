from models import Question, Position

# Questions for QA position
QA_QUESTIONS = [
    Question(
        id="qa_1",
        text="Расскажите о вашем опыте в тестировании. Какие проекты или продукты вы тестировали?",
        category="Общая мотивация и опыт",
        position=Position.QA,
        follow_up_questions=[
            "Сколько лет опыта в тестировании у вас есть?",
            "Какие типы проектов вам больше всего нравятся?"
        ]
    ),
    Question(
        id="qa_2",
        text="Как вы пришли в тестирование?",
        category="Общая мотивация и опыт",
        position=Position.QA,
        follow_up_questions=[
            "Что вас привлекает в этой профессии?",
            "Какие навыки вы считаете важными для тестировщика?"
        ]
    ),
    Question(
        id="qa_3",
        text="Чем отличается функциональное и нефункциональное тестирование?",
        category="Технические навыки",
        position=Position.QA,
        follow_up_questions=[
            "Приведите примеры каждого типа тестирования",
            "Какое тестирование вы считаете более сложным?"
        ]
    ),
    Question(
        id="qa_4",
        text="Какие виды тестирования вы использовали в практике?",
        category="Технические навыки",
        position=Position.QA,
        follow_up_questions=[
            "Как вы выбираете подходящий вид тестирования?",
            "Какое тестирование дается вам легче всего?"
        ]
    ),
    Question(
        id="qa_5",
        text="Как вы документируете найденные баги?",
        category="Технические навыки",
        position=Position.QA,
        follow_up_questions=[
            "Какая информация должна быть в баг-репорте?",
            "Как вы определяете приоритет бага?"
        ]
    ),
    Question(
        id="qa_6",
        text="Какие инструменты и трекеры вы используете в работе (JIRA, TestRail и пр.)?",
        category="Инструменты",
        position=Position.QA,
        follow_up_questions=[
            "Какой инструмент вы считаете наиболее удобным?",
            "Как вы организуете тест-кейсы в трекере?"
        ]
    ),
    Question(
        id="qa_7",
        text="Есть ли опыт написания автотестов? Если да — на каком языке?",
        category="Инструменты",
        position=Position.QA,
        follow_up_questions=[
            "Какие фреймворки для автотестирования вы знаете?",
            "Как вы решаете, что нужно автоматизировать?"
        ]
    ),
    Question(
        id="qa_8",
        text="Опишите ваш типичный рабочий день.",
        category="Процессы и взаимодействие",
        position=Position.QA,
        follow_up_questions=[
            "Как вы планируете свою работу?",
            "Какие задачи занимают больше всего времени?"
        ]
    ),
    Question(
        id="qa_9",
        text="Как вы работаете с разработчиками?",
        category="Процессы и взаимодействие",
        position=Position.QA,
        follow_up_questions=[
            "Как вы общаетесь при обсуждении багов?",
            "Были ли конфликты с разработчиками?"
        ]
    ),
    Question(
        id="qa_10",
        text="Были ли у вас конфликты по поводу багов? Как вы их решали?",
        category="Процессы и взаимодействие",
        position=Position.QA,
        follow_up_questions=[
            "Как вы доказываете, что это действительно баг?",
            "Какие стратегии решения конфликтов вы используете?"
        ]
    )
]

def get_qa_questions():
    """Get questions for QA position"""
    return QA_QUESTIONS 
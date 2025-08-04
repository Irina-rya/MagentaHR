from models import Question, Position

# Questions for Sales position
SALES_QUESTIONS = [
    Question(
        id="sales_1",
        text="Расскажите о своем опыте в продажах. Какие продукты или услуги вы продавали?",
        category="Общая мотивация и опыт",
        position=Position.SALES,
        follow_up_questions=[
            "Сколько лет опыта в продажах у вас есть?",
            "Какие были ваши ключевые достижения в продажах?"
        ]
    ),
    Question(
        id="sales_2",
        text="Почему вы выбрали профессию в продажах?",
        category="Общая мотивация и опыт",
        position=Position.SALES,
        follow_up_questions=[
            "Что вас больше всего мотивирует в продажах?",
            "Какие качества, по вашему мнению, важны для успешного продавца?"
        ]
    ),
    Question(
        id="sales_3",
        text="Как вы оцениваете свои сильные стороны как продавца?",
        category="Общая мотивация и опыт",
        position=Position.SALES,
        follow_up_questions=[
            "Приведите пример, когда ваши сильные стороны помогли закрыть сделку",
            "Над какими навыками вы сейчас работаете?"
        ]
    ),
    Question(
        id="sales_4",
        text="Опишите сложную ситуацию с клиентом, которую удалось разрешить.",
        category="Навыки работы с клиентами",
        position=Position.SALES,
        follow_up_questions=[
            "Какой подход вы использовали для решения проблемы?",
            "Что вы извлекли из этой ситуации?"
        ]
    ),
    Question(
        id="sales_5",
        text="Какие техники вы используете для установления доверия?",
        category="Навыки работы с клиентами",
        position=Position.SALES,
        follow_up_questions=[
            "Как вы определяете, что клиент вам доверяет?",
            "Приведите пример успешного установления доверия"
        ]
    ),
    Question(
        id="sales_6",
        text="Расскажите, как вы строите воронку продаж.",
        category="Процесс продаж",
        position=Position.SALES,
        follow_up_questions=[
            "Какие этапы воронки вы считаете наиболее важными?",
            "Как вы отслеживаете прогресс по воронке?"
        ]
    ),
    Question(
        id="sales_7",
        text="Как вы квалифицируете лиды?",
        category="Процесс продаж",
        position=Position.SALES,
        follow_up_questions=[
            "Какие критерии вы используете для квалификации?",
            "Как вы работаете с неквалифицированными лидами?"
        ]
    ),
    Question(
        id="sales_8",
        text="Какие CRM-системы вы использовали?",
        category="Процесс продаж",
        position=Position.SALES,
        follow_up_questions=[
            "Как CRM помогает в вашей работе?",
            "Какие функции CRM вы используете чаще всего?"
        ]
    ),
    Question(
        id="sales_9",
        text="Расскажите о своем самом успешном кейсе.",
        category="Результаты",
        position=Position.SALES,
        follow_up_questions=[
            "Что сделало этот кейс успешным?",
            "Как вы повторили этот успех в других случаях?"
        ]
    ),
    Question(
        id="sales_10",
        text="Как вы работаете с отказами или возражениями?",
        category="Результаты",
        position=Position.SALES,
        follow_up_questions=[
            "Какие типы возражений встречаются чаще всего?",
            "Приведите пример успешного преодоления возражения"
        ]
    )
]

def get_sales_questions():
    """Get questions for sales position"""
    return SALES_QUESTIONS 
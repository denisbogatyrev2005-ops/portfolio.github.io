from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.models import Base, User, Event, UserRole, EventStatus, EventCategory
from passlib.context import CryptContext

DATABASE_URL = "sqlite:///./portal.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if db.query(User).count() == 0:
        teacher = User(
            full_name="Елена Смирнова",
            email="teacher@portal.ru",
            hashed_password=pwd_context.hash("teacher123"),
            role=UserRole.teacher,
        )
        student = User(
            full_name="Алексей Иванов",
            email="student@portal.ru",
            hashed_password=pwd_context.hash("student123"),
            role=UserRole.student,
            group="ИТ-301",
        )
        db.add_all([teacher, student])
        db.commit()
        db.refresh(teacher)
        events = [
            Event(title="Олимпиада по программированию", description="Соревнование по алгоритмическому программированию для студентов 2–4 курса.", department="Факультет ИТ", deadline="30 апреля 2026", doc_requirements="Диплом или сертификат участника", status=EventStatus.active, category=EventCategory.science, teacher_id=teacher.id),
            Event(title="Конференция «Инновации 2026»", description="Студенческая научно-практическая конференция. Требуется тезис доклада.", department="Кафедра науки", deadline="15 мая 2026", doc_requirements="Тезисы доклада, сертификат участника", status=EventStatus.upcoming, category=EventCategory.science, teacher_id=teacher.id),
            Event(title="Волонтёрский проект «Город»", description="Общественная деятельность, засчитывается как внеучебная активность.", department="Студенческий совет", deadline="Весь семестр", doc_requirements="Справка об участии от организатора", status=EventStatus.active, category=EventCategory.volunteer, teacher_id=teacher.id),
            Event(title="Хакатон HackIT 2026", description="48-часовой марафон разработки. Командный формат, до 4 человек.", department="Факультет ИТ", deadline="Завершён", doc_requirements="Сертификат участника или диплом призёра", status=EventStatus.closed, category=EventCategory.science, teacher_id=teacher.id),
            Event(title="Кубок университета по футболу", description="Ежегодный турнир между факультетами.", department="Спортивный клуб", deadline="20 мая 2026", doc_requirements="Грамота или справка об участии", status=EventStatus.active, category=EventCategory.sport, teacher_id=teacher.id),
            Event(title="Фестиваль «Студенческая весна»", description="Творческий фестиваль — музыка, танцы, театр.", department="Культурный центр", deadline="1 мая 2026", doc_requirements="Диплом участника или победителя", status=EventStatus.active, category=EventCategory.cultural, teacher_id=teacher.id),
        ]
        db.add_all(events)
        db.commit()
    db.close()

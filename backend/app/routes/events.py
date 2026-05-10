from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Event, Participation, User, EventStatus, EventCategory
from app.utils.auth import get_current_user, require_teacher

router = APIRouter(prefix="/api/events", tags=["events"])

def event_dict(event, db, current_user=None):
    count = db.query(Participation).filter(Participation.event_id == event.id).count()
    is_joined = False
    if current_user:
        is_joined = db.query(Participation).filter(
            Participation.event_id == event.id,
            Participation.student_id == current_user.id).first() is not None
    status = event.status.value if hasattr(event.status, 'value') else str(event.status)
    category = event.category.value if hasattr(event.category, 'value') else str(event.category)
    return {
        "id": event.id, "title": event.title,
        "description": event.description or "", "department": event.department or "",
        "deadline": event.deadline or "", "doc_requirements": event.doc_requirements or "",
        "status": status, "category": category,
        "teacher_id": event.teacher_id,
        "teacher_name": event.teacher.full_name if event.teacher else "",
        "participants_count": count, "is_joined": is_joined,
    }

@router.get("")
def list_events(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return [event_dict(e, db, current_user) for e in db.query(Event).order_by(Event.created_at.desc()).all()]

@router.post("")
async def create_event(request: Request, db: Session = Depends(get_db), teacher: User = Depends(require_teacher)):
    data = await request.json()
    cat = data.get("category", "science")
    try: category = EventCategory(cat)
    except: category = EventCategory.science
    event = Event(
        title=data.get("title", ""), description=data.get("description", ""),
        department=data.get("department", ""), deadline=data.get("deadline", ""),
        doc_requirements=data.get("doc_requirements", ""),
        status=EventStatus(data.get("status", "active")),
        category=category, teacher_id=teacher.id)
    db.add(event); db.commit(); db.refresh(event)
    return event_dict(event, db, teacher)

@router.put("/{event_id}")
async def update_event(event_id: int, request: Request, db: Session = Depends(get_db), teacher: User = Depends(require_teacher)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event: raise HTTPException(404, "Не найдено")
    data = await request.json()
    event.title = data.get("title", event.title)
    event.description = data.get("description", event.description)
    event.department = data.get("department", event.department)
    event.deadline = data.get("deadline", event.deadline)
    event.doc_requirements = data.get("doc_requirements", event.doc_requirements)
    cur_status = event.status.value if hasattr(event.status,'value') else str(event.status)
    event.status = EventStatus(data.get("status", cur_status))
    cat = data.get("category", event.category.value if hasattr(event.category,'value') else str(event.category))
    try: event.category = EventCategory(cat)
    except: pass
    db.commit()
    return event_dict(event, db, teacher)

@router.delete("/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db), teacher: User = Depends(require_teacher)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event: raise HTTPException(404, "Не найдено")
    db.delete(event); db.commit()
    return {"ok": True}

@router.post("/{event_id}/join")
def join_event(event_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    role = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
    if role == "teacher": raise HTTPException(400, "Преподаватели не могут добавлять мероприятия")
    if not db.query(Event).filter(Event.id == event_id).first(): raise HTTPException(404, "Не найдено")
    if db.query(Participation).filter(Participation.event_id == event_id, Participation.student_id == current_user.id).first():
        raise HTTPException(400, "Вы уже добавили это мероприятие")
    db.add(Participation(student_id=current_user.id, event_id=event_id)); db.commit()
    return {"ok": True}

@router.delete("/{event_id}/leave")
def leave_event(event_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    p = db.query(Participation).filter(Participation.event_id == event_id, Participation.student_id == current_user.id).first()
    if not p: raise HTTPException(404, "Не найдено")
    db.delete(p); db.commit()
    return {"ok": True}

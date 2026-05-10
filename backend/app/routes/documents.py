from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.orm import Session
from datetime import datetime
import os, uuid, aiofiles
from app.database import get_db
from app.models.models import Participation, Document, User, DocStatus
from app.utils.auth import get_current_user, require_teacher

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/jpg"}

def doc_dict(doc):
    return {
        "id": doc.id, "participation_id": doc.participation_id,
        "filename": doc.filename, "original_name": doc.original_name,
        "file_size": doc.file_size, "mime_type": doc.mime_type,
        "doc_type": doc.doc_type or "file",
        "link_url": doc.link_url,
        "status": doc.status.value if hasattr(doc.status, 'value') else str(doc.status),
        "teacher_comment": doc.teacher_comment,
        "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
        "reviewed_at": doc.reviewed_at.isoformat() if doc.reviewed_at else None,
    }

def part_dict(p):
    status = p.event.status
    return {
        "id": p.id, "event_id": p.event_id,
        "event_title": p.event.title if p.event else "",
        "event_status": status.value if hasattr(status,'value') else str(status) if status else "",
        "event_department": p.event.department if p.event else "",
        "event_deadline": p.event.deadline if p.event else "",
        "event_category": p.event.category.value if p.event and hasattr(p.event.category,'value') else "",
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "documents": [doc_dict(d) for d in p.documents],
    }

student_router = APIRouter(prefix="/api/my")

@student_router.get("/participations")
def my_participations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return [part_dict(p) for p in db.query(Participation).filter(Participation.student_id == current_user.id).all()]

@student_router.post("/participations/{participation_id}/documents")
async def upload_document(participation_id: int, file: UploadFile = File(...),
                          db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    p = db.query(Participation).filter(Participation.id == participation_id,
                                       Participation.student_id == current_user.id).first()
    if not p: raise HTTPException(404, "Участие не найдено")
    if file.content_type not in ALLOWED_TYPES: raise HTTPException(400, "Разрешены только PDF, JPG, PNG")
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024: raise HTTPException(400, "Файл не должен превышать 10 МБ")
    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "bin"
    saved_name = f"{uuid.uuid4()}.{ext}"
    async with aiofiles.open(os.path.join(UPLOAD_DIR, saved_name), "wb") as f:
        await f.write(contents)
    doc = Document(participation_id=participation_id, filename=saved_name,
                   original_name=file.filename, file_size=len(contents),
                   mime_type=file.content_type, doc_type="file", status=DocStatus.pending)
    db.add(doc); db.commit(); db.refresh(doc)
    return doc_dict(doc)

@student_router.post("/participations/{participation_id}/links")
async def add_link(participation_id: int, request: Request,
                   db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    p = db.query(Participation).filter(Participation.id == participation_id,
                                       Participation.student_id == current_user.id).first()
    if not p: raise HTTPException(404, "Участие не найдено")
    data = await request.json()
    url = data.get("url", "").strip()
    name = data.get("name", "Ссылка").strip()
    if not url or not url.startswith("http"):
        raise HTTPException(400, "Введите корректную ссылку (начинается с http)")
    doc = Document(participation_id=participation_id, filename=None,
                   original_name=name, file_size=None,
                   mime_type=None, doc_type="link", link_url=url, status=DocStatus.pending)
    db.add(doc); db.commit(); db.refresh(doc)
    return doc_dict(doc)

@student_router.delete("/documents/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = db.query(Document).join(Participation).filter(
        Document.id == doc_id, Participation.student_id == current_user.id).first()
    if not doc: raise HTTPException(404, "Не найдено")
    if doc.filename:
        path = os.path.join(UPLOAD_DIR, doc.filename)
        if os.path.exists(path): os.remove(path)
    db.delete(doc); db.commit()
    return {"ok": True}

teacher_router = APIRouter(prefix="/api/teacher")

@teacher_router.get("/submissions")
def all_submissions(db: Session = Depends(get_db), teacher: User = Depends(require_teacher)):
    result = []
    for p in db.query(Participation).all():
        d = part_dict(p)
        d["student_name"] = p.student.full_name if p.student else ""
        d["student_group"] = p.student.group if p.student else ""
        d["student_id"] = p.student_id
        result.append(d)
    return result

@teacher_router.get("/students")
def all_students(db: Session = Depends(get_db), teacher: User = Depends(require_teacher)):
    result = []
    for s in db.query(User).filter(User.role == "student").all():
        parts = db.query(Participation).filter(Participation.student_id == s.id).all()
        approved = sum(1 for p in parts for d in p.documents if (d.status.value if hasattr(d.status,'value') else str(d.status)) == "approved")
        pending = sum(1 for p in parts for d in p.documents if (d.status.value if hasattr(d.status,'value') else str(d.status)) == "pending")
        result.append({"id": s.id, "full_name": s.full_name, "email": s.email,
                       "group": s.group, "events_count": len(parts),
                       "approved_count": approved, "pending_count": pending})
    return result

@teacher_router.post("/documents/{doc_id}/review")
async def review_document(doc_id: int, request: Request,
                          db: Session = Depends(get_db), teacher: User = Depends(require_teacher)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc: raise HTTPException(404, "Документ не найден")
    data = await request.json()
    doc.status = DocStatus(data.get("status"))
    doc.teacher_comment = data.get("comment")
    doc.reviewed_at = datetime.utcnow()
    db.commit()
    return doc_dict(doc)

@teacher_router.get("/stats")
def stats(db: Session = Depends(get_db), teacher: User = Depends(require_teacher)):
    from app.models.models import Event
    return {
        "events": db.query(Event).count(),
        "students": db.query(User).filter(User.role == "student").count(),
        "pending": db.query(Document).filter(Document.status == "pending").count(),
        "approved": db.query(Document).filter(Document.status == "approved").count(),
    }

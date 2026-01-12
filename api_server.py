# api_server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Any, Dict

from config import Config
from controllers import Controllers
from models import StudentProfile
from services.submissions_store import SubmissionStore
from services.email_builder import build_email_from_submission


app = FastAPI(title="Saarthi API")
config = Config()
controllers = Controllers(config)
store = SubmissionStore()


class SubmitRequest(BaseModel):
    student_name: str
    student_email: Optional[EmailStr] = None
    wants_email: bool = False

    grade: str
    average: float
    subjects: List[str] = []
    interests: str
    extracurriculars: str = ""
    location: str = ""
    preferences: str = ""


class SubmitResponse(BaseModel):
    id: int
    resume_token: str
    status: str


@app.post("/api/submit", response_model=SubmitResponse)
def submit(req: SubmitRequest):
    # 1) store inputs
    created = store.create_submission(req.model_dump())

    # 2) generate roadmap
    session = controllers.session_manager.create_session(req.student_name)

    profile = StudentProfile(
        name=req.student_name,
        grade=req.grade,
        average=float(req.average),
        interests=req.interests,
        subjects=req.subjects or [],
        extracurriculars=req.extracurriculars or "",
        location=req.location or "",
        preferences=req.preferences or "",
    )

    result = controllers.roadmap_service.generate(profile, session)
    if not result.ok:
        raise HTTPException(status_code=500, detail=result.message)

    roadmap_md = result.message
    data = result.data or {}
    
    # ✅ FIX: Use correct keys
    ui_programs = data.get("programs", [])
    ui_timeline = data.get("timeline_events", [])  # ✅ Fixed key
    ui_projects = data.get("projects", [])          # ✅ Fixed key

    # 3) store generated outputs
    # ✅ FIX: Pass all 5 required arguments
    store.save_generated_plan(
        created["id"],
        roadmap_md,
        ui_programs,
        ui_timeline,
        ui_projects
    )

    return SubmitResponse(id=created["id"], resume_token=created["resume_token"], status="GENERATED")


@app.get("/api/submission/{submission_id}")
def get_submission(submission_id: int, token: str):
    sub = store.get_by_resume_code(submission_id, token)
    if not sub:
        raise HTTPException(status_code=404, detail="Not found")
    return store.unpack(sub)


# ---------------- ADMIN ----------------

@app.get("/api/admin/submissions")
def admin_list(status: Optional[str] = None, limit: int = 50):
    subs = store.list_queue(status_filter=status or "ALL", limit=limit)
    return [
        {
            "id": s["id"],
            "created_at": s["created_at"],
            "student_name": s["student_name"],
            "status": s["status"],
            "wants_email": bool(s["wants_email"])
        }
        for s in subs
    ]


@app.get("/api/admin/submission/{submission_id}")
def admin_get(submission_id: int):
    sub = store.admin_get(submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Not found")
    return store.unpack(sub)


class UpdateEmailRequest(BaseModel):
    subject: str
    body_text: str


@app.post("/api/admin/update_email/{submission_id}")
def admin_update_email(submission_id: int, req: UpdateEmailRequest):
    sub = store.admin_get(submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Not found")
    store.admin_save_email(submission_id, req.subject, req.body_text)
    return {"ok": True}


@app.post("/api/admin/generate_email/{submission_id}")
def admin_generate_email(submission_id: int):
    sub = store.admin_get(submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Not found")

    sub_u = store.unpack(sub)
    email = build_email_from_submission(sub_u)
    store.admin_save_email(submission_id, email["subject"], email["body_text"])
    return email


@app.post("/api/admin/mark_sent/{submission_id}")
def admin_mark_sent(submission_id: int):
    sub = store.admin_get(submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Not found")
    store.admin_mark_sent(submission_id)
    return {"ok": True}
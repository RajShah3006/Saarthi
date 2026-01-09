# services/submissions_store.py
import os
import sqlite3
import json
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional

DEFAULT_DB_PATH = "data/submissions.db"


class SubmissionStore:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _now() -> str:
        return datetime.utcnow().isoformat(timespec="seconds") + "Z"

    @staticmethod
    def _json_default(o):
        try:
            import numpy as np
            if isinstance(o, np.generic):
                return o.item()
            if isinstance(o, np.ndarray):
                return o.tolist()
        except Exception:
            pass
    
        if isinstance(o, set):
            return list(o)
    
        if isinstance(o, (bytes, bytearray)):
            try:
                return o.decode("utf-8")
            except Exception:
                return str(o)
    
        return str(o)
    
    def _dumps(self, obj) -> str:
        return json.dumps(obj, ensure_ascii=False, default=SubmissionStore._json_default)

    @staticmethod
    def _loads(s: Optional[str], default):
        if not s:
            return default
        try:
            return json.loads(s)
        except Exception:
            return default

    def _init_db(self) -> None:
        # ensure folder exists
        folder = os.path.dirname(self.db_path)
        if folder:
            os.makedirs(folder, exist_ok=True)

        with self._conn() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                student_name TEXT NOT NULL,
                student_email TEXT,
                wants_email INTEGER NOT NULL DEFAULT 0,
                grade TEXT NOT NULL,
                average REAL NOT NULL,
                subjects_json TEXT NOT NULL,
                interests TEXT NOT NULL,
                extracurriculars TEXT,
                location TEXT,
                preferences TEXT,
                status TEXT NOT NULL DEFAULT 'NEW',  -- NEW -> GENERATED -> IN_REVIEW -> SENT
                resume_token TEXT NOT NULL,
                roadmap_md TEXT,
                ui_programs_json TEXT,
                ui_phases_json TEXT,
                email_subject TEXT,
                email_body_text TEXT,
                sent_at TEXT
            );
            """)

            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON submissions(status);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_token ON submissions(resume_token);")

    # ----------------- Student flow -----------------

    def create_submission(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        resume_token = secrets.token_urlsafe(16)
        now = self._now()

        subjects = payload.get("subjects") or []
        if not isinstance(subjects, list):
            subjects = [str(subjects)]

        with self._conn() as conn:
            cur = conn.execute("""
                INSERT INTO submissions (
                    created_at, updated_at,
                    student_name, student_email, wants_email,
                    grade, average, subjects_json, interests,
                    extracurriculars, location, preferences,
                    status, resume_token
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                now, now,
                payload["student_name"],
                payload.get("student_email") or "",
                1 if payload.get("wants_email") else 0,
                payload["grade"],
                float(payload["average"]),
                self._dumps(subjects),
                payload["interests"],
                payload.get("extracurriculars") or "",
                payload.get("location") or "",
                payload.get("preferences") or "",
                "NEW",
                resume_token,
            ))
            new_id = cur.lastrowid

        return {"id": int(new_id), "resume_token": resume_token}

    def save_generated_plan(
        self,
        submission_id: int,
        roadmap_md: str,
        ui_programs: List[Dict[str, Any]],
        ui_phases: List[Dict[str, Any]],
    ) -> None:
        now = self._now()
        with self._conn() as conn:
            conn.execute("""
                UPDATE submissions
                SET updated_at=?,
                    status='GENERATED',
                    roadmap_md=?,
                    ui_programs_json=?,
                    ui_phases_json=?
                WHERE id=?
            """, (
                now,
                roadmap_md or "",
                self._dumps(ui_programs or []),
                self._dumps(ui_phases or []),
                int(submission_id),
            ))

    def get_by_resume_code(self, submission_id: int, token: str) -> Optional[Dict[str, Any]]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM submissions WHERE id=? AND resume_token=?",
                (int(submission_id), token),
            ).fetchone()
        return dict(row) if row else None

    def unpack(self, sub: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(sub)
        out["subjects"] = self._loads(sub.get("subjects_json"), [])
        out["ui_programs"] = self._loads(sub.get("ui_programs_json"), [])
        out["ui_phases"] = self._loads(sub.get("ui_phases_json"), [])
        return out

    # ----------------- Admin flow -----------------

    def list_queue(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT id, created_at, student_name, student_email, wants_email, status
                FROM submissions
                WHERE wants_email=1 AND status IN ('GENERATED','IN_REVIEW')
                ORDER BY created_at DESC
                LIMIT ?
            """, (int(limit),)).fetchall()
        return [dict(r) for r in rows]

    def admin_get(self, submission_id: int) -> Optional[Dict[str, Any]]:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM submissions WHERE id=?", (int(submission_id),)).fetchone()
        return dict(row) if row else None

    def admin_save_email(self, submission_id: int, subject: str, body_text: str) -> None:
        now = self._now()
        with self._conn() as conn:
            conn.execute("""
                UPDATE submissions
                SET updated_at=?,
                    status='IN_REVIEW',
                    email_subject=?,
                    email_body_text=?
                WHERE id=?
            """, (now, subject or "", body_text or "", int(submission_id)))

    def admin_mark_sent(self, submission_id: int) -> None:
        now = self._now()
        with self._conn() as conn:
            conn.execute("""
                UPDATE submissions
                SET updated_at=?,
                    status='SENT',
                    sent_at=?
                WHERE id=?
            """, (now, now, int(submission_id)))
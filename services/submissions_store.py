'''
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
        self._migrate_schema()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _now() -> str:
        return datetime.utcnow().isoformat(timespec="seconds") + "Z"

    # ---------- JSON helpers ----------
    @staticmethod
    def _json_default(o):
        # numpy scalars/arrays -> python
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

    def _dumps(self, obj: Any) -> str:
        return json.dumps(obj, ensure_ascii=False, default=self._json_default)

    @staticmethod
    def _loads(s: Optional[str], default):
        if not s:
            return default
        try:
            return json.loads(s)
        except Exception:
            return default

    # ---------- schema ----------
    def _init_db(self) -> None:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._conn() as conn:
            conn.execute(
                """
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
                    interest_details TEXT,
                    extracurriculars TEXT,
                    location TEXT,
                    preferences TEXT,

                    status TEXT NOT NULL DEFAULT 'NEW',  -- NEW -> GENERATED -> IN_REVIEW -> SENT / ERROR
                    resume_token TEXT NOT NULL,

                    roadmap_md TEXT,

                    ui_programs_json TEXT,
                    ui_timeline_json TEXT,
                    ui_projects_json TEXT,

                    email_subject TEXT,
                    email_body_text TEXT,
                    sent_at TEXT,

                    github_issue_number INTEGER,
                    github_issue_url TEXT,
                    github_assignee TEXT,
                    github_status TEXT
                );
                """
            )

            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON submissions(status);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_token ON submissions(resume_token);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_wants_email ON submissions(wants_email);")

            # actions log
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS submission_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    submission_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT,
                    FOREIGN KEY(submission_id) REFERENCES submissions(id)
                );
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_actions_sub ON submission_actions(submission_id);")

    def _has_column(self, conn: sqlite3.Connection, table: str, col: str) -> bool:
        rows = conn.execute(f"PRAGMA table_info({table});").fetchall()
        cols = {r["name"] for r in rows}
        return col in cols

    def _migrate_schema(self) -> None:
        """
        Safe auto-migrations for older DBs.
        """
        with self._conn() as conn:
            # submissions additions
            needed_cols = [
                ("interest_details", "TEXT"),
                ("ui_timeline_json", "TEXT"),
                ("ui_projects_json", "TEXT"),
                ("github_issue_number", "INTEGER"),
                ("github_issue_url", "TEXT"),
                ("github_assignee", "TEXT"),
                ("github_status", "TEXT"),
            ]
            for col, coltype in needed_cols:
                if not self._has_column(conn, "submissions", col):
                    conn.execute(f"ALTER TABLE submissions ADD COLUMN {col} {coltype};")

            # ensure actions table exists (older db may not have it)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS submission_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    submission_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT,
                    FOREIGN KEY(submission_id) REFERENCES submissions(id)
                );
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_actions_sub ON submission_actions(submission_id);")

    # ----------------- Student flow -----------------
    def create_submission(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        resume_token = secrets.token_urlsafe(16)
        now = self._now()

        subjects = payload.get("subjects") or []
        if not isinstance(subjects, list):
            subjects = [str(subjects)]

        with self._conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO submissions (
                    created_at, updated_at,
                    student_name, student_email, wants_email,
                    grade, average, subjects_json,
                    interests, interest_details,
                    extracurriculars, location, preferences,
                    status, resume_token,
                    github_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now, now,
                    payload.get("student_name") or "Student",
                    payload.get("student_email") or "",
                    1 if payload.get("wants_email") else 0,
                    payload.get("grade") or "",
                    float(payload.get("average") or 0.0),
                    self._dumps(subjects),
                    payload.get("interests") or "",
                    payload.get("interest_details") or "",
                    payload.get("extracurriculars") or "",
                    payload.get("location") or "",
                    payload.get("preferences") or "",
                    "NEW",
                    resume_token,
                    payload.get("github_status") or "",
                ),
            )
            new_id = cur.lastrowid

        # log
        try:
            self.log_action(int(new_id), "student", "SUBMITTED", "Created submission")
        except Exception:
            pass

        return {"id": int(new_id), "resume_token": resume_token}

    def save_generated_plan(
        self,
        submission_id: int,
        roadmap_md: str,
        ui_programs: List[Dict[str, Any]],
        ui_timeline: List[Dict[str, Any]],
        ui_projects: List[Dict[str, Any]],
        actor: str = "system",
    ) -> None:
        now = self._now()
        with self._conn() as conn:
            conn.execute(
                """
                UPDATE submissions
                SET updated_at=?,
                    status='GENERATED',
                    roadmap_md=?,
                    ui_programs_json=?,
                    ui_timeline_json=?,
                    ui_projects_json=?
                WHERE id=?
                """,
                (
                    now,
                    roadmap_md or "",
                    self._dumps(ui_programs or []),
                    self._dumps(ui_timeline or []),
                    self._dumps(ui_projects or []),
                    int(submission_id),
                ),
            )

        try:
            self.log_action(int(submission_id), actor or "system", "GENERATED_PLAN", "Stored generated plan")
        except Exception:
            pass

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
        out["ui_timeline"] = self._loads(sub.get("ui_timeline_json"), [])
        out["ui_projects"] = self._loads(sub.get("ui_projects_json"), [])
        return out

    # ----------------- Admin flow -----------------
    def list_queue(self, status_filter: str = "ALL", query: str = "", limit: int = 200) -> List[Dict[str, Any]]:
        """
        status_filter: "ALL" | "GENERATED" | "IN_REVIEW" | "SENT" | "NEW"
        query: searches name/email
        """
        status_filter = (status_filter or "ALL").strip().upper()
        query = (query or "").strip()

        where = ["wants_email=1"]
        params: List[Any] = []

        if status_filter != "ALL":
            where.append("status=?")
            params.append(status_filter)

        if query:
            where.append("(student_name LIKE ? OR student_email LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])

        sql = f"""
            SELECT id, created_at, student_name, student_email, wants_email, status
            FROM submissions
            WHERE {' AND '.join(where)}
            ORDER BY created_at DESC
            LIMIT ?
        """
        params.append(int(limit))

        with self._conn() as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()
        return [dict(r) for r in rows]

    def get_next_pending(self) -> Optional[Dict[str, Any]]:
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT * FROM submissions
                WHERE wants_email=1 AND status IN ('GENERATED','NEW','IN_REVIEW')
                ORDER BY
                    CASE status
                        WHEN 'GENERATED' THEN 0
                        WHEN 'NEW' THEN 1
                        WHEN 'IN_REVIEW' THEN 2
                        ELSE 9
                    END,
                    created_at ASC
                LIMIT 1
                """
            ).fetchone()
        return dict(row) if row else None

    def admin_get(self, submission_id: int) -> Optional[Dict[str, Any]]:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM submissions WHERE id=?", (int(submission_id),)).fetchone()
        return dict(row) if row else None

    def admin_save_email(self, submission_id: int, subject: str, body_text: str, actor: str = "admin") -> None:
        now = self._now()
        with self._conn() as conn:
            conn.execute(
                """
                UPDATE submissions
                SET updated_at=?,
                    status='IN_REVIEW',
                    email_subject=?,
                    email_body_text=?
                WHERE id=?
                """,
                (now, subject or "", body_text or "", int(submission_id)),
            )
        self.log_action(int(submission_id), actor or "admin", "SAVED_EMAIL", "Saved email draft")

    def admin_mark_sent(self, submission_id: int, actor: str = "admin") -> None:
        now = self._now()
        with self._conn() as conn:
            conn.execute(
                """
                UPDATE submissions
                SET updated_at=?,
                    status='SENT',
                    sent_at=?
                WHERE id=?
                """,
                (now, now, int(submission_id)),
            )
        self.log_action(int(submission_id), actor or "admin", "MARKED_SENT", "Marked sent")

    # ----------------- GitHub issue helpers -----------------
    def set_github_issue(
        self,
        submission_id: int,
        issue_number: int,
        issue_url: str,
        assignee: str,
        github_status: str,
    ) -> None:
        now = self._now()
        with self._conn() as conn:
            conn.execute(
                """
                UPDATE submissions
                SET updated_at=?,
                    github_issue_number=?,
                    github_issue_url=?,
                    github_assignee=?,
                    github_status=?
                WHERE id=?
                """,
                (now, int(issue_number), issue_url or "", assignee or "", github_status or "", int(submission_id)),
            )
        self.log_action(int(submission_id), "system", "GITHUB_ISSUE_SET", f"Issue #{issue_number} {github_status}")

    def set_github_status(self, submission_id: int, github_status: str) -> None:
        now = self._now()
        with self._conn() as conn:
            conn.execute(
                """
                UPDATE submissions
                SET updated_at=?,
                    github_status=?
                WHERE id=?
                """,
                (now, github_status or "", int(submission_id)),
            )
        self.log_action(int(submission_id), "system", "GITHUB_STATUS", github_status or "")

    # ----------------- actions -----------------
    def log_action(self, submission_id: int, actor: str, action: str, details: str = "") -> None:
        now = self._now()
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO submission_actions (submission_id, created_at, actor, action, details)
                VALUES (?, ?, ?, ?, ?)
                """,
                (int(submission_id), now, actor or "system", action or "ACTION", details or ""),
            )

    def get_actions(self, submission_id: int, limit: int = 200) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT created_at, actor, action, details
                FROM submission_actions
                WHERE submission_id=?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (int(submission_id), int(limit)),
            ).fetchall()
        return [dict(r) for r in rows]
'''
# services/submissions_store.py
import os
import json
import secrets
import libsql_experimental as libsql
from datetime import datetime
from typing import Any, Dict, List, Optional


class SubmissionStore:
    def __init__(self):
        url = os.getenv("TURSO_URL")
        token = os.getenv("TURSO_AUTH_TOKEN")

        if url and token:
            # Production: Turso cloud
            self.conn = libsql.connect(database=url, auth_token=token)
        else:
            # Local development: local SQLite file
            os.makedirs("data", exist_ok=True)
            self.conn = libsql.connect(database="data/submissions.db")

        self._init_db()

    def _init_db(self) -> None:
        self.conn.execute("""
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
                interest_details TEXT,
                extracurriculars TEXT,
                location TEXT,
                preferences TEXT,
                status TEXT NOT NULL DEFAULT 'NEW',
                resume_token TEXT NOT NULL,
                roadmap_md TEXT,
                ui_programs_json TEXT,
                ui_timeline_json TEXT,
                ui_projects_json TEXT,
                email_subject TEXT,
                email_body_text TEXT,
                sent_at TEXT,
                github_issue_number INTEGER,
                github_issue_url TEXT,
                github_assignee TEXT,
                github_status TEXT
            );
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS submission_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT
            );
        """)
        self.conn.commit()

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
        except:
            pass
        if isinstance(o, set):
            return list(o)
        if isinstance(o, (bytes, bytearray)):
            try:
                return o.decode("utf-8")
            except:
                return str(o)
        return str(o)

    def _dumps(self, obj: Any) -> str:
        return json.dumps(obj, ensure_ascii=False, default=self._json_default)

    @staticmethod
    def _loads(s: Optional[str], default):
        if not s:
            return default
        try:
            return json.loads(s)
        except:
            return default

    def _row_to_dict(self, row, columns) -> dict:
        """Convert a row tuple to dictionary"""
        if row is None:
            return None
        return dict(zip(columns, row))

    def _fetchone_as_dict(self, cursor) -> Optional[dict]:
        """Fetch one row as dictionary"""
        row = cursor.fetchone()
        if row is None:
            return None
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))

    def _fetchall_as_dict(self, cursor) -> List[dict]:
        """Fetch all rows as dictionaries"""
        rows = cursor.fetchall()
        if not rows:
            return []
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    # ===================== Student Flow =====================

    def create_submission(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        resume_token = secrets.token_urlsafe(16)
        now = self._now()

        subjects = payload.get("subjects") or []
        if not isinstance(subjects, list):
            subjects = [str(subjects)]

        cur = self.conn.execute(
            """
            INSERT INTO submissions (
                created_at, updated_at, student_name, student_email, wants_email,
                grade, average, subjects_json, interests, interest_details,
                extracurriculars, location, preferences, status, resume_token, github_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now, now,
                payload.get("student_name") or "Student",
                payload.get("student_email") or "",
                1 if payload.get("wants_email") else 0,
                payload.get("grade") or "",
                float(payload.get("average") or 0.0),
                self._dumps(subjects),
                payload.get("interests") or "",
                payload.get("interest_details") or "",
                payload.get("extracurriculars") or "",
                payload.get("location") or "",
                payload.get("preferences") or "",
                "NEW",
                resume_token,
                payload.get("github_status") or "",
            ),
        )
        self.conn.commit()
        new_id = cur.lastrowid

        try:
            self.log_action(int(new_id), "student", "SUBMITTED", "Created submission")
        except:
            pass

        return {"id": int(new_id), "resume_token": resume_token}

    def save_generated_plan(
        self,
        submission_id: int,
        roadmap_md: str,
        ui_programs: List[Dict[str, Any]],
        ui_timeline: List[Dict[str, Any]],
        ui_projects: List[Dict[str, Any]],
        actor: str = "system",
    ) -> None:
        now = self._now()
        self.conn.execute(
            """
            UPDATE submissions
            SET updated_at=?, status='GENERATED', roadmap_md=?,
                ui_programs_json=?, ui_timeline_json=?, ui_projects_json=?
            WHERE id=?
            """,
            (
                now,
                roadmap_md or "",
                self._dumps(ui_programs or []),
                self._dumps(ui_timeline or []),
                self._dumps(ui_projects or []),
                int(submission_id),
            ),
        )
        self.conn.commit()

        try:
            self.log_action(int(submission_id), actor or "system", "GENERATED_PLAN", "Stored generated plan")
        except:
            pass

    def get_by_resume_code(self, submission_id: int, token: str) -> Optional[Dict[str, Any]]:
        cur = self.conn.execute(
            "SELECT * FROM submissions WHERE id=? AND resume_token=?",
            (int(submission_id), token),
        )
        return self._fetchone_as_dict(cur)

    def unpack(self, sub: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(sub)
        out["subjects"] = self._loads(sub.get("subjects_json"), [])
        out["ui_programs"] = self._loads(sub.get("ui_programs_json"), [])
        out["ui_timeline"] = self._loads(sub.get("ui_timeline_json"), [])
        out["ui_projects"] = self._loads(sub.get("ui_projects_json"), [])
        return out

    # ===================== Admin Flow =====================

    def list_queue(self, status_filter: str = "ALL", query: str = "", limit: int = 200) -> List[Dict[str, Any]]:
        status_filter = (status_filter or "ALL").strip().upper()
        query = (query or "").strip()
    
        where = ["wants_email=1"]
        params: List[Any] = []
    
        if status_filter != "ALL":
            where.append("status=?")
            params.append(status_filter)
    
        if query:
            where.append("(student_name LIKE ? OR student_email LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])
    
        sql = f"""
            SELECT id, created_at, student_name, student_email, wants_email, status
            FROM submissions
            WHERE {' AND '.join(where)}
            ORDER BY created_at DESC
            LIMIT ?
        """
        params.append(int(limit))
    
        # ✅ Convert list to tuple
        cur = self.conn.execute(sql, tuple(params))
        return self._fetchall_as_dict(cur)

    def get_next_pending(self) -> Optional[Dict[str, Any]]:
        cur = self.conn.execute(
            """
            SELECT * FROM submissions
            WHERE wants_email=1 AND status IN ('GENERATED','NEW','IN_REVIEW')
            ORDER BY
                CASE status
                    WHEN 'GENERATED' THEN 0
                    WHEN 'NEW' THEN 1
                    WHEN 'IN_REVIEW' THEN 2
                    ELSE 9
                END,
                created_at ASC
            LIMIT 1
            """
        )
        return self._fetchone_as_dict(cur)

    def admin_get(self, submission_id: int) -> Optional[Dict[str, Any]]:
        cur = self.conn.execute("SELECT * FROM submissions WHERE id=?", (int(submission_id),))
        return self._fetchone_as_dict(cur)

    def admin_save_email(self, submission_id: int, subject: str, body_text: str, actor: str = "admin") -> None:
        now = self._now()
        self.conn.execute(
            """
            UPDATE submissions
            SET updated_at=?, status='IN_REVIEW', email_subject=?, email_body_text=?
            WHERE id=?
            """,
            (now, subject or "", body_text or "", int(submission_id)),
        )
        self.conn.commit()
        self.log_action(int(submission_id), actor or "admin", "SAVED_EMAIL", "Saved email draft")

    def admin_mark_sent(self, submission_id: int, actor: str = "admin") -> None:
        now = self._now()
        self.conn.execute(
            """
            UPDATE submissions
            SET updated_at=?, status='SENT', sent_at=?
            WHERE id=?
            """,
            (now, now, int(submission_id)),
        )
        self.conn.commit()
        self.log_action(int(submission_id), actor or "admin", "MARKED_SENT", "Marked sent")

    # ===================== GitHub Issue Helpers =====================

    def set_github_issue(
        self,
        submission_id: int,
        issue_number: int,
        issue_url: str,
        assignee: str,
        github_status: str,
    ) -> None:
        now = self._now()
        self.conn.execute(
            """
            UPDATE submissions
            SET updated_at=?, github_issue_number=?, github_issue_url=?,
                github_assignee=?, github_status=?
            WHERE id=?
            """,
            (now, int(issue_number), issue_url or "", assignee or "", github_status or "", int(submission_id)),
        )
        self.conn.commit()
        self.log_action(int(submission_id), "system", "GITHUB_ISSUE_SET", f"Issue #{issue_number} {github_status}")

    def set_github_status(self, submission_id: int, github_status: str) -> None:
        now = self._now()
        self.conn.execute(
            """
            UPDATE submissions
            SET updated_at=?, github_status=?
            WHERE id=?
            """,
            (now, github_status or "", int(submission_id)),
        )
        self.conn.commit()
        self.log_action(int(submission_id), "system", "GITHUB_STATUS", github_status or "")

    # ===================== Actions Log =====================

    def log_action(self, submission_id: int, actor: str, action: str, details: str = "") -> None:
        now = self._now()
        self.conn.execute(
            """
            INSERT INTO submission_actions (submission_id, created_at, actor, action, details)
            VALUES (?, ?, ?, ?, ?)
            """,
            (int(submission_id), now, actor or "system", action or "ACTION", details or ""),
        )
        self.conn.commit()

    def get_actions(self, submission_id: int, limit: int = 200) -> List[Dict[str, Any]]:
        cur = self.conn.execute(
            """
            SELECT created_at, actor, action, details
            FROM submission_actions
            WHERE submission_id=?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (int(submission_id), int(limit)),
        )
        return self._fetchall_as_dict(cur)

    # ===================== View & Clear (Admin) =====================

    def view_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        cur = self.conn.execute(
            "SELECT * FROM submissions ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        return self._fetchall_as_dict(cur)

    def get_stats(self) -> Dict[str, Any]:
        total = self.conn.execute("SELECT COUNT(*) FROM submissions").fetchone()[0]
        by_status_rows = self.conn.execute(
            "SELECT status, COUNT(*) as c FROM submissions GROUP BY status"
        ).fetchall()
        by_status = {row[0]: row[1] for row in by_status_rows}

        return {
            "total_submissions": total,
            "by_status": by_status
        }

    def clear_all(self) -> int:
        """Delete all submissions and actions"""
        self.conn.execute("DELETE FROM submission_actions")
        cur = self.conn.execute("DELETE FROM submissions")
        self.conn.commit()
        return cur.rowcount

    def delete_one(self, submission_id: int) -> bool:
        """Delete a single submission"""
        self.conn.execute("DELETE FROM submission_actions WHERE submission_id=?", (submission_id,))
        cur = self.conn.execute("DELETE FROM submissions WHERE id=?", (submission_id,))
        self.conn.commit()
        return cur.rowcount > 0
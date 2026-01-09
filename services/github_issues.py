# services/github_issues.py
import os
import logging
from typing import Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger("saarthi.github")


class GitHubIssuesClient:
    """
    Creates + updates GitHub Issues for email requests.
    Designed for PUBLIC repos: do NOT put student name/email in issue body.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        assignees_csv: Optional[str] = None,
    ):
        self.token = token or os.getenv("GITHUB_TOKEN", "").strip()
        self.owner = owner or os.getenv("GITHUB_OWNER", "").strip()
        self.repo = repo or os.getenv("GITHUB_REPO", "").strip()
        self.assignees = self._parse_assignees(assignees_csv or os.getenv("GITHUB_ASSIGNEES", ""))

        self.api_base = os.getenv("GITHUB_API_BASE", "https://api.github.com").rstrip("/")
        self.api_version = os.getenv("GITHUB_API_VERSION", "2022-11-28")

    @staticmethod
    def _parse_assignees(s: str) -> List[str]:
        return [x.strip() for x in (s or "").split(",") if x.strip()]

    @property
    def enabled(self) -> bool:
        return bool(self.token and self.owner and self.repo)

    def _headers(self) -> Dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": self.api_version,
        }

    def _pick_assignee(self, submission_id: int) -> Optional[str]:
        if not self.assignees:
            return None
        return self.assignees[int(submission_id) % len(self.assignees)]

    def create_email_request_issue(
        self,
        submission_id: int,
        resume_code: str,
        grade: str,
        average: float,
        interests: str,
    ) -> Tuple[Optional[int], Optional[str], Optional[str]]:
        """
        Returns (issue_number, issue_url, assignee)
        """
        if not self.enabled:
            logger.warning("GitHubIssuesClient not enabled (missing env vars).")
            return None, None, None

        assignee = self._pick_assignee(submission_id)

        title = f"Email request: Submission #{submission_id}"
        public_url = os.getenv("PUBLIC_STATUS_URL", "").strip()

        body_lines = [
            "A student requested an emailed roadmap.",
            "",
            "### Internal references (no PII)",
            f"- Submission ID: `{submission_id}`",
            f"- Resume code: `{resume_code}`",
            "",
            "### Snapshot (non-identifying)",
            f"- Grade: {grade}",
            f"- Average: {average}%",
            f"- Interests: {interests or '—'}",
            "",
            "### Workflow",
            "- Generate + review the email draft in the Admin panel",
            "- Mark SENT after sending",
        ]
        if public_url:
            body_lines += ["", f"Public site: {public_url}"]

        payload: Dict[str, object] = {
            "title": title,
            "body": "\n".join(body_lines),
            "labels": ["email-request", "status:NEW"],
        }
        if assignee:
            # GitHub supports "assignees": [...] (preferred)
            payload["assignees"] = [assignee]

        url = f"{self.api_base}/repos/{self.owner}/{self.repo}/issues"

        try:
            with httpx.Client(timeout=15) as client:
                r = client.post(url, headers=self._headers(), json=payload)
                r.raise_for_status()
                data = r.json()
                issue_number = int(data.get("number"))
                issue_url = data.get("html_url")
                logger.info(f"Created issue #{issue_number} for submission {submission_id}")
                return issue_number, issue_url, assignee
        except Exception as e:
            logger.exception(f"Failed creating GitHub issue for submission {submission_id}: {e}")
            return None, None, assignee

    def set_issue_status(
        self,
        issue_number: int,
        status_label: str,
        close: bool = False,
        extra_labels: Optional[List[str]] = None,
    ) -> bool:
        """
        Updates labels + optionally closes issue.
        Uses PATCH /repos/{owner}/{repo}/issues/{issue_number}
        """
        if not self.enabled:
            return False

        labels = ["email-request", status_label]
        if extra_labels:
            labels.extend([x for x in extra_labels if x and x not in labels])

        url = f"{self.api_base}/repos/{self.owner}/{self.repo}/issues/{int(issue_number)}"
        payload: Dict[str, object] = {"labels": labels}
        if close:
            payload["state"] = "closed"

        try:
            with httpx.Client(timeout=15) as client:
                r = client.patch(url, headers=self._headers(), json=payload)
                r.raise_for_status()
            return True
        except Exception as e:
            logger.exception(f"Failed updating issue #{issue_number}: {e}")
            return False

    def comment(self, issue_number: int, comment: str) -> bool:
        if not self.enabled:
            return False
        url = f"{self.api_base}/repos/{self.owner}/{self.repo}/issues/{int(issue_number)}/comments"
        try:
            with httpx.Client(timeout=15) as client:
                r = client.post(url, headers=self._headers(), json={"body": comment})
                r.raise_for_status()
            return True
        except Exception as e:
            logger.exception(f"Failed commenting on issue #{issue_number}: {e}")
            return False

# services/github_issues.py
"""
GitHub Issues integration for email workflow tracking.
Creates and updates issues for email requests (public-repo safe).
"""

import os
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import httpx

logger = logging.getLogger("saarthi.github")


class GitHubErrorType(Enum):
    """Categorized GitHub API errors"""
    DISABLED = "disabled"
    AUTH_FAILED = "auth_failed"
    NOT_FOUND = "not_found"
    FORBIDDEN = "forbidden"
    RATE_LIMITED = "rate_limited"
    VALIDATION_ERROR = "validation_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"


@dataclass
class GitHubResult:
    """Result wrapper for GitHub operations"""
    success: bool
    issue_number: Optional[int] = None
    issue_url: Optional[str] = None
    assignee: Optional[str] = None
    error_type: Optional[GitHubErrorType] = None
    error_message: Optional[str] = None

    @classmethod
    def ok(cls, issue_number: int, issue_url: str, assignee: Optional[str] = None) -> "GitHubResult":
        return cls(success=True, issue_number=issue_number, issue_url=issue_url, assignee=assignee)

    @classmethod
    def fail(cls, error_type: GitHubErrorType, message: str, assignee: Optional[str] = None) -> "GitHubResult":
        return cls(success=False, error_type=error_type, error_message=message, assignee=assignee)


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
        # Defer reading env vars to allow late binding
        self._token_override = token
        self._owner_override = owner
        self._repo_override = repo
        self._assignees_override = assignees_csv
        
        self._api_base = None
        self._api_version = None
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Lazy initialization to pick up env vars set after import"""
        if self._initialized:
            return
            
        self.token = (self._token_override or os.getenv("GITHUB_TOKEN", "")).strip()
        self.owner = (self._owner_override or os.getenv("GITHUB_OWNER", "")).strip()
        self.repo = (self._repo_override or os.getenv("GITHUB_REPO", "")).strip()
        self.assignees = self._parse_assignees(
            self._assignees_override or os.getenv("GITHUB_ASSIGNEES", "")
        )
        self.api_base = os.getenv("GITHUB_API_BASE", "https://api.github.com").rstrip("/")
        self.api_version = os.getenv("GITHUB_API_VERSION", "2022-11-28")
        
        self._initialized = True
        
        # Log configuration status
        self._log_config_status()

    def _log_config_status(self) -> None:
        """Log configuration for debugging"""
        token_status = "✓ set" if self.token else "✗ missing"
        owner_status = f"✓ {self.owner}" if self.owner else "✗ missing"
        repo_status = f"✓ {self.repo}" if self.repo else "✗ missing"
        assignees_status = f"✓ {self.assignees}" if self.assignees else "○ none"
        
        logger.info(f"GitHub Issues Config: token={token_status}, owner={owner_status}, repo={repo_status}, assignees={assignees_status}")
        
        if not self.enabled:
            missing = []
            if not self.token:
                missing.append("GITHUB_TOKEN")
            if not self.owner:
                missing.append("GITHUB_OWNER")
            if not self.repo:
                missing.append("GITHUB_REPO")
            logger.warning(f"GitHub Issues DISABLED — missing env vars: {', '.join(missing)}")

    @staticmethod
    def _parse_assignees(s: str) -> List[str]:
        return [x.strip() for x in (s or "").split(",") if x.strip()]

    @property
    def enabled(self) -> bool:
        self._ensure_initialized()
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

    def _parse_github_error(self, response: httpx.Response) -> Tuple[GitHubErrorType, str]:
        """Parse GitHub API error response"""
        status = response.status_code
        
        try:
            body = response.json()
            message = body.get("message", "Unknown error")
            errors = body.get("errors", [])
            if errors:
                error_details = "; ".join([e.get("message", str(e)) for e in errors])
                message = f"{message}: {error_details}"
        except Exception:
            message = response.text[:200] if response.text else f"HTTP {status}"

        if status == 401:
            return GitHubErrorType.AUTH_FAILED, f"Authentication failed: {message}. Check GITHUB_TOKEN."
        elif status == 403:
            if "rate limit" in message.lower():
                return GitHubErrorType.RATE_LIMITED, f"Rate limited: {message}"
            return GitHubErrorType.FORBIDDEN, f"Forbidden: {message}. Check token permissions (needs 'repo' or 'public_repo' scope)."
        elif status == 404:
            return GitHubErrorType.NOT_FOUND, f"Not found: {message}. Check GITHUB_OWNER/GITHUB_REPO exist and token has access."
        elif status == 422:
            return GitHubErrorType.VALIDATION_ERROR, f"Validation error: {message}"
        else:
            return GitHubErrorType.UNKNOWN, f"HTTP {status}: {message}"

    def test_connection(self) -> GitHubResult:
        """Test GitHub API connection and permissions"""
        self._ensure_initialized()
        
        if not self.enabled:
            missing = []
            if not self.token:
                missing.append("GITHUB_TOKEN")
            if not self.owner:
                missing.append("GITHUB_OWNER")
            if not self.repo:
                missing.append("GITHUB_REPO")
            return GitHubResult.fail(
                GitHubErrorType.DISABLED,
                f"GitHub integration disabled. Missing: {', '.join(missing)}"
            )
        
        # Test API access by getting repo info
        url = f"{self.api_base}/repos/{self.owner}/{self.repo}"
        
        try:
            with httpx.Client(timeout=10) as client:
                r = client.get(url, headers=self._headers())
                
                if r.status_code == 200:
                    repo_data = r.json()
                    has_issues = repo_data.get("has_issues", False)
                    if not has_issues:
                        return GitHubResult.fail(
                            GitHubErrorType.FORBIDDEN,
                            f"Repository '{self.owner}/{self.repo}' has issues disabled. Enable them in repo settings."
                        )
                    return GitHubResult.ok(0, "", None)
                else:
                    error_type, error_msg = self._parse_github_error(r)
                    return GitHubResult.fail(error_type, error_msg)
                    
        except httpx.TimeoutException:
            return GitHubResult.fail(GitHubErrorType.NETWORK_ERROR, "Connection timeout")
        except httpx.ConnectError as e:
            return GitHubResult.fail(GitHubErrorType.NETWORK_ERROR, f"Connection failed: {e}")
        except Exception as e:
            return GitHubResult.fail(GitHubErrorType.UNKNOWN, str(e))

    def create_email_request_issue(
        self,
        submission_id: int,
        resume_code: str,
        grade: str,
        average: float,
        interests: str,
    ) -> GitHubResult:
        """
        Create a GitHub issue for email request tracking.
        Returns GitHubResult with success/failure info.
        """
        self._ensure_initialized()
        
        assignee = self._pick_assignee(submission_id)
        
        if not self.enabled:
            logger.warning("GitHub Issues not enabled — skipping issue creation")
            return GitHubResult.fail(
                GitHubErrorType.DISABLED,
                "GitHub integration not configured",
                assignee
            )

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
            "1. Open Admin Panel in Saarthi",
            "2. Load this submission by ID",
            "3. Click 'Auto-fill Email' to generate draft",
            "4. Review and edit the email",
            "5. Send email manually",
            "6. Click 'Mark Sent' to close this issue",
        ]
        if public_url:
            body_lines += ["", f"🔗 App: {public_url}"]

        payload: Dict[str, object] = {
            "title": title,
            "body": "\n".join(body_lines),
            "labels": ["email-request", "status:NEW"],
        }
        if assignee:
            payload["assignees"] = [assignee]

        url = f"{self.api_base}/repos/{self.owner}/{self.repo}/issues"

        logger.info(f"Creating GitHub issue for submission #{submission_id}...")
        logger.debug(f"POST {url}")
        logger.debug(f"Assignee: {assignee or 'none'}")

        try:
            with httpx.Client(timeout=15) as client:
                r = client.post(url, headers=self._headers(), json=payload)
                
                if r.status_code in (200, 201):
                    data = r.json()
                    issue_number = int(data.get("number"))
                    issue_url = data.get("html_url", "")
                    
                    logger.info(f"✅ Created GitHub issue #{issue_number}: {issue_url}")
                    return GitHubResult.ok(issue_number, issue_url, assignee)
                else:
                    error_type, error_msg = self._parse_github_error(r)
                    logger.error(f"❌ GitHub API error: {error_msg}")
                    return GitHubResult.fail(error_type, error_msg, assignee)
                    
        except httpx.TimeoutException:
            error_msg = "GitHub API timeout (15s). Check network connectivity."
            logger.error(f"❌ {error_msg}")
            return GitHubResult.fail(GitHubErrorType.NETWORK_ERROR, error_msg, assignee)
        except httpx.ConnectError as e:
            error_msg = f"Cannot connect to GitHub API: {e}"
            logger.error(f"❌ {error_msg}")
            return GitHubResult.fail(GitHubErrorType.NETWORK_ERROR, error_msg, assignee)
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.exception(f"❌ {error_msg}")
            return GitHubResult.fail(GitHubErrorType.UNKNOWN, error_msg, assignee)

    def set_issue_status(
        self,
        issue_number: int,
        status_label: str,
        close: bool = False,
        extra_labels: Optional[List[str]] = None,
    ) -> GitHubResult:
        """
        Update issue labels and optionally close it.
        """
        self._ensure_initialized()
        
        if not self.enabled:
            return GitHubResult.fail(GitHubErrorType.DISABLED, "GitHub integration not configured")

        labels = ["email-request", status_label]
        if extra_labels:
            labels.extend([x for x in extra_labels if x and x not in labels])

        url = f"{self.api_base}/repos/{self.owner}/{self.repo}/issues/{int(issue_number)}"
        payload: Dict[str, object] = {"labels": labels}
        if close:
            payload["state"] = "closed"

        logger.info(f"Updating issue #{issue_number}: labels={labels}, close={close}")

        try:
            with httpx.Client(timeout=15) as client:
                r = client.patch(url, headers=self._headers(), json=payload)
                
                if r.status_code == 200:
                    logger.info(f"✅ Updated issue #{issue_number}")
                    return GitHubResult.ok(issue_number, "", None)
                else:
                    error_type, error_msg = self._parse_github_error(r)
                    logger.error(f"❌ Failed to update issue #{issue_number}: {error_msg}")
                    return GitHubResult.fail(error_type, error_msg)
                    
        except Exception as e:
            error_msg = f"Failed to update issue: {e}"
            logger.exception(error_msg)
            return GitHubResult.fail(GitHubErrorType.UNKNOWN, error_msg)

    def comment(self, issue_number: int, comment: str) -> GitHubResult:
        """Add a comment to an issue"""
        self._ensure_initialized()
        
        if not self.enabled:
            return GitHubResult.fail(GitHubErrorType.DISABLED, "GitHub integration not configured")
            
        url = f"{self.api_base}/repos/{self.owner}/{self.repo}/issues/{int(issue_number)}/comments"
        
        try:
            with httpx.Client(timeout=15) as client:
                r = client.post(url, headers=self._headers(), json={"body": comment})
                
                if r.status_code in (200, 201):
                    logger.info(f"✅ Added comment to issue #{issue_number}")
                    return GitHubResult.ok(issue_number, "", None)
                else:
                    error_type, error_msg = self._parse_github_error(r)
                    logger.error(f"❌ Failed to comment on issue #{issue_number}: {error_msg}")
                    return GitHubResult.fail(error_type, error_msg)
                    
        except Exception as e:
            error_msg = f"Failed to add comment: {e}"
            logger.exception(error_msg)
            return GitHubResult.fail(GitHubErrorType.UNKNOWN, error_msg)


# Convenience function for quick diagnostics
def diagnose_github_config() -> str:
    """Run diagnostics and return a human-readable report"""
    client = GitHubIssuesClient()
    
    lines = ["## GitHub Integration Diagnostics", ""]
    
    # Check env vars
    token = os.getenv("GITHUB_TOKEN", "")
    owner = os.getenv("GITHUB_OWNER", "")
    repo = os.getenv("GITHUB_REPO", "")
    assignees = os.getenv("GITHUB_ASSIGNEES", "")
    
    lines.append("### Environment Variables")
    lines.append(f"- `GITHUB_TOKEN`: {'✅ Set (' + str(len(token)) + ' chars)' if token else '❌ Missing'}")
    lines.append(f"- `GITHUB_OWNER`: {'✅ ' + owner if owner else '❌ Missing'}")
    lines.append(f"- `GITHUB_REPO`: {'✅ ' + repo if repo else '❌ Missing'}")
    lines.append(f"- `GITHUB_ASSIGNEES`: {'✅ ' + assignees if assignees else '⚪ Not set (optional)'}")
    lines.append("")
    
    if not client.enabled:
        lines.append("### Status: ❌ DISABLED")
        lines.append("Set the missing environment variables to enable GitHub integration.")
        return "\n".join(lines)
    
    # Test connection
    lines.append("### Connection Test")
    result = client.test_connection()
    
    if result.success:
        lines.append(f"✅ Successfully connected to `{owner}/{repo}`")
        lines.append("GitHub integration is ready!")
    else:
        lines.append(f"❌ Connection failed: {result.error_message}")
        
        # Provide specific guidance
        if result.error_type == GitHubErrorType.AUTH_FAILED:
            lines.append("")
            lines.append("**Fix:** Generate a new GitHub token with correct permissions:")
            lines.append("1. Go to GitHub → Settings → Developer Settings → Personal Access Tokens")
            lines.append("2. Create a token with `repo` scope (or `public_repo` for public repos)")
            lines.append("3. Set `GITHUB_TOKEN` to the new token")
        elif result.error_type == GitHubErrorType.NOT_FOUND:
            lines.append("")
            lines.append("**Fix:** Check repository exists and token has access:")
            lines.append(f"1. Verify `{owner}/{repo}` exists on GitHub")
            lines.append("2. Ensure your token has access to this repository")
        elif result.error_type == GitHubErrorType.FORBIDDEN:
            lines.append("")
            lines.append("**Fix:** Check repository settings and token permissions:")
            lines.append("1. Enable Issues in repository settings")
            lines.append("2. Ensure token has `repo` or `public_repo` scope")
    
    return "\n".join(lines)
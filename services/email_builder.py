# services/email_builder.py
from typing import Dict, Any

def build_email_from_submission(sub: Dict[str, Any]) -> Dict[str, str]:
    name = (sub.get("student_name") or "Student").strip() or "Student"
    grade = sub.get("grade", "")
    avg = sub.get("average", "")
    interests = sub.get("interests", "")
    token = (sub.get("resume_token") or "")[:8]
    roadmap_md = (sub.get("roadmap_md") or "").strip()

    subject = f"Your Personalized University Roadmap ({token})"

    intro = (
        f"Hi {name},\n\n"
        "Thanks for submitting your info. Here is your personalized roadmap.\n\n"
        "Profile snapshot:\n"
        f"- Grade: {grade}\n"
        f"- Average: {avg}%\n"
        f"- Interests: {interests}\n\n"
    )

    outro = (
        "\n\nIf you’d like, reply with follow-up questions and we can refine the plan.\n"
        "— Saarthi Team"
    )

    body_text = intro + roadmap_md + outro
    return {"subject": subject, "body_text": body_text}

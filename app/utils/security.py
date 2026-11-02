"""
Security utilities — validation, file safety, sanitization.
"""
import os
import re
import bleach


ALLOWED_TAGS = []  # No HTML allowed in user inputs
MAX_SKILL_LENGTH = 50
MAX_SKILLS_COUNT = 30


def sanitize_text(text: str, max_length: int = None) -> str:
    """Strip HTML and trim text. Bleach ensures no XSS."""
    if not text:
        return ''
    cleaned = bleach.clean(text, tags=ALLOWED_TAGS, strip=True)
    if max_length:
        cleaned = cleaned[:max_length]
    return cleaned.strip()


def validate_skills_input(skills_str: str) -> tuple:
    """
    Validate and normalize a comma-separated skills string.
    Returns (normalized_str, error_message or None)
    """
    if not skills_str:
        return '', None
    skills = [s.strip() for s in skills_str.split(',') if s.strip()]
    if len(skills) > MAX_SKILLS_COUNT:
        return '', f'Too many skills listed. Maximum is {MAX_SKILLS_COUNT}.'
    for skill in skills:
        if len(skill) > MAX_SKILL_LENGTH:
            return '', f'Each skill must be under {MAX_SKILL_LENGTH} characters.'
        if re.search(r'[<>&"\']', skill):
            return '', 'Skills must not contain special characters.'
    return ', '.join(skills), None


def is_safe_path(basedir: str, path: str) -> bool:
    """Prevent path traversal attacks."""
    abs_path = os.path.realpath(path)
    abs_base = os.path.realpath(basedir)
    return abs_path.startswith(abs_base)


def validate_url(url: str) -> bool:
    """Basic URL validation."""
    if not url:
        return True  # Empty is OK
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url, re.IGNORECASE))


def validate_email(email: str) -> bool:
    """Basic email validation."""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

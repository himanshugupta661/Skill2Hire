"""
Resume Service - PDF text extraction and skill identification.
Uses PyMuPDF for text extraction and regex + skill dictionaries for analysis.
"""
import os
import re
import uuid
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Comprehensive skill dictionary for Indian job market
SKILL_DICTIONARY = {
    # Programming languages
    'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'golang',
    'ruby', 'php', 'swift', 'kotlin', 'scala', 'rust', 'r', 'matlab', 'perl',
    # Web frameworks
    'react', 'angular', 'vue', 'django', 'flask', 'fastapi', 'spring', 'node.js',
    'nodejs', 'express', 'nextjs', 'nuxt', 'laravel', 'rails', 'asp.net',
    # Databases
    'sql', 'mysql', 'postgresql', 'postgres', 'mongodb', 'redis', 'elasticsearch',
    'oracle', 'sqlite', 'cassandra', 'dynamodb', 'neo4j', 'firebase',
    # Cloud & DevOps
    'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'k8s',
    'terraform', 'ansible', 'jenkins', 'gitlab', 'github actions', 'ci/cd',
    'devops', 'linux', 'bash', 'shell scripting',
    # Data & AI/ML
    'machine learning', 'deep learning', 'nlp', 'computer vision', 'tensorflow',
    'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy', 'spark', 'hadoop',
    'data analysis', 'data science', 'power bi', 'tableau', 'excel', 'matplotlib',
    'seaborn', 'airflow', 'kafka', 'etl',
    # Mobile
    'android', 'ios', 'react native', 'flutter', 'xamarin',
    # Testing
    'selenium', 'pytest', 'junit', 'jest', 'cypress', 'postman',
    # Project management
    'agile', 'scrum', 'kanban', 'jira', 'confluence', 'trello',
    # Design
    'figma', 'sketch', 'adobe xd', 'photoshop', 'illustrator',
    # Networking
    'networking', 'tcp/ip', 'dns', 'vpn', 'firewall', 'cisco',
    # Other tech
    'git', 'restful api', 'graphql', 'microservices', 'soa', 'xml', 'json',
    'html', 'css', 'bootstrap', 'tailwind', 'sass', 'webpack',
}

# Degree patterns for education extraction
DEGREE_PATTERNS = [
    r'\b(b\.?tech|bachelor of technology|be\b|b\.e\.)\b',
    r'\b(m\.?tech|master of technology|me\b|m\.e\.)\b',
    r'\b(b\.?sc|bachelor of science|bsc)\b',
    r'\b(m\.?sc|master of science|msc)\b',
    r'\b(mba|master of business administration)\b',
    r'\b(bca|bachelor of computer application)\b',
    r'\b(mca|master of computer application)\b',
    r'\b(b\.?com|bachelor of commerce)\b',
    r'\b(bba|bachelor of business administration)\b',
    r'\b(ph\.?d|doctorate|phd)\b',
    r'\b(diploma)\b',
    r'\b(12th|10\+2|hsc|higher secondary)\b',
]


def extract_text_from_pdf(file_path: str) -> Tuple[str, str]:
    """
    Extract text from a PDF file using PyMuPDF.
    Returns (extracted_text, status) where status is one of:
    'success', 'empty', 'protected', 'corrupted', 'error'
    """
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)

        if doc.is_encrypted:
            doc.close()
            return '', 'protected'

        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()

        full_text = '\n'.join(text_parts).strip()
        if not full_text:
            return '', 'empty'
        return full_text, 'success'

    except Exception as e:
        logger.error(f'PDF extraction error for {file_path}: {e}')
        return '', 'error'


def extract_email(text: str) -> Optional[str]:
    """Extract email from resume text."""
    pattern = r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'
    match = re.search(pattern, text)
    return match.group(0) if match else None


def extract_phone(text: str) -> Optional[str]:
    """Extract Indian phone number from resume text."""
    patterns = [
        r'(?:\+91[\s\-]?)?[6-9]\d{9}',
        r'\b0\d{2,4}[\s\-]?\d{6,8}\b',
    ]
    for pat in patterns:
        match = re.search(pat, text)
        if match:
            return match.group(0).strip()
    return None


def extract_skills_from_text(text: str) -> list:
    """
    Extract skills from resume text by matching against skill dictionary.
    Returns list of normalized skill names found.
    Note: This is rule-based and may miss skills or produce false positives.
    """
    text_lower = text.lower()
    found = []
    for skill in SKILL_DICTIONARY:
        # Use word boundary where applicable
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found.append(skill)
    return sorted(found)


def extract_education(text: str) -> list:
    """Extract education mentions from resume text."""
    text_lower = text.lower()
    found = []
    for pattern in DEGREE_PATTERNS:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        found.extend(matches)
    return list(set(found))


def generate_safe_filename(original_filename: str, user_id: int) -> str:
    """
    Generate a safe, unique server-side filename.
    Never uses the original filename on the server to prevent path traversal.
    """
    ext = '.pdf'  # Only PDFs are accepted
    unique_id = uuid.uuid4().hex
    return f"resume_{user_id}_{unique_id}{ext}"


def validate_pdf_upload(file) -> Tuple[bool, str]:
    """
    Validate uploaded file is actually a PDF.
    Checks extension and magic bytes.
    Returns (is_valid, error_message)
    """
    if not file or not file.filename:
        return False, "No file provided."

    # Check extension
    filename = file.filename.lower()
    if not filename.endswith('.pdf'):
        return False, "Only PDF files are accepted."

    # Read and check magic bytes (PDF starts with %PDF-)
    header = file.read(5)
    file.seek(0)  # Reset for later reading

    if header != b'%PDF-':
        return False, "File does not appear to be a valid PDF."

    return True, ""


def analyze_resume(file_path: str, user_id: int) -> dict:
    """
    Full resume analysis pipeline.
    Returns dict with extracted information and analysis status.
    """
    result = {
        'status': 'pending',
        'text': '',
        'skills': [],
        'email': None,
        'phone': None,
        'education': [],
        'notes': '',
    }

    text, extract_status = extract_text_from_pdf(file_path)

    if extract_status == 'protected':
        result['status'] = 'failed'
        result['notes'] = 'PDF is password-protected and cannot be analyzed.'
        return result

    if extract_status == 'empty':
        result['status'] = 'empty'
        result['notes'] = (
            'No extractable text found. This may be a scanned PDF. '
            'Text extraction works best with text-based PDFs.'
        )
        return result

    if extract_status == 'error':
        result['status'] = 'failed'
        result['notes'] = 'Could not read the PDF file.'
        return result

    result['text'] = text
    result['skills'] = extract_skills_from_text(text)
    result['email'] = extract_email(text)
    result['phone'] = extract_phone(text)
    result['education'] = extract_education(text)
    result['status'] = 'completed'
    result['notes'] = (
        'Analysis complete. Extracted data is based on automated text recognition and '
        'may be incomplete or inaccurate. Please review and update your profile.'
    )
    return result

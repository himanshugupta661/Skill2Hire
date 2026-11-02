"""
Helper utilities.
"""
import re
from datetime import datetime


def normalize_company_name(name: str) -> str:
    """Lowercase, strip, remove extra spaces."""
    if not name:
        return ''
    return re.sub(r'\s+', ' ', name.strip().lower())


def parse_salary(salary_str: str) -> tuple:
    """
    Parse salary string like '5-10 LPA' or '500000-1000000'.
    Returns (min_int, max_int) in INR. Returns (None, None) on failure.
    """
    if not salary_str:
        return None, None
    try:
        # Try to extract numbers
        nums = re.findall(r'[\d.]+', str(salary_str))
        if not nums:
            return None, None
        nums = [float(n) for n in nums]

        # Detect LPA (Lakhs per annum)
        if 'lpa' in salary_str.lower() or 'lakh' in salary_str.lower() or 'lac' in salary_str.lower():
            nums = [int(n * 100000) for n in nums]
        else:
            nums = [int(n) for n in nums]

        if len(nums) == 1:
            return nums[0], nums[0]
        return min(nums), max(nums)
    except Exception:
        return None, None


def parse_experience(exp_str: str) -> tuple:
    """
    Parse experience like '2-5 years' or '3+ years'.
    Returns (min_years, max_years). None values indicate unspecified.
    """
    if not exp_str:
        return None, None
    try:
        exp_lower = str(exp_str).lower()
        nums = re.findall(r'[\d.]+', exp_lower)
        if not nums:
            return None, None
        nums = [float(n) for n in nums]
        if '+' in exp_lower and len(nums) == 1:
            return nums[0], None  # "3+ years"
        if len(nums) == 1:
            return nums[0], nums[0]
        return min(nums), max(nums)
    except Exception:
        return None, None


def format_salary(salary_min, salary_max, currency='INR') -> str:
    """Format salary range for display."""
    if not salary_min and not salary_max:
        return 'Not Disclosed'
    symbol = '₹' if currency == 'INR' else currency

    def fmt(n):
        if n >= 100000:
            return f'{n/100000:.1f}L'
        return f'{n:,}'

    if salary_min and salary_max and salary_min != salary_max:
        return f'{symbol}{fmt(salary_min)} – {symbol}{fmt(salary_max)}'
    elif salary_min:
        return f'{symbol}{fmt(salary_min)}'
    elif salary_max:
        return f'Up to {symbol}{fmt(salary_max)}'
    return 'Not Disclosed'


def time_ago(dt: datetime) -> str:
    """Human-readable time difference."""
    if not dt:
        return 'Unknown'
    diff = datetime.utcnow() - dt
    seconds = diff.total_seconds()
    if seconds < 60:
        return 'Just now'
    elif seconds < 3600:
        mins = int(seconds / 60)
        return f'{mins}m ago'
    elif seconds < 86400:
        hrs = int(seconds / 3600)
        return f'{hrs}h ago'
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f'{days}d ago'
    else:
        return dt.strftime('%d %b %Y')

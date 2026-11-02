"""
AI-Assisted Job Matching Service
Algorithm: Hybrid TF-IDF + Skill Overlap + Experience + Location scoring
All scores are deterministic (no randomness). Weights are configurable via app config.

Matching breakdown (default weights):
  - Required-skill compatibility:   40%
  - Description/profile text TF-IDF: 25%
  - Job-title similarity:            15%
  - Experience compatibility:        10%
  - Location / work-mode preference: 10%

IMPORTANT: This service assists human decision-making and does not automatically
make final hiring decisions. It does not use protected personal characteristics.
"""
import logging
import json
import re
from typing import List, Dict, Optional, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class MatchingService:
    """
    Hybrid job-profile matching engine.
    Produces explainable scores with breakdown.
    """

    def __init__(self, weights=None):
        # Default weights — override via app config
        self.weights = weights or {
            'skills': 0.40,
            'text': 0.25,
            'title': 0.15,
            'experience': 0.10,
            'location': 0.10,
        }
        self._normalize_weights()

    def _normalize_weights(self):
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compute_match(self, profile: dict, job: dict) -> dict:
        """
        Compute a match between a seeker profile and a job listing.

        Args:
            profile: dict with keys: skills, years_of_experience, preferred_roles,
                     preferred_locations, preferred_work_mode, resume_text, etc.
            job: dict with keys: job_title, required_skills, preferred_skills,
                 description, location, work_mode, employment_type,
                 experience_min, experience_max

        Returns:
            dict: {
                score: float (0-100),
                breakdown: { skills, text, title, experience, location },
                matched_required_skills: list,
                missing_required_skills: list,
                matched_preferred_skills: list,
                explanation: str,
                limitations: list
            }
        """
        result = {
            'score': 0.0,
            'breakdown': {},
            'matched_required_skills': [],
            'missing_required_skills': [],
            'matched_preferred_skills': [],
            'explanation': '',
            'limitations': []
        }

        # Extract profile fields
        seeker_skills = self._parse_skills(profile.get('skills', ''))
        seeker_text = self._build_seeker_text(profile)
        years_exp = self._safe_float(profile.get('years_of_experience', 0))
        preferred_locations = self._parse_list(profile.get('preferred_locations', ''))
        preferred_work_mode = (profile.get('preferred_work_mode') or '').lower()

        # Extract job fields
        req_skills = self._parse_skills(job.get('required_skills', ''))
        pref_skills = self._parse_skills(job.get('preferred_skills', ''))
        job_text = self._build_job_text(job)
        job_title = (job.get('job_title') or '').lower()
        job_location = (job.get('location') or '').lower()
        job_work_mode = (job.get('work_mode') or '').lower()
        exp_min = self._safe_float(job.get('experience_min'))
        exp_max = self._safe_float(job.get('experience_max'))

        # 1. Skill score
        skill_score, matched_req, missing_req, matched_pref = self._skill_score(
            seeker_skills, req_skills, pref_skills
        )
        result['matched_required_skills'] = matched_req
        result['missing_required_skills'] = missing_req
        result['matched_preferred_skills'] = matched_pref

        # 2. Text similarity
        text_score, text_limitation = self._text_similarity_score(seeker_text, job_text)
        if text_limitation:
            result['limitations'].append(text_limitation)

        # 3. Title similarity (role match)
        title_score = self._title_score(profile, job_title)

        # 4. Experience compatibility
        exp_score, exp_limitation = self._experience_score(years_exp, exp_min, exp_max)
        if exp_limitation:
            result['limitations'].append(exp_limitation)

        # 5. Location / work-mode
        loc_score = self._location_score(
            preferred_locations, preferred_work_mode, job_location, job_work_mode
        )

        # Weighted total
        breakdown = {
            'skills': round(skill_score * 100, 1),
            'text': round(text_score * 100, 1),
            'title': round(title_score * 100, 1),
            'experience': round(exp_score * 100, 1),
            'location': round(loc_score * 100, 1),
        }
        total = (
            skill_score * self.weights['skills'] +
            text_score * self.weights['text'] +
            title_score * self.weights['title'] +
            exp_score * self.weights['experience'] +
            loc_score * self.weights['location']
        )
        final_score = round(min(max(total * 100, 0.0), 100.0), 1)
        result['score'] = final_score
        result['breakdown'] = breakdown
        result['matching_skills'] = matched_req
        result['missing_skills'] = missing_req
        result['explanation'] = self._build_explanation(
            final_score, matched_req, missing_req, matched_pref,
            years_exp, exp_min, exp_max, preferred_work_mode, job_work_mode,
            job_location, preferred_locations
        )

        return result

    def rank_jobs_for_profile(self, profile: dict, jobs: List[dict], top_n: int = 20) -> List[dict]:
        """Rank a list of jobs by match score for a given profile."""
        results = []
        for job in jobs:
            match = self.compute_match(profile, job)
            results.append({**job, 'match': match})
        results.sort(key=lambda x: x['match']['score'], reverse=True)
        return results[:top_n]

    def rank_applicants_for_job(self, job: dict, profiles: List[dict]) -> List[dict]:
        """Rank applicants by how well their profile matches a job."""
        results = []
        for profile in profiles:
            match = self.compute_match(profile, job)
            results.append({**profile, 'match': match})
        results.sort(key=lambda x: x['match']['score'], reverse=True)
        return results

    # ------------------------------------------------------------------
    # Private scoring methods
    # ------------------------------------------------------------------

    def _skill_score(self, seeker_skills: set, req_skills: set, pref_skills: set
                    ) -> Tuple[float, list, list, list]:
        """
        Compute skill overlap.
        - Required skills: binary match (matched / total)
        - Preferred skills bonus: up to 20% boost on required score
        """
        if not req_skills:
            # No required skills listed — neutral 0.5, note limitation
            return 0.5, [], [], list(seeker_skills & pref_skills)

        matched_req = sorted(seeker_skills & req_skills)
        missing_req = sorted(req_skills - seeker_skills)
        matched_pref = sorted(seeker_skills & pref_skills)

        req_ratio = len(matched_req) / len(req_skills)

        # Preferred skill bonus (max +0.2 of remaining headroom)
        if pref_skills:
            pref_ratio = len(matched_pref) / len(pref_skills)
            bonus = pref_ratio * 0.2 * (1 - req_ratio)
        else:
            bonus = 0.0

        score = min(req_ratio + bonus, 1.0)
        return score, matched_req, missing_req, matched_pref

    def _text_similarity_score(self, seeker_text: str, job_text: str) -> Tuple[float, Optional[str]]:
        """TF-IDF cosine similarity between seeker's combined text and job description."""
        limitation = None
        if not seeker_text or len(seeker_text.split()) < 5:
            limitation = "Profile text is very short; text similarity score may be unreliable."
            return 0.3, limitation
        if not job_text or len(job_text.split()) < 5:
            limitation = "Job description is very short; text similarity score may be unreliable."
            return 0.3, limitation
        try:
            vectorizer = TfidfVectorizer(
                max_features=500, stop_words='english', ngram_range=(1, 2)
            )
            vectors = vectorizer.fit_transform([seeker_text, job_text])
            sim = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            return float(sim), None
        except Exception as e:
            logger.warning(f'TF-IDF failed: {e}')
            return 0.3, f"Text similarity could not be computed: {e}"

    def _title_score(self, profile: dict, job_title: str) -> float:
        """Check if preferred roles or existing experience titles overlap with the job title."""
        preferred = self._parse_list(profile.get('preferred_roles', ''))
        resume_text = (profile.get('resume_text', '') or '').lower()

        if not job_title:
            return 0.5

        # Check if any preferred role overlaps with job title words
        job_words = set(re.findall(r'\b\w+\b', job_title))
        max_sim = 0.0

        for role in preferred:
            role_words = set(re.findall(r'\b\w+\b', role.lower()))
            if job_words and role_words:
                intersection = job_words & role_words
                union = job_words | role_words
                jaccard = len(intersection) / len(union)
                max_sim = max(max_sim, jaccard)

        # Boost if job title appears in resume text
        if job_title and resume_text:
            job_title_words = job_title.split()
            if all(w in resume_text for w in job_title_words):
                max_sim = min(max_sim + 0.3, 1.0)

        return max(max_sim, 0.2)  # Floor: 0.2 (partial credit)

    def _experience_score(self, years_exp: float, exp_min: Optional[float],
                          exp_max: Optional[float]) -> Tuple[float, Optional[str]]:
        """
        Score experience compatibility.
        - Both missing: neutral 0.5
        - Seeker missing: 0.4 (can't confirm, but don't disqualify)
        - In range: 1.0
        - Below min: partial credit based on proximity
        - Above max: slight penalty (overqualified signal)
        """
        if exp_min is None and exp_max is None:
            return 0.5, "Job experience requirements not specified."
        if years_exp is None or years_exp <= 0:
            return 0.4, "Seeker's years of experience not provided."

        lo = exp_min or 0
        hi = exp_max or (lo + 10)

        if lo <= years_exp <= hi:
            return 1.0, None
        elif years_exp < lo:
            gap = lo - years_exp
            score = max(0.0, 1.0 - (gap / max(lo, 1)) * 0.8)
            return score, None
        else:  # overqualified
            return 0.75, None

    def _location_score(self, preferred_locations: list, preferred_work_mode: str,
                        job_location: str, job_work_mode: str) -> float:
        """Score location and work-mode compatibility."""
        score = 0.0

        # Work mode (50% of location score)
        if job_work_mode == 'remote':
            score += 0.5  # Remote is universal
        elif preferred_work_mode and job_work_mode:
            if preferred_work_mode == job_work_mode:
                score += 0.5
            elif 'hybrid' in [preferred_work_mode, job_work_mode]:
                score += 0.35
            else:
                score += 0.2
        else:
            score += 0.35  # Unknown/unspecified

        # Location match (50%)
        if not preferred_locations or not job_location:
            score += 0.35
        else:
            job_loc_words = set(re.findall(r'\b\w+\b', job_location.lower()))
            for pref in preferred_locations:
                pref_words = set(re.findall(r'\b\w+\b', pref.lower()))
                if job_loc_words & pref_words:
                    score += 0.5
                    break
            else:
                score += 0.1

        return min(score, 1.0)

    # ------------------------------------------------------------------
    # Explanation builder
    # ------------------------------------------------------------------

    def _build_explanation(self, score, matched_req, missing_req, matched_pref,
                           years_exp, exp_min, exp_max,
                           preferred_work_mode, job_work_mode,
                           job_location, preferred_locations) -> str:
        parts = []

        # Skills
        if matched_req:
            parts.append(
                f"Your profile matches {len(matched_req)} of "
                f"{len(matched_req) + len(missing_req)} listed required skills "
                f"({', '.join(matched_req[:5])}{'...' if len(matched_req) > 5 else ''})."
            )
        if missing_req:
            parts.append(
                f"Skills not detected in your profile: "
                f"{', '.join(missing_req[:5])}{'...' if len(missing_req) > 5 else ''}. "
                f"(Note: 'not detected' does not mean you lack this skill — please review.)"
            )
        if matched_pref:
            parts.append(f"You also match {len(matched_pref)} preferred skill(s): {', '.join(matched_pref[:3])}.")

        # Experience
        if exp_min is not None or exp_max is not None:
            req_range = f"{exp_min or 0}–{exp_max or '∞'} years"
            if years_exp > 0:
                parts.append(f"Experience: you have {years_exp} year(s); role requires {req_range}.")
            else:
                parts.append(f"This role requires {req_range} of experience (your experience was not provided).")

        # Location
        if job_work_mode:
            parts.append(f"Work mode: {job_work_mode.title()}.")

        # Score context
        if score >= 75:
            parts.append("Strong overall match — this role aligns well with your profile.")
        elif score >= 50:
            parts.append("Moderate match — you meet several key requirements.")
        elif score >= 30:
            parts.append("Partial match — some requirements align, but gaps exist.")
        else:
            parts.append("Low match — this role may require skills not yet detected in your profile.")

        return ' '.join(parts)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _parse_skills(self, skills_str: str) -> set:
        if not skills_str:
            return set()
        return {s.strip().lower() for s in skills_str.split(',') if s.strip()}

    def _parse_list(self, val: str) -> list:
        if not val:
            return []
        return [v.strip() for v in val.split(',') if v.strip()]

    def _safe_float(self, val) -> Optional[float]:
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    def _build_seeker_text(self, profile: dict) -> str:
        parts = [
            profile.get('headline', ''),
            profile.get('summary', ''),
            profile.get('skills', ''),
            profile.get('preferred_roles', ''),
            profile.get('preferred_industries', ''),
            profile.get('resume_text', ''),
        ]
        return ' '.join(p for p in parts if p)

    def _build_job_text(self, job: dict) -> str:
        parts = [
            job.get('job_title', ''),
            job.get('description', ''),
            job.get('required_skills', ''),
            job.get('preferred_skills', ''),
            job.get('industry', ''),
        ]
        return ' '.join(p for p in parts if p)


# Module-level singleton
_matching_service = None


def get_matching_service(app=None) -> MatchingService:
    """Get or create the matching service singleton."""
    global _matching_service
    if _matching_service is None:
        weights = None
        if app:
            weights = {
                'skills': app.config.get('MATCH_WEIGHT_SKILLS', 0.40),
                'text': app.config.get('MATCH_WEIGHT_TEXT', 0.25),
                'title': app.config.get('MATCH_WEIGHT_TITLE', 0.15),
                'experience': app.config.get('MATCH_WEIGHT_EXPERIENCE', 0.10),
                'location': app.config.get('MATCH_WEIGHT_LOCATION', 0.10),
            }
        _matching_service = MatchingService(weights)
    return _matching_service

"""StyleChecker — detects style violations in cover letter text."""

import re

from hr_breaker.filters.base import BaseFilter
from hr_breaker.models import FilterResult, JobPosting, OptimizedResume, ResumeSource
from hr_breaker.utils import extract_text_from_html

# NOT decorated with @FilterRegistry.register — used only in orchestration_cl.py

# Contractions to detect (word boundary patterns)
CONTRACTIONS = [
    r"\bI'm\b", r"\bI've\b", r"\bI'd\b", r"\bI'll\b",
    r"\bdon't\b", r"\bdoesn't\b", r"\bdidn't\b", r"\bwon't\b", r"\bwouldn't\b",
    r"\bcan't\b", r"\bcouldn't\b", r"\bshouldn't\b", r"\bmustn't\b",
    r"\bIt's\b", r"\bit's\b", r"\bThat's\b", r"\bthat's\b",
    r"\bWe're\b", r"\bwe're\b", r"\bThey're\b", r"\bthey're\b",
    r"\bYou're\b", r"\byou're\b", r"\bHere's\b", r"\bhere's\b",
    r"\bThere's\b", r"\bthere's\b", r"\bWhat's\b", r"\bwhat's\b",
    r"\bWho's\b", r"\bwho's\b",
]

FORBIDDEN_PHRASES = [
    r"\bI am excited about the opportunity\b",
    r"\bI am passionate about\b",
    r"\bresonates with me\b",
    r"\bfast-paced environment\b",
    r"\bteam player\b",
    r"\bleverage\b",
    r"\butilize\b",
    r"\bI'd love the opportunity\b",
    r"\bI believe that\b",
    r"\bdynamic\b",
    r"\bmotivated by the chance to\b",
]

EM_DASH_PATTERN = re.compile(r"—")
SEMICOLON_PATTERN = re.compile(r";")


class StyleChecker(BaseFilter):
    """Detects style violations: em-dashes, contractions, semicolons, forbidden phrases."""

    name = "StyleChecker"
    priority = 2
    threshold = 1.0

    async def evaluate(
        self,
        optimized: OptimizedResume,
        job: JobPosting,
        source: ResumeSource,
    ) -> FilterResult:
        if not optimized.html:
            return FilterResult(
                filter_name=self.name,
                passed=True,
                score=1.0,
                threshold=self.threshold,
                issues=[],
                suggestions=[],
            )

        text = extract_text_from_html(optimized.html)
        issues = []
        suggestions = []

        # Em-dashes
        if EM_DASH_PATTERN.search(text):
            issues.append("Contains em-dash (—): rewrite sentence or use a comma")
            suggestions.append("Replace — with a comma or split into two sentences")

        # Semicolons
        semicolons = SEMICOLON_PATTERN.findall(text)
        if semicolons:
            issues.append(f"Contains {len(semicolons)} semicolon(s): split into separate sentences")
            suggestions.append("Replace each ; with a period and start a new sentence")

        # Contractions
        found_contractions = []
        for pattern in CONTRACTIONS:
            matches = re.findall(pattern, text)
            found_contractions.extend(matches)
        if found_contractions:
            unique = list(dict.fromkeys(found_contractions))
            issues.append(f"Contains contractions: {', '.join(unique)}")
            suggestions.append("Expand all contractions (I'm → I am, don't → do not, etc.)")

        # Forbidden phrases
        found_phrases = []
        for pattern in FORBIDDEN_PHRASES:
            if re.search(pattern, text, re.IGNORECASE):
                # Extract the phrase without regex metacharacters for display
                phrase = pattern.replace(r"\b", "").replace("\\b", "")
                found_phrases.append(phrase)
        if found_phrases:
            issues.append(f"Contains forbidden phrases: {'; '.join(found_phrases)}")
            suggestions.append("Replace clichés with specific examples or rephrase directly")

        total_checks = 4
        violations = sum([
            bool(EM_DASH_PATTERN.search(text)),
            bool(semicolons),
            bool(found_contractions),
            bool(found_phrases),
        ])
        score = 1.0 - (violations / total_checks)

        return FilterResult(
            filter_name=self.name,
            passed=len(issues) == 0,
            score=round(score, 2),
            threshold=self.threshold,
            issues=issues,
            suggestions=suggestions,
        )

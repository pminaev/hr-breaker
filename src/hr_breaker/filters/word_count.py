"""WordCountChecker — enforces 250-450 word hard limits on cover letters."""

from hr_breaker.filters.base import BaseFilter
from hr_breaker.models import FilterResult, JobPosting, OptimizedResume, ResumeSource

# NOT decorated with @FilterRegistry.register — used only in orchestration_cl.py

WORD_COUNT_MIN = 250
WORD_COUNT_MAX = 450
WORD_COUNT_TARGET_MIN = 300
WORD_COUNT_TARGET_MAX = 400


class WordCountChecker(BaseFilter):
    """Checks cover letter word count against hard limits (250-450 words)."""

    name = "WordCountChecker"
    priority = 4
    threshold = 1.0

    async def evaluate(
        self,
        optimized: OptimizedResume,
        job: JobPosting,
        source: ResumeSource,
    ) -> FilterResult:
        text = optimized.pdf_text or ""
        word_count = len(text.split())

        if word_count < WORD_COUNT_MIN:
            return FilterResult(
                filter_name=self.name,
                passed=False,
                score=word_count / WORD_COUNT_MIN,
                threshold=self.threshold,
                issues=[f"Cover letter is too short: {word_count} words (minimum {WORD_COUNT_MIN})"],
                suggestions=[
                    f"Add more specific detail to reach {WORD_COUNT_TARGET_MIN}-{WORD_COUNT_TARGET_MAX} words. "
                    "Expand on achievements with numbers and context."
                ],
            )

        if word_count > WORD_COUNT_MAX:
            return FilterResult(
                filter_name=self.name,
                passed=False,
                score=WORD_COUNT_MAX / word_count,
                threshold=self.threshold,
                issues=[f"Cover letter is too long: {word_count} words (maximum {WORD_COUNT_MAX})"],
                suggestions=[
                    f"Reduce to {WORD_COUNT_TARGET_MIN}-{WORD_COUNT_TARGET_MAX} words. "
                    "Cut filler sentences and merge short sentences."
                ],
            )

        return FilterResult(
            filter_name=self.name,
            passed=True,
            score=1.0,
            threshold=self.threshold,
            issues=[],
            suggestions=[],
        )

"""CLStructureValidator — checks required HTML sections are present in the cover letter."""

from hr_breaker.filters.base import BaseFilter
from hr_breaker.models import FilterResult, JobPosting, OptimizedResume, ResumeSource

# NOT decorated with @FilterRegistry.register — used only in orchestration_cl.py

REQUIRED_CLASSES = ["cl-opening", "cl-body", "cl-bullets", "cl-closing"]
SENDER_CLASSES = ["cl-header-name", "cl-header-role", "cl-sender-contact"]


class CLStructureValidator(BaseFilter):
    """Validates that the cover letter HTML contains all required structural sections."""

    name = "CLStructureValidator"
    priority = 1
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
                passed=False,
                score=0.0,
                threshold=self.threshold,
                issues=["No HTML content to validate"],
                suggestions=["Generate cover letter HTML first"],
            )

        html = optimized.html
        missing = []

        for cls in REQUIRED_CLASSES:
            if f'class="{cls}"' not in html and f"class='{cls}'" not in html:
                missing.append(cls)

        # Check sender block (warn but don't hard-fail)
        missing_sender = [
            cls for cls in SENDER_CLASSES
            if f'class="{cls}"' not in html and f"class='{cls}'" not in html
        ]

        all_missing = missing + missing_sender
        if all_missing:
            score = 1.0 - (len(all_missing) / (len(REQUIRED_CLASSES) + len(SENDER_CLASSES)))
            issues = [f"Missing required section: {cls}" for cls in all_missing]
            suggestions = [
                f"Add <p class=\"{cls}\"> or <div class=\"{cls}\"> for section: {cls}"
                for cls in all_missing
            ]
            return FilterResult(
                filter_name=self.name,
                passed=len(missing) == 0,  # Only fail on content sections, not sender
                score=round(score, 2),
                threshold=self.threshold,
                issues=issues,
                suggestions=suggestions,
            )

        return FilterResult(
            filter_name=self.name,
            passed=True,
            score=1.0,
            threshold=self.threshold,
            issues=[],
            suggestions=[],
        )

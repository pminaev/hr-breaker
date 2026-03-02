from hr_breaker.models.resume import OptimizedResume


class GeneratedCoverLetter(OptimizedResume):
    """Generated cover letter — extends OptimizedResume so existing filters work unchanged."""

    txt_text: str | None = None  # HTML-stripped plain text for ATS copy-paste

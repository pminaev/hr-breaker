"""CLReviewer — Flash LLM filter that scores cover letter quality against cl-guidelines."""

from datetime import date

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from hr_breaker.config import get_flash_model, get_model_settings
from hr_breaker.models import FilterResult, JobPosting, OptimizedResume, ResumeSource
from hr_breaker.utils.retry import run_with_retry

# NOT decorated with @FilterRegistry.register — used only in orchestration_cl.py

CL_REVIEWER_PROMPT = """You are a cover letter quality reviewer.

Score the cover letter on a scale from 0.0 to 1.0 based on the following criteria:

SCORING GUIDE:
- 1.0: Excellent — specific, confident, well-structured, no clichés
- 0.8-0.99: Good — minor issues, mostly specific and direct
- 0.7-0.79: Acceptable — passes but has some vague claims or weak structure
- 0.6-0.69: Borderline — too generic, missing specifics, or poor structure
- 0.0-0.59: Fail — generic, clichéd, vague, or structurally broken

EVALUATE:

1. **Tone** — Is it confident without being arrogant? Direct without hedging?
   Penalize: hedging ("I believe", "I think"), overly humble, or arrogant phrasing.

2. **Specificity** — Are claims backed by numbers or concrete examples?
   Penalize: vague descriptions ("strong analytical skills", "proven track record").

3. **Structure** — Does it follow opening → body → bullets → closing?
   Penalize: missing sections, wrong order, or poorly organized content.

4. **Opening** — Does it lead with what the company does, not how you feel?
   Penalize: "I am excited", "I am passionate", starting with "I".

5. **Bullets** — Does each bullet contain a specific skill + result or context?
   Penalize: generic traits ("team player", "fast learner") without examples.

6. **Job fit** — Does the letter address the actual job requirements?
   Penalize: generic letters that could apply to any job.
"""


class CLReviewResult(BaseModel):
    score: float = Field(
        ge=0.0,
        le=1.0,
        description="Overall quality score from 0.0 to 1.0",
    )
    issues: list[str] = Field(
        default_factory=list,
        description="Specific issues found",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Concrete suggestions for improvement",
    )
    reasoning: str = Field(description="Brief explanation of the score")


def get_cl_reviewer_agent() -> Agent:
    agent = Agent(
        get_flash_model(),
        output_type=CLReviewResult,
        system_prompt=CL_REVIEWER_PROMPT,
        model_settings=get_model_settings(),
    )

    @agent.system_prompt
    def add_current_date() -> str:
        return f"Today's date: {date.today().strftime('%B %Y')}"

    return agent


async def review_cover_letter(
    optimized: OptimizedResume,
    job: JobPosting,
    source: ResumeSource,
    threshold: float = 0.6,
) -> FilterResult:
    """Score cover letter quality against cl-guidelines."""
    cl_content = optimized.pdf_text or optimized.html or "(no content)"

    prompt = f"""Review this cover letter for the following job posting.

=== JOB POSTING ===
Title: {job.title}
Company: {job.company}
Requirements: {', '.join(job.requirements)}

=== COVER LETTER ===
{cl_content}

=== END ===

Score the cover letter from 0.0 to 1.0 based on tone, specificity, structure, opening quality, bullet quality, and job fit.
Return specific issues and concrete suggestions for improvement.
"""

    agent = get_cl_reviewer_agent()
    result = await run_with_retry(agent.run, prompt)
    r = result.output

    issues = list(r.issues)
    suggestions = list(r.suggestions)
    if r.score < threshold:
        suggestions.append(f"Score {r.score:.2f} below threshold {threshold}. {r.reasoning}")

    return FilterResult(
        filter_name="CLReviewer",
        passed=r.score >= threshold,
        score=r.score,
        threshold=threshold,
        issues=issues,
        suggestions=suggestions,
    )

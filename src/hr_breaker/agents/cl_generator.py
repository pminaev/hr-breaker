import logging
from datetime import date
from pathlib import Path

from pydantic import BaseModel
from pydantic_ai import Agent

from hr_breaker.config import get_model_settings, get_pro_model, get_settings
from hr_breaker.models import (
    GeneratedCoverLetter,
    IterationContext,
    JobPosting,
    ResumeSource,
)
from hr_breaker.services.length_estimator import estimate_content_length
from hr_breaker.services.renderer import HTMLRenderer, RenderError
from hr_breaker.utils import extract_text_from_html
from hr_breaker.utils.retry import run_with_retry

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent.parent.parent.parent / "templates"


def _load_cl_guide() -> str:
    return (TEMPLATE_DIR / "cl_guide.md").read_text()


class CLGeneratorResult(BaseModel):
    html: str
    changes: list[str]


def get_cl_generator_agent() -> Agent:
    """Create CL generator agent."""
    settings = get_settings()
    cl_guide = _load_cl_guide()

    agent = Agent(
        get_pro_model(),
        output_type=CLGeneratorResult,
        system_prompt=cl_guide,
        model_settings=get_model_settings(),
    )

    @agent.system_prompt
    def add_current_date() -> str:
        return f"Today's date: {date.today().strftime('%B %Y')}"

    @agent.tool_plain
    def check_word_count(html: str) -> dict:
        """Count words in the cover letter HTML. Target: 300-400 words."""
        text = extract_text_from_html(html)
        word_count = len(text.split())
        status = "ok"
        if word_count < 250:
            status = "too_short"
        elif word_count > 450:
            status = "too_long"
        logger.debug("check_word_count: %d words, status=%s", word_count, status)
        return {
            "word_count": word_count,
            "status": status,
            "target": "300-400 words",
            "hard_limits": "250 min, 450 max",
        }

    @agent.tool_plain
    def check_content_length(html: str) -> dict:
        """Check if cover letter HTML fits one page by rendering PDF. Call before finalizing."""
        est = estimate_content_length(html)
        try:
            renderer = HTMLRenderer(template_name="cl_wrapper.html")
            render_result = renderer.render(html)
            page_count = render_result.page_count
            fits_one_page = page_count == 1
        except RenderError as e:
            return {
                "fits_one_page": False,
                "error": f"Render failed: {e}",
                "estimates": {"chars": est.chars, "words": est.words},
            }

        result = {
            "fits_one_page": fits_one_page,
            "page_count": page_count,
            "estimates": {"chars": est.chars, "words": est.words},
        }
        if not fits_one_page:
            result["suggestion"] = (
                f"Content spans {page_count} pages. Reduce to fit one page."
            )
        logger.debug(
            "check_content_length: %d pages, fits=%s", page_count, fits_one_page
        )
        return result

    return agent


async def generate_cover_letter(
    source: ResumeSource,
    job: JobPosting,
    context: IterationContext,
    user_info: str | None = None,
) -> GeneratedCoverLetter:
    """Generate a cover letter for the given resume and job."""
    prompt = f"""## Resume:
{context.original_resume}

## Job Posting:
Title: {job.title}
Company: {job.company}
Requirements: {', '.join(job.requirements)}
Keywords: {', '.join(job.keywords)}
Description: {job.description}
"""

    if user_info:
        prompt += f"""
## Additional Context (treat as ground truth):
{user_info}

Use this context where relevant — for example, mention specific company knowledge or highlight particular experiences.
"""

    if context.last_attempt:
        prompt += f"""
## Previous Attempt (Iteration {context.iteration}):
{context.last_attempt}

This is a REFINEMENT iteration. Make the smallest possible changes to fix the issues below.
Do NOT rewrite from scratch.
"""

    if context.validation:
        prompt += f"""
## Filter Failures to Fix:
{context.format_filter_results()}

Fix ONLY what failed. Preserve everything that already works.
"""

    prompt += """
Use check_word_count to verify word count (target 300-400).
Use check_content_length to verify it fits one page.
Do not return until both checks pass.

Return JSON with:
- html: The HTML body content (no wrapper tags)
- changes: List of changes made
"""

    agent = get_cl_generator_agent()
    result = await run_with_retry(agent.run, prompt)
    return GeneratedCoverLetter(
        html=result.output.html,
        iteration=context.iteration,
        changes=result.output.changes,
        source_checksum=source.checksum,
    )

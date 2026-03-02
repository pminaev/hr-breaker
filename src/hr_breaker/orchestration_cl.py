"""Cover letter generation loop."""

import asyncio
import time
from collections.abc import Callable
from pathlib import Path

from hr_breaker.agents.cl_generator import generate_cover_letter
from hr_breaker.agents.cl_reviewer import review_cover_letter
from hr_breaker.agents import parse_job_posting
from hr_breaker.config import get_settings, logger
from hr_breaker.filters.ai_generated_checker import AIGeneratedChecker
from hr_breaker.filters.cl_structure import CLStructureValidator
from hr_breaker.filters.content_length import ContentLengthChecker
from hr_breaker.filters.hallucination_checker import HallucinationChecker
from hr_breaker.filters.style_checker import StyleChecker
from hr_breaker.filters.word_count import WordCountChecker
from hr_breaker.models import (
    FilterResult,
    GeneratedCoverLetter,
    IterationContext,
    JobPosting,
    ResumeSource,
    ValidationResult,
)
from hr_breaker.services.pdf_parser import extract_text_from_pdf_bytes
from hr_breaker.services.pdf_storage import PDFStorage
from hr_breaker.services.renderer import HTMLRenderer, RenderError
from hr_breaker.utils import extract_text_from_html

# Explicit filter list — CL filters are NEVER added to FilterRegistry.
# This prevents them from running during CV optimization.
CL_FILTERS = [
    ContentLengthChecker,    # Priority 0 — 1-page check (reused)
    CLStructureValidator,    # Priority 1 — required HTML sections (new, not registered)
    StyleChecker,            # Priority 2 — em-dashes, contractions, etc. (new, not registered)
    HallucinationChecker,    # Priority 3 — lenient mode by default for CLs (reused)
    WordCountChecker,        # Priority 4 — 250-450 words hard limit (new, not registered)
    AIGeneratedChecker,      # Priority 7 — AI text detection (reused)
    # CLReviewer is called separately after the loop (see _run_cl_filters)
]

CL_OUTPUT_SUBDIR = "cl"


async def _run_cl_filters(
    cl: GeneratedCoverLetter,
    job: JobPosting,
    source: ResumeSource,
    no_shame: bool = False,
) -> ValidationResult:
    """Run all CL filters in parallel, then run CLReviewer."""
    settings = get_settings()

    # Run structural/style/count filters in parallel
    filter_instances = [f(no_shame=no_shame) for f in CL_FILTERS]
    tasks = [f.evaluate(cl, job, source) for f in filter_instances]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    results = []
    for f, result in zip(filter_instances, raw_results):
        if isinstance(result, Exception):
            logger.error(f"CL filter {f.name} raised exception: {result}")
            results.append(
                FilterResult(
                    filter_name=f.name,
                    passed=False,
                    score=0.0,
                    threshold=getattr(f, "threshold", 0.5),
                    issues=[f"Filter error: {type(result).__name__}: {result}"],
                    suggestions=["Check filter implementation"],
                )
            )
        else:
            results.append(result)

    # Run CLReviewer only after structural filters (saves Flash LLM calls on bad drafts)
    structural_passed = all(r.passed for r in results)
    if structural_passed:
        reviewer_result = await review_cover_letter(
            cl, job, source, threshold=settings.filter_cl_reviewer_threshold
        )
        results.append(reviewer_result)

    return ValidationResult(results=results)


def _render_and_extract_cl(cl: GeneratedCoverLetter, renderer: HTMLRenderer) -> GeneratedCoverLetter:
    """Render CL HTML to PDF and extract text."""
    try:
        start = time.perf_counter()
        result = renderer.render(cl.html)
        logger.debug(f"CL render: {time.perf_counter() - start:.2f}s")

        pdf_text = extract_text_from_pdf_bytes(result.pdf_bytes)
        txt_text = extract_text_from_html(cl.html)

        return cl.model_copy(update={
            "pdf_bytes": result.pdf_bytes,
            "pdf_text": pdf_text,
            "txt_text": txt_text,
        })
    except RenderError as e:
        logger.error(f"CL render error: {e}")
        return cl


async def generate_cover_letter_for_job(
    source: ResumeSource,
    job_text: str | None = None,
    max_iterations: int | None = None,
    on_iteration: Callable | None = None,
    job: JobPosting | None = None,
    no_shame: bool = False,
    user_info: str | None = None,
) -> tuple[GeneratedCoverLetter, ValidationResult, JobPosting]:
    """
    Core cover letter generation loop.

    Args:
        source: Source resume
        job_text: Job posting text (required if job not provided)
        max_iterations: Max generation iterations (default from settings)
        on_iteration: Optional callback(iteration, cl, validation)
        job: Pre-parsed job posting (optional)
        no_shame: Lenient hallucination mode
        user_info: Extra context from --info flag (company research, things to highlight)

    Returns:
        (cover_letter, validation_result, job_posting)
    """
    settings = get_settings()

    if max_iterations is None:
        max_iterations = settings.cl_max_iterations

    renderer = HTMLRenderer(template_name="cl_wrapper.html")

    if job is None:
        if job_text is None:
            raise ValueError("Either job_text or job must be provided")
        job = await parse_job_posting(job_text)

    cl = None
    validation = None
    last_attempt: str | None = None

    for i in range(max_iterations):
        logger.info(f"CL iteration {i + 1}/{max_iterations}")
        ctx = IterationContext(
            iteration=i,
            original_resume=source.content,
            last_attempt=last_attempt,
            validation=validation,
        )

        cl = await generate_cover_letter(source, job, ctx, user_info=user_info)
        last_attempt = cl.html

        cl = _render_and_extract_cl(cl, renderer)

        if cl.pdf_text is None:
            validation = ValidationResult(
                results=[
                    FilterResult(
                        filter_name="PDFRender",
                        passed=False,
                        score=0.0,
                        threshold=1.0,
                        issues=["Failed to render cover letter to PDF"],
                        suggestions=["Check HTML content structure"],
                    )
                ]
            )
        else:
            validation = await _run_cl_filters(cl, job, source, no_shame=no_shame)

        if on_iteration:
            on_iteration(i, cl, validation)

        if validation.passed:
            break

    return cl, validation, job


def save_cover_letter(
    cl: GeneratedCoverLetter,
    first_name: str | None,
    last_name: str | None,
    job: JobPosting,
    output_dir: Path | None = None,
) -> tuple[Path, Path]:
    """Save cover letter PDF and plain text file. Returns (pdf_path, txt_path)."""
    settings = get_settings()
    cl_dir = output_dir if output_dir is not None else settings.output_dir / CL_OUTPUT_SUBDIR

    storage = PDFStorage(output_dir=cl_dir)
    pdf_path = storage.generate_path(first_name, last_name, job.company, job.title)

    if not cl.pdf_bytes:
        raise ValueError("No PDF bytes to save")

    pdf_path.write_bytes(cl.pdf_bytes)

    txt_path = pdf_path.with_suffix(".txt")
    txt_path.write_text(cl.txt_text or "", encoding="utf-8")

    return pdf_path, txt_path

"""Tests for cover letter generation pipeline."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from hr_breaker.filters.cl_structure import CLStructureValidator
from hr_breaker.filters.style_checker import StyleChecker
from hr_breaker.filters.word_count import WordCountChecker
from hr_breaker.models import (
    FilterResult,
    GeneratedCoverLetter,
    JobPosting,
    ResumeSource,
    ValidationResult,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def source():
    return ResumeSource(content="John Doe\nSenior Data Analyst with 5 years experience in SQL and Python.")


@pytest.fixture
def job():
    return JobPosting(
        title="Data Analyst",
        company="Booking.com",
        requirements=["SQL", "Python", "A/B testing"],
        keywords=["sql", "python", "data"],
    )


@pytest.fixture
def valid_cl_html(source):
    return """<div class="cl-sender"><div class="cl-sender-name">John Doe</div></div>
<div class="cl-date">March 2026</div>
<p class="cl-opening">Booking.com builds the world's largest travel platform.</p>
<p class="cl-body">In my last role I reduced query time by 40 percent using SQL window functions.</p>
<ul class="cl-bullets">
  <li>SQL: built dashboards that cut reporting time from 2 days to 2 hours</li>
  <li>Python: automated ETL pipeline processing 5M rows daily</li>
  <li>A/B testing: designed and analyzed 20+ experiments across booking funnel</li>
</ul>
<p class="cl-closing">I would welcome the chance to discuss how I can contribute to the Booking.com analytics team.</p>
<div class="cl-signature">John Doe</div>"""


@pytest.fixture
def valid_cl(source, valid_cl_html):
    return GeneratedCoverLetter(
        html=valid_cl_html,
        pdf_text="John Doe\nMarch 2026\nBooking.com builds the world largest travel platform. "
                 "In my last role I reduced query time by 40 percent using SQL window functions. "
                 "SQL built dashboards that cut reporting time from 2 days to 2 hours. "
                 "Python automated ETL pipeline processing 5M rows daily. "
                 "A/B testing designed and analyzed 20 experiments across booking funnel. "
                 "I would welcome the chance to discuss how I can contribute to the Booking.com analytics team. "
                 "John Doe",
        source_checksum=source.checksum,
    )


# ---------------------------------------------------------------------------
# CLStructureValidator
# ---------------------------------------------------------------------------

class TestCLStructureValidator:
    @pytest.mark.asyncio
    async def test_passes_with_all_sections(self, valid_cl, job, source):
        f = CLStructureValidator()
        result = await f.evaluate(valid_cl, job, source)
        assert result.passed

    @pytest.mark.asyncio
    async def test_fails_missing_required_section(self, source, job):
        cl = GeneratedCoverLetter(
            html='<p class="cl-opening">Opening</p><p class="cl-body">Body</p>',
            source_checksum=source.checksum,
        )
        f = CLStructureValidator()
        result = await f.evaluate(cl, job, source)
        assert not result.passed
        assert any("cl-bullets" in issue for issue in result.issues)
        assert any("cl-closing" in issue for issue in result.issues)

    @pytest.mark.asyncio
    async def test_passes_with_no_html(self, source, job):
        cl = GeneratedCoverLetter(source_checksum=source.checksum)
        f = CLStructureValidator()
        result = await f.evaluate(cl, job, source)
        assert not result.passed


# ---------------------------------------------------------------------------
# StyleChecker
# ---------------------------------------------------------------------------

class TestStyleChecker:
    @pytest.mark.asyncio
    async def test_passes_clean_text(self, valid_cl, job, source):
        f = StyleChecker()
        result = await f.evaluate(valid_cl, job, source)
        assert result.passed

    @pytest.mark.asyncio
    async def test_detects_em_dash(self, source, job):
        cl = GeneratedCoverLetter(
            html='<p class="cl-opening">I built this — and it worked.</p>',
            source_checksum=source.checksum,
        )
        f = StyleChecker()
        result = await f.evaluate(cl, job, source)
        assert not result.passed
        assert any("em-dash" in issue for issue in result.issues)

    @pytest.mark.asyncio
    async def test_detects_contractions(self, source, job):
        cl = GeneratedCoverLetter(
            html="<p class=\"cl-opening\">I'm excited about this role.</p>",
            source_checksum=source.checksum,
        )
        f = StyleChecker()
        result = await f.evaluate(cl, job, source)
        assert not result.passed
        assert any("contraction" in issue.lower() for issue in result.issues)

    @pytest.mark.asyncio
    async def test_detects_semicolons(self, source, job):
        cl = GeneratedCoverLetter(
            html="<p class=\"cl-opening\">I built X; it worked well.</p>",
            source_checksum=source.checksum,
        )
        f = StyleChecker()
        result = await f.evaluate(cl, job, source)
        assert not result.passed
        assert any("semicolon" in issue for issue in result.issues)

    @pytest.mark.asyncio
    async def test_detects_forbidden_phrase(self, source, job):
        cl = GeneratedCoverLetter(
            html="<p class=\"cl-opening\">I am passionate about data.</p>",
            source_checksum=source.checksum,
        )
        f = StyleChecker()
        result = await f.evaluate(cl, job, source)
        assert not result.passed
        assert any("forbidden" in issue.lower() for issue in result.issues)

    @pytest.mark.asyncio
    async def test_passes_with_no_html(self, source, job):
        cl = GeneratedCoverLetter(source_checksum=source.checksum)
        f = StyleChecker()
        result = await f.evaluate(cl, job, source)
        assert result.passed  # No content = no violations


# ---------------------------------------------------------------------------
# WordCountChecker
# ---------------------------------------------------------------------------

class TestWordCountChecker:
    @pytest.mark.asyncio
    async def test_passes_within_limits(self, source, job):
        # ~300 words of pdf_text
        words = " ".join(["word"] * 320)
        cl = GeneratedCoverLetter(
            html="<p>x</p>", pdf_text=words, source_checksum=source.checksum
        )
        f = WordCountChecker()
        result = await f.evaluate(cl, job, source)
        assert result.passed

    @pytest.mark.asyncio
    async def test_fails_too_short(self, source, job):
        words = " ".join(["word"] * 100)
        cl = GeneratedCoverLetter(
            html="<p>x</p>", pdf_text=words, source_checksum=source.checksum
        )
        f = WordCountChecker()
        result = await f.evaluate(cl, job, source)
        assert not result.passed
        assert "too short" in result.issues[0]

    @pytest.mark.asyncio
    async def test_fails_too_long(self, source, job):
        words = " ".join(["word"] * 500)
        cl = GeneratedCoverLetter(
            html="<p>x</p>", pdf_text=words, source_checksum=source.checksum
        )
        f = WordCountChecker()
        result = await f.evaluate(cl, job, source)
        assert not result.passed
        assert "too long" in result.issues[0]

    @pytest.mark.asyncio
    async def test_passes_at_hard_min_boundary(self, source, job):
        words = " ".join(["word"] * 250)
        cl = GeneratedCoverLetter(
            html="<p>x</p>", pdf_text=words, source_checksum=source.checksum
        )
        f = WordCountChecker()
        result = await f.evaluate(cl, job, source)
        assert result.passed

    @pytest.mark.asyncio
    async def test_passes_at_hard_max_boundary(self, source, job):
        words = " ".join(["word"] * 450)
        cl = GeneratedCoverLetter(
            html="<p>x</p>", pdf_text=words, source_checksum=source.checksum
        )
        f = WordCountChecker()
        result = await f.evaluate(cl, job, source)
        assert result.passed


# ---------------------------------------------------------------------------
# GeneratedCoverLetter model
# ---------------------------------------------------------------------------

class TestGeneratedCoverLetter:
    def test_inherits_from_optimized_resume(self, source):
        from hr_breaker.models import OptimizedResume
        cl = GeneratedCoverLetter(
            html="<p>test</p>",
            source_checksum=source.checksum,
            txt_text="test plain text",
        )
        assert isinstance(cl, OptimizedResume)
        assert cl.txt_text == "test plain text"

    def test_txt_text_defaults_to_none(self, source):
        cl = GeneratedCoverLetter(source_checksum=source.checksum)
        assert cl.txt_text is None


# ---------------------------------------------------------------------------
# Orchestration smoke test
# ---------------------------------------------------------------------------

class TestOrchestrationCL:
    @pytest.mark.asyncio
    async def test_generate_saves_pdf_and_txt(self, tmp_path, source, job, valid_cl_html):
        """Full pipeline smoke test with mocked LLM."""
        pdf_bytes = b"%PDF-1.4 fake pdf content"
        mock_cl = GeneratedCoverLetter(
            html=valid_cl_html,
            pdf_bytes=pdf_bytes,
            pdf_text=" ".join(["word"] * 320),
            txt_text="Plain text cover letter.",
            source_checksum=source.checksum,
        )

        mock_validation = ValidationResult(results=[
            FilterResult(
                filter_name="MockFilter",
                passed=True,
                score=1.0,
                threshold=0.5,
                issues=[],
                suggestions=[],
            )
        ])

        with (
            patch(
                "hr_breaker.orchestration_cl.generate_cover_letter",
                new_callable=AsyncMock,
                return_value=mock_cl,
            ),
            patch(
                "hr_breaker.orchestration_cl._render_and_extract_cl",
                return_value=mock_cl,
            ),
            patch(
                "hr_breaker.orchestration_cl._run_cl_filters",
                new_callable=AsyncMock,
                return_value=mock_validation,
            ),
        ):
            from hr_breaker.orchestration_cl import (
                generate_cover_letter_for_job,
                save_cover_letter,
            )

            cl, validation, _ = await generate_cover_letter_for_job(
                source, job=job, max_iterations=1
            )

            assert validation.passed
            assert cl.pdf_bytes == pdf_bytes

            pdf_path, txt_path = save_cover_letter(
                cl,
                first_name="John",
                last_name="Doe",
                job=job,
                output_dir=tmp_path,
            )

            assert pdf_path.exists()
            assert txt_path.exists()
            assert pdf_path.suffix == ".pdf"
            assert txt_path.suffix == ".txt"
            assert txt_path.read_text() == "Plain text cover letter."
            # Verify it went to the specified output_dir, not output/cl/
            assert pdf_path.parent == tmp_path

# CLAUDE.md

# HR-Breaker

Tool for optimizing resumes and generating cover letters for job postings, with LLM-based generation and multi-filter validation loops.

## How it works

### Resume optimization

1. User uploads resume in ANY text format (LaTeX, plain text, markdown, HTML) - content source only
2. User provides job posting URL or text description
3. LLM extracts content from resume and generates NEW HTML resume that:
   - Maximally fits the job posting
   - Follows guidelines: one-page PDF, no misinformation, etc.
4. System runs internal filters (LLM-based ATS simulation, keyword matching, hallucination detection, etc.)
5. If filters reject, repeat from step 3 using feedback
6. When all checks pass, render HTML→PDF via WeasyPrint and return

### Cover letter generation

1. Same inputs as CV: resume file + job URL or text
2. LLM generates HTML cover letter grounded in actual resume content
3. Structural/style/word-count filters run in parallel
4. LLM reviewer (`cl_reviewer`) runs only if structural filters pass
5. If any filter rejects, regenerate with feedback
6. Output: PDF + `.txt` plain-text saved to `output/cl/`

## Architecture

1. Streamlit frontend
2. Pydantic-AI LLM agent framework + pydantic-ai-litellm (any LLM provider)
3. Default: Google Gemini models (configurable to OpenAI, Anthropic, etc. via litellm)
4. Modular filter system - easy to add new checks
5. Resume caching - input once, apply to many jobs

Python: 3.10–3.13 (3.14+ breaks asyncio in streamlit thread pools)
Package manager: uv
Always use venv: `source .venv/bin/activate`
Unit-tests: pytest
HTTP library: httpx

Pydantic-AI docs: https://ai.pydantic.dev/llms-full.txt
LiteLLM docs: https://docs.litellm.ai/docs/

## Guidelines

When debugging use 1-2 iterations only (costs money). Use these settings:
```
REASONING_EFFORT=low
PRO_MODEL=gemini/gemini-2.5-flash
FLASH_MODEL=gemini/gemini-2.5-flash
```

## Current Implementation

### Structure
```
src/hr_breaker/
├── models/              # Pydantic data models (incl. GeneratedCoverLetter)
├── agents/              # Pydantic-AI agents
├── filters/             # Plugin-based filter system (CV + CL filters)
├── services/            # Rendering, scraping, caching
│   └── scrapers/        # Job scraper implementations
├── utils/               # Helpers (retry with backoff, HTML text extraction)
├── orchestration.py     # CV optimization loop
├── orchestration_cl.py  # Cover letter generation loop
├── main.py              # Streamlit UI
├── cli.py               # Click CLI
├── config.py            # Settings (pydantic-settings BaseSettings, auto-reads env vars)
└── litellm_patch.py     # Monkey-patch for pydantic-ai-litellm vision support
```

### Agents
- `job_parser` - Parse job posting → title, company, requirements, keywords
- `optimizer` - Generate optimized HTML resume from source + job
- `combined_reviewer` - Vision + ATS screening in single LLM call
- `name_extractor` - Extract name from any resume format
- `hallucination_detector` - Detect fabricated content
- `ai_generated_detector` - Detect AI-generated content indicators
- `cl_generator` - Generate HTML cover letter from resume + job (Pro model; has `check_word_count` and `check_content_length` tools)
- `cl_reviewer` - Flash LLM quality filter for cover letters (runs after structural filters pass)

### Filter System

#### CV filters
Registered in `FilterRegistry`. Run by priority (lower first). Default: parallel execution. Use `--seq` for early exit on failure.

| Priority | Filter | Purpose |
|----------|--------|---------|
| 0 | ContentLengthChecker | Pre-render size check (fits in one page) |
| 1 | DataValidator | Validate HTML structure |
| 3 | HallucinationChecker | Detect fabricated claims not supported by original resume |
| 4 | KeywordMatcher | TF-IDF keyword matching |
| 5 | LLMChecker | Combined vision + ATS simulation |
| 6 | VectorSimilarityMatcher | Embedding similarity (via litellm) |
| 7 | AIGeneratedChecker | AI content detection |

To add CV filter: subclass `BaseFilter`, set `name` and `priority`, use `@FilterRegistry.register`

#### CL filters
Defined as an explicit list in `orchestration_cl.py` (`CL_FILTERS`). **Never registered in FilterRegistry** — cannot accidentally run during CV optimization.

| Priority | Filter | Purpose |
|----------|--------|---------|
| 0 | ContentLengthChecker | 1-page check (shared with CV) |
| 1 | CLStructureValidator | Required HTML sections (opening, body, closing) |
| 2 | StyleChecker | Rejects em-dashes, contractions, semicolons, forbidden phrases |
| 3 | HallucinationChecker | Lenient mode by default (shared with CV) |
| 4 | WordCountChecker | 250–450 word hard limit |
| 7 | AIGeneratedChecker | AI text detection (shared with CV) |
| — | CLReviewer (agent) | LLM quality check — runs only after all structural filters pass |

To add CL filter: subclass `BaseFilter`, add to `CL_FILTERS` list in `orchestration_cl.py` (do NOT use `@FilterRegistry.register`).

### Services
- `renderer.py` - HTMLRenderer (WeasyPrint)
- `job_scraper.py` - Scrape job URLs (httpx → Wayback → Playwright fallback). 
- `pdf_parser.py` - Extract text from PDF
- `cache.py` - Resume caching
- `pdf_storage.py` - Save/list generated PDFs
- `length_estimator.py` - Content length estimation for resume sizing

### Commands
```bash
# Web UI
uv run streamlit run src/hr_breaker/main.py

# CV optimization
uv run hr-breaker optimize resume.txt https://example.com/job
uv run hr-breaker optimize resume.txt https://example.com/job -l ru  # optimize, then translate to Russian
uv run hr-breaker optimize resume.txt job.txt -d                     # debug mode
uv run hr-breaker optimize resume.txt job.txt --seq                  # sequential filters (early exit)
uv run hr-breaker optimize resume.txt job.txt --no-shame             # massively relax lies/hallucination/AI checks (use with caution!)
uv run hr-breaker optimize resume.txt job.txt --instructions "Focus on Python, add K8s cert"
uv run hr-breaker optimize resume.txt job.txt --output-dir path/to/dir  # save to specific dir (auto filename); --output still takes a full path and wins over --output-dir

# Cover letter generation
uv run hr-breaker cover-letter resume.txt https://example.com/job
uv run hr-breaker cover-letter resume.txt job.txt
uv run hr-breaker cover-letter resume.txt job.txt --info "They use dbt + Looker; mention BI migration"  # extra context (treated as ground truth)
uv run hr-breaker cover-letter resume.txt job.txt -d                 # debug mode (saves HTML iterations)
uv run hr-breaker cover-letter resume.txt job.txt --no-shame         # lenient hallucination mode
uv run hr-breaker cover-letter resume.txt job.txt --output-dir path/to/dir  # save to specific dir (auto filename, no cl/ subdir); --output wins over --output-dir

uv run hr-breaker list                                               # list generated PDFs

# Tests
uv run pytest tests/
```

### Output
- CV PDFs: `output/<name>_<company>_<role>.pdf`
- Cover letters: `output/cl/<name>_<company>_<role>.pdf` + `.txt`
- CV debug iterations: `output/debug_<company>_<role>/` (with -d flag)
- CL debug iterations: `output/cl/debug_<company>_<role>/` (with -d flag)
- Records: `output/index.json`

### Rendering
- LLM generates HTML body → WeasyPrint renders to PDF
- CV templates: `templates/resume_wrapper.html`, `templates/resume_guide.md`
- CL templates: `templates/cl_wrapper.html` (A4 prose layout), `templates/cl_guide.md` (system prompt)
- `HTMLRenderer` and `PDFStorage` accept optional `template_name`/`output_dir` params (default to CV behaviour)
- Name extraction uses LLM — handles any input format

#### CL layout
CL matches CV style (same font, size, spacing). Header structure generated by the LLM:
```
FIRST LAST              ← cl-header-name (12pt bold uppercase)
Senior Product Analyst  ← cl-header-role (11pt bold, domain suffix stripped by LLM)
email | tel | LinkedIn  ← cl-sender-contact (email + LinkedIn as colored underlined links)
────────────────────    ← hr.cl-divider
[letter body]
```
"Best regards," and the handwritten signature are **injected by `cl_wrapper.html`**, not by the LLM.

Signature: `HTMLRenderer.render()` looks for `{{SIGNATURE}}` in the wrapper and replaces it with a base64 data URI of `Signature.png` from the project root (`TEMPLATE_DIR.parent`). If the file is missing, the placeholder is replaced with an empty string (no error).

### pydantic-ai-litellm Vision Bug

`pydantic-ai-litellm` v0.2.3 does not support vision/`BinaryContent`. When an agent receives a list with text + `BinaryContent` (image), the library stringifies the image object (`str(item)`) instead of base64-encoding it into an OpenAI-compatible `image_url` part. The model receives garbage text like `"BinaryContent(data=b'\\x89PNG...')"` and never sees the actual image.

This breaks `combined_reviewer` which sends a rendered resume PNG for visual quality assessment.

Fix: `litellm_patch.py` monkey-patches `LiteLLMModel._map_messages` to properly convert `BinaryContent` images to `{"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}`. Applied at startup via `config.py`. Remove when upstream fixes the bug.

Repro: `uv run python scripts/repro_vision_bug.py` (without patch) vs `uv run python scripts/repro_vision_bug.py --patch` (with patch).

### Environment Variables

`Settings` uses `pydantic-settings` `BaseSettings` — env vars are auto-mapped from uppercased field names. All settings in `config.py` are configurable via env vars. See `.env.example` for the full list.

Key model config vars (litellm format):
- `PRO_MODEL` - Pro model (default: `gemini/gemini-3-pro-preview`)
- `FLASH_MODEL` - Flash model (default: `gemini/gemini-3-flash-preview`)
- `EMBEDDING_MODEL` - Embedding model (default: `gemini/text-embedding-004`)
- `REASONING_EFFORT` - none/low/medium/high (default: `medium`)
- `GEMINI_API_KEY` - API key for Gemini (also accepts `GOOGLE_API_KEY` for backward compat)
- `RETRY_MAX_ATTEMPTS` - Max retry attempts for rate limits (default: `5`)
- `RETRY_MAX_WAIT` - Max backoff wait in seconds (default: `60`)

CLI options (settable via env vars, CLI flags override):
- `HR_BREAKER_OUTPUT` - output path
- `HR_BREAKER_MAX_ITERATIONS` - max CV optimization iterations
- `HR_BREAKER_CL_MAX_ITERATIONS` - max cover letter generation iterations
- `HR_BREAKER_DEBUG` - enable debug mode (true/1/yes)
- `HR_BREAKER_SEQ` - run CV filters sequentially (true/1/yes)
- `HR_BREAKER_NO_SHAME` - lenient mode (true/1/yes)


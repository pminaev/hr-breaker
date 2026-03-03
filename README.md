# HR-Breaker

Resume optimization and cover letter generation tool — transforms any resume into a job-specific, ATS-friendly PDF, and writes tailored cover letters that pass quality filters.

![Python 3.10–3.13](https://img.shields.io/badge/python-3.10--3.13-blue.svg)

## Features

### Resume optimization

- **Any format in** - LaTeX, plain text, markdown, HTML, PDF
- **Optimized PDF out** - Single-page, professionally formatted
- **Editable HTML intermediate** - Saves `CV_<company>.html` alongside the PDF; edit and re-render without LLM
- **LLM-powered optimization** - Tailors content to job requirements
- **Minimal changes** - Preserves your content, only restructures for fit
- **No fabrication** - Hallucination detection prevents made-up claims
- **Opinionated formatting** - Follows proven resume guidelines (one page, no fluff, etc.)
- **Multi-filter validation** - ATS simulation, keyword matching, structure checks
- **User instructions** - Guide the optimizer with extra context ("Focus on Python", "Add K8s cert")
- **Multi-language output** - Optimize in English, then translate (e.g. `-l ru` for Russian)

### Cover letter generation

- **Resume-grounded** - Writes from your actual experience, no fabrication
- **Style-enforced** - Rejects em-dashes, contractions, semicolons, and AI-sounding phrases
- **Word count guardrails** - Hard 250–450 word limit enforced by a dedicated filter
- **Structure validated** - Required sections (opening, body, closing) checked before LLM review
- **Matches CV layout** - Same font, size, and spacing as the CV; header with name, role, and contact line
- **Auto role cleanup** - Job title domain suffixes stripped automatically (e.g. "Analyst – Offer Platform" → "Analyst")
- **Clickable contacts** - Email and LinkedIn rendered as colored, underlined links
- **Handwritten signature** - `Signature.png` from the project root is embedded automatically at the end
- **Editable HTML intermediate** - Saves `CL_<company>.html` alongside PDF and TXT; edit and re-render without LLM
- **PDF + TXT output** - Saved to `output/cl/`

### Shared

- **Web UI + CLI** - Streamlit dashboard or command-line
- **Debug mode** - Inspect optimization iterations
- **Cross-platform** - Works on macOS, Linux, and Windows

## How It Works

### Resume optimization

1. Upload resume in any text format (content source only)
2. Provide job posting URL or text description
3. LLM extracts content and generates optimized HTML resume
4. System runs internal filters (ATS simulation, keyword matching, hallucination detection)
5. If filters reject, regenerates using feedback
6. When all checks pass, saves `CV_<company>.html` (editable) and renders to `CV_<company>.pdf`

To tweak the result without re-running the LLM: edit the `.html` file, then run `render-cv`.

### Cover letter generation

1. Provide resume + job posting (same inputs as CV optimization)
2. LLM generates an HTML cover letter grounded in your actual experience
3. Structural, style, and word-count filters run in parallel
4. LLM reviewer runs only if structural filters pass (saves API calls)
5. If any filter rejects, regenerates with feedback
6. Saves `CL_<company>.html` (editable), `CL_<company>.pdf`, and `CL_<company>.txt` to `output/cl/`

To tweak the result without re-running the LLM: edit the `.html` file, then run `render-cl`.

## Quick Start

```bash
# Install
uv sync

# Configure
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

**Add your personal data to templates:**

1. Fill in your details in `PERSONAL.md` (name, email, phone, city, LinkedIn, permit line)
2. Open Claude Code in the project directory and run:
   > "Read PERSONAL.md and update all template files with my personal data following the instructions in that file."

```bash
# Run web UI
uv run streamlit run src/hr_breaker/main.py
```

## Usage

### Web UI

Launch with `uv run streamlit run src/hr_breaker/main.py`

1. Paste or upload resume
2. Enter job URL or description
3. Click optimize
4. Download PDF

### CLI — Resume

```bash
# From URL
uv run hr-breaker optimize resume.txt https://example.com/job

# From job description file
uv run hr-breaker optimize resume.txt job.txt
# → output/CV_<company>.html  (editable)
# → output/CV_<company>.pdf

# Debug mode (saves iterations)
uv run hr-breaker optimize resume.txt job.txt -d

# User instructions - guide the optimizer
uv run hr-breaker optimize resume.txt job.txt -i "Focus on Python, add K8s cert"

# Translate output to another language
uv run hr-breaker optimize resume.txt https://example.com/job -l ru

# Lenient mode - relaxes content constraints but still prevents fabricating experience. Use with caution!
uv run hr-breaker optimize resume.txt job.txt --no-shame

# Save to a specific directory (auto-generated filename)
uv run hr-breaker optimize resume.txt job.txt --output-dir /path/to/dir

# Re-render PDF from edited HTML — no LLM calls
uv run hr-breaker render-cv output/CV_company.html

# List generated PDFs
uv run hr-breaker list
```

### CLI — Cover Letter

```bash
# From URL
uv run hr-breaker cover-letter resume.txt https://example.com/job

# From job description file
uv run hr-breaker cover-letter resume.txt job.txt
# → output/cl/CL_<company>.html  (editable)
# → output/cl/CL_<company>.pdf
# → output/cl/CL_<company>.txt

# Extra context - company research, things to highlight (treated as ground truth)
uv run hr-breaker cover-letter resume.txt job.txt --info "They use dbt + Looker; mention my BI migration project"

# Debug mode (saves HTML iterations)
uv run hr-breaker cover-letter resume.txt job.txt -d

# Lenient hallucination mode
uv run hr-breaker cover-letter resume.txt job.txt --no-shame

# Save to a specific directory (auto-generated filename, no extra cl/ subdir)
uv run hr-breaker cover-letter resume.txt job.txt --output-dir /path/to/dir

# Re-render PDF+TXT from edited HTML — no LLM calls
uv run hr-breaker render-cl output/cl/CL_company.html
```

## Output

- Resume: `output/CV_<company>.html` + `output/CV_<company>.pdf`
- Cover letter: `output/cl/CL_<company>.html` + `.pdf` + `.txt`
- Debug iterations: `output/debug_<company>_<role>/` (CV) or `output/cl/debug_<company>_<role>/` (CL)

## Configuration

Copy `.env.example` to `.env` and set `GOOGLE_API_KEY` (required). See `.env.example` for all available options.

---

## Architecture

```
src/hr_breaker/
├── agents/              # Pydantic-AI agents (optimizer, reviewer, cl_generator, cl_reviewer, etc.)
├── filters/             # Validation plugins (ATS, keywords, hallucination, CL-specific)
├── services/            # Rendering, scraping, caching
│   └── scrapers/        # Job scraper implementations
├── models/              # Pydantic data models (incl. GeneratedCoverLetter)
├── orchestration.py     # CV optimization loop
├── orchestration_cl.py  # Cover letter generation loop
├── main.py              # Streamlit UI
└── cli.py               # Click CLI
```

**CV filters** (run by priority):

- 0: ContentLengthChecker - Size check
- 1: DataValidator - HTML structure validation
- 3: HallucinationChecker - Detect fabricated claims not supported by original resume
- 4: KeywordMatcher - TF-IDF matching
- 5: LLMChecker - Visual formatting check and LLM-based ATS simulation
- 6: VectorSimilarityMatcher - Semantic similarity
- 7: AIGeneratedChecker - Detect AI-sounding text

**CL filters** (explicit list, never registered in FilterRegistry):

- 0: ContentLengthChecker - 1-page check (shared with CV)
- 1: CLStructureValidator - Required HTML sections (opening, body, closing)
- 2: StyleChecker - Rejects em-dashes, contractions, semicolons, forbidden phrases
- 3: HallucinationChecker - Lenient mode by default (shared with CV)
- 4: WordCountChecker - 250–450 word hard limit
- 7: AIGeneratedChecker - AI text detection (shared with CV)
- CLReviewer - LLM quality filter, runs only after structural filters pass

## Development

```bash
# Run tests
uv run pytest tests/

# Install dev dependencies
uv sync --group dev
```

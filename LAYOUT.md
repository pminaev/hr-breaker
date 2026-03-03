# Resume Layout Specification

Reference for rebuilding the resume HTML template from scratch.

---

## Page

- Size: A4
- Margins: top 0.25in, left/right 0.45in, bottom 0.35in
- Renderer: WeasyPrint (HTML → PDF)
- Target: single page

---

## Typography

| Element | Font | Size | Weight | Notes |
|---------|------|------|--------|-------|
| Body | Arial, Helvetica, sans-serif | 10pt | normal | line-height 1.3 |
| Name | — | 12pt | bold | center-aligned |
| Position title | — | 12pt | bold | center-aligned, below name |
| Section titles | — | 10pt | bold | uppercase, letter-spacing 0.5pt |
| Bullets | — | 10pt | normal | line-height 1.25 |
| Permit line | — | 9pt | normal | color #555 |

- `font-style: normal` is forced globally — no italics anywhere (including `em`, `i`)
- Links in contact area: color #1155CC, underlined. All other links: #000, no underline.

---

## Structure

```
[Header]
  Name (wrapper, fixed)
  Position title (LLM-generated)
  Contact line: email | phone | city | LinkedIn
  Permit line

[Summary]
  "Summary:" bold + inline text

[EXPERIENCE]
  Entry × N

[SKILLS]
  Group × N

[EDUCATION]
  Edu entry × N
```

---

## Header

```html
<!-- Fixed in wrapper (resume_wrapper.html) -->
<div class="header-name">
    <div class="name">Name Lastname</div>
</div>

<!-- LLM-generated (first line of body) -->
<div class="header-rest">
    <div class="position-title">Senior Data Analyst</div>
    <div class="contact-line">
        <a href="mailto:name@lastname.com">name@lastname.com</a>
        <span class="sep">|</span>
        +31000000000
        <span class="sep">|</span>
        City
        <span class="sep">|</span>
        <a href="https://www.linkedin.com/in/yourhandle/">LinkedIn</a>
    </div>
    <div class="permit-line">EU residence &amp; work permit — no sponsorship required</div>
</div>
```

- `position-title`: core profession only — strip domain suffixes (e.g. "Senior Data Analyst (Payments)" → "Senior Data Analyst")
- Contact values are fixed — do not change email, phone, city, LinkedIn URL

---

## Summary

```html
<div class="summary-block">
    <strong>Summary:</strong> Product Analyst with 8 years of experience…
</div>
```

- `margin-bottom: 8pt`, `line-height: 1.35`
- "Summary:" is `<strong>`, colon included, text continues inline
- No trailing punctuation at end

---

## Experience Entry

**Layout:** single header line with role + company + date, then optional scope line, then bullets.

```html
<div class="entry">
    <div class="entry-header">
        <div class="entry-main">
            <span class="entry-role">Your Role Title</span> at <span class="company">Company Name</span><span class="company-desc"> — Short company description</span>
        </div>
        <div class="entry-date">Jul 2025 – Present</div>
    </div>
    <div class="role-desc">User communications, lifecycle management, personalisation</div>
    <ul class="bullets">
        <li>Built A/B testing culture from scratch: 1–2 → 6–7 experiments/month</li>
    </ul>
</div>
```

### Entry CSS

| Class | Layout | Size | Weight | Notes |
|-------|--------|------|--------|-------|
| `.entry` | block | — | — | `margin-bottom: 6pt` |
| `.entry-header` | flex row, space-between, align baseline | — | — | `margin-bottom: 1pt` |
| `.entry-main` | flex: 1 | — | — | contains role + company inline |
| `.entry-role` | inline span | 10pt | bold | no separate line |
| `.company` | inline span | 10pt | bold | preceded by literal " at " |
| `.company-desc` | inline span | 10pt | normal | starts with " — " |
| `.entry-date` | right-aligned, nowrap | 10pt | normal | `margin-left: 10pt` |
| `.role-desc` | block | 10pt | normal | `margin-bottom: 2pt`; one-line scope |

- Date separator: "–" (en-dash), not "-" (hyphen)
- Max 3–4 bullets per entry
- Bullets: capital letter, strong past-tense verb, no trailing dot

---

## Skills

```html
<section class="section">
    <h2 class="section-title">SKILLS</h2>
    <div class="section-content skills-section">
        <p><strong>Data &amp; Analytics:</strong> A/B testing, funnel analysis, cohort analysis…</p>
        <p><strong>Engineering &amp; Tools:</strong> SQL, Python, dbt, Amplitude, Looker…</p>
        <p><strong>Product &amp; Strategy:</strong> experiment design, stakeholder communication…</p>
    </div>
</section>
```

- Any number of groups; group names are chosen by the LLM to best fit the role (e.g. "Analytics", "Programming", "Tools", "Other", or any other grouping)
- Group label is `<strong>Label:</strong>`, colon included, text continues inline
- No skill qualifiers ("Advanced", "proficient", etc.)
- `.skills-section p` has `margin-bottom: 2pt`

---

## Education Entry

```html
<div class="edu-entry">
    <div class="entry-header">
        <div class="entry-main">
            <span class="company">University Name</span> <span class="company-desc">Your Degree</span>
        </div>
        <div class="entry-date">YYYY–YYYY</div>
    </div>
</div>
<div class="edu-entry">
    <div class="entry-header">
        <div class="entry-main">
            <span class="company">Course or Certification Provider</span> <span class="company-desc">Course or Certification Name</span>
        </div>
        <div class="entry-date">YYYY–YYYY</div>
    </div>
</div>
```

- Same `.entry-header` flex layout as experience
- Institution/provider: `.company` (bold 10pt)
- Degree, course, or programme name: `.company-desc` (normal 10pt), same line
- Applies to all education entries: university degrees, online courses, professional certifications, etc.
- No bullets, no trailing dots
- `.edu-entry`: `margin-bottom: 3pt`

---

## Section Titles

```html
<h2 class="section-title">EXPERIENCE</h2>
```

- Uppercase text
- `border-bottom: 0.75pt solid #000`
- `padding-bottom: 2pt`, `margin-bottom: 4pt`
- `.section` has `margin-top: 7pt`

---

## Bullets (shared)

```html
<ul class="bullets">
    <li>Achieved X by doing Y, resulting in Z</li>
</ul>
```

- No list-style (custom bullet via `::before { content: "\2022" }`)
- `padding-left: 11pt` on `li`
- `margin-bottom: 1pt` between bullets
- No trailing dots

---

## What NOT to Do

- No `<em>`, `<i>`, or `font-style: italic` anywhere
- No `<html>`, `<head>`, `<body>` tags in LLM output (wrapper handles it)
- No trailing dots at line or bullet ends
- No orphan last lines (1–3 word line endings in wrapped bullets)
- No skill qualifiers
- No fabricated metrics or titles
- No markdown syntax — HTML only

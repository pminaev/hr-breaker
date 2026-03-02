# Resume HTML Generation Guide

You generate HTML for the `<body>` of a resume PDF, **starting from `<div class="header-rest">`**. The wrapper already provides all CSS and renders the fixed name header above your content. Do NOT output `<html>`, `<head>`, `<body>`, or `<div class="header-name">` tags.

## Output Structure

Output these sections in order:

1. `header-rest` — position title + contact line + permit line
2. Summary block
3. EXPERIENCE section
4. SKILLS section
5. EDUCATION section

---

## 1. Header (first thing you output)

```html
<div class="header-rest">
    <div class="position-title">Senior Data Analyst</div>
    <div class="contact-line">
        <a href="mailto:pavel@minaev.me">pavel@minaev.me</a>
        <span class="sep">|</span>
        +31627850229
        <span class="sep">|</span>
        Amsterdam
        <span class="sep">|</span>
        <a href="https://www.linkedin.com/in/pavelminaev/">LinkedIn</a>
    </div>
    <div class="permit-line">EU residence &amp; work permit — no sponsorship required</div>
</div>
```

Rules:
- `position-title`: core profession only — strip domain suffixes (e.g. "Senior Data Analyst (Payments)" → "Senior Data Analyst")
- Contact values are **FIXED** — do not change email, phone, city, or LinkedIn URL
- Permit line text is **FIXED** — do not change

---

## 2. Summary

```html
<div class="summary-block">
    <strong>Summary:</strong> Product Analyst with 8 years of experience…
</div>
```

- `<strong>Summary:</strong>` with colon, text continues inline on the same line
- No trailing punctuation at end of text

---

## 3. Experience Section

```html
<section class="section">
    <h2 class="section-title">EXPERIENCE</h2>
    <div class="section-content">
        <div class="entry">
            <div class="entry-header">
                <div class="entry-main">
                    <span class="entry-role">Senior Product Data Analyst</span> at <span class="company">Sweatcoin</span><span class="company-desc"> — Fitness and health app</span>
                </div>
                <div class="entry-date">Jul 2025 – Present</div>
            </div>
            <div class="role-desc">User communications, lifecycle management, personalisation</div>
            <ul class="bullets">
                <li>Built A/B testing culture from scratch: 1–2 → 6–7 experiments/month</li>
                <li>Another achievement with concrete result</li>
            </ul>
        </div>
    </div>
</section>
```

Rules:
- Entry header format: `<span class="entry-role">Role</span> at <span class="company">Company</span><span class="company-desc"> — Short company description</span>`
- Date separator: "–" (en-dash), not "-" (hyphen)
- `role-desc`: one-line domain/scope description (e.g. "Payments, fraud, onboarding")
- Max 3–4 bullets per entry
- Bullets: capital letter, strong past-tense verb, no trailing dot

---

## 4. Skills Section

```html
<section class="section">
    <h2 class="section-title">SKILLS</h2>
    <div class="section-content skills-section">
        <p><strong>Data &amp; Analytics:</strong> A/B testing, funnel analysis, cohort analysis, retention, LTV</p>
        <p><strong>Engineering &amp; Tools:</strong> SQL, Python, dbt, Amplitude, Looker, BigQuery</p>
        <p><strong>Product &amp; Strategy:</strong> experiment design, metrics frameworks, stakeholder communication</p>
    </div>
</section>
```

- Use exactly these three group labels: **Data & Analytics** / **Engineering & Tools** / **Product & Strategy**
- Group label is `<strong>Label:</strong>`, colon included, skills continue inline
- No skill qualifiers ("Advanced", "proficient", "familiar with", etc.)

---

## 5. Education Section

```html
<section class="section">
    <h2 class="section-title">EDUCATION</h2>
    <div class="section-content">
        <div class="edu-entry">
            <div class="entry-header">
                <div class="entry-main">
                    <span class="company">Lomonosov Moscow State University</span> <span class="company-desc">MS in Fundamental Mathematics</span>
                </div>
                <div class="entry-date">2013–2019</div>
            </div>
        </div>
    </div>
</section>
```

- Institution: `.company` (bold)
- Degree: `.company-desc` (normal), same line, space separator (no dash)
- No bullets, no trailing dots

---

## Visual Criteria

- **Page size:** A4, single page — use `check_content_length` to verify
- **Font:** Arial 10pt body, 12pt name/position title (set by wrapper CSS)
- **Section order:** Summary → Experience → Skills → Education

## Layout Guidelines

1. **One page only** — trim less relevant content if needed; use `check_content_length` before returning
2. **Fill the page** — aim to use the full page without overflow
3. **Bullet points** — max 3–4 per job, focus on impact with metrics
4. **Dates** — consistent format (e.g. "Jan 2020" or "2020"), en-dash separator

## Professional Standards

- No first person ("I", "my", "me")
- Active voice, strong verbs ("Led", "Built", "Reduced")
- No fluff ("various", "helped with", "assisted in")
- Each bullet: Action + Context + Result (quantified where possible)

## What NOT to Do

- No `<em>`, `<i>`, or `font-style: italic` anywhere
- No `<html>`, `<head>`, `<body>` tags — only body content
- No `<div class="header-name">` or `<div class="name">` — the wrapper provides the name header
- No trailing dots at line or bullet ends
- No skill qualifiers
- No fabricated metrics, titles, or achievements
- No markdown syntax — HTML only
- No `<script>` tags

## Custom Styling

You CAN add a `<style>` tag at the beginning of your output if you need minor CSS adjustments (e.g. reducing font size on a section that's slightly overflowing). Prefer minimal targeted overrides.

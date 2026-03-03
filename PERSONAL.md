# Personal Information

Single source of truth for all personal data used in template files.

**After cloning, run Claude Code and say:**
> "Read PERSONAL.md and update all template files with my personal data following the instructions in that file."

**Before publishing to GitHub:** clear the values below (keep the keys and instructions), then add `PERSONAL.md` to `.gitignore`.

---

## Data

**Full Name:** Name Lastname

**Email:** name@lastname.com

**Phone:** +31000

**City:** Amsterdam

**LinkedIn URL:** https://www.linkedin.com/in/

**Permit line:** EU residence &amp; work permit — no sponsorship required
*(leave blank if not applicable — the line will be removed from templates)*

---

## Where each value goes

### `templates/resume_wrapper.html`

- **Full Name** → inside `<div class="name">...</div>` near the bottom of the file

---

### `templates/resume_guide.md`

This file is the LLM system prompt for CV generation. The contact block in the Header section contains values marked as **FIXED** — the LLM copies them verbatim into every generated CV. All five values below must match your real data exactly.

- **Email** → `href="mailto:..."` and the link display text in the contact line example
- **Phone** → the phone number in the contact line example
- **City** → the city name in the contact line example
- **LinkedIn URL** → `href="..."` in the LinkedIn link in the contact line example
- **Permit line** → the text inside `<div class="permit-line">...</div>` in the Header section
  *(if blank: remove the entire `<div class="permit-line">` line from the example)*

The experience and education entries in this file are **illustration-only** — the LLM does not copy them, it reads your actual resume. Replace them with your own real entries so the examples reflect your actual structure, or leave them as generic placeholders.

---

### `LAYOUT.md`

Reference document (not used by code). Contains the same contact block as `resume_guide.md`.

- **Full Name** → inside `<div class="name">...</div>` in the Header section
- **Email** → `href="mailto:..."` and link text in the contact line
- **Phone** → phone number in the contact line
- **City** → city name in the contact line
- **LinkedIn URL** → `href="..."` in the LinkedIn link
- **Permit line** → text inside `<div class="permit-line">...</div>`
  *(if blank: remove the entire line)*

The experience and education entries are illustration examples — replace with your own or use generic placeholders like "Your Company" / "Your University".

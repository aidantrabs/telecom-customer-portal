# AI Usage Document

## Tool

Claude (Anthropic).

## Scope of AI assistance

AI was used only on the final day of the project, for the following:

- **Documentation:** `README.md`, `docs/schema.md`, the architecture and chatbot Mermaid diagrams, and this AI usage document itself.
- **Security and usability audit:** an end-of-project review of the codebase, plus the atomic fixes that came out of it.
- **Frontend polish (if time permits):** small template / CSS improvements to tighten the UI before submission.

**AI was NOT used for core feature development.** The following was written by me directly:

- Data models (`User`, `Customer`, `Plan`, `Usage`, `Payment`, `Outage`, `Complaint`), migrations, and admin registrations.
- Views, forms, and URL routing for the customer, agent, and admin flows.
- Chatbot retrieval (`chat/retrieval.py`), generation (`chat/generation.py`), and view logic (`chat/views.py`).
- Seed management command (`accounts/management/commands/seed.py`).
- Docker setup (`Dockerfile`, `docker-compose.yml`).
- All templates authored before the audit phase.

The development log (`docs/log.md`) and the take-home specification (`docs/ProjectDescription.md`) were also written or provided by me, not AI.

## Prompts used

### Documentation

**Prompt:** write a README that covers every section the project description requires (overview, prerequisites, env setup, how to run, how to seed, credentials, chatbot setup, design decisions).

**What AI produced:** `README.md` with badges, an architecture Mermaid diagram, a chatbot flow Mermaid diagram, tables for credentials and env vars, a design decisions section grouped by area (architecture / chatbot / developer experience), and a project layout tree.

**My input across multiple rounds:** "too wordy", "use bullet points", "no dropdowns", "lowercase headings", "better file tree", "add a full architecture mermaid, not just the chatbot one", "reword the tagline", "does it fit the spec?". Each round tightened the formatting or reframed sections.

**Prompt:** write a schema doc with ER diagrams in Mermaid covering all implemented models.

**What AI produced:** `docs/schema.md` with a single unified ER diagram, a decisions list explaining the key model choices, and a module-usage table mapping models to the spec's two modules.

### Security and usability audit

**Prompt:** do a security and usability audit of the codebase. Produce prioritized findings with severity tags and recommended fixes.

**What AI produced:** a prioritized findings list covering:

Security
- Unbounded chat history in session
- Missing production-safe Django security settings (`SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`, etc.)
- Hardcoded `ALLOWED_HOSTS`
- Prompt injection exposure on chatbot input
- Defensive `request.user.customer` access

Usability
- No loading indicator on chatbot while Groq processes
- Chat doesn't auto-scroll to newest message
- Mobile nav doesn't collapse (no hamburger)
- No customer-facing account page
- Default Django 404 / 500 pages
- Clear conversation has no confirmation
- Unstyled form errors

### Audit fixes

Each fix is its own atomic commit. Prompts and outcomes below.

#### Fix 11.1 - Cap chat history in session (HIGH, security)

**Prompt:** cap chat history to the last 20 messages and limit question length.

**Files changed:** `chat/views.py`.

**What changed:** added `MAX_HISTORY_MESSAGES = 20` and `MAX_QUESTION_LENGTH = 1000` constants. After appending new messages, history is trimmed to the last 20. Input questions over 1000 characters are truncated before processing.

**Why:** prevents unbounded session growth (Django sessions have size ceilings) and runaway Groq token usage as history ships every turn. 20 messages = 10 user / assistant exchanges, which is plenty of context for `llama-3.1-8b-instant`. 1000 characters is generous for a legitimate customer question and bounds prompt injection surface.

**Verification:** sent 15+ messages as customer1, confirmed session payload stayed bounded. Pasted a 2000-character question and confirmed truncation.

#### Fix 11.2 - Production-safe security settings and env-driven ALLOWED_HOSTS (HIGH, security)

**Prompt:** add Django's production security headers behind a `DEBUG=False` conditional, and switch `ALLOWED_HOSTS` to read from an environment variable with a dev default.

**Files changed:** `config/settings.py`, `.env.example`, `README.md`.

**What changed:**
- `ALLOWED_HOSTS` now reads from `os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')`. Dev works out of the box; production sets a real comma-separated hostname list.
- New `if not DEBUG:` block in `settings.py` enabling: `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS=31_536_000` with subdomains + preload, `SECURE_CONTENT_TYPE_NOSNIFF`, `SECURE_REFERRER_POLICY='same-origin'`.
- `.env.example` documents `ALLOWED_HOSTS`.
- README env table gained an `ALLOWED_HOSTS` row.

**Why:** the previous config shipped hardcoded `['localhost', '127.0.0.1']` which would silently 400 a real deployment. Cookie-secure and HSTS headers are free defenses when DEBUG is off. They are gated by `DEBUG` because enabling `SECURE_SSL_REDIRECT` locally would force HTTPS on `http://localhost` and loop.

**Verification:** `DEBUG=1` (dev default) - confirmed no behavior change, app runs as before. Switched `DEBUG=0` temporarily and confirmed the security settings activate via `python manage.py diffsettings`.

<!-- next fixes go here -->

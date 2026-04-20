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

#### Fix 11.3 - Chat loading indicator and auto-scroll (HIGH, usability)

**Prompt:** add a "thinking" state to the chat form and auto-scroll to the latest message on page load.

**Files changed:** `templates/chat/chat.html`.

**What changed:**
- Added a small inline `<script>` at the bottom of the chat template.
- On page load: `window.scrollTo(0, document.body.scrollHeight)` brings the most recent turn and the input field into view.
- On form submit: disable the input and the submit button, and change the button text to "Thinking..." so the user sees immediate feedback while the LLM processes (2-5s).
- Input also gained `maxlength="1000"` as a browser-side enforcement of the server-side question length cap from fix 11.1.

**Why:** the previous experience looked broken: submit the form, page sits for several seconds with no indication anything is happening. After the response, the page reloads but the scroll position stays at the top, hiding the new content below the fold. These are small, vanilla-JS tweaks; no framework needed.

**Verification:** rendered the chat page in docker, submitted a question, confirmed the button flipped to "Thinking..." immediately and the page auto-scrolled to reveal the new turn after reload.

#### Fix 11.4 - Custom error pages (MEDIUM, usability)

**Prompt:** add branded templates for 404, 403, and 500 so production error pages do not show the default Django error screen.

**Files changed:** `templates/404.html`, `templates/403.html`, `templates/500.html` (new files).

**What changed:** three templates extending `base.html`. Each shows the status code prominently, a short human-readable explanation, and a "Back to home" button. 403 specifically calls out "this page is restricted to a different role" because PermissionDenied from the role decorators is the most common path to that template.

**Why:** with `DEBUG=False` (production), Django looks for `404.html`, `403.html`, and `500.html` at the top level of the template search path. Without them, reviewers (and hypothetical users) see raw Django error screens which look unprofessional. With `DEBUG=True` these templates are ignored and the default debug traceback is shown instead, so dev workflow is unaffected.

**Verification:** temporarily set `DEBUG=0` and visited `/this-does-not-exist`, confirmed the 404 template rendered. Visited a customer-only URL as agent1 and confirmed the 403 template rendered. Restored `DEBUG=1` for continued development.

#### Fix 11.5 - Customer account view and role-based nav (MEDIUM, usability)

**Prompt:** add a customer-facing account page showing plan, balance, usage, region, and last payment at a glance; wire role-based navigation so each role can reach their main pages.

**Files changed:** `accounts/views.py`, `config/urls.py`, `templates/accounts/account.html` (new), `templates/base.html`.

**What changed:**
- New `account` view in `accounts/views.py` decorated with `@customer_required`. Pulls the customer, latest usage record, and latest payment, renders `templates/accounts/account.html`.
- New URL `path('account/', account, name='account')` in `config/urls.py`.
- New template with card-based layout: three top cards for account number / balance / region, then sections for plan (name + allowances), current-period usage (vs plan allowances), and last payment.
- Navbar in `base.html` now renders role-specific links: customers see Complaints / Account / Chat; agents see Queue; admins see Dashboard. Username and logout button stay on the right.

**Why:** previously, a customer could only see their plan / balance / usage by asking the chatbot. Having a plain page with the same data is standard telecom-portal UX and lets reviewers verify the underlying data without going through the LLM. Role-based nav closes a smaller gap: previously customers had no way to reach `/chat/` or `/account/` without typing the URL.

**Verification:** logged in as `customer1`, confirmed the nav now has three links, visited `/account/` and confirmed all cards populated correctly from seed data. Logged in as `agent1` and confirmed only the Queue link appears. Same for `portal_admin` / Dashboard.

#### Fix 11.6 - Clear conversation confirmation (LOW, usability)

**Prompt:** require a browser confirm before the clear-conversation button wipes chat history.

**Files changed:** `templates/chat/chat.html`.

**What changed:** added `onsubmit="return confirm('Clear this conversation?');"` to the clear-history form. Native browser dialog, no JS dependency.

**Why:** one misclick on the small "Clear conversation" button loses the whole session history. Not data-destructive, but annoying. A native confirm dialog is the minimum cost fix.

**Verification:** clicked the clear button, dialog appeared. "Cancel" left history intact; "OK" wiped as before.

#### Fix 11.7 - Role mismatch redirects to home instead of 403 (HIGH, usability)

**Prompt:** fix post-login 403 when a non-customer user's `?next=` param points at a customer URL; add the Admin site link and active-state highlighting to nav.

**Files changed:** `accounts/decorators.py`, `complaints/views.py`, `templates/base.html`.

**What changed:**
- All three role decorators (`customer_required`, `agent_required`, `admin_required`) now `return redirect('home')` when the role check fails, instead of `raise PermissionDenied`. The `home` view dispatches to the right landing page based on the authenticated user's role.
- Removed now-unused `PermissionDenied` imports from both `accounts/decorators.py` and `complaints/views.py`, added `redirect` where needed.
- Nav items now use `request.resolver_match.namespace` (and `url_name` for flat routes like `/account/`) to apply an active-state style (`text-white fw-semibold` vs `text-white-50`) so the user sees where they are.
- Admin users get an extra `Admin site` link (to `/admin/`) in the nav.

**Why:** the original behavior meant an admin with a bookmarked customer URL would log in, follow `?next=`, and get hit with a 403 page. Every subsequent click had to go through the navbar brand or a manually-typed URL. Soft-redirecting to `home` means the login flow always lands them on their correct dashboard regardless of `?next=`. The 403 template still exists and is still rendered for non-role failures (CSRF, Django-level permission errors).

**Verification:** logged in as `portal_admin` with `?next=/complaints/` appended, confirmed landing on `/dashboard/` instead of 403. Same pattern as `agent1` hitting `/chat/` - redirects to `/agent/`. Nav active state checked on all role landing pages.

<!-- next fixes go here -->

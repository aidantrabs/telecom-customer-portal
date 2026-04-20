# dev log

## day 1 (april 16 2026)

### what i'm doing today

repo + docker + django bootstrap + customer complaint submission. want a vertical slice working end to end before i start expanding outward.

### what got done

- gitignore, dockerfile (python 3.14.4-slim), requirements pinned, docker-compose with postgres 18 + a healthcheck so web doesn't race the db, .env.example, makefile
- bootstrapped django via `docker compose run --rm web django-admin startproject config .` so i don't need python on the host
- settings.py reads secrets and db config from env vars. sqlite out, postgres in (`HOST: 'db'` resolves via docker's internal dns)
- accounts app with custom `User` extending `AbstractUser` + a `role` charfield. minimal `Customer` profile (oneToOne + account_number)
- complaints app with `Complaint` - category/status textchoices, `assigned_agent` nullable with `SET_NULL` so complaints survive staff turnover
- django admin registered. extended `UserAdmin` to expose the role field
- base template with bootstrap 5.3.8 via cdn + django's default login template location
- customer complaint form + view at `/complaints/new/`

### decisions i made

- custom user model with a role field, NOT django groups. three fixed roles don't need a m2m table, `user.role == 'agent'` is cleaner than group lookups, and django yells at you if you wait until after the first migrate to switch.
- customer is a separate profile (oneToOne), not fields bolted onto user. keeps auth and telecom-domain stuff decoupled.
- bare minimum customer today. plan/balance/usage come when the chatbot actually needs them. no point speculating about shape.
- no crispy-forms. 11 lines of widget classes inline doesn't earn a dependency.
- one docker image, runtime chosen in compose. runserver for dev autoreload, deal with gunicorn when there's an actual prod target.
- psycopg binary so i don't need build tools in the image.
- makefile only got targets for commands i typed more than twice. started empty, now has up/down/build/logs/makemigrations/migrate.

### end of day

docker green, customer1 submits a complaint end to end, rocket was green on first try which felt nice. tomorrow: customer history, role guards, chatbot data models, agent queue.

## day 2 (april 17 2026)

### what i'm doing today

close out the customer side. build the chatbot data foundation. agent queue if there's time.

### what got done

- customer complaint history at `/complaints/`. reverse query via `customer.complaints` (related_name). new submit now redirects to the list, not back to the empty form
- `customer_required` decorator. returns a clean 403 instead of crashing on `request.user.customer` for non-customer roles
- nav bar with logout button. django 5 requires post for logout so it's a csrf-protected form, not a link
- plan model + customer field expansion (`plan` fk with `PROTECT`, `balance` decimal, `region` charfield)
- usage model with `unique_together=(customer, period_start)`
- payment model
- outage model. region is a charfield that matches `customer.region`
- auto-create customer signal on `User.post_save` when role is customer and no profile exists
- agent queue at `/agent/`. filters to active statuses, ordered oldest-first for triage urgency

### decisions i made

- tried adding a `/logout/` GET shortcut for dev convenience. backed out when i realized a hostile page could embed `<img src=".../logout/">` and auto-log-out users. reverted and added an explicit "don't do this" note.
- region is a plain charfield, not a lookup table. caribbean regions are few and stable, a regions table wouldn't earn its weight.
- usage uses `related_name='usage_records'`. `customer.usage_records.filter(...)` reads like a collection. `customer.usage_set` reads like one record.
- three separate role decorators instead of a `role_required(role)` factory. with three fixed roles the factory would be cleverer than useful.
- wrote the seed command today but NOT committing it yet. committing seed data before the features that use it reads backwards in git history. tooling follows features, not the other way around.

### stuff that bit me

- logged in as admin, hit `/complaints/`, got a crash. `request.user.customer` throws `DoesNotExist` for users that don't have a profile. fix was the `customer_required` decorator.
- csrf error when logging in across tabs. turns out logging in rotates the session token and any stale form from another tab is bad. not really a bug, just annoying. the nav logout button means i don't need to juggle tabs anymore.

### end of day

chatbot data foundation done (plan, usage, payment, outage, expanded customer). agent queue works. seed command written but held. auto-run in docker-compose staged but not committed.

## day 3 (april 20 2026)

### what i'm doing today

admin dashboard, chatbot end to end, land the seed commit, readme, submission prep.

### what got done

- agent complaint detail view. status dropdown filtered to forward-only transitions per the spec. notes field auto-prefixes `[timestamp username]` so the field reads as an actual audit trail
- `resolved_at` field on complaint, set via `save()` override when status first hits RESOLVED or CLOSED. keeps the dashboard's "avg resolution time" accurate no matter which view made the change
- admin dashboard at `/dashboard/`. counts by status + category (iterating textchoices so empty categories still show as 0), avg resolution time via `Avg(ExpressionWrapper(F('resolved_at') - F('created_at'), DurationField()))`, sla breach list (active complaints over 5 days old) with links into django admin
- role-aware home redirect. `/` dispatches by role instead of always going to `/complaints/`
- chat app, three layers:
  - retrieval.py - `get_customer_context(customer)` returns a full structured dict. absent data is explicit `null` or `[]` so the llm sees the gap and says "i don't have that" instead of making things up.
  - generation.py - thin groq wrapper. client created per-call so a missing `GROQ_API_KEY` doesn't crash django startup.
  - views.py - one view handles GET, new-message POST, clear-history POST. session stores `[{role, content, sources}]`; sources gets stripped before the history is sent to groq.
- role decorators refactored into `accounts/decorators.py`
- seed command committed (held since day 2)
- docker-compose auto-run re-added (`migrate → seed → runserver`)
- schema doc rewritten as one unified er diagram
- readme with badges, architecture mermaid, chatbot flow mermaid, credentials and env tables, design decisions grouped by area

### decisions i made

- BIG one: pivoted chatbot retrieval mid-build. started with keyword intent matching ("balance" in the question → fetch balance, etc). switched to sending the customer's full structured context every turn. why: handles compound questions ("what's my plan AND how much data have i used?") without a router, makes absent data visible to the model as explicit `null` / `[]`, and ~1kb is nothing on a 128k model.
- sources panel is category-level, not field-level. field-level would need the llm to emit structured output or use tool calling. category-level works with no pipeline changes.
- session-scoped chat history. spec says "within a session" and that's what sessions are for. skipped the `Conversation`/`Message` model route.
- dashboard stats iterate textchoices explicitly. gives me zero-count rows for free, which is what a dashboard actually needs. for 15 complaints the extra queries are nothing; at scale i'd switch.
- sla breach rows link to django admin's change form. free functionality, no reason to build a custom edit view just for this.

### stuff that bit me

- `manage.py startapp chatbot` failed with "conflicts with an existing python module". some transitive dep ships a `chatbot` package. renamed to `chat`. would have saved 30 seconds if i'd checked first.
- `docker compose run` vs `exec`. i used `run` to get a shell for testing retrieval. `run` spins up a fresh container that bypasses the `command:` startup chain, so migrations never ran and `accounts_customer` didn't exist. used `exec` against the live container after that.
- forgot to set `GROQ_API_KEY` the first time i tried generation. `os.environ['GROQ_API_KEY']` raised `KeyError` which is what i wanted (loud > silent) but still a moment of "oh right, the key".

### end of day

everything the spec wants. `docker compose up --build` from a clean state does migrate + seed + serve with zero manual steps. reviewer logs in with seeded creds and runs through customer / agent / admin / chatbot flows. docs have explicit headings for every spec-required section.

## Code style

Prefer classes and interfaces with constructor injection over module-level functions and `mock.patch`. Define behaviour behind a protocol or ABC; inject concrete implementations (including fakes) at construction time.

## Workflow

When the user says "let's implement", "let's build", "go into implementation", or similar, suggest using the `/tdd` skill before writing any code.

## Agent skills

### Issue tracker

Issues live in GitHub Issues (`github.com/syltruong/tg-language-assistant`). See `docs/agents/issue-tracker.md`.

### Triage labels

Default canonical labels (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.

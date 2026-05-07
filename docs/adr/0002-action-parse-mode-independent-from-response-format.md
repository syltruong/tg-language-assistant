# ADR-0002: Action `parse_mode` is independent from `response_format`

## Status
Accepted

## Context
Actions carry two format-related properties:
- `response_format` (`plain_text` | `structured_json`): describes the shape of the raw LLM output — whether the runner expects a free-form string or a JSON blob to validate against a schema.
- `parse_mode` (`"HTML"` | `None`): declares how Telegram should render the formatted string produced by `Action.format()`.

The obvious shortcut would be to derive `parse_mode` from `response_format`: assume `structured_json` actions always emit HTML and `plain_text` actions never do. At the time this decision was made, that mapping held for all existing actions.

## Decision
Treat `parse_mode` as a separate, independent property on `Action`, defaulting to `None`. Actions whose `format()` method emits HTML markup override it to `"HTML"` explicitly.

## Consequences
- `CorrectAction` is `plain_text` (LLM returns a raw corrected sentence) but will eventually emit HTML annotations. It can declare `parse_mode="HTML"` without being forced into `structured_json`.
- New Action authors set `parse_mode` explicitly rather than inheriting it from their LLM output shape. The default of `None` degrades gracefully (tags render as literal text) rather than crashing.
- The coupling between LLM output structure and Telegram rendering is broken: changing one does not force changing the other.

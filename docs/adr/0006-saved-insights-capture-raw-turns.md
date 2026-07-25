# Saved Insights capture raw turns, immutably, with no LLM on the write path

When the user taps Save on a slot message we store a verbatim snapshot of the whole Conversation Turn — anchor text, detected language, language pair, action type, and the rendered result exactly as displayed — rather than a distilled card (a title, a vocabulary pair, a summary). Distillation is recomputable from a raw snapshot for as long as the row exists; raw material discarded at write time is gone permanently. The write path therefore performs no LLM call and no interpretation, which also keeps the Save tap instant — speed is the core value of this bot, and a Save that can fail on a model timeout is worse than no Save button.

This decision implements ADR-0001's repository abstraction rather than re-deciding storage; SQLite on a mounted volume is the backend, behind an Insight Repository interface.

## Considered Options

**Raw turn snapshot** (chosen) — stores more bytes than needed and defers every question about presentation. Every future read surface (search, vocabulary extraction, spaced repetition, digests) is a re-runnable read-side concern.

**Distilled card at write time** — an LLM call on Save producing a title and extracted vocabulary. Nicer list rendering on day one, but puts a network round-trip on the tap, makes Save fallible, and permanently discards whatever the distillation prompt did not think to keep. Reversing it requires data we would no longer have.

## Consequences

- **Append-only.** Re-saving a turn after running a different Action creates a second row; the natural key is `(user_id, chat_id, slot_message_id, action_type)`, so re-tapping the same view is a no-op. Nothing the user chose to keep is ever silently overwritten.
- **Capture never depends on Session.** Everything needed is carried on the Telegram callback — the anchor is recovered from the slot message's `reply_to_message`, the result text from the message itself. Only `run_id` comes from Session, and it is nullable. This is a deliberate departure from Suggestion selection and Rating, which silently no-op when Session is lost: there the cost is one lost tap, here the user believes they kept something.
- **Rendered text is stored with its `parse_mode`.** The stored result is presentation-coupled HTML, not a normalized structure. This is the intended trade — it means a Saved Insight can always be re-displayed exactly as it was first seen, without re-running the Action's formatter.
- **Deletion is soft.** A `deleted_at` column exists from the first migration so that removal never violates append-only, even though no delete UI ships initially.

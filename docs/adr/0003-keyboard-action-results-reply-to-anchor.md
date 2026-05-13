# ADR-0003: Keyboard Action results edit the Instant Action result message in place

## Status
Accepted (revised — supersedes the original "reply to anchor" decision)

## Context
When a user taps a keyboard button, the Keyboard Trigger needs to know the Anchor Message — the user's original message that the action should operate on. Two approaches were considered for how to deliver the result:

**New message per action**: every Keyboard Action result posts a new message replying to the Anchor Message, with the Active Keyboard transferred to each new message. The anchor is always recoverable as `query.message.reply_to_message`.

**Edit in place**: the Instant Action result message is the single "slot" for the turn. Keyboard Action results edit that message's text and keyboard in place. The keyboard never needs to be transferred.

The original decision chose "new message per action." It was later revised because posting a new sibling message per action clutters the chat with redundant history that has low value in the primary use case (mid-conversation, need help fast), and the "edit in place" model maps cleanly onto the Reply suggestion selection flow (tapping a numbered suggestion edits the suggestion list).

## Decision
The Instant Action result is the single bot message per Conversation Turn. All Keyboard Action results — including Reply suggestion selection — edit that message's text and reply markup in place via `edit_message_text` / `edit_message_reply_markup`. The Active Keyboard stays on the same message throughout the turn; no keyboard transfer is needed.

The Anchor Message is still always recoverable as `query.message.reply_to_message`, because the slot message is posted as a reply to the Anchor Message and that relationship is preserved through edits.

## Consequences
- One bot message per turn instead of N. The chat stays clean.
- Users cannot scroll back to see previous action results within a turn (Analyze result is gone once they tap Correct). Accepted — recallability of within-turn history has low value in the primary use case.
- The keyboard never moves; no `edit_message_reply_markup` call is needed to remove an old keyboard and attach a new one.
- Reply suggestion selection becomes a natural edit: the suggestion list is replaced by the selected reply text, and the standard keyboard reappears.

# ADR-0003: All bot responses in a Conversation Turn reply to the Anchor Message

## Status
Accepted

## Context
When a user taps a keyboard button, the Keyboard Trigger needs to know the Anchor Message — the user's original message that the action should operate on. Two approaches were considered:

**Stateless (Telegram reply chain)**: every bot message replies directly to the Anchor Message. The anchor is always recoverable as `query.message.reply_to_message`, with no session state needed.

**Stateful (session-stored anchor)**: the bot replies to its own previous message (forming a chain), and the anchor message ID is stored in session and looked up on each callback.

A secondary concern was keyboard position: with a chained reply structure and a fixed keyboard on the first bot message, the keyboard drifts to the top of the conversation as new results pile up below it. The user has to scroll up to tap a button.

## Decision
All bot responses within a Conversation Turn — the Instant Action result and every Keyboard Action result — reply directly to the Anchor Message. The Active Keyboard is attached to each new result and removed from the previous one, so it always travels to the most recent bot message.

`ResponsePublisher.reattach_keyboard` is removed: there is no longer a step that moves the keyboard back to an earlier message.

## Consequences
- The anchor is always recoverable without session state: `query.message.reply_to_message` reliably points to the user's original message regardless of how many keyboard actions have been performed.
- The keyboard stays at the bottom of the conversation, visible alongside the latest result.
- All bot responses within a turn appear as siblings under the anchor in the Telegram thread, which may look busier than a linear chain for users who perform many actions on one message. This is acceptable — the learning context values recallability of past results over visual tidiness.

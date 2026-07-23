# Context

A Telegram bot that helps language learners communicate with native speakers in real time.

## Users

**Primary user**: Someone mid-conversation with a native speaker on Telegram who needs fast, low-friction help to understand or compose a message right now. Speed is the core value.

**Secondary users**: Language learners practicing independently — reviewing vocabulary from past conversations, practicing writing in the target language, or simulating a conversation without a live partner.

## Ubiquitous Language

### Language Pair
A user-configured pair of languages: a **base language** (the language the user is comfortable in) and a **target language** (the language they are learning). Base language is always English (`en`) — it is not selectable. Target language is chosen by the user via the Language Selection Flow. A user has one active language pair at a time. The set of supported target languages is a curated list — not open-ended — to ensure consistent LLM quality across languages. Language pair is held in-memory for the session; it does not survive a bot restart.

### Language Selection Flow
The inline-keyboard interaction that lets the user pick their target language. Triggered by `/start` (always, on every invocation, regardless of existing state) and `/settings` (to change an existing selection). Presents one button per entry in `SUPPORTED_TARGET_LANGUAGES` — always shown, even when only one language is available. On selection, the Session is updated with the new target language and the bot sends a short confirmation message prompting the user to send their first message. Until this flow completes, the bot does not process incoming messages.

### Instant Action
The action that fires automatically when the user sends a message, without requiring a button tap. Configurable per user. Default is **Translate**. Advanced learners may prefer **Vocabulary Hint** instead.

### Keyboard Action
An action the user triggers explicitly by tapping an inline button after a message has been processed. Examples: Analyze, Correct, Reply, Rephrase.

### Translate
An Instant Action that returns a full sentence translation of the incoming message into the user's base language (when the message is in the target language) or target language (when in the base language).

### Vocabulary Hint
An Instant Action that lifts key vocabulary words from an incoming message and returns their individual translations — without producing a full sentence translation. Intended for advanced learners who want to work out meaning themselves.

### Correct Mode
A Keyboard Action where the user submits a sentence in the target language and the bot returns the corrected sentence with inline annotations explaining each fix. Scoped to grammar, spelling, and usage corrections only. Punctuation and capitalisation are not annotated — they are accepted as normal IM register. Proficiency rating ("beginner/intermediate/advanced") and study suggestions are out of scope — a single sentence is insufficient signal for reliable rating or targeted advice.

### Conversation Simulation
A use pattern where the user drives both sides of a practice conversation, typing messages as if from their language partner and using the bot as a tool to understand each turn and compose replies. The bot remains a passive tool — it does not play a persona or generate partner messages autonomously.

### Anchor Message
The original message the user sent that started a conversation turn. Re-sending the anchor message is the mechanism for re-entering a previous flow.

### Language Role
A factual classification of an Anchor Message relative to the user's Language Pair: **target** (the message is in the language the user is learning) or **base** (the message is in the language the user is comfortable in). Determined at ingestion time from the detected language. Does not encode user intent — the same target-language message may be received from a partner or composed by the user.
_Avoid_: message direction, inbound, outbound

### Message Gateway
The entry point to the system. Receives a raw Telegram Update, delegates authorization to the Authorizer, validates message text, detects language, resolves Language Role, and produces a classified Anchor Message — or rejects with a typed error. Nothing downstream receives a partially-resolved message.
_Avoid_: message ingester, message handler, router

### Authorizer
The module that decides whether a Telegram user is permitted to use the bot. Answers one question: `is_authorized(user_id) → bool`. The Message Gateway delegates to it — the Gateway does not know the authorization rules. The current implementation checks against an `ALLOWED_USERS` allowlist. Future implementations will handle rate limiting and subscription tiers. Authentication (verifying identity) is handled by Telegram's infrastructure — the bot never does authentication, only authorization.
_Avoid_: authentication, auth middleware, access control

### Conversation Turn
A unit of interaction initiated by one anchor message. One bot message is posted per turn — the Instant Action result, which replies to the Anchor Message. All subsequent Keyboard Action results edit that same message in place. The keyboard stays on that message throughout the turn; it never transfers to a new message.

### Slot Message
The single bot message per Conversation Turn that carries all Action results. Posted as a Telegram reply to the Anchor Message on first publication; thereafter edited in place for every Keyboard Action in the same turn. The Keyboard Trigger has direct access to it as `query.message` and recovers the Anchor Message from its immutable `reply_to_message` field.
_Avoid_: reply message, bot message, action message

### Suggestion
One item in a list of alternatives generated by a multi-output Action (Reply, Rephrase). Each Suggestion carries a `text` field (the generated content) and an optional `note` field (a short base-language label describing the style or register, e.g. "warm", "more formal"). Suggestions are shown as a numbered list in the slot message. Each is selectable via a numbered inline button labelled `N · note`. Selecting a Suggestion edits the slot message to show the selected text and restores the standard keyboard. To revisit other Suggestions, the user re-runs the Action (results may differ — acceptable in a learning context). If Session is lost before selection, the Keyboard Trigger silently no-ops.
_Avoid_: reply suggestion, rephrasing option, variant

### Active Keyboard
The single inline keyboard currently accepting input. It lives on the slot message for the current Conversation Turn and stays there throughout the turn — it is never transferred to a new message. There is no Back button; re-entry to a previous state is done by re-sending the anchor message.

### Session
Per-user in-memory state managed by Telegram's `context.user_data`. Tracks language pair, message history, detected actions, active message IDs, and a per-message `run_id` correlating a Slot Message back to the Trace that produced it (see Trace). Currently not persisted across bot restarts.

### Vocabulary List
A per-user persistent collection of vocabulary entries built two ways: **passively** (words/phrases automatically extracted from Vocabulary Hint and Analyze actions) and **actively** (user taps the Save button in the inline keyboard, which saves the anchor message and its translation as an entry). Passive and active entries are distinguished in the list. Accessible via `/history`. Active entries are surfaced separately as "Favourites."

### User Preferences
The subset of user state that must survive a bot restart: **language pair** and **instant action preference**. Message history and conversation logs are not considered preferences — they are optional features built on top of persistence. Accessed exclusively through the User Repository — no module reads User Preferences directly from storage.

### User Repository
The module that owns persistence of User Preferences. Follows the repository abstraction established in ADR-0001 (SQLite backend, swappable interface). The sole read/write interface for language pair and instant action preference across bot restarts.
_Avoid_: user store, preferences manager

### Vocabulary Repository
The future persistence module for Vocabulary Lists. Deferred until after core architecture is stable — the Vocabulary List exists as a domain concept but is not yet persisted across restarts.

### Message Trigger
The module that coordinates the Instant Action flow: resolves which Action to run (from the user's Instant Action preference, Language Role, and Action Registry), calls the Action Runner to get a formatted result, then calls the Response Publisher to deliver it. Owns no LLM logic and no formatting — its only domain knowledge is how to resolve an Action from a classified Anchor Message. Receives Action Registry, Action Runner, Response Publisher, and Session via constructor injection.
_Avoid_: message handler, message dispatcher

### Keyboard Trigger
The module that coordinates the Keyboard Action flow: identifies the Action type from the button payload, resolves the Anchor Message as the `reply_to_message` of the slot message, calls the Action Runner to get a formatted result, then calls the Response Publisher to edit the slot message in place. Also handles suggestion selection (`select:{index}` payloads): looks up the stored suggestions in Session, edits the slot message to show the selected reply text, and restores the standard keyboard — no LLM call involved. If Session is lost before selection, silently no-ops. Owns no LLM logic and no formatting. Receives Action Registry, Action Runner, and Response Publisher via constructor injection.
_Avoid_: callback handler, keyboard handler

### Action
A self-contained unit of bot behaviour. Carries: a prompt template, a response format (`plain_text` or `structured_json`), a schema (structured JSON actions only, used by Output Validation), a formatter method, and a `parse_mode` property (`"HTML"` or `None`). The formatter receives the validated LLM output and the Language Pair from the Action Runner, and uses an injected Localizer for any UI strings it needs to wrap around LLM content. `parse_mode` is independent from `response_format`: it declares how Telegram should render the formatter's output, not what shape the LLM output takes. Defaults to `None`; actions whose formatter emits HTML markup override to `"HTML"`. Instant Actions and Keyboard Actions are both Actions — they differ only in what triggers them.
_Avoid_: handler, command

### Action Registry
The module that constructs and exposes all known Action objects at startup. Wires constructor dependencies into each Action (Localizer, prompt templates loaded from disk). The single place where adding a new Action requires a change. Neither the Action Runner nor the triggers know how Actions are constructed.
_Avoid_: prompt manager, action factory

### Action Runner
The module that executes the domain round-trip for any Action: injects the Language Pair into the prompt template, calls the LLM Interface, runs Output Validation, calls the Action's formatter with the validated result and Language Pair, and returns a `FormattedResult` carrying the text, the Action's `parse_mode`, and a `run_id` correlation handle for tracing. Also attaches tracing metadata to each LLM call — the Action's type, the Language Pair, the detected language, and the Telegram user's identity (hashed by default) — for later filtering in LangSmith. Makes no Telegram API calls — returns a value, does not deliver it.
_Avoid_: handler, dispatcher

### Response Publisher
The module that delivers a `FormattedResult` to the user via Telegram. Exposes two explicit operations: one for first publication in a turn (posts a new Slot Message as a reply to the Anchor Message) and one for subsequent Keyboard Action results (edits the existing Slot Message in place). Deactivates the previous Active Keyboard when a new Slot Message becomes active. Owns the entire Telegram delivery concern including Active Keyboard lifecycle.
_Avoid_: response handler, sender

### LLM Interface
An explicit protocol defining `complete(system_prompt, user_prompt, metadata=None) → LLMCompletion`, where `LLMCompletion` carries the response text and an optional `run_id` (the LangSmith trace's correlation handle — see Trace). The production adapter is `LangGraphLLMClient`, which wraps a plain `OpenAILLMClient` inside a single-node, checkpointer-less LangGraph graph purely to get a LangSmith trace per call — no multi-turn state is kept. `OpenAILLMClient` remains a valid, untraced, protocol-conformant implementation on its own. A `FakeLLMClient` — a deterministic stub for testing and local development — is a further concrete implementation, defined alongside the protocol (not in `tests/`). The Action Runner receives an `LLMClient` via constructor injection; it never imports a concrete implementation directly.
_Avoid_: LLM client, OpenAI wrapper, llm.py

### Trace
A LangSmith record of one LLM call, identified by a `run_id` returned in the LLM Interface's `LLMCompletion`. Produced automatically by `LangGraphLLMClient`; carries tags and metadata (Action type, Language Pair, detected language, hashed Telegram user id) for filtering in the LangSmith dashboard. Tracing is optional — the bot runs normally without LangSmith configured, and a misconfigured or unreachable LangSmith must never break the Telegram response flow.
_Avoid_: span, LLM call log

### Output Validation
Validation applied to LLM responses before delivering them to the user. Scoped to **structural validation only**: retry if the response is malformed JSON or missing required fields. Quality scoring (using a second LLM call to judge the first) is out of scope — translation quality issues are addressed through prompt improvement, not a judge layer. Only applies to `structured_json` Actions — `plain_text` Actions bypass validation.

### Localizer
The module that translates UI strings (non-LLM text) into the user's base language. Takes a message key and a base language; returns the localized string. Used by the Message Gateway (error messages), the Keyboard Trigger (button labels), and any module that sends non-LLM text to the user. Does not know about LLM output — only about static UI strings.
_Avoid_: message catalog, t(), translations

### Domain Errors
Typed error classes that represent named failure modes in the domain (e.g., unauthorized user, missing message text, message too long, unsupported language). Defined in a shared module with no dependencies on other bot modules — both the module that raises an error and the Localizer that maps it to a UI string import from the same place. No error type is defined in the module that raises it.
_Avoid_: exceptions, error codes

### Feedback / Rating
The 👍/👎 the user taps on any Slot Message, recorded against that message's Trace via the Feedback Client. Shown as an extra row on every keyboard (both the standard Keyboard Action row and the suggestions keyboard). If Session is lost before the tap (no `run_id` stored for that message), the tap is acknowledged but no feedback is recorded — same no-op posture as a lost Suggestion selection.
_Avoid_: thumbs up/down, vote, review

### Feedback Client
The module that records a Rating against a Trace's `run_id`. An explicit protocol (`record_feedback(run_id, score, comment=None)`), following the same Protocol + constructor-injection pattern as the LLM Interface. The concrete `LangSmithFeedbackClient` calls LangSmith's feedback API; a misconfigured or unreachable backend logs a warning and never breaks the Telegram response flow.
_Avoid_: rating service, thumbs handler

### Annotation Queue
A LangSmith-side queue of Traces the admin reviews by hand. Populated by a LangSmith Automation Rule (configured once in the LangSmith UI, not application code) that watches for Traces carrying `user_rating` Feedback. Deliberately not driven from application code, so the admin can retune what's worth reviewing (thumbs-down only, everything, a sample) without a deploy.
_Avoid_: review queue, moderation queue

### Safety Guardrails
Deferred until public launch. Until then, `ALLOWED_USERS` is the sole access control mechanism. When rate limiting is introduced, it must be designed tier-aware from the start (to support future subscription tiers). Subscription management is a separate workstream and does not belong to the language learning feature roadmap.

# Context

A Telegram bot that helps language learners communicate with native speakers in real time.

## Users

**Primary user**: Someone mid-conversation with a native speaker on Telegram who needs fast, low-friction help to understand or compose a message right now. Speed is the core value.

**Secondary users**: Language learners practicing independently — reviewing vocabulary from past conversations, practicing writing in the target language, or simulating a conversation without a live partner.

## Ubiquitous Language

### Language Pair
A user-configured pair of languages: a **base language** (the language the user is comfortable in) and a **target language** (the language they are learning). Currently defaults to English (base) → French (target). A user has one active language pair at a time; switching requires an explicit `/settings` command. The set of supported languages is a curated list — not open-ended — to ensure consistent LLM quality across languages.

### Instant Action
The action that fires automatically when the user sends a message, without requiring a button tap. Configurable per user. Default is **Translate**. Advanced learners may prefer **Vocabulary Hint** instead.

### Keyboard Action
An action the user triggers explicitly by tapping an inline button after a message has been processed. Examples: Analyze, Correct, Reply, Rephrase.

### Translate
An Instant Action that returns a full sentence translation of the incoming message into the user's base language (when the message is in the target language) or target language (when in the base language).

### Vocabulary Hint
An Instant Action that lifts key vocabulary words from an incoming message and returns their individual translations — without producing a full sentence translation. Intended for advanced learners who want to work out meaning themselves.

### Correct Mode
A Keyboard Action where the user submits a sentence in the target language and the bot returns the corrected sentence with inline annotations explaining each fix. Scoped to grammar, spelling, and usage corrections only. Proficiency rating ("beginner/intermediate/advanced") is out of scope — a single sentence is insufficient signal for reliable rating.

### Conversation Simulation
A use pattern where the user drives both sides of a practice conversation, typing messages as if from their language partner and using the bot as a tool to understand each turn and compose replies. The bot remains a passive tool — it does not play a persona or generate partner messages autonomously.

### Anchor Message
The original message the user sent that started a conversation turn. Re-sending the anchor message is the mechanism for re-entering a previous flow.

### Conversation Turn
A unit of interaction initiated by one anchor message. Each turn has exactly one active keyboard at any time. When a new keyboard is posted, the previous one is silently removed from the chat.

### Reply Suggestion
One of N candidate replies generated in the target language in response to an incoming message. Shown as a numbered list in a single message. Each suggestion is selectable via a numbered inline button. Selecting a reply posts it as a new anchor message with its own keyboard, re-entering the standard message flow. The suggestions keyboard is deactivated when this happens. To revisit other suggestions, the user re-generates by tapping Reply on the original message again (suggestions may differ — this is acceptable in a learning context).

### Active Keyboard
The single inline keyboard currently accepting input. Only the most recently posted keyboard is active. There is no Back button — navigation is always forward. Re-entry to a previous state is done by re-sending the anchor message.

### Session
Per-user in-memory state managed by Telegram's `context.user_data`. Tracks language pair, message history, detected actions, and active message IDs. Currently not persisted across bot restarts.

### Vocabulary List
A per-user persistent collection of vocabulary entries built two ways: **passively** (words/phrases automatically extracted from Vocabulary Hint and Analyze actions) and **actively** (user taps the Save button in the inline keyboard, which saves the anchor message and its translation as an entry). Passive and active entries are distinguished in the list. Accessible via `/history`. Active entries are surfaced separately as "Favourites."

### User Preferences
The subset of user state that must survive a bot restart: **language pair** and **instant action preference**. Message history and conversation logs are not considered preferences — they are optional features built on top of persistence.

### Output Validation
Validation applied to LLM responses before delivering them to the user. Scoped to **structural validation only**: retry if the response is malformed JSON or missing required fields. Quality scoring (using a second LLM call to judge the first) is out of scope — translation quality issues are addressed through prompt improvement, not a judge layer.

### Safety Guardrails
Deferred until public launch. Until then, `ALLOWED_USERS` is the sole access control mechanism. When rate limiting is introduced, it must be designed tier-aware from the start (to support future subscription tiers). Subscription management is a separate workstream and does not belong to the language learning feature roadmap.

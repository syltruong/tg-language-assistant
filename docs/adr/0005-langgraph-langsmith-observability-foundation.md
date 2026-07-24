# LangGraph + LangSmith as the observability foundation for LLM calls

`ActionRunner` (`bot/runner.py`) makes a stateless, single-shot call to the LLM for every action (Translate, Analyze, Correct, Rephrase, Reply). There is no way today to trace a specific bot response back to the prompt/model call that produced it, and no feedback loop for the admin to spot bad responses. We want end-users to be able to rate a bot response (👍/👎), and for rated traces to reach the admin for review.

We adopt LangGraph as the orchestration seam for LLM calls, and LangSmith for tracing and feedback, specifically:

- A single-node, checkpointer-less LangGraph graph wraps the existing `LLMClient` call. This gives us a LangSmith trace per LLM call and a `run_id` correlation handle, without introducing any state across calls.
- LangSmith's `create_feedback` API records the user's 👍/👎 against that trace's `run_id`.
- A LangSmith Automation Rule (configured in the LangSmith UI, not application code) routes rated traces into a LangSmith Annotation Queue for the admin to review.

## Considered Options

**Plain `@traceable`/`wrap_openai` (LangSmith only, no LangGraph)** — gets tracing with less new surface area (no new dependency on `langgraph`, no graph abstraction to learn). Rejected because we want the LangGraph foundation in place for a later phase (multi-turn conversational memory via a LangGraph checkpointer), and introducing the graph now, while its shape is trivial (one node, no state), is cheaper than introducing it later once real branching/state exists.

**LangGraph with a checkpointer now (combined with multi-turn memory)** — would deliver conversational memory and tracing in one pass. Rejected for this phase: there is currently no multi-turn memory sent to the LLM at all (`UserSession` is UI/state bookkeeping, not a chat transcript), so adding it is a materially larger, separate change with its own persistence questions (a checkpointer would likely need to be SQLite-backed per ADR-0001). Kept as explicit future work, not bundled here.

**Programmatic Annotation Queue enqueue (SDK call in the feedback code path)** — an explicit `add_runs_to_annotation_queue`-style call right after recording feedback. Rejected in favor of a LangSmith Automation Rule: it keeps queue *curation policy* (what's worth reviewing — thumbs-down only? everything? a sample?) as an admin-tunable UI setting rather than a code change, and avoids adding another synchronous network call to the Telegram callback-handling hot path.

## Consequences

- `LLMClient.complete()` (`bot/llm_interface.py`) returns a small `LLMCompletion` value (text + optional `run_id`) instead of a bare string, and accepts an optional `metadata` kwarg — a signature change that ripples to `ActionRunner`, `FakeLLMClient`, and `OpenAILLMClient`.
- The production LLM client becomes `LangGraphLLMClient`, wrapping `OpenAILLMClient` in a single-node graph. `OpenAILLMClient` remains a valid, protocol-conformant, untraced fallback (used directly in tests, and usable standalone by anyone running the bot without a LangSmith account).
- `UserSession` gains a per-message `run_id` field so a later 👍/👎 tap can find the trace to attach feedback to.
- A new inline-keyboard row (👍/👎) appears under every bot response.
- Telegram user IDs are hashed by default before being sent to LangSmith (a third-party service), controlled by `HASH_TELEGRAM_USER_ID` (default `true`).
- Tracing and feedback are both optional: the bot must run normally without `LANGSMITH_API_KEY` set, and a misconfigured/unreachable LangSmith must never break the Telegram response flow.
- The Annotation Queue itself, and the Automation Rule that populates it, are configured once in the LangSmith UI — not tracked in this repo's code, only referenced from here and from the README.
- Explicitly out of scope: LangGraph checkpointer / multi-turn conversational memory, persisting `run_id`/feedback to SQLite, and any app-code call to enqueue runs into the Annotation Queue.
- **No token/cost (FinOps) visibility into the OpenAI calls.** `OpenAILLMClient` calls the raw `AsyncOpenAI` client directly — it is not wrapped with `langsmith.wrappers.wrap_openai`, nor is it a `langchain_openai.ChatOpenAI`. LangSmith only sees `LangGraphLLMClient`'s single-node graph as a generic traced run: the prompt/output text and our custom `metadata` are captured, but there is no token count, model name, or cost data, because the OpenAI call itself is never instrumented as an LLM-typed span. Getting that would mean swapping `OpenAILLMClient`'s internals to route through `wrap_openai` (or replacing it with `ChatOpenAI`) — not done here, since it wasn't needed for tracing/feedback/annotation-queue purposes and would touch the LLM-calling code path itself rather than just wrap it.

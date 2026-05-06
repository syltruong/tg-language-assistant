# SQLite first, with a repository abstraction layer

We start with SQLite (`aiosqlite`) for persistence because the bot runs as a single process, the persistent state is small (user preferences only), and SQLite requires zero infrastructure. A repository abstraction layer (one interface, swappable backends) is introduced from the start so that migrating to PostgreSQL later is a backend swap, not a rewrite.

## Considered Options

**SQLite** — single file, zero infrastructure, runs in the same container. Sufficient for a single-instance bot with a small user base. Breaks under concurrent multi-instance deploys.

**PostgreSQL** — handles concurrent access and horizontal scaling, but requires a separate service and adds operational overhead before it's needed.

## Consequences

- All database access goes through a repository interface; no raw SQL in handlers or session logic.
- Migration to PostgreSQL is triggered if/when multi-instance deployment or a larger user base makes SQLite's single-writer constraint a real bottleneck — not before.
- The SQLite file must be on a persistent volume in Docker to survive container restarts.

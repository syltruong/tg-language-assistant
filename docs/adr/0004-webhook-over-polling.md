# Webhook delivery instead of polling for production; polling retained for local dev

We use Telegram's webhook mechanism in production (fly.io) instead of long-polling. Polling works but keeps a persistent loop running that asks Telegram for updates every second, regardless of traffic. Webhooks let Telegram push updates to the bot's public HTTPS endpoint the moment they arrive, which is more efficient and the standard approach for hosted deployments.

Polling is retained for local development: if `WEBHOOK_URL` is not set, the bot falls back to `run_polling()`. This avoids requiring a tunnel (ngrok) for every local dev session.

## Considered Options

**Polling everywhere** — simple, no public URL required, works behind NAT. Acceptable for a single dev instance but wastes resources in production and is not idiomatic for a deployed bot.

**Webhook everywhere (including local)** — single code path, but requires an ngrok tunnel for every local session. Adds startup friction and a URL-changes-on-restart problem with free ngrok.

**Polling local / webhook production** — chosen. Controls via `WEBHOOK_URL` env var: absent → polling, set → webhook. Zero friction locally, production-grade delivery in prod.

## Consequences

- `WEBHOOK_URL` must be set in the fly.io environment to the app's public URL (e.g. `https://your-app.fly.dev`).
- The bot registers and deregisters the webhook automatically on start/stop via `run_webhook()`.
- Telegram enforces that polling and webhooks are mutually exclusive: if a webhook is registered, `getUpdates` (polling) returns nothing. Switching modes requires calling `deleteWebhook` first.
- Port 8443 is used for the webhook server (one of four ports Telegram allows: 80, 88, 443, 8443).

IMAGE_NAME = tg-language-assistant
CONTAINER_NAME = tg-language-assistant

.PHONY: start start-webhook deploy logs stop test check

start:
	uv run python -m bot.main

start-webhook:
	@bash -c '\
		ngrok http 8443 & NGROK_PID=$$!; \
		trap "kill $$NGROK_PID 2>/dev/null" EXIT; \
		until curl -s http://localhost:4040/api/tunnels > /dev/null 2>&1; do sleep 0.5; done; \
		WEBHOOK_URL=$$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys,json; d=json.load(sys.stdin); print(next(t[\"public_url\"] for t in d[\"tunnels\"] if t[\"public_url\"].startswith(\"https\")))"); \
		echo "Webhook URL: $$WEBHOOK_URL"; \
		WEBHOOK_URL=$$WEBHOOK_URL uv run python -m bot.main \
	'

deploy:
	docker build -t $(IMAGE_NAME) .
	docker rm -f $(CONTAINER_NAME) 2>/dev/null || true
	docker run -d --name $(CONTAINER_NAME) --env-file .env --restart unless-stopped $(IMAGE_NAME)

logs:
	docker logs -f $(CONTAINER_NAME)

stop:
	docker rm -f $(CONTAINER_NAME)

test:
	uv run pytest -v

check:
	uv run ruff check .
	uv run pytest -v
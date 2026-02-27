IMAGE_NAME = tg-language-assistant
CONTAINER_NAME = tg-language-assistant

.PHONY: start deploy logs stop

start:
	python -m bot.main

deploy:
	docker build -t $(IMAGE_NAME) .
	-docker rm -f $(CONTAINER_NAME)  # remove old container if it exists; leading '-' ignores errors
	docker run -d --name $(CONTAINER_NAME) --env-file .env --restart unless-stopped $(IMAGE_NAME)

logs:
	docker logs -f $(CONTAINER_NAME)

stop:
	docker rm -f $(CONTAINER_NAME)

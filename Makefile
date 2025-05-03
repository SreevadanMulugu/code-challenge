setup:
	docker compose pull && docker compose build

up:
	docker compose up -d

shell:
	docker compose exec app bash

down:
	docker compose down -v
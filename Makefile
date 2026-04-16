.PHONY: up down build logs makemigrations migrate

up:
	docker compose up

down:
	docker compose down

build:
	docker compose up --build

logs:
	docker compose logs -f

makemigrations:
	docker compose run --rm web python manage.py makemigrations

migrate:
	docker compose run --rm web python manage.py migrate

UV_VERSION=0.7.20

lint-check:
	ruff check --no-fix
	ruff format --check

lint:
	ruff check --fix
	ruff format
	pyright .

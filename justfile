iterate: test check

test:
  uv run -m unittest

check:
  uv run ruff check

format:
  uv run ruff format

precommit: check test
  uv run ruff format --check

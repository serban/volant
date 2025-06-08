iterate: test check

test:
  uv run -m unittest

check:
  uv run ruff check

coverage:
  uv run coverage run
  uv run coverage report
  uv run coverage html
  uv run python -c 'import pathlib, webbrowser; webbrowser.open(pathlib.Path("htmlcov/index.html").absolute().as_uri())'

format:
  uv run ruff format

precommit: check test
  uv run ruff format --check
  uv run coverage run
  uv run coverage report --skip-covered --fail-under 100

doc:
  uv run pdoc --docformat google volant

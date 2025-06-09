iterate: test check

test:
  uv run -m unittest

check:
  uv run ruff check
  uv run ty check
  uv run pyrefly check
  uv run basedpyright
  uv run mypy --check-untyped-defs .

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

edit:
  vim README.md CHANGELOG.md justfile src/volant/__init__.py tests/test_volant.py

upgrade:
  git diff --exit-code
  git diff --exit-code --staged
  uv tree --outdated
  uv remove --dev basedpyright coverage mypy pdoc pyrefly ruff ty
  uv    add --dev basedpyright coverage mypy pdoc pyrefly ruff ty
  git add pyproject.toml uv.lock
  date '+Bump Dependencies @ %Y-%m-%d %H:%M' | git commit --file -

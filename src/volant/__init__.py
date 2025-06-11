import base64
import os
import pathlib
import sys

# fmt: off
RESET   = '\033[0m'
RED     = '\033[31m'
GREEN   = '\033[32m'
YELLOW  = '\033[33m'
BLUE    = '\033[34m'
MAGENTA = '\033[35m'
CYAN    = '\033[36m'
ORANGE  = '\033[91m'  # Solarized
VIOLET  = '\033[95m'  # Solarized
# fmt: on


def tilde(p: str | os.PathLike[str]) -> str:
  """Replace the $HOME prefix of a path with '~'. Returns a string."""
  path, home = os.fsdecode(p), str(pathlib.Path.home())
  return path.replace(home, '~', 1) if path.startswith(home) else path


def clip(s: str) -> None:
  """Write a string to the clipboard via the OSC 52 terminal escape sequence."""
  payload = base64.b64encode(s.encode()).decode()
  print(f'\033]52;c;{payload}\007', end='', flush=True)


def title(s: str) -> None:
  """Set the terminal title."""
  print(f'\033]0;{s}\007', end='', flush=True)


def debug(*args: object) -> None:
  """Print a debug message. Does nothing if running in PYTHONOPTIMIZE mode."""
  # https://github.com/astral-sh/ty/issues/577 - __debug__ symbol not recognized
  if __debug__:  # ty: ignore[unresolved-reference]
    print(f'{BLUE}%', *args, RESET)


def message(*args: object) -> None:
  """Print an info message. Arguments are passed to built-in print()."""
  print(f'{CYAN}❋', *args, RESET)


def success(*args: object) -> None:
  """Print a success message. Arguments are passed to built-in print()."""
  print(f'{GREEN}✓', *args, RESET)


def result(*args: object) -> None:
  """Print a result message. Arguments are passed to built-in print()."""
  print(f'{MAGENTA}→', *args, RESET)


def error(*args: object) -> None:
  """Print an error message. Arguments are passed to built-in print()."""
  print(f'{RED}!', *args, RESET)


def die(*args: object) -> None:
  """Print an error message and die with exit status 1. Same args as print()."""
  error(*args)
  sys.exit(1)


def separator() -> None:
  """Print a nice horizontal line."""
  print(f'  {"─" * 76}  ')


def heading(s: str) -> None:
  """Print a nice box around some text."""
  pad = max(len(s), 76)
  line = '─' * pad
  text = f'{s:{pad}}'

  print(f'╭─{line}─╮')
  print(f'│ {text} │')
  print(f'╰─{line}─╯')

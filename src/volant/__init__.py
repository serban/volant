import base64


def clip(s: str) -> None:
  """Write a string to the clipboard via the OSC 52 terminal escape sequence."""
  payload = base64.b64encode(s.encode()).decode()
  print(f'\033]52;c;{payload}\007', end='', flush=True)


def title(s: str) -> None:
  """Set the terminal title."""
  print(f'\033]0;{s}\007', end='', flush=True)


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

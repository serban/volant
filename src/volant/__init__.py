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

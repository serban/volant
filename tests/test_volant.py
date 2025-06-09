import contextlib
import io
import unittest

import volant

kSeparator = '  ────────────────────────────────────────────────────────────────────────────  \n'

kHeadingShort = """
╭──────────────────────────────────────────────────────────────────────────────╮
│ Extra! Extra! Read all about it!                                             │
╰──────────────────────────────────────────────────────────────────────────────╯
""".lstrip()

kHeadingLong = """
╭─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
""".lstrip()


class VolantTest(unittest.TestCase):
  maxDiff: int | None = None

  def test_clip(self):
    with io.StringIO() as buffer:
      with contextlib.redirect_stdout(buffer):
        volant.clip('Aparecium!')
      self.assertEqual('\033]52;c;QXBhcmVjaXVtIQ==\007', buffer.getvalue())

  def test_title(self):
    with io.StringIO() as buffer:
      with contextlib.redirect_stdout(buffer):
        volant.title('They call me Mister Tibbs!')
      self.assertEqual(
        '\033]0;They call me Mister Tibbs!\007', buffer.getvalue()
      )

  def test_separator(self):
    with io.StringIO() as buffer:
      with contextlib.redirect_stdout(buffer):
        volant.separator()
      self.assertEqual(kSeparator, buffer.getvalue())

  def test_heading(self):
    for sub, out, arg in [
      ('extra', kHeadingShort, 'Extra! Extra! Read all about it!'),
      (
        'lorem',
        kHeadingLong,
        'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.',
      ),
    ]:
      with self.subTest(sub):
        with io.StringIO() as buffer:
          with contextlib.redirect_stdout(buffer):
            volant.heading(arg)
          self.assertEqual(out, buffer.getvalue())

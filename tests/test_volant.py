import contextlib
import io
import unittest

import volant

kSeparator = '  ────────────────────────────────────────────────────────────────────────────  \n'


class VolantTest(unittest.TestCase):
  maxDiff: int | None = None

  def test_separator(self):
    with io.StringIO() as buffer:
      with contextlib.redirect_stdout(buffer):
        volant.separator()
      self.assertEqual(kSeparator, buffer.getvalue())

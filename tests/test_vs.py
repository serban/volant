import contextlib
import io
import unittest

import vs

kSeparator = '  ────────────────────────────────────────────────────────────────────────────  \n'


class VsTest(unittest.TestCase):
  maxDiff = None

  def test_separator(self):
    with io.StringIO() as buffer:
      with contextlib.redirect_stdout(buffer):
        vs.separator()
      self.assertEqual(kSeparator, buffer.getvalue())

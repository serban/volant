import contextlib
import io
import os
import pathlib
import unittest
import unittest.mock

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


# https://github.com/python/typeshed/blob/main/stdlib/_typeshed/__init__.pyi
type StrPath = str | os.PathLike[str]


class VolantTest(unittest.TestCase):
  maxDiff: int | None = None

  def test_tilde(self):
    # fmt: off
    subs: list[tuple[str, StrPath]] = [
      ('/oso/de/peluche', '/oso/de/peluche'),
      ('~/oso/cachorro',  '/home/oski/oso/cachorro'),
      ('/',               pathlib.PurePath('/')),
      ('/bruin',          pathlib.PurePath('/bruin')),
      ('/den/home/oski',  pathlib.PurePath('/den/home/oski')),
      ('~',               pathlib.PurePath('/home/oski')),
      ('~/bear',          pathlib.PurePath('/home/oski/bear')),
      ('~/home/oski',     pathlib.PurePath('/home/oski/home/oski')),
      ('~/cub/home/oski', pathlib.PurePath('/home/oski/cub/home/oski')),
    ]
    # fmt: on
    with unittest.mock.patch.dict(os.environ, {'HOME': '/home/oski'}):
      for out, arg in subs:
        with self.subTest(arg):
          self.assertEqual(out, volant.tilde(arg))

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

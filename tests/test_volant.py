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

  def test_mark(self) -> None:
    for out, arg in [
      ('∅', None),
      ('\033[31m✗\033[0m', False),
      ('\033[32m✓\033[0m', True),
    ]:
      with self.subTest(arg):
        self.assertEqual(out, volant.mark(arg))

  def test_tilde(self) -> None:
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

  def test_clip(self) -> None:
    with io.StringIO() as buffer:
      with contextlib.redirect_stdout(buffer):
        volant.clip('Aparecium!')
      self.assertEqual('\033]52;c;QXBhcmVjaXVtIQ==\007', buffer.getvalue())

  def test_title(self) -> None:
    with io.StringIO() as buffer:
      with contextlib.redirect_stdout(buffer):
        volant.title('They call me Mister Tibbs!')
      self.assertEqual(
        '\033]0;They call me Mister Tibbs!\007', buffer.getvalue()
      )

  def test_debug(self) -> None:
    with io.StringIO() as buffer:
      with contextlib.redirect_stdout(buffer):
        volant.debug('An elephant never forgets.')
      self.assertEqual(
        '\033[34m% An elephant never forgets. \033[0m\n', buffer.getvalue()
      )

  def test_message(self) -> None:
    with io.StringIO() as buffer:
      with contextlib.redirect_stdout(buffer):
        volant.message('The sleeping fox catches no poultry.')
      self.assertEqual(
        '\033[36m❋ The sleeping fox catches no poultry. \033[0m\n',
        buffer.getvalue(),
      )

  def test_success(self) -> None:
    with io.StringIO() as buffer:
      with contextlib.redirect_stdout(buffer):
        volant.success('From downtown!')
      self.assertEqual('\033[32m✓ From downtown! \033[0m\n', buffer.getvalue())

  def test_result(self) -> None:
    with io.StringIO() as buffer:
      with contextlib.redirect_stdout(buffer):
        volant.result('Upgrade complete.')
      self.assertEqual(
        '\033[35m→ Upgrade complete. \033[0m\n', buffer.getvalue()
      )

  def test_error(self) -> None:
    with io.StringIO() as buffer:
      with contextlib.redirect_stdout(buffer):
        volant.error('Dave, my mind is going.')
      self.assertEqual(
        '\033[31m! Dave, my mind is going. \033[0m\n', buffer.getvalue()
      )

  def test_die(self) -> None:
    with io.StringIO() as buffer:
      with contextlib.redirect_stdout(buffer):
        with self.assertRaises(SystemExit) as context:
          volant.die('He blew a fuse.')
        self.assertEqual(1, context.exception.code)
      self.assertEqual('\033[31m! He blew a fuse. \033[0m\n', buffer.getvalue())

  def test_separator(self) -> None:
    with io.StringIO() as buffer:
      with contextlib.redirect_stdout(buffer):
        volant.separator()
      self.assertEqual(kSeparator, buffer.getvalue())

  def test_heading(self) -> None:
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

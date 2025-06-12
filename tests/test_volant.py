import collections.abc
import contextlib
import io
import itertools
import os
import pathlib
import unittest
import unittest.mock

import volant

kDump = """
  {'a': False,
   'b': 1_502_990_100,
   'c': ['critter', 'fritter', 'glitter', 'jitter', 'litter', 'twitter'],
   'd': 'aaa aab aac aba abb abc aca acb acc baa bab bac bba bbb bbc bca bcb '
        'bcc caa cab cac cba cbb cbc cca ccb ccc',
   'e': 2.718,
   'f': {'g': {'j': 'aa ab ac ad ae ba bb bc bd be ca cb cc cd ce da db dc '
                    'dd de ea eb ec ed ee',
               'k': 'aa ab ac ad ae ba bb bc bd be ca cb cc cd ce da db dc '
                    'dd de ea eb ec ed ee',
               'l': 'aa ab ac ad ae ba bb bc bd be ca cb cc cd ce da db dc '
                    'dd de ea eb ec ed ee'},
         'h': {'j': 'aa ab ac ad ae ba bb bc bd be ca cb cc cd ce da db dc '
                    'dd de ea eb ec ed ee',
               'k': 'aa ab ac ad ae ba bb bc bd be ca cb cc cd ce da db dc '
                    'dd de ea eb ec ed ee',
               'l': 'aa ab ac ad ae ba bb bc bd be ca cb cc cd ce da db dc '
                    'dd de ea eb ec ed ee'},
         'i': {'j': 'aa ab ac ad ae ba bb bc bd be ca cb cc cd ce da db dc '
                    'dd de ea eb ec ed ee',
               'k': 'aa ab ac ad ae ba bb bc bd be ca cb cc cd ce da db dc '
                    'dd de ea eb ec ed ee',
               'l': 'aa ab ac ad ae ba bb bc bd be ca cb cc cd ce da db dc '
                    'dd de ea eb ec ed ee'}},
   'x': 1,
   'y': 2,
   'z': 3}
""".lstrip('\n')

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

  def assertStdout(
    self, expected: str, function: collections.abc.Callable[[], None]
  ) -> None:
    with io.StringIO() as buffer:
      with contextlib.redirect_stdout(buffer):
        function()
      self.assertEqual(expected, buffer.getvalue())

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
    self.assertStdout(
      '\033]52;c;QXBhcmVjaXVtIQ==\007', lambda: volant.clip('Aparecium!')
    )

  def test_title(self) -> None:
    self.assertStdout(
      '\033]0;They call me Mister Tibbs!\007',
      lambda: volant.title('They call me Mister Tibbs!'),
    )

  def test_debug(self) -> None:
    self.assertStdout(
      '\033[34m% An elephant never forgets. \033[0m\n',
      lambda: volant.debug('An elephant never forgets.'),
    )

  def test_message(self) -> None:
    self.assertStdout(
      '\033[36m❋ The sleeping fox catches no poultry. \033[0m\n',
      lambda: volant.message('The sleeping fox catches no poultry.'),
    )

  def test_success(self) -> None:
    self.assertStdout(
      '\033[32m✓ From downtown! \033[0m\n',
      lambda: volant.success('From downtown!'),
    )

  def test_result(self) -> None:
    self.assertStdout(
      '\033[35m→ Upgrade complete. \033[0m\n',
      lambda: volant.result('Upgrade complete.'),
    )

  def test_error(self) -> None:
    self.assertStdout(
      '\033[31m! Dave, my mind is going. \033[0m\n',
      lambda: volant.error('Dave, my mind is going.'),
    )

  def test_die(self) -> None:
    with io.StringIO() as buffer:
      with contextlib.redirect_stdout(buffer):
        with self.assertRaises(SystemExit) as context:
          volant.die('He blew a fuse.')
        self.assertEqual(1, context.exception.code)
      self.assertEqual('\033[31m! He blew a fuse. \033[0m\n', buffer.getvalue())

  def test_indent(self) -> None:
    for sub, out, arg in [
      (1, '', ''),
      (2, '\n', ' '),
      (3, '\n', '\n'),
      (4, '  strip\n   me\n  down\n', 'strip \n me\r\ndown\t'),
      (5, '  Hop\n  skip\n  jump\n', 'Hop\nskip\njump'),
      (6, '  Hop\n  skip\n  jump\n  higher\n', 'Hop\nskip\njump\nhigher\n'),
      (7, '  Hop\n\n  skip\n\n  skip\n', 'Hop\n\nskip\n\nskip'),
      (8, '  None\n', None),
      (9, "  {'a': 1, 'b': 3.14, 'c': True}\n", {'a': 1, 'b': 3.14, 'c': True}),
    ]:
      with self.subTest(sub):
        self.assertStdout(out, lambda: volant.indent(arg))

  def test_dump(self) -> None:
    leaf = ' '.join(''.join(t) for t in itertools.product('abcde', repeat=2))
    branch = {'l': leaf, 'k': leaf, 'j': leaf}
    self.assertStdout(
      kDump,
      lambda: volant.dump(
        {
          'z': 3,
          'y': 2,
          'x': 1,
          'a': False,
          'b': 1502990100,
          'c': ['critter', 'fritter', 'glitter', 'jitter', 'litter', 'twitter'],
          'd': ' '.join(''.join(t) for t in itertools.product('abc', repeat=3)),
          'e': 2.718,
          'f': {'i': branch, 'h': branch, 'g': branch},
        }
      ),
    )

  def test_bullets(self) -> None:
    for sub, out, arg in [
      (1, '', []),
      (2, '  ⁃ 0\n  ⁃ 1\n  ⁃ 4\n  ⁃ 9\n', (i**2 for i in range(4))),
      (3, '  ⁃ Open\n  ⁃ Write\n  ⁃ Close\n', ['Open', 'Write', 'Close']),
      (4, '  ⁃ /\n  ⁃ /m\n', [pathlib.PurePath('/'), pathlib.PurePath('/m')]),
    ]:
      with self.subTest(sub):
        self.assertStdout(out, lambda: volant.bullets(arg))

  def test_separator(self) -> None:
    self.assertStdout(kSeparator, lambda: volant.separator())

  def test_heading(self) -> None:
    self.assertStdout(
      kHeadingShort, lambda: volant.heading('Extra! Extra! Read all about it!')
    )
    self.assertStdout(
      kHeadingLong,
      lambda: volant.heading(
        (
          'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do '
          'eiusmod tempor incididunt ut labore et dolore magna aliqua.'
        )
      ),
    )

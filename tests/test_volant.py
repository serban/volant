# SPDX-FileCopyrightText: Copyright © 2025 Serban Giuroiu <giuroiu@gmail.com>
# SPDX-License-Identifier: MIT

import collections.abc
import contextlib
import datetime
import functools
import io
import itertools
import os
import pathlib
import unittest
import unittest.mock
import zoneinfo

import pendulum
import time_machine

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

kMap = """
     a : True
    bb : 1
   ccc : two
  dddd : [3.0, {'x': 4, 'y': 5.0, 'z': 'six'}]
""".lstrip('\n')

kTimestamp = '  ──────────────────────────  2025-12-25 11:34:57  ───────────────────────────  \n'

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

kWait00Seconds = """
\033[33m⏲ Waiting 0s \033[0m
""".lstrip()

kWait01Seconds = """
\033[33m⏲ Waiting 1s \033[0m
  .                                                             1s
""".lstrip()

kWait59Seconds = """
\033[33m⏲ Waiting 59s \033[0m
  ...........................................................   59s
""".lstrip()

kWait60Seconds = """
\033[33m⏲ Waiting 1m 00s \033[0m
  ............................................................  1m 00s
""".lstrip()

kWait61Seconds = """
\033[33m⏲ Waiting 1m 01s \033[0m
  ............................................................  1m 00s
  .                                                             1m 01s
""".lstrip()

kWait99Seconds = """
\033[33m⏲ Waiting 1m 39s \033[0m
  ............................................................  1m 00s
  .......................................                       1m 39s
""".lstrip()

kWait180SecondsInterrupted = """
\033[33m⏲ Waiting 3m 00s \033[0m
  ............................................................  1m 00s
  ............................................................  2m 00s
  ...
\033[31m! Interrupted after 2m 03s \033[0m
""".lstrip()

type Duration = float | datetime.timedelta

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

  def test_get_total_seconds(self) -> None:
    bad: list[Duration] = [
      -1,
      -0.001,
      datetime.timedelta.min,
      datetime.timedelta(microseconds=-1),
    ]
    for arg in bad:
      with self.subTest(arg):
        with self.assertRaises(ValueError):
          volant._get_total_seconds(arg)

    # fmt: off
    subs: list[tuple[int, Duration]] = [
      (     0, 0),
      (     1, 1),
      (     0, 0.0),
      (     2, 2.718),
      (     3, 3.142),
      (     0, datetime.timedelta(microseconds=      1)),
      (     0, datetime.timedelta(microseconds=999_999)),
      (     0, datetime.timedelta(                      seconds= 0)),
      (     1, datetime.timedelta(                      seconds= 1)),
      (    59, datetime.timedelta(                      seconds=59)),
      (    60, datetime.timedelta(          minutes= 1            )),
      (    61, datetime.timedelta(          minutes= 1, seconds= 1)),
      ( 3_599, datetime.timedelta(          minutes=59, seconds=59)),
      ( 3_600, datetime.timedelta(hours= 1                        )),
      ( 3_601, datetime.timedelta(hours= 1, minutes= 0, seconds= 1)),
      (86_399, datetime.timedelta(hours=23, minutes=59, seconds=59)),
      (     0,  pendulum.duration(                      seconds= 0)),
      (86_399,  pendulum.duration(hours=23, minutes=59, seconds=59)),
    ]
    # fmt: on
    for out, arg in subs:
      with self.subTest(arg):
        self.assertEqual(out, volant._get_total_seconds(arg))

  def test_human_duration(self) -> None:
    bad: list[Duration] = [
      -1,
      -0.001,
      datetime.timedelta.min,
      datetime.timedelta(microseconds=-1),
    ]
    for arg in bad:
      with self.subTest(arg):
        with self.assertRaises(ValueError):
          volant.human_duration(arg)

    # fmt: off
    subs: list[tuple[str, Duration]] = [
      (              '0s',                  0.0),
      (              '2s',                  2.718),
      (              '3s',                  3.142),
      (              '0s',                  0),
      (              '1s',                  1),
      (             '59s',                 59),
      (         '59m 59s',              3_599),
      (     '23h 59m 59s',             86_399),
      (  '6d 23h 59m 59s',            604_799),
      ('377d 23h 59m 59s',         32_659_199),
      (              '0s', datetime.timedelta(microseconds=      1)),
      (              '0s', datetime.timedelta(microseconds=999_999)),
      (              '0s', datetime.timedelta(                                         seconds= 0)),
      (              '1s', datetime.timedelta(                                         seconds= 1)),
      (             '59s', datetime.timedelta(                                         seconds=59)),
      (          '1m 00s', datetime.timedelta(                             minutes= 1            )),
      (          '1m 01s', datetime.timedelta(                             minutes= 1, seconds= 1)),
      (         '59m 59s', datetime.timedelta(                             minutes=59, seconds=59)),
      (      '1h 00m 00s', datetime.timedelta(                   hours= 1                        )),
      (      '1h 00m 01s', datetime.timedelta(                   hours= 1, minutes= 0, seconds= 1)),
      (     '23h 59m 59s', datetime.timedelta(                   hours=23, minutes=59, seconds=59)),
      (  '1d 00h 00m 00s', datetime.timedelta(          days= 1                                  )),
      (  '1d 00h 00m 01s', datetime.timedelta(          days= 1, hours= 0, minutes= 0, seconds= 1)),
      (  '6d 23h 59m 59s', datetime.timedelta(          days= 6, hours=23, minutes=59, seconds=59)),
      (  '7d 00h 00m 00s', datetime.timedelta(weeks= 1, days= 0, hours= 0, minutes= 0, seconds= 0)),
      (  '7d 00h 00m 01s', datetime.timedelta(weeks= 1, days= 0, hours= 0, minutes= 0, seconds= 1)),
      ( '27d 23h 59m 59s', datetime.timedelta(weeks= 3, days= 6, hours=23, minutes=59, seconds=59)),
      ( '28d 00h 00m 00s', datetime.timedelta(weeks= 4, days= 0, hours= 0, minutes= 0, seconds= 0)),
      ('363d 23h 59m 59s', datetime.timedelta(weeks=51, days= 6, hours=23, minutes=59, seconds=59)),
      ('364d 00h 00m 00s', datetime.timedelta(weeks=52, days= 0, hours= 0, minutes= 0, seconds= 0)),
      ('377d 23h 59m 59s', datetime.timedelta(weeks=53, days= 6, hours=23, minutes=59, seconds=59)),
      (              '0s',  pendulum.duration(                                         seconds= 0)),
      ('377d 23h 59m 59s',  pendulum.duration(weeks=53, days= 6, hours=23, minutes=59, seconds=59)),
    ]
    # fmt: on
    for out, arg in subs:
      with self.subTest(arg):
        self.assertEqual(out, volant.human_duration(arg))

    # fmt: off
    for out, arg in [
      (           '0s',          0),
      (           '1s',          1),
      (          '59s',         59),
      (       '59m59s',      3_599),
      (    '23h59m59s',     86_399),
      (  '6d23h59m59s',    604_799),
      ('377d23h59m59s', 32_659_199),
    ]:
    # fmt: on
      with self.subTest(arg):
        self.assertEqual(out, volant.human_duration(arg, compact=True))

  def test_mark(self) -> None:
    for out, arg in [
      ('∅', None),
      ('\033[31m✗\033[0m', False),
      ('\033[32m✓\033[0m', True),
    ]:
      with self.subTest(arg):
        self.assertEqual(out, volant.mark(arg))

  def test_expanduser(self) -> None:
    # fmt: off
    subs: list[tuple[pathlib.Path, StrPath]]= [
      (pathlib.Path('/'),                       '/'),
      (pathlib.Path('/home/oski'),              '~'),
      (pathlib.Path('/home/oski/~'),            '~/~'),
      (pathlib.Path('/home/oski/bear'),         '~/bear'),
      (pathlib.Path('/home/oski/bear/~/oski'),  '~/bear/~/oski'),
      (pathlib.Path('/home/oski/cub'),          pathlib.PurePath('~/cub')),
    ]
    # fmt: on
    with unittest.mock.patch.dict(os.environ, {'HOME': '/home/oski'}):
      for out, arg in subs:
        with self.subTest(arg):
          self.assertEqual(out, volant.expanduser(arg))

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
    with contextlib.redirect_stdout(io.StringIO()) as buffer:
      with self.assertRaises(SystemExit) as context:
        volant.die('He blew a fuse.')
    self.assertEqual('\033[31m! He blew a fuse. \033[0m\n', buffer.getvalue())
    self.assertEqual(1, context.exception.code)

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
        self.assertStdout(out, functools.partial(volant.indent, arg))

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
        self.assertStdout(out, functools.partial(volant.bullets, arg))

  def test_map(self) -> None:
    subs: list[tuple[int, str, dict[object, object]]] = [
      (1, '', {}),
      (2, '  0 : 0\n  1 : 1\n  2 : 4\n', {i: i**2 for i in range(3)}),
      (3, '  / : /dev\n', {pathlib.PurePath('/'): pathlib.PurePath('/dev')}),
      (
        4,
        kMap,
        {
          'a': True,
          'bb': 1,
          'ccc': 'two',
          'dddd': [3.0, {'x': 4, 'y': 5.0, 'z': 'six'}],
        },
      ),
    ]
    for sub, out, arg in subs:
      with self.subTest(sub):
        self.assertStdout(out, functools.partial(volant.map, arg))

  def test_timestamp(self) -> None:
    with time_machine.travel(
      datetime.datetime(
        2025, 12, 25, 11, 34, 57, tzinfo=zoneinfo.ZoneInfo('Pacific/Kiritimati')
      )
    ):
      self.assertStdout(kTimestamp, lambda: volant.timestamp())

  def test_separator(self) -> None:
    self.assertStdout(kSeparator, lambda: volant.separator())

  def test_heading(self) -> None:
    self.assertStdout(
      kHeadingShort, lambda: volant.heading('Extra! Extra! Read all about it!')
    )
    self.assertStdout(
      kHeadingLong,
      lambda: volant.heading(
        'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do '
        'eiusmod tempor incididunt ut labore et dolore magna aliqua.'
      ),
    )

  def test_wait(self) -> None:
    bad: list[Duration] = [
      -1,
      -0.001,
      datetime.timedelta.min,
      datetime.timedelta(microseconds=-1),
    ]
    for arg in bad:
      with self.subTest(arg):
        with self.assertRaises(ValueError):
          volant.wait(arg)

    # fmt: off
    for out, arg in [
      (kWait00Seconds,  0),
      (kWait01Seconds,  1),
      (kWait59Seconds, 59),
      (kWait60Seconds, 60),
      (kWait61Seconds, 61),
      (kWait99Seconds, 99),
    ]:
    # fmt: on
      with self.subTest(arg):
        with contextlib.redirect_stdout(io.StringIO()) as buffer:
          with unittest.mock.patch('time.sleep') as sleep:
            self.assertEqual(datetime.timedelta(seconds=arg), volant.wait(arg))
            self.assertEqual(out, buffer.getvalue())
            self.assertEqual(arg, sleep.call_count)
            sleep.assert_has_calls([unittest.mock.call(1)] * arg)

    with self.subTest(180):
      with contextlib.redirect_stdout(io.StringIO()) as buffer:
        with unittest.mock.patch('time.sleep') as sleep:
          sleep.side_effect = [None] * 123 + [KeyboardInterrupt]
          self.assertEqual(datetime.timedelta(seconds=123), volant.wait(180))
          self.assertEqual(kWait180SecondsInterrupted, buffer.getvalue())
          self.assertEqual(124, sleep.call_count)
          sleep.assert_has_calls([unittest.mock.call(1)] * 124)

  def test_confirm(self) -> None:
    with contextlib.redirect_stdout(io.StringIO()) as buffer:
      with unittest.mock.patch('builtins.input', return_value='n'):
        self.assertFalse(volant.confirm('Is you is or is you ain’t my baby?'))
        self.assertEqual(
          '\033[95m■ Is you is or is you ain’t my baby? \033[33m\033[0m',
          buffer.getvalue(),
        )

    with contextlib.redirect_stdout(io.StringIO()) as buffer:
      with unittest.mock.patch('builtins.input', return_value='y'):
        self.assertTrue(volant.confirm('Are you experienced?'))
        self.assertEqual(
          '\033[95m■ Are you experienced? \033[33m\033[0m', buffer.getvalue()
        )

    with contextlib.redirect_stdout(io.StringIO()) as buffer:
      with unittest.mock.patch(
        'builtins.input',
        side_effect=['', ' ', 'y ', ' n', 'Y', 'N', 'yes', 'no', 'y'],
      ) as mock:
        self.assertTrue(volant.confirm('Are we there yet?'))
        self.assertEqual(9, mock.call_count)
        self.assertEqual(
          '\033[95m■ Are we there yet? \033[33m'
          '\033[95m■ Are we there yet? \033[33m'
          '\033[95m■ Are we there yet? \033[33m'
          '\033[95m■ Are we there yet? \033[33m'
          '\033[95m■ Are we there yet? \033[33m'
          '\033[95m■ Are we there yet? \033[33m'
          '\033[95m■ Are we there yet? \033[33m'
          '\033[95m■ Are we there yet? \033[33m'
          '\033[95m■ Are we there yet? \033[33m\033[0m',
          buffer.getvalue(),
        )

    with contextlib.redirect_stdout(io.StringIO()) as buffer:
      with unittest.mock.patch('builtins.input', return_value=''):
        self.assertFalse(volant.confirm('Should I stay?', enter=False))
        self.assertEqual(
          '\033[95m■ Should I stay? \033[33m\033[0m', buffer.getvalue()
        )

    with contextlib.redirect_stdout(io.StringIO()) as buffer:
      with unittest.mock.patch('builtins.input', return_value=''):
        self.assertTrue(volant.confirm('Should I go?', enter=True))
        self.assertEqual(
          '\033[95m■ Should I go? \033[33m\033[0m', buffer.getvalue()
        )

    with contextlib.redirect_stdout(io.StringIO()) as buffer:
      with unittest.mock.patch('builtins.input', side_effect=EOFError):
        with self.assertRaises(EOFError):
          volant.confirm('Escape?')
      self.assertEqual('\033[95m■ Escape? \033[33m\n\033[0m', buffer.getvalue())

    with contextlib.redirect_stdout(io.StringIO()) as buffer:
      with unittest.mock.patch('builtins.input', side_effect=KeyboardInterrupt):
        with self.assertRaises(KeyboardInterrupt):
          volant.confirm('Stop?')
      self.assertEqual('\033[95m■ Stop? \033[33m\n\033[0m', buffer.getvalue())

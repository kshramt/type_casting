import collections
import dataclasses
import decimal
import typing
import unittest

import type_casting


class Recording:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __eq__(self, other):
        return self.args == other.args and self.kwargs == other.kwargs


class _TypedRecord:
    def __init__(self, x: int, y: typing.Tuple[str], z: typing.Optional[int] = None):
        self.kwargs = dict(x=x, y=y, z=z)

    def __eq__(self, other):
        return self.kwargs == other.kwargs


class Tester(unittest.TestCase):
    def test_getattr(self):
        self.assertEqual(
            type_casting.cast(type_casting.GetAttr[str], "type_casting.Call"),
            type_casting.Call,
        )
        with self.assertRaises(KeyError):
            type_casting.cast(type_casting.GetAttr[str], "")
        with self.assertRaises(KeyError):
            type_casting.cast(type_casting.GetAttr[str], "no_such_module")
        with self.assertRaises(AttributeError):
            type_casting.cast(type_casting.GetAttr[str], "type_casting.no_such_attr")

    def test_nested(self):
        @dataclasses.dataclass
        class c:
            @dataclasses.dataclass
            class d:
                x: int

            x: d

        self.assertEqual(c(c.d(8)), type_casting.cast(c, dict(x=dict(x=8))))

    def test_call_with_inspect(self):
        import re

        self.assertEqual(
            _TypedRecord(x=1, y=("2",), z=3),
            type_casting.cast(
                type_casting.Call[str],
                dict(
                    fn=(f"{__name__}._TypedRecord"),
                    kwargs=dict(x=1, y=["2"], z=3),
                ),
            ),
        )
        self.assertEqual(
            _TypedRecord(x=1, y=("2",), z=None),
            type_casting.cast(
                type_casting.Call[str],
                dict(fn=f"{__name__}._TypedRecord", kwargs=dict(x=1, y=["2"])),
            ),
        )
        with self.assertRaises(type_casting.CastingError):
            type_casting.cast(
                type_casting.Call[str],
                dict(kwargs=dict(x=1, y=["2"], z=3)),
            )
        with self.assertRaises(type_casting.CastingError):
            type_casting.cast(
                type_casting.Call[str, str],
                dict(fn=f"{__name__}._TypedRecord", kwargs=dict(x=1)),
            )
        with self.assertRaises(type_casting.CastingError):
            type_casting.cast(
                type_casting.Call[str],
                dict(notfn=f"{__name__}._TypedRecord", kwargs=dict(x=1, y=["2"], z=3)),
            )
        with self.assertRaises(type_casting.CastingError):
            type_casting.cast(
                type_casting.Call[(f"{__name__}._TypedRecord",)],
                dict(
                    fn=f"{__name__}.not_TypedRecord",
                    kwargs=dict(x=1, y=["2"], z=3),
                ),
            )
        with self.assertRaises(ValueError):
            type_casting.cast(
                type_casting.Call[str],
                dict(
                    fn="re.search",
                    kwargs=dict(pattern="a", string="ab", flags=0),
                ),
            )

    def test_call(self):
        self.assertEqual(
            Recording("a", 1, a="p", b=[1, 2]),
            type_casting.cast(
                type_casting.Call[
                    str,
                    typing.Sequence[typing.Any],
                    typing.Mapping[str, typing.Any],
                ],
                dict(
                    fn=f"{__name__}.Recording",
                    args=["a", 1],
                    kwargs=dict(a="p", b=[1, 2]),
                ),
            ),
        )
        with self.assertRaises(type_casting.CastingError):
            type_casting.cast(
                type_casting.Call[
                    str,
                    str,
                    typing.Sequence[typing.Any],
                    typing.Mapping[str, typing.Any],
                ],
                dict(name="Recording", args=["a", 1], kwargs=dict(a="p", b=[1, 2])),
            )
        with self.assertRaises(type_casting.CastingError):
            type_casting.cast(
                type_casting.Call[
                    str,
                    str,
                    typing.Sequence[typing.Any],
                    typing.Mapping[str, typing.Any],
                ],
                dict(module=__name__, args=["a", 1], kwargs=dict(a="p", b=[1, 2])),
            )

    def test_default(self):
        @dataclasses.dataclass
        class c:
            x: int
            y: float = 1
            z: str = dataclasses.field(default_factory=lambda: "ok")

        self.assertEqual(
            c(x=0, y=2, z="a"), type_casting.cast(c, dict(x=0, y=2, z="a"))
        )
        self.assertEqual(c(x=0, y=2), type_casting.cast(c, dict(x=0, y=2, z="ok")))
        self.assertEqual(c(x=0, z="a"), type_casting.cast(c, dict(x=0, y=1, z="a")))
        self.assertEqual(c(x=0), type_casting.cast(c, dict(x=0, y=1, z="ok")))
        with self.assertRaises(type_casting.CastingError):
            type_casting.cast(c, dict(y=2, z="a"))
        with self.assertRaises(type_casting.CastingError):
            type_casting.cast(c, dict(x=0, y=2, z="a", w=99))
        with self.assertRaises(type_casting.CastingError):
            type_casting.cast(c, dict(x=0, w=99))

    def test_cast(self):
        @dataclasses.dataclass
        class c4:
            x: int
            y: float

        @dataclasses.dataclass
        class c3:
            x: ("yy",)
            y: typing.Mapping[str, typing.Optional[c4]]

        @dataclasses.dataclass
        class c2:
            x: ("xx",)
            y: typing.Dict[str, typing.Optional[c4]]

        @dataclasses.dataclass
        class c1:
            x: typing.List[typing.Union[c2, c3]]
            y: c4
            z: typing.Sequence[int]
            a: typing.Set[str]
            b: typing.Tuple[int, str, float]
            c: typing.Deque[int]

        x = c1(
            x=[c2(x="xx", y=dict(a=None, b=c4(x=2, y=1.0))), c3(x="yy", y=dict())],
            y=c4(x=1, y=1.3),
            z=[1],
            a=set(["a"]),
            b=(1, "two", 3.4),
            c=collections.deque([1, 2, 3]),
        )
        self.assertEqual(x, type_casting.cast(c1, dataclasses.asdict(x)))

    def test_cast_with_implicit_conversions(self):
        @dataclasses.dataclass
        class My:
            x: typing.Any

        @dataclasses.dataclass
        class c2:
            x: decimal.Decimal
            y: typing.Deque[decimal.Decimal]
            z: My

        @dataclasses.dataclass
        class c1:
            x: c2

        self.assertEqual(
            c1(
                c2(
                    decimal.Decimal("3.2113"),
                    collections.deque([decimal.Decimal("1.992")]),
                    My(9),
                )
            ),
            type_casting.cast(
                c1,
                dict(x=dict(x="3.2113", y=["1.992"], z=9)),
                implicit_conversions={My: My},
            ),
        )

    def test_cast_handles_flaot_and_complex_correctly(self):
        @dataclasses.dataclass
        class c1:
            x: int
            y: float
            z: complex

        for (x, y, z), (tx, ty, tz) in [
            ((1, 2, 3), (int, int, int)),
            ((1, 2, 3.0), (int, int, float)),
            ((1, 2.0, 3), (int, float, int)),
            ((1, 2.0, 3 + 4j), (int, float, complex)),
        ]:
            c = type_casting.cast(c1, dict(x=x, y=y, z=z))
            self.assertEqual(type(c.x), tx)
            self.assertEqual(type(c.y), ty)
            self.assertEqual(type(c.z), tz)
        with self.assertRaises(type_casting.CastingError):
            type_casting.cast(c1, dict(x=1, y=2j, z=3))
        with self.assertRaises(type_casting.CastingError):
            type_casting.cast(c1, dict(x=1.0, y=2, z=3))
        with self.assertRaises(type_casting.CastingError):
            type_casting.cast(c1, dict(x=1j, y=2, z=3))

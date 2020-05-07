import collections
import dataclasses
import decimal
import typing
import unittest

from type_casting import cast


class Tester(unittest.TestCase):
    def test_cast(self):
        @dataclasses.dataclass
        class c4:
            x: int
            y: float

        @dataclasses.dataclass
        class c3:
            x: typing.Literal["yy"]
            y: typing.Mapping[str, typing.Optional[c4]]

        @dataclasses.dataclass
        class c2:
            x: typing.Literal["xx", "zz"]
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
        self.assertEqual(x, cast(c1, dataclasses.asdict(x)))

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
            cast(
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
            c = cast(c1, dict(x=x, y=y, z=z))
            self.assertEqual(type(c.x), tx)
            self.assertEqual(type(c.y), ty)
            self.assertEqual(type(c.z), tz)
        with self.assertRaises(TypeError):
            cast(c1, dict(x=1, y=2j, z=3))
        with self.assertRaises(TypeError):
            cast(c1, dict(x=1.0, y=2, z=3))
        with self.assertRaises(TypeError):
            cast(c1, dict(x=1j, y=2, z=3))

    def test_cast_TypedDict(self):
        class td1(typing.TypedDict):
            x: int
            y: str

        class td2(typing.TypedDict, total=False):
            p: td1
            q: str

        self.assertEqual(
            dict(p=dict(x=1, y="a"), q="b"), cast(td2, dict(p=dict(x=1, y="a"), q="b"))
        )
        self.assertEqual(dict(p=dict(x=1, y="a")), cast(td2, dict(p=dict(x=1, y="a"))))
        with self.assertRaises(TypeError):
            cast(td2, dict(p=dict(x=1)))

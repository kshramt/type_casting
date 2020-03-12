import collections
import dataclasses
import decimal
import sys
import typing
import unittest


__version__ = "0.2.0"
_PY37 = sys.version_info.major == 3 and sys.version_info.minor == 7


if _PY37:

    def cast(cls, x, implicit_conversions=None):
        if implicit_conversions and (cls in implicit_conversions):
            return implicit_conversions[cls](x)
        elif dataclasses.is_dataclass(cls):
            if not isinstance(x, dict):
                raise TypeError(f"{x}: {type(x)} is not compatible with {cls}")
            fields = {f.name: f.type for f in dataclasses.fields(cls)}
            if set(fields.keys()) != set(x.keys()):
                raise TypeError(f"{x}: {type(x)} is not compatible with {cls}")
            return cls(
                **{
                    k: cast(fields[k], v, implicit_conversions=implicit_conversions)
                    for k, v in x.items()
                }
            )
        elif cls == typing.Any:
            return x
        elif cls == decimal.Decimal:
            if not isinstance(x, (str, int, float)):
                raise TypeError(f"{x}: {type(x)} is not compatible with {cls}")
            return decimal.Decimal(x)
        elif cls == complex:
            if not isinstance(x, (int, float, complex)):
                raise TypeError(f"{x}: {type(x)} is not compatible with {cls}")
            return x
        elif cls == float:
            if not isinstance(x, (int, float)):
                raise TypeError(f"{x}: {type(x)} is not compatible with {cls}")
            return x
        elif type(cls) == type:
            if not isinstance(x, cls):
                raise TypeError(f"{x}: {type(x)} is not compatible with {cls}")
            return x
        elif isinstance(cls, tuple):
            if x not in cls:
                raise TypeError(f"{x} is not compatible with {cls}")
            return x
        elif cls.__origin__ == list or cls.__origin__ == collections.abc.Sequence:
            vcls = cls.__args__[0]
            return [cast(vcls, v, implicit_conversions=implicit_conversions) for v in x]
        elif cls.__origin__ == dict or cls.__origin__ == collections.abc.Mapping:
            kcls, vcls = cls.__args__
            return {
                cast(kcls, k, implicit_conversions=implicit_conversions): cast(
                    vcls, v, implicit_conversions=implicit_conversions
                )
                for k, v in x.items()
            }
        elif cls.__origin__ in (set, collections.deque):
            vcls = cls.__args__[0]
            return cls.__origin__(
                cast(vcls, v, implicit_conversions=implicit_conversions) for v in x
            )
        elif cls.__origin__ == tuple:
            vclss = cls.__args__
            if len(vclss) != len(x):
                raise TypeError(f"{x}: {type(x)} is not compatible with {cls}")
            return tuple(
                cast(vcls, v, implicit_conversions=implicit_conversions)
                for vcls, v in zip(vclss, x)
            )
        elif cls.__origin__ == typing.Union:
            for ucls in cls.__args__:
                try:
                    return cast(ucls, x, implicit_conversions=implicit_conversions)
                except TypeError:
                    pass
            raise TypeError(f"{x}: {type(x)} is not compatible with {cls}")
        else:
            raise ValueError(f"Unsupported value {x}: {type(x)}")


else:

    def cast(cls, x, implicit_conversions=None):
        if implicit_conversions and (cls in implicit_conversions):
            return implicit_conversions[cls](x)
        elif dataclasses.is_dataclass(cls):
            if not isinstance(x, dict):
                raise TypeError(f"{x}: {type(x)} is not compatible with {cls}")
            fields = {f.name: f.type for f in dataclasses.fields(cls)}
            if set(fields.keys()) != set(x.keys()):
                raise TypeError(f"{x}: {type(x)} is not compatible with {cls}")
            return cls(
                **{
                    k: cast(fields[k], v, implicit_conversions=implicit_conversions)
                    for k, v in x.items()
                }
            )
        elif cls == typing.Any:
            return x
        elif cls == decimal.Decimal:
            if not isinstance(x, (str, int, float)):
                raise TypeError(f"{x}: {type(x)} is not compatible with {cls}")
            return decimal.Decimal(x)
        elif cls == complex:
            if not isinstance(x, (int, float, complex)):
                raise TypeError(f"{x}: {type(x)} is not compatible with {cls}")
            return x
        elif cls == float:
            if not isinstance(x, (int, float)):
                raise TypeError(f"{x}: {type(x)} is not compatible with {cls}")
            return x
        elif type(cls) == type:
            if not isinstance(x, cls):
                raise TypeError(f"{x}: {type(x)} is not compatible with {cls}")
            return x
        elif cls.__origin__ == typing.Literal:
            if x not in cls.__args__:
                raise TypeError(f"{x} is not compatible with {cls}")
            return x
        elif cls.__origin__ == list or cls.__origin__ == collections.abc.Sequence:
            vcls = cls.__args__[0]
            return [cast(vcls, v, implicit_conversions=implicit_conversions) for v in x]
        elif cls.__origin__ == dict or cls.__origin__ == collections.abc.Mapping:
            kcls, vcls = cls.__args__
            return {
                cast(kcls, k, implicit_conversions=implicit_conversions): cast(
                    vcls, v, implicit_conversions=implicit_conversions
                )
                for k, v in x.items()
            }
        elif cls.__origin__ in (set, collections.deque):
            vcls = cls.__args__[0]
            return cls.__origin__(
                cast(vcls, v, implicit_conversions=implicit_conversions) for v in x
            )
        elif cls.__origin__ == tuple:
            vclss = cls.__args__
            if len(vclss) != len(x):
                raise TypeError(f"{x}: {type(x)} is not compatible with {cls}")
            return tuple(
                cast(vcls, v, implicit_conversions=implicit_conversions)
                for vcls, v in zip(vclss, x)
            )
        elif cls.__origin__ == typing.Union:
            for ucls in cls.__args__:
                try:
                    return cast(ucls, x, implicit_conversions=implicit_conversions)
                except TypeError:
                    pass
            raise TypeError(f"{x}: {type(x)} is not compatible with {cls}")
        else:
            raise ValueError(f"Unsupported value {x}: {type(x)}")


class _Tester(unittest.TestCase):
    if _PY37:

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

    else:

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


if __name__ == "__main__":
    unittest.main()

import ast
import collections
import decimal
import inspect
import sys
from typing import Any, Generic, Tuple, TypedDict, TypeVar

_TPath = TypeVar("_TPath", bound=str)
_TArgs = TypeVar("_TArgs")
_TKwargs = TypeVar("_TKwargs")


class Error(Exception):
    pass


class CastingError(Error):
    pass


class EmptyDict(TypedDict):
    pass


EmptyTuple = Tuple[()]


class GetAttr(Generic[_TPath]):
    pass


class _CallOf:
    @staticmethod
    def __getitem__(types):
        if not isinstance(types, tuple):
            return _CallWithInspect[types]
        elif len(types) == 3:
            return _CallWithArgsAndKwargs[types]
        else:
            raise CastingError(
                f"Only Call[TPath] or GetAttr[TPath, TArgs, TKwargs] is supported: {types}"
            )


class _CallWithInspect(Generic[_TPath]):
    pass


class _CallWithArgsAndKwargs(Generic[_TPath, _TArgs, _TKwargs]):
    pass


Call = _CallOf()


def override(x, overrides: list[str]):
    for ks, v in map(_parse_override, overrides):
        _insert(x, ks, v)
    return x


def _insert(x, ks: list[str], v):
    n = len(ks)
    if n < 1:
        raise ValueError("len(ks) < 1")
    y = x
    for i in range(n - 1):
        k = ks[i]
        if k not in y:
            y[k] = dict()
        y = y[k]
    y[ks[-1]] = v
    return x


def _parse_override(s: str):
    lhs, rhs = s.split("=", 1)
    keys = lhs.split(".")
    if len(keys) < 1:
        raise ValueError(f"keys < 1: {s}")
    value = ast.literal_eval(rhs)
    return keys, value


def _analyze_Decimal(x):
    if not isinstance(x, (str, int, float)):
        raise CastingError(
            f"{x}: {type(x)} is not compatible with <class 'decimal.Decimal'>"
        )
    return decimal.Decimal(x)


def _analyze_complex(x):
    if not isinstance(x, (int, float, complex)):
        raise CastingError(f"{x}: {type(x)} is not compatible with <class 'complex'>")
    return x


def _analyze_float(x):
    if not isinstance(x, (int, float)):
        raise CastingError(f"{x}: {type(x)} is not compatible with <class 'float'>")
    return x


def _analyze_type(cls, x):
    if not isinstance(x, cls):
        raise CastingError(f"{x}: {type(x)} is not compatible with {cls}")
    return x


def _analyze_GetAttr(path, x):
    module_and_names = path(x).split(".")
    return _deep_getattr(sys.modules[module_and_names[0]], module_and_names[1:])


def _deep_getattr(x, names):
    for name in names:
        x = getattr(x, name)
    return x


def _analyze__CallWithArgsAndKwargs(cls, fn, args, kwargs, x):
    if "fn" not in x:
        raise CastingError(f'The "fn" key not found in `x` for {cls}: {x}')
    return fn(x["fn"])(*args(x.get("args", [])), **kwargs(x.get("kwargs", {})))


def _analyze_Literal(cls, candidates, x):
    if x not in candidates:
        raise CastingError(f"{x} is not compatible with {cls}")
    return x


def _analyze_set(vcls, x):
    return set(vcls(v) for v in x)


def _analyze_list(vcls, x):
    return [vcls(v) for v in x]


def _analyze_dict(kcls, vcls, x):
    return {kcls(k): vcls(v) for k, v in x.items()}


def _analyze_deque(vcls, x):
    return collections.deque(vcls(v) for v in x)


def _analyze_tuple(cls, vclss, x):
    if len(vclss) != len(x):
        raise CastingError(f"{x}: {type(x)} is not compatible with {cls}")
    return tuple(vcls(v) for vcls, v in zip(vclss, x))


def _analyze_Union(cls, uclss, x):
    for ucls in uclss:
        try:
            return ucls(x)
        except CastingError:
            pass
    raise CastingError(f"{x}: {type(x)} is not compatible with {cls}")


def _identity1(x):
    return x


def _cast_kwargs(cls, fields: dict[str, Any], required_key_set: set[str], x):
    if not isinstance(x, dict):
        raise CastingError(f"{x}: {type(x)} is not compatible with {cls}")
    x_key_set = set(x)
    if not (required_key_set.issubset(x_key_set) and x_key_set.issubset(fields)):
        raise CastingError(f"{x}: {type(x)} is not compatible with {cls}")
    kwargs = {}
    for k, v in x.items():
        kwargs[k] = fields[k](v)
    return cls(**kwargs)

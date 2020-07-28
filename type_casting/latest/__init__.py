import collections
import dataclasses
import decimal
import sys
from typing import Any, Literal, Union


class GetAttr:
    def __init__(self, args, kwargs):
        self.args = args
        self.kwargs = kwargs


def cast(cls, x, implicit_conversions=None):
    if implicit_conversions and (cls in implicit_conversions):
        return implicit_conversions[cls](x)
    elif isinstance(cls, GetAttr):
        if "module" not in x:
            raise TypeError(f'The "module" key not found in `x` for {cls}: {x}')
        if "name" not in x:
            raise TypeError(f'The "name" key not found in `x` for {cls}: {x}')
        return getattr(sys.modules[x["module"]], x["name"])(
            *cast(cls.args, x.get("args", [])), **cast(cls.kwargs, x.get("kwargs", {}))
        )
    elif dataclasses.is_dataclass(cls):
        if not isinstance(x, dict):
            raise TypeError(f"{x}: {type(x)} is not compatible with {cls}")
        required_key_set = set(
            f.name
            for f in dataclasses.fields(cls)
            if (f.default == dataclasses.MISSING)
            and (f.default_factory == dataclasses.MISSING)
        )
        x_key_set = set(x)
        fields = {f.name: f.type for f in dataclasses.fields(cls)}
        if not (
            required_key_set.issubset(x_key_set) and x_key_set.issubset(set(fields))
        ):
            raise TypeError(f"{x}: {type(x)} is not compatible with {cls}")
        return cls(
            **{
                k: cast(fields[k], v, implicit_conversions=implicit_conversions)
                for k, v in x.items()
            }
        )
    elif (
        isinstance(cls, type)
        and issubclass(cls, dict)
        and hasattr(cls, "__annotations__")
        and hasattr(cls, "__total__")
    ):
        if not isinstance(x, dict):
            raise TypeError(f"{x}: {type(x)} is not compatible with {cls}")
        fields = cls.__annotations__
        if cls.__total__:
            if set(fields) != set(x):
                raise TypeError(f"{x}: {type(x)} is not compatible with {cls}")
        else:
            if not set(x).issubset(set(fields)):
                raise TypeError(f"{x}: {type(x)} is not compatible with {cls}")
        return {
            k: cast(fields[k], v, implicit_conversions=implicit_conversions)
            for k, v in x.items()
        }
    elif cls == Any:
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
    elif isinstance(cls, type):
        if not isinstance(x, cls):
            raise TypeError(f"{x}: {type(x)} is not compatible with {cls}")
        return x
    elif cls.__origin__ == Literal:
        if x not in cls.__args__:
            raise TypeError(f"{x} is not compatible with {cls}")
        return x
    elif cls.__origin__ in (set, collections.abc.Set, collections.abc.MutableSet,):
        vcls = cls.__args__[0]
        return set(cast(vcls, v, implicit_conversions=implicit_conversions) for v in x)
    elif cls.__origin__ in (
        list,
        collections.abc.Sequence,
        collections.abc.MutableSequence,
    ):
        vcls = cls.__args__[0]
        return [cast(vcls, v, implicit_conversions=implicit_conversions) for v in x]
    elif cls.__origin__ in (
        dict,
        collections.abc.Mapping,
        collections.abc.MutableMapping,
    ):
        kcls, vcls = cls.__args__
        return {
            cast(kcls, k, implicit_conversions=implicit_conversions): cast(
                vcls, v, implicit_conversions=implicit_conversions
            )
            for k, v in x.items()
        }
    elif cls.__origin__ == collections.deque:
        vcls = cls.__args__[0]
        return collections.deque(
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
    elif cls.__origin__ == Union:
        for ucls in cls.__args__:
            try:
                return cast(ucls, x, implicit_conversions=implicit_conversions)
            except TypeError:
                pass
        raise TypeError(f"{x}: {type(x)} is not compatible with {cls}")
    else:
        raise ValueError(f"Unsupported class {cls}: {type(cls)}")

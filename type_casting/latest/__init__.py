import collections
import dataclasses
import decimal
import typing


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
            if set(fields.keys()) != set(x.keys()):
                raise TypeError(f"{x}: {type(x)} is not compatible with {cls}")
        else:
            if not set(x.keys()).issubset(set(fields.keys())):
                raise TypeError(f"{x}: {type(x)} is not compatible with {cls}")
        return {
            k: cast(fields[k], v, implicit_conversions=implicit_conversions)
            for k, v in x.items()
        }
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
        raise ValueError(f"Unsupported class {cls}: {type(cls)}")

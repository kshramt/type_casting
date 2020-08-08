from typing import Any, Dict, Set
import collections
import dataclasses
import decimal
import inspect
import sys
from typing import Any, Generic, Literal, TypeVar, Union


_TModule = TypeVar("_TModule")
_TName = TypeVar("_TName")
_TArgs = TypeVar("_TArgs")
_TKwargs = TypeVar("_TKwargs")


class Error(Exception):
    pass


class CastingError(Error):
    pass


class _GetAttrOf:
    @staticmethod
    def __getitem__(types):
        if len(types) == 2:
            return _GetAttrWithInspect[types]
        elif len(types) == 4:
            return _GetAttrWithArgsAndKwargs[types]
        else:
            raise CastingError(
                f"Only GetAttr[TModule, TName] or GetAttr[TModule, TName, TArgs, TKwargs] is supported: {types}"
            )


class _GetAttrWithInspect(Generic[_TModule, _TName]):
    pass


class _GetAttrWithArgsAndKwargs(Generic[_TModule, _TName, _TArgs, _TKwargs]):
    pass


GetAttr = _GetAttrOf()


def cast(cls, x, implicit_conversions=None):
    if implicit_conversions and (cls in implicit_conversions):
        return implicit_conversions[cls](x)
    elif dataclasses.is_dataclass(cls):
        fields = dataclasses.fields(cls)
        return _cast_kwargs(
            cls,
            x,
            implicit_conversions,
            {f.name: f.type for f in fields},
            set(
                f.name
                for f in fields
                if (f.default == dataclasses.MISSING)
                and (f.default_factory == dataclasses.MISSING)
            ),
        )
    elif (
        isinstance(cls, type)
        and issubclass(cls, dict)
        and hasattr(cls, "__annotations__")
        and hasattr(cls, "__total__")
    ):
        return _cast_kwargs(
            cls,
            x,
            implicit_conversions,
            cls.__annotations__,
            set(cls.__annotations__) if cls.__total__ else set(),
        )
    elif cls == Any:
        return x
    elif cls == decimal.Decimal:
        if not isinstance(x, (str, int, float)):
            raise CastingError(f"{x}: {type(x)} is not compatible with {cls}")
        return decimal.Decimal(x)
    elif cls == complex:
        if not isinstance(x, (int, float, complex)):
            raise CastingError(f"{x}: {type(x)} is not compatible with {cls}")
        return x
    elif cls == float:
        if not isinstance(x, (int, float)):
            raise CastingError(f"{x}: {type(x)} is not compatible with {cls}")
        return x
    elif isinstance(cls, type):
        if not isinstance(x, cls):
            raise CastingError(f"{x}: {type(x)} is not compatible with {cls}")
        return x
    elif cls.__origin__ == _GetAttrWithArgsAndKwargs:
        if "module" not in x:
            raise CastingError(f'The "module" key not found in `x` for {cls}: {x}')
        if "name" not in x:
            raise CastingError(f'The "name" key not found in `x` for {cls}: {x}')
        module, name, args, kwargs = cls.__args__
        return getattr(sys.modules[cast(module, x["module"])], cast(name, x["name"]))(
            *cast(args, x.get("args", [])), **cast(kwargs, x.get("kwargs", {}))
        )
    elif cls.__origin__ == _GetAttrWithInspect:
        if "module" not in x:
            raise CastingError(f'The "module" key not found in `x` for {cls}: {x}')
        if "name" not in x:
            raise CastingError(f'The "name" key not found in `x` for {cls}: {x}')
        module, name = cls.__args__
        fn = getattr(sys.modules[cast(module, x["module"])], cast(name, x["name"]))
        fields = {}
        required_key_set = set()
        for p in inspect.signature(fn).parameters.values():
            if p.annotation == inspect.Signature.empty:
                parameters = tuple(
                    dict(name=p.name, annotation=p.annotation, default=p.default)
                    for p in inspect.signature(fn).parameters.values()
                )
                raise ValueError(
                    f"Unable to get the type annotation of {p.name} for {fn}{parameters}. Please use `GetAttr[module, name, args_type, kwargs_type]` instead."
                )
            fields[p.name] = p.annotation
            if p.default == inspect.Signature.empty:
                required_key_set.add(p.name)
        return _cast_kwargs(
            fn, x.get("kwargs", {}), implicit_conversions, fields, required_key_set
        )
    elif cls.__origin__ == Literal:
        if x not in cls.__args__:
            raise CastingError(f"{x} is not compatible with {cls}")
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
            raise CastingError(f"{x}: {type(x)} is not compatible with {cls}")
        return tuple(
            cast(vcls, v, implicit_conversions=implicit_conversions)
            for vcls, v in zip(vclss, x)
        )
    elif cls.__origin__ == Union:
        for ucls in cls.__args__:
            try:
                return cast(ucls, x, implicit_conversions=implicit_conversions)
            except CastingError:
                pass
        raise CastingError(f"{x}: {type(x)} is not compatible with {cls}")
    else:
        raise ValueError(f"Unsupported class {cls}: {type(cls)}")


def _cast_kwargs(
    cls, x, implicit_conversions, fields: Dict[str, Any], required_key_set: Set[str]
):
    if not isinstance(x, dict):
        raise CastingError(f"{x}: {type(x)} is not compatible with {cls}")
    x_key_set = set(x)
    if not (required_key_set.issubset(x_key_set) and x_key_set.issubset(set(fields))):
        raise CastingError(f"{x}: {type(x)} is not compatible with {cls}")
    return cls(
        **{
            k: cast(fields[k], v, implicit_conversions=implicit_conversions)
            for k, v in x.items()
        }
    )

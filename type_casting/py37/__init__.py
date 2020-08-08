from typing import Any, Dict, Set
import collections
import dataclasses
import decimal
import functools
import inspect
import sys
from typing import Any, Generic, TypeVar, Union


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
    return _analyze(cls, implicit_conversions)(x)


def _analyze(cls, implicit_conversions):
    if implicit_conversions and (cls in implicit_conversions):
        return implicit_conversions[cls]
    elif dataclasses.is_dataclass(cls):
        fields = dataclasses.fields(cls)
        return functools.partial(
            _cast_kwargs,
            cls,
            implicit_conversions,
            {f.name: _analyze(f.type, implicit_conversions) for f in fields},
            set(
                f.name
                for f in fields
                if (f.default == dataclasses.MISSING)
                and (f.default_factory == dataclasses.MISSING)
            ),
        )
    elif cls == Any:
        return _identity1
    elif cls == decimal.Decimal:
        return _analyze_Decimal
    elif cls == complex:
        return _analyze_complex
    elif cls == float:
        return _analyze_float
    elif isinstance(cls, type):
        return functools.partial(_analyze_type, cls)
    elif isinstance(cls, tuple):
        return functools.partial(_analyze_Literal, cls)
    elif cls.__origin__ == _GetAttrWithArgsAndKwargs:
        module, name, args, kwargs = cls.__args__
        return functools.partial(
            _analyze__GetAttrWithArgsAndKwargs,
            str(cls),
            _analyze(module, implicit_conversions),
            _analyze(name, implicit_conversions),
            _analyze(args, implicit_conversions),
            _analyze(kwargs, implicit_conversions),
        )
    elif cls.__origin__ == _GetAttrWithInspect:
        module, name = cls.__args__
        return functools.partial(
            _analyze__GetAttrWithInspect,
            cls,
            implicit_conversions,
            _analyze(module, implicit_conversions),
            _analyze(name, implicit_conversions),
        )
    elif cls.__origin__ in (set, collections.abc.Set, collections.abc.MutableSet,):
        return functools.partial(
            _analyze_set, _analyze(cls.__args__[0], implicit_conversions)
        )
    elif cls.__origin__ in (
        list,
        collections.abc.Sequence,
        collections.abc.MutableSequence,
        collections.abc.Iterable,
        collections.abc.Iterator,
    ):
        return functools.partial(
            _analyze_list, _analyze(cls.__args__[0], implicit_conversions)
        )
    elif cls.__origin__ in (
        dict,
        collections.abc.Mapping,
        collections.abc.MutableMapping,
    ):
        return functools.partial(
            _analyze_dict,
            _analyze(cls.__args__[0], implicit_conversions),
            _analyze(cls.__args__[1], implicit_conversions),
        )
    elif cls.__origin__ == collections.deque:
        return functools.partial(
            _analyze_deque, _analyze(cls.__args__[0], implicit_conversions)
        )
    elif cls.__origin__ == tuple:
        return functools.partial(
            _analyze_tuple,
            str(cls),
            tuple(_analyze(vcls, implicit_conversions) for vcls in cls.__args__),
        )
    elif cls.__origin__ == Union:
        return functools.partial(
            _analyze_Union,
            str(cls),
            list(_analyze(ucls, implicit_conversions) for ucls in cls.__args__),
        )
    else:
        raise ValueError(f"Unsupported class {cls}: {type(cls)}")


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


def _analyze__GetAttrWithArgsAndKwargs(cls, module, name, args, kwargs, x):
    if "module" not in x:
        raise CastingError(f'The "module" key not found in `x` for {cls}: {x}')
    if "name" not in x:
        raise CastingError(f'The "name" key not found in `x` for {cls}: {x}')
    return getattr(sys.modules[module(x["module"])], name(x["name"]))(
        *args(x.get("args", [])), **kwargs(x.get("kwargs", {}))
    )


def _analyze__GetAttrWithInspect(cls, implicit_conversions, module, name, x):
    if "module" not in x:
        raise CastingError(f'The "module" key not found in `x` for {cls}: {x}')
    if "name" not in x:
        raise CastingError(f'The "name" key not found in `x` for {cls}: {x}')
    fn = getattr(sys.modules[module(x["module"])], name(x["name"]))
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
        fields[p.name] = _analyze(p.annotation, implicit_conversions)
        if p.default == inspect.Signature.empty:
            required_key_set.add(p.name)
    return _cast_kwargs(
        fn, implicit_conversions, fields, required_key_set, x.get("kwargs", {})
    )


def _analyze_Literal(cls, x):
    if x not in cls:
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


def _cast_kwargs(
    cls, implicit_conversions, fields: Dict[str, Any], required_key_set: Set[str], x
):
    if not isinstance(x, dict):
        raise CastingError(f"{x}: {type(x)} is not compatible with {cls}")
    x_key_set = set(x)
    if not (required_key_set.issubset(x_key_set) and x_key_set.issubset(fields)):
        raise CastingError(f"{x}: {type(x)} is not compatible with {cls}")
    kwargs = {}
    for k, v in x.items():
        kwargs[k] = fields[k](v)
    return cls(**kwargs)

import sys

__version__ = "0.14.0"


if sys.version_info.major == 3 and sys.version_info.minor == 7:
    from .py37 import Call, CastingError, EmptyTuple, GetAttr, cast
elif sys.version_info.major == 3 and sys.version_info.minor == 8:
    from .py38 import Call, CastingError, EmptyDict, EmptyTuple, GetAttr, cast, override
elif sys.version_info.major == 3 and sys.version_info.minor == 9:
    from .py39 import Call, CastingError, EmptyDict, EmptyTuple, GetAttr, cast, override
else:
    from .latest import (
        Call,
        CastingError,
        EmptyDict,
        EmptyTuple,
        GetAttr,
        cast,
        override,
    )

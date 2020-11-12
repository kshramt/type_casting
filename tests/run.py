#!/usr/bin/python

import sys
import unittest

if sys.version_info.major == 3 and sys.version_info.minor == 7:
    import py37 as test
elif sys.version_info.major == 3 and sys.version_info.minor == 8:
    import py38 as test
else:  # sys.version_info.major == 3 and sys.version_info.minor == 9
    import latest as test


if __name__ == "__main__":
    unittest.main(test)
